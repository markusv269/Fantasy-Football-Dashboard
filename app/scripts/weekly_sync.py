"""Wöchentliche Synchronisierung aller Ligen aus Supabase mit Sleeper-Daten.

Nutzung:
    python -m app.scripts.weekly_sync
    python -m app.scripts.weekly_sync --limit 10
    python -m app.scripts.weekly_sync --league-id 123456789
    python -m app.scripts.weekly_sync --skip-matchups

Voraussetzungen:
    - Umgebungsvariablen SUPABASE_URL und SUPABASE_KEY müssen gesetzt sein
      (z.B. via .env-Datei im Projekt-Root).
    - Nutzt die echten Sleeper- und Supabase-APIs, keine Mock-Daten.

Das Skript ist idempotent und kann jederzeit erneut ausgeführt werden.
Einzelne Liga-Fehler werden protokolliert; die Verarbeitung der übrigen
Ligen wird fortgesetzt.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime

import dotenv

dotenv.load_dotenv()

from app.sleeper_api import (
    get_draft,
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
log = logging.getLogger("weekly_sync")


def _print(msg: str) -> None:
    print(msg, flush=True)


def _current_week() -> int:
    try:
        state = get_nfl_state() or {}
        w = int(state.get("week") or 0)
        return max(w, 1)
    except Exception as e:
        logging.exception(f"Failed to fetch NFL week: {e}")
        return 1


def _sync_league_metadata(client, league_id: str) -> tuple[dict, str]:
    """Update leagues row metadata while preserving league_type."""
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
        logging.exception(f"League_type lookup failed for {league_id}: {e}")
    safe_type = existing_type or "dynasty"
    payload = {
        "league_id": str(league_id),
        "league_name": data.get("name", "") or f"Liga {league_id}",
        "league_season": season_val,
        "league_type": safe_type,
        "roster_positions": data.get("roster_positions") or [],
    }
    client.table("leagues").upsert(payload, on_conflict="league_id").execute()
    return data, safe_type


def _sync_managers(client, league_id: str) -> int:
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
    if rows:
        client.table("managers").upsert(
            rows, on_conflict="league_id,roster_id"
        ).execute()
    return len(rows)


def _sync_rosters(client, league_id: str, week: int) -> int:
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
    if rows:
        client.table("rosters").upsert(
            rows, on_conflict="league_id,roster_id,week"
        ).execute()
    return len(rows)


def _sync_matchup_weeks(client, league_id: str, up_to_week: int) -> int:
    total_rows = 0
    for week in range(1, max(up_to_week, 1) + 1):
        try:
            data = get_matchups(league_id, week)
        except Exception as e:
            logging.exception(
                f"Matchups fetch failed for {league_id} w{week}: {e}"
            )
            data = None
        if not data:
            continue
        rows = []
        for m in data:
            pts = m.get("points")
            try:
                pts_val = float(pts) if pts is not None else 0.0
            except Exception:
                logging.exception("Invalid matchup points value")
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
        if not rows:
            continue
        try:
            client.table("matchup_week_stats").upsert(
                rows, on_conflict="league_id,week,roster_id"
            ).execute()
            total_rows += len(rows)
        except Exception as e:
            logging.exception(
                f"Matchup upsert failed for {league_id} w{week}: {e}"
            )
    return total_rows


def _sync_drafts(client, league_id: str) -> int:
    try:
        drafts = get_league_drafts(league_id) or []
    except Exception as e:
        logging.exception(f"League drafts fetch failed for {league_id}: {e}")
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
                logging.exception("Invalid draft start_time")
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
    try:
        client.table("drafts").upsert(rows, on_conflict="draft_id").execute()
    except Exception as e:
        logging.exception(f"Drafts upsert failed for {league_id}: {e}")
        return 0
    return len(rows)


def _load_all_leagues(client) -> list[dict]:
    try:
        res = (
            client.table("leagues")
            .select("league_id,league_name,league_season,league_type")
            .order("league_season", desc=True)
            .execute()
        )
        return res.data if res and res.data else []
    except Exception as e:
        logging.exception(f"Failed to load leagues from Supabase: {e}")
        return []


def sync_all(
    limit: int | None = None,
    league_ids: list[str] | None = None,
    skip_matchups: bool = False,
    skip_drafts: bool = False,
) -> int:
    """Run the full weekly sync. Returns process exit code (0 on success)."""
    _print("=" * 70)
    _print("Stoned Lack — wöchentliche Liga-Synchronisierung")
    _print("=" * 70)

    client = get_supabase_client()
    if client is None:
        _print(
            "FEHLER: Supabase-Credentials fehlen. "
            "Bitte SUPABASE_URL und SUPABASE_KEY setzen "
            "(z.B. in einer .env-Datei im Projekt-Root)."
        )
        return 2

    week = _current_week()
    _print(f"Aktuelle NFL-Woche: {week}")

    if league_ids:
        leagues = [{"league_id": lid} for lid in league_ids]
        _print(f"Modus: gezielte Ligen ({len(leagues)})")
    else:
        leagues = _load_all_leagues(client)
        if limit and limit > 0:
            leagues = leagues[:limit]
        _print(f"Ligen aus Supabase geladen: {len(leagues)}")

    if not leagues:
        _print("Keine Ligen zu verarbeiten. Abbruch.")
        return 0

    total = len(leagues)
    ok = 0
    fail = 0
    started = time.time()
    failures: list[tuple[str, str]] = []
    totals = {
        "managers": 0,
        "rosters": 0,
        "matchups": 0,
        "drafts": 0,
    }

    for i, lg in enumerate(leagues, start=1):
        lid = str(lg.get("league_id", "")).strip()
        if not lid:
            continue
        lname = str(lg.get("league_name", "") or f"Liga {lid}")
        prefix = f"[{i}/{total}] {lid} — {lname}"
        _print(f"\n{prefix}")
        try:
            _sync_league_metadata(client, lid)
            _print("  ✓ Metadaten aktualisiert")

            mcount = _sync_managers(client, lid)
            totals["managers"] += mcount
            _print(f"  ✓ Manager: {mcount}")

            rcount = _sync_rosters(client, lid, week)
            totals["rosters"] += rcount
            _print(f"  ✓ Roster (Woche {week}): {rcount}")

            if skip_matchups:
                _print("  · Matchups übersprungen (--skip-matchups)")
            else:
                mucount = _sync_matchup_weeks(client, lid, week)
                totals["matchups"] += mucount
                _print(f"  ✓ Matchup-Einträge (W1..W{week}): {mucount}")

            if skip_drafts:
                _print("  · Drafts übersprungen (--skip-drafts)")
            else:
                dcount = _sync_drafts(client, lid)
                totals["drafts"] += dcount
                _print(f"  ✓ Drafts: {dcount}")

            ok += 1
        except Exception as e:
            fail += 1
            failures.append((lid, str(e)))
            logging.exception(f"Sync failed for league {lid}: {e}")
            _print(f"  ✗ FEHLER: {e}")
            continue

    elapsed = time.time() - started
    _print("\n" + "=" * 70)
    _print("Zusammenfassung")
    _print("=" * 70)
    _print(f"Gesamt:            {total}")
    _print(f"Erfolgreich:       {ok}")
    _print(f"Fehlgeschlagen:    {fail}")
    _print(f"Manager gesamt:    {totals['managers']}")
    _print(f"Roster gesamt:     {totals['rosters']}")
    _print(f"Matchups gesamt:   {totals['matchups']}")
    _print(f"Drafts gesamt:     {totals['drafts']}")
    _print(f"Dauer:             {elapsed:.1f}s")
    _print(f"Abgeschlossen um:  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    if failures:
        _print("\nFehlgeschlagene Ligen:")
        for lid, err in failures:
            _print(f"  - {lid}: {err}")

    return 0 if fail == 0 else 1


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Wöchentliche Synchronisierung aller Ligen "
        "aus der Supabase-Tabelle 'leagues' mit Sleeper-Daten."
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nur die ersten N Ligen verarbeiten (optional).",
    )
    p.add_argument(
        "--league-id",
        action="append",
        default=None,
        help="Nur diese Liga(n) synchronisieren. Mehrfach nutzbar.",
    )
    p.add_argument(
        "--skip-matchups",
        action="store_true",
        help="Matchup-Synchronisierung überspringen.",
    )
    p.add_argument(
        "--skip-drafts",
        action="store_true",
        help="Draft-Synchronisierung überspringen.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return sync_all(
        limit=args.limit,
        league_ids=args.league_id,
        skip_matchups=args.skip_matchups,
        skip_drafts=args.skip_drafts,
    )


if __name__ == "__main__":
    sys.exit(main())
