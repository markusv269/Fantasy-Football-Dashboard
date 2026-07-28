"""Gezielte Datenbank-Synchronisierung für einzelne Datentypen.

Dieses Skript erweitert die vorhandene wöchentliche Synchronisierung
(:mod:`app.scripts.weekly_sync`) um gezielte, kombinierbare Modi, damit
GitHub-Actions- oder Cron-Jobs nur die Datenbereiche aktualisieren, die
sich tatsächlich häufig ändern. Es wird ausschließlich die echte
Sleeper- und Supabase-API verwendet — keine Mock-Daten.

Modi (Kommaliste über ``--modes``):

    metadata      leagues (Name, Saison, roster_positions, previous_league_id, avatar)
    managers      managers (User + Roster-Owner)
    rosters       rosters (pro Woche; Spieler/Starter/Reserve/Taxi)
    matchups      matchup_week_stats (pro Woche)
    drafts        drafts (Metadaten; on_conflict draft_id)
    draft_picks   draft_picks (delete+insert pro Draft)
    nfl_players   nfl_players (kompletter Sleeper-Katalog, ~11k Zeilen)
    all           alle Modi oben

Batch-Optionen für ligaspezifische Modi:
    --league-id ID  (mehrfach), --offset N, --start N, --end N, --limit N

Wochenoptionen (nur für matchups / rosters):
    --week-mode single|range|all|current
    --week N        (single)
    --week-start N  (range)
    --week-end N    (range)

Weitere Flags:
    --dry-run       Loggen, was passieren würde — keine DB-Schreibvorgänge.
    --verbose-http  HTTP-INFO-Logs von httpx/postgrest wieder aktivieren.

Beispiele:
    # Nur Matchups + Roster für die aktuelle NFL-Woche synchronisieren
    python -m app.scripts.targeted_sync --modes matchups,rosters

    # Alle Wochen 0..18 für eine einzelne Liga
    python -m app.scripts.targeted_sync --modes matchups,rosters \\
        --league-id 1313986550769422336 --week-mode all

    # Nur Draft-Metadaten + Picks synchronisieren (Draft-Saison)
    python -m app.scripts.targeted_sync --modes drafts,draft_picks

    # Kompletten NFL-Spieler-Katalog aktualisieren
    python -m app.scripts.targeted_sync --modes nfl_players

    # Trockenlauf für Manager-Sync eines Batches
    python -m app.scripts.targeted_sync --modes managers \\
        --offset 100 --limit 50 --dry-run

Alle Operationen sind idempotent (upsert mit definierten on_conflict-Keys)
und können jederzeit erneut ausgeführt werden.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone

import dotenv

dotenv.load_dotenv()

from app.sleeper_api import (
    get_all_nfl_players,
    get_draft_picks,
    get_league,
    get_league_drafts,
    get_league_users,
    get_matchups,
    get_nfl_state,
    get_rosters,
)
from app.supabase_client import get_supabase_client


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
for _noisy in (
    "httpx",
    "httpcore",
    "httpcore.http11",
    "httpcore.connection",
    "hpack",
    "urllib3",
    "urllib3.connectionpool",
    "postgrest",
    "postgrest._async.request_builder",
    "postgrest._sync.request_builder",
    "supabase",
    "gotrue",
    "storage3",
    "realtime",
):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

log = logging.getLogger("targeted_sync")

ALL_MODES: tuple[str, ...] = (
    "metadata",
    "managers",
    "rosters",
    "matchups",
    "drafts",
    "draft_picks",
    "nfl_players",
)
LEAGUE_SCOPED_MODES: frozenset[str] = frozenset(
    {"metadata", "managers", "rosters", "matchups", "drafts", "draft_picks"}
)
WEEK_SCOPED_MODES: frozenset[str] = frozenset({"rosters", "matchups"})


def _print(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Helpers shared with weekly_sync — duplicated here so this script can run
# stand-alone without relying on private internals of weekly_sync.
# ---------------------------------------------------------------------------


def _current_nfl_week() -> int:
    try:
        state = get_nfl_state() or {}
        w = int(state.get("week") or 0)
        return max(w, 1)
    except Exception as e:
        logging.exception(f"NFL-Woche konnte nicht ermittelt werden: {e}")
        return 1


def _resolve_weeks(mode: str, single: int, start: int, end: int) -> list[int]:
    if mode == "single":
        return [max(0, min(18, int(single)))]
    if mode == "range":
        lo = max(0, min(18, int(min(start, end))))
        hi = max(0, min(18, int(max(start, end))))
        return list(range(lo, hi + 1))
    if mode == "all":
        return list(range(0, 19))
    # current
    return [_current_nfl_week()]


def _load_leagues(
    client,
    league_ids: list[str] | None,
    offset: int,
    start: int | None,
    end: int | None,
    limit: int | None,
) -> list[dict]:
    """Return league rows honouring the batch window flags."""
    try:
        if league_ids:
            res = (
                client.table("leagues")
                .select("league_id,league_name,league_season")
                .in_("league_id", league_ids)
                .execute()
            )
            return res.data if res and res.data else []
        res = (
            client.table("leagues")
            .select("league_id,league_name,league_season")
            .order("league_season", desc=True)
            .execute()
        )
        rows = res.data if res and res.data else []
    except Exception as e:
        logging.exception(f"Ligen konnten nicht geladen werden: {e}")
        return []

    effective_offset = 0
    if start is not None and start > 0:
        effective_offset = start - 1
    elif offset and offset > 0:
        effective_offset = offset

    if effective_offset:
        rows = rows[effective_offset:]

    if end is not None and end > 0:
        end_zero = end - effective_offset
        if end_zero < 0:
            return []
        rows = rows[:end_zero]

    if limit and limit > 0:
        rows = rows[:limit]

    return rows


# ---------------------------------------------------------------------------
# Per-mode sync functions. All are idempotent and respect ``dry_run``.
# ---------------------------------------------------------------------------


def _sync_metadata(client, league_id: str, dry_run: bool) -> int:
    data = get_league(league_id)
    if not data:
        raise RuntimeError(f"Sleeper API: Liga {league_id} nicht gefunden.")
    season_raw = data.get("season", "")
    season_val = int(season_raw) if str(season_raw).isdigit() else season_raw
    existing_type = ""
    try:
        existing = (
            client.table("leagues")
            .select("league_type")
            .eq("league_id", str(league_id))
            .limit(1)
            .execute()
        )
        if existing and existing.data:
            existing_type = str(existing.data[0].get("league_type") or "")
    except Exception as e:
        logging.exception(f"league_type-Lookup {league_id} fehlgeschlagen: {e}")
    safe_type = existing_type or "dynasty"
    prev_raw = data.get("previous_league_id")
    prev_val = (
        str(prev_raw).strip() if prev_raw not in (None, "", "null") else None
    )
    avatar_raw = data.get("avatar")
    avatar_val = (
        str(avatar_raw).strip()
        if avatar_raw not in (None, "", "null")
        else None
    )
    payload = {
        "league_id": str(league_id),
        "league_name": data.get("name", "") or f"Liga {league_id}",
        "league_season": season_val,
        "league_type": safe_type,
        "roster_positions": data.get("roster_positions") or [],
        "previous_league_id": prev_val,
        "avatar": avatar_val,
    }
    if dry_run:
        return 1
    try:
        client.table("leagues").upsert(
            payload, on_conflict="league_id"
        ).execute()
    except Exception as e:
        msg = str(e)
        if "avatar" in msg and ("column" in msg or "PGRST204" in msg):
            logging.exception(
                f"metadata upsert mit avatar fehlgeschlagen, retry ohne: {e}"
            )
            payload.pop("avatar", None)
            client.table("leagues").upsert(
                payload, on_conflict="league_id"
            ).execute()
        else:
            raise
    return 1


def _sync_managers(client, league_id: str, dry_run: bool) -> int:
    users = get_league_users(league_id) or []
    rosters = get_rosters(league_id) or []
    user_map = {u.get("user_id"): u for u in users}
    rows = []
    for r in rosters:
        owner_id = r.get("owner_id")
        u = user_map.get(owner_id, {}) or {}
        meta = u.get("metadata", {}) or {}
        rows.append(
            {
                "league_id": str(league_id),
                "roster_id": int(r.get("roster_id") or 0),
                "user_id": str(owner_id or ""),
                "display_name": u.get("display_name", "") or "",
                "team_name": meta.get("team_name")
                or u.get("display_name", "")
                or "",
            }
        )
    if rows and not dry_run:
        client.table("managers").upsert(
            rows, on_conflict="league_id,roster_id"
        ).execute()
    return len(rows)


def _sync_rosters(client, league_id: str, week: int, dry_run: bool) -> int:
    rosters = get_rosters(league_id) or []
    rows = []
    for r in rosters:
        settings = r.get("settings", {}) or {}
        fpts = (
            float(settings.get("fpts", 0) or 0)
            + float(settings.get("fpts_decimal", 0) or 0) / 100.0
        )
        fpts_ag = (
            float(settings.get("fpts_against", 0) or 0)
            + float(settings.get("fpts_against_decimal", 0) or 0) / 100.0
        )
        rows.append(
            {
                "league_id": str(league_id),
                "roster_id": int(r.get("roster_id") or 0),
                "week": int(week),
                "wins": int(settings.get("wins") or 0),
                "losses": int(settings.get("losses") or 0),
                "ties": int(settings.get("ties") or 0),
                "fpts_for": round(fpts, 2),
                "fpts_against": round(fpts_ag, 2),
                "json_data": {
                    "players": r.get("players") or [],
                    "starters": r.get("starters") or [],
                    "reserve": r.get("reserve") or [],
                    "taxi": r.get("taxi") or [],
                },
            }
        )
    if rows and not dry_run:
        client.table("rosters").upsert(
            rows, on_conflict="league_id,roster_id,week"
        ).execute()
    return len(rows)


def _sync_matchups(client, league_id: str, week: int, dry_run: bool) -> int:
    try:
        data = get_matchups(league_id, week)
    except Exception as e:
        logging.exception(
            f"Matchups {league_id} W{week} konnten nicht geladen werden: {e}"
        )
        return 0
    if not data:
        return 0
    rows = []
    for m in data:
        pts = m.get("points")
        try:
            pts_val = float(pts) if pts is not None else 0.0
        except Exception:
            logging.exception("Ungültiger points-Wert im Matchup")
            pts_val = 0.0
        rows.append(
            {
                "league_id": str(league_id),
                "week": int(week),
                "matchup_id": int(m.get("matchup_id") or 0),
                "roster_id": int(m.get("roster_id") or 0),
                "points": round(pts_val, 2),
            }
        )
    if rows and not dry_run:
        try:
            client.table("matchup_week_stats").upsert(
                rows, on_conflict="league_id,week,roster_id"
            ).execute()
        except Exception as e:
            logging.exception(
                f"matchup upsert {league_id} W{week} fehlgeschlagen: {e}"
            )
            return 0
    return len(rows)


def _sync_drafts(client, league_id: str, dry_run: bool) -> int:
    try:
        drafts = get_league_drafts(league_id) or []
    except Exception as e:
        logging.exception(f"league drafts {league_id} fetch: {e}")
        return 0
    if not drafts:
        return 0
    rows = []
    dtype_map = {"snake": "0", "linear": "1", "auction": "2"}
    for d in drafts:
        draft_id = str(d.get("draft_id") or "")
        if not draft_id:
            continue
        start_time_iso = ""
        start = d.get("start_time")
        if start:
            try:
                start_time_iso = datetime.fromtimestamp(
                    int(start) / 1000
                ).isoformat()
            except Exception:
                logging.exception("Ungültiger draft start_time-Wert")
                start_time_iso = ""
        dtype_raw = d.get("type", "")
        dtype_val = dtype_map.get(str(dtype_raw).lower(), dtype_raw)
        rows.append(
            {
                "draft_id": draft_id,
                "league_id": str(league_id),
                "season": str(d.get("season") or ""),
                "draft_type": dtype_val,
                "status": str(d.get("status") or ""),
                "start_time": start_time_iso,
            }
        )
    if not rows:
        return 0
    if dry_run:
        return len(rows)
    try:
        client.table("drafts").upsert(rows, on_conflict="draft_id").execute()
    except Exception as e:
        logging.exception(f"drafts upsert {league_id} fehlgeschlagen: {e}")
        return 0
    return len(rows)


def _sync_draft_picks_for_league(client, league_id: str, dry_run: bool) -> int:
    """Refresh draft_picks for every draft attached to ``league_id``.

    Uses the well-established delete+insert pattern per draft (same as the
    admin bulk-import) so the target table stays consistent even if Sleeper
    removes picks (e.g. after a pick reversal).
    """
    try:
        drafts_res = (
            client.table("drafts")
            .select("draft_id")
            .eq("league_id", str(league_id))
            .execute()
        )
        drafts = drafts_res.data if drafts_res and drafts_res.data else []
    except Exception as e:
        logging.exception(f"drafts lookup {league_id} fehlgeschlagen: {e}")
        return 0

    total = 0
    for d in drafts:
        did = str(d.get("draft_id") or "")
        if not did:
            continue
        try:
            picks = get_draft_picks(did) or []
        except Exception as e:
            logging.exception(f"draft picks {did} fetch: {e}")
            continue
        if not dry_run:
            try:
                client.table("draft_picks").delete().eq(
                    "draft_id", did
                ).execute()
            except Exception as e:
                logging.exception(f"draft_picks delete {did}: {e}")
                continue
        if not picks:
            continue
        rows = []
        for p in picks:
            rows.append(
                {
                    "draft_id": did,
                    "round": int(p.get("round") or 0),
                    "pick_no": int(p.get("pick_no") or 0),
                    "roster_id": int(p.get("roster_id") or 0)
                    if p.get("roster_id") is not None
                    else None,
                    "player_id": str(p.get("player_id") or ""),
                    "metadata": p.get("metadata") or {},
                    "json_data": p,
                }
            )
        if not dry_run:
            try:
                batch = 500
                for i in range(0, len(rows), batch):
                    client.table("draft_picks").insert(
                        rows[i : i + batch]
                    ).execute()
            except Exception as e:
                logging.exception(f"draft_picks insert {did}: {e}")
                continue
        total += len(rows)
    return total


def _sync_nfl_players(client, dry_run: bool) -> int:
    """Refresh the ``nfl_players`` catalog from Sleeper (~11k rows).

    This mode is league-independent and only needs to run occasionally
    (e.g. once per week).
    """
    data = get_all_nfl_players()
    if not data:
        raise RuntimeError("Sleeper-API lieferte keine Spielerdaten.")
    now_iso = datetime.now(timezone.utc).isoformat()
    rows = []
    for pid, p in data.items():
        if not pid:
            continue
        first = p.get("first_name") or ""
        last = p.get("last_name") or ""
        full = (p.get("full_name") or f"{first} {last}").strip()
        rows.append(
            {
                "player_id": str(pid),
                "name": full or f"Player {pid}",
                "team": p.get("team"),
                "position": p.get("position"),
                "json_data": p,
                "updated_at": now_iso,
            }
        )
    if dry_run:
        return len(rows)
    batch = 500
    for i in range(0, len(rows), batch):
        chunk = rows[i : i + batch]
        try:
            client.table("nfl_players").upsert(
                chunk, on_conflict="player_id"
            ).execute()
        except Exception as e:
            logging.exception(f"nfl_players batch {i} fehlgeschlagen: {e}")
    return len(rows)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _parse_modes(raw: str) -> list[str]:
    if not raw:
        return list(ALL_MODES)
    tokens = [t.strip().lower() for t in raw.split(",") if t.strip()]
    if not tokens:
        return list(ALL_MODES)
    if "all" in tokens:
        return list(ALL_MODES)
    invalid = [t for t in tokens if t not in ALL_MODES]
    if invalid:
        raise SystemExit(
            f"Unbekannte Modi: {', '.join(invalid)}. "
            f"Erlaubt: {', '.join(ALL_MODES)} oder all."
        )
    # Preserve deterministic order matching ALL_MODES.
    return [m for m in ALL_MODES if m in tokens]


def run(
    modes: list[str],
    league_ids: list[str] | None,
    offset: int,
    start: int | None,
    end: int | None,
    limit: int | None,
    week_mode: str,
    week_single: int,
    week_start: int,
    week_end: int,
    dry_run: bool,
) -> int:
    """Execute the requested modes and return a process exit code."""
    _print("=" * 70)
    _print("Stoned Lack — gezielte Datenbank-Synchronisierung")
    _print("=" * 70)
    _print(f"Modi:      {', '.join(modes)}")
    if dry_run:
        _print(
            "Modus:     DRY-RUN — es werden KEINE DB-Schreibvorgänge ausgeführt."
        )

    client = get_supabase_client()
    if client is None:
        _print(
            "FEHLER: Supabase-Credentials fehlen. Bitte SUPABASE_URL und "
            "SUPABASE_KEY setzen (z. B. .env im Projekt-Root)."
        )
        return 2

    league_modes = [m for m in modes if m in LEAGUE_SCOPED_MODES]
    needs_leagues = bool(league_modes)
    leagues: list[dict] = []
    if needs_leagues:
        leagues = _load_leagues(client, league_ids, offset, start, end, limit)
        _print(f"Ligen im Batch: {len(leagues)}")
        if not leagues:
            _print("Keine Ligen zu verarbeiten. Abbruch.")
            return 0

    weeks: list[int] = []
    if any(m in WEEK_SCOPED_MODES for m in modes):
        weeks = _resolve_weeks(week_mode, week_single, week_start, week_end)
        _print(
            f"Wochen:    {weeks[0]}"
            if len(weeks) == 1
            else f"Wochen:    {weeks[0]}..{weeks[-1]} ({len(weeks)} Wochen)"
        )

    totals: dict[str, int] = {m: 0 for m in modes}
    failures: list[tuple[str, str, str]] = []
    started = time.time()

    # nfl_players is league-independent — handle first if requested.
    if "nfl_players" in modes:
        _print("\n[nfl_players] Lade Sleeper NFL-Spielerkatalog…")
        try:
            n = _sync_nfl_players(client, dry_run)
            totals["nfl_players"] = n
            _print(f"[nfl_players] {n} Zeilen synchronisiert.")
        except Exception as e:
            failures.append(("nfl_players", "-", str(e)))
            logging.exception(f"nfl_players fehlgeschlagen: {e}")
            _print(f"[nfl_players] FEHLER: {e}")

    # League-scoped modes.
    for i, lg in enumerate(leagues, start=1):
        lid = str(lg.get("league_id", "")).strip()
        if not lid:
            continue
        lname = str(lg.get("league_name", "") or f"Liga {lid}")
        _print(f"\n[{i}/{len(leagues)}] {lid} — {lname}")

        if "metadata" in modes:
            try:
                n = _sync_metadata(client, lid, dry_run)
                totals["metadata"] += n
                _print(f"  ✓ metadata: aktualisiert")
            except Exception as e:
                failures.append(("metadata", lid, str(e)))
                logging.exception(f"metadata {lid} fehlgeschlagen: {e}")
                _print(f"  ✗ metadata: {e}")

        if "managers" in modes:
            try:
                n = _sync_managers(client, lid, dry_run)
                totals["managers"] += n
                _print(f"  ✓ managers: {n} Manager")
            except Exception as e:
                failures.append(("managers", lid, str(e)))
                logging.exception(f"managers {lid} fehlgeschlagen: {e}")
                _print(f"  ✗ managers: {e}")

        if "rosters" in modes:
            try:
                sub = 0
                for w in weeks:
                    sub += _sync_rosters(client, lid, w, dry_run)
                totals["rosters"] += sub
                _print(f"  ✓ rosters: {sub} Zeilen über {len(weeks)} Woche(n)")
            except Exception as e:
                failures.append(("rosters", lid, str(e)))
                logging.exception(f"rosters {lid} fehlgeschlagen: {e}")
                _print(f"  ✗ rosters: {e}")

        if "matchups" in modes:
            try:
                sub = 0
                for w in weeks:
                    sub += _sync_matchups(client, lid, w, dry_run)
                totals["matchups"] += sub
                _print(
                    f"  ✓ matchups: {sub} Einträge über {len(weeks)} Woche(n)"
                )
            except Exception as e:
                failures.append(("matchups", lid, str(e)))
                logging.exception(f"matchups {lid} fehlgeschlagen: {e}")
                _print(f"  ✗ matchups: {e}")

        if "drafts" in modes:
            try:
                n = _sync_drafts(client, lid, dry_run)
                totals["drafts"] += n
                _print(f"  ✓ drafts: {n} Draft(s)")
            except Exception as e:
                failures.append(("drafts", lid, str(e)))
                logging.exception(f"drafts {lid} fehlgeschlagen: {e}")
                _print(f"  ✗ drafts: {e}")

        if "draft_picks" in modes:
            try:
                n = _sync_draft_picks_for_league(client, lid, dry_run)
                totals["draft_picks"] += n
                _print(f"  ✓ draft_picks: {n} Picks")
            except Exception as e:
                failures.append(("draft_picks", lid, str(e)))
                logging.exception(f"draft_picks {lid} fehlgeschlagen: {e}")
                _print(f"  ✗ draft_picks: {e}")

    elapsed = time.time() - started
    _print("\n" + "=" * 70)
    _print("Zusammenfassung")
    _print("=" * 70)
    for m in modes:
        _print(f"  {m:12s}  {totals.get(m, 0)}")
    _print(f"Ligen im Batch: {len(leagues)}")
    _print(f"Fehler:         {len(failures)}")
    _print(f"Dauer:          {elapsed:.1f}s")
    _print(f"Beendet um:     {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    if failures:
        _print("\nFehlerdetails (Stichprobe):")
        for mode, lid, err in failures[:15]:
            _print(f"  - [{mode}] {lid}: {err}")

    return 0 if not failures else 1


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Gezielte Synchronisierung einzelner DB-Tabellen aus Sleeper. "
            "Unterstützt Modi, Batch-Fenster, Wochenbereiche und Dry-Run."
        )
    )
    p.add_argument(
        "--modes",
        type=str,
        default="all",
        help=(
            "Kommaliste der Sync-Modi. Erlaubt: "
            + ", ".join(ALL_MODES)
            + " oder 'all'. Standard: all."
        ),
    )
    p.add_argument(
        "--league-id",
        action="append",
        default=None,
        help="Nur diese Liga(n) synchronisieren. Mehrfach nutzbar. "
        "Deaktiviert --offset/--start/--end/--limit.",
    )
    p.add_argument(
        "--offset",
        type=int,
        default=0,
        help="0-basiert: Anzahl der Ligen, die am Anfang übersprungen werden.",
    )
    p.add_argument(
        "--start",
        type=int,
        default=None,
        help="1-basierte Startposition (inklusive). Überschreibt --offset.",
    )
    p.add_argument(
        "--end",
        type=int,
        default=None,
        help="1-basierte Endposition (inklusive).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximal N Ligen im Batch.",
    )
    p.add_argument(
        "--week-mode",
        choices=("single", "range", "all", "current"),
        default="current",
        help=(
            "Wochenbereich für matchups/rosters. "
            "current=aktuelle NFL-Woche (Default), single=eine Woche, "
            "range=--week-start..--week-end, all=0..18."
        ),
    )
    p.add_argument(
        "--week",
        type=int,
        default=1,
        help="Woche für --week-mode single (0..18).",
    )
    p.add_argument(
        "--week-start",
        type=int,
        default=1,
        help="Startwoche für --week-mode range (0..18).",
    )
    p.add_argument(
        "--week-end",
        type=int,
        default=18,
        help="Endwoche für --week-mode range (0..18).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, was getan würde — keine DB-Schreibvorgänge.",
    )
    p.add_argument(
        "--verbose-http",
        action="store_true",
        help="HTTP-INFO-Logs von httpx/postgrest wieder aktivieren.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.verbose_http:
        for _noisy in (
            "httpx",
            "httpcore",
            "urllib3",
            "postgrest",
            "supabase",
        ):
            logging.getLogger(_noisy).setLevel(logging.INFO)
    modes = _parse_modes(args.modes)
    return run(
        modes=modes,
        league_ids=args.league_id,
        offset=args.offset,
        start=args.start,
        end=args.end,
        limit=args.limit,
        week_mode=args.week_mode,
        week_single=args.week,
        week_start=args.week_start,
        week_end=args.week_end,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
