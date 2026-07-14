"""Sicherer Sync der Sleeper-Liga-Avatare in die Supabase-Tabelle ``leagues``.

Dieses Skript aktualisiert ausschließlich die Spalte ``avatar`` bereits
existierender Zeilen. Es werden keine neuen Zeilen eingefügt, damit
NOT-NULL-Constraints (z. B. auf ``league_name``) nicht verletzt werden.

Nutzung:
    python -m app.scripts.sync_league_avatars
    python -m app.scripts.sync_league_avatars --limit 100
    python -m app.scripts.sync_league_avatars --offset 100 --limit 100
    python -m app.scripts.sync_league_avatars --league-id 123456789
    python -m app.scripts.sync_league_avatars --dry-run

Voraussetzungen:
    - Umgebungsvariablen SUPABASE_URL und SUPABASE_KEY müssen gesetzt sein.
    - Nutzt die echte Sleeper-API und den bestehenden Supabase-Client.

Sicherheitshinweise:
    - Nur ``UPDATE ... WHERE league_id = ?`` — keinerlei ``INSERT``.
    - Fehlende Sleeper-Ligen (404) werden übersprungen und gezählt.
    - Leere Avatar-Werte werden gezählt, aber standardmäßig NICHT
      persistiert (damit bestehende Werte nicht überschrieben werden).
      Mit ``--clear-empty`` können leere Werte als ``NULL`` gespeichert
      werden.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import dotenv

dotenv.load_dotenv()

import requests

from app.supabase_client import get_supabase_client


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
for _noisy in (
    "httpx",
    "httpcore",
    "urllib3",
    "postgrest",
    "supabase",
):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

log = logging.getLogger("sync_league_avatars")

SLEEPER_LEAGUE_URL = "https://api.sleeper.app/v1/league/"
CDN_THUMB_FMT = "https://sleepercdn.com/avatars/thumbs/{avatar}"


def _print(msg: str) -> None:
    print(msg, flush=True)


def _cdn_url(avatar: str) -> str:
    return CDN_THUMB_FMT.format(avatar=avatar)


def _fetch_sleeper_avatar(league_id: str, timeout: float = 10.0) -> dict:
    """Fetch a league's avatar from Sleeper.

    Returns a dict with one of:
      - {"ok": True, "avatar": "<id or ''>"}
      - {"missing": True}
      - {"error": "<msg>"}
    """
    try:
        r = requests.get(SLEEPER_LEAGUE_URL + league_id, timeout=timeout)
        if r.status_code == 404:
            return {"missing": True}
        r.raise_for_status()
        data = r.json() or {}
        raw = data.get("avatar")
        avatar = str(raw).strip() if raw not in (None, "", "null") else ""
        return {"ok": True, "avatar": avatar}
    except Exception as e:
        logging.exception(f"Sleeper fetch failed for {league_id}: {e}")
        return {"error": str(e)}


def _load_leagues(
    client,
    league_ids: list[str] | None,
    offset: int,
    limit: int | None,
) -> list[dict]:
    try:
        query = client.table("leagues").select(
            "league_id,league_name,league_season,avatar"
        )
        if league_ids:
            query = query.in_("league_id", league_ids)
        else:
            query = query.order("league_season", desc=True).order(
                "league_name", desc=False
            )
        res = query.execute()
        rows = res.data if res and res.data else []
    except Exception as e:
        logging.exception(f"Failed to load leagues: {e}")
        return []

    if league_ids:
        return rows

    if offset and offset > 0:
        rows = rows[offset:]
    if limit and limit > 0:
        rows = rows[:limit]
    return rows


def sync_avatars(
    league_ids: list[str] | None = None,
    offset: int = 0,
    limit: int | None = None,
    workers: int = 16,
    clear_empty: bool = False,
    dry_run: bool = False,
    samples: int = 10,
) -> int:
    _print("=" * 70)
    _print("Stoned Lack — Sleeper-Liga-Avatare synchronisieren")
    _print("=" * 70)

    client = get_supabase_client()
    if client is None:
        _print(
            "FEHLER: Supabase-Credentials fehlen. "
            "Bitte SUPABASE_URL und SUPABASE_KEY setzen "
            "(z. B. in einer .env-Datei im Projekt-Root)."
        )
        return 2

    rows = _load_leagues(client, league_ids, offset, limit)
    if not rows:
        _print("Keine Ligen zu verarbeiten. Abbruch.")
        return 0

    total = len(rows)
    _print(f"Verarbeite {total} Liga(en) (offset={offset}, limit={limit}).")
    if dry_run:
        _print(
            "Modus: DRY-RUN — es werden KEINE Datenbank-Updates geschrieben."
        )

    started = time.time()

    fetched: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            pool.submit(
                _fetch_sleeper_avatar, str(row.get("league_id") or "").strip()
            ): str(row.get("league_id") or "").strip()
            for row in rows
            if str(row.get("league_id") or "").strip()
        }
        done = 0
        for fut in as_completed(futures):
            lid = futures[fut]
            fetched[lid] = fut.result()
            done += 1
            if done % 100 == 0:
                _print(f"  … {done}/{total} von Sleeper geladen")

    checked = 0
    updated = 0
    unchanged = 0
    empty_avatar = 0
    sleeper_missing = 0
    fetch_errors: list[dict] = []
    write_errors: list[dict] = []
    update_samples: list[dict] = []

    for row in rows:
        lid = str(row.get("league_id") or "").strip()
        if not lid:
            fetch_errors.append({"league_id": lid, "error": "empty league_id"})
            continue
        checked += 1
        result = fetched.get(lid) or {"error": "no result"}
        if result.get("missing"):
            sleeper_missing += 1
            continue
        if "error" in result:
            fetch_errors.append({"league_id": lid, "error": result["error"]})
            continue

        avatar = str(result.get("avatar") or "").strip()
        current = str(row.get("avatar") or "").strip()

        if not avatar:
            empty_avatar += 1
            if not clear_empty:
                if current == "":
                    unchanged += 1
                # else: keep the existing value; do not overwrite with empty.
                continue

        target_value: str | None = avatar if avatar else None
        current_norm = current if current else ""
        if (target_value or "") == current_norm:
            unchanged += 1
            continue

        if dry_run:
            updated += 1
        else:
            try:
                client.table("leagues").update({"avatar": target_value}).eq(
                    "league_id", lid
                ).execute()
                updated += 1
            except Exception as e:
                logging.exception(f"Update failed for {lid}: {e}")
                write_errors.append({"league_id": lid, "error": str(e)})
                continue

        if len(update_samples) < samples:
            update_samples.append(
                {
                    "league_id": lid,
                    "league_name": row.get("league_name") or "",
                    "season": row.get("league_season") or "",
                    "old_avatar": current or "",
                    "new_avatar": avatar or "",
                    "image_url": _cdn_url(avatar) if avatar else "",
                }
            )

    elapsed = time.time() - started
    _print("\n" + "=" * 70)
    _print("Zusammenfassung")
    _print("=" * 70)
    _print(f"Geprüft:                {checked}")
    _print(f"Aktualisiert:           {updated}")
    _print(f"Unverändert:            {unchanged}")
    _print(f"Leerer Sleeper-Avatar:  {empty_avatar}")
    _print(f"Sleeper 404 (fehlend):  {sleeper_missing}")
    _print(f"Fetch-Fehler:           {len(fetch_errors)}")
    _print(f"Schreib-Fehler:         {len(write_errors)}")
    _print(f"Dauer:                  {elapsed:.1f}s")

    if update_samples:
        _print("\nBeispiel-Updates (mit CDN-URL):")
        for s in update_samples:
            _print(
                f"  - {s['league_id']} ({s['season']}) „{s['league_name']}“: "
                f"{s['old_avatar'] or '∅'} → {s['new_avatar'] or '∅'}"
            )
            if s["image_url"]:
                _print(f"      {s['image_url']}")

    if fetch_errors[:5]:
        _print("\nFetch-Fehler (Stichprobe):")
        for e in fetch_errors[:5]:
            _print(f"  - {e['league_id']}: {e['error']}")
    if write_errors[:5]:
        _print("\nSchreib-Fehler (Stichprobe):")
        for e in write_errors[:5]:
            _print(f"  - {e['league_id']}: {e['error']}")

    return 0 if (not fetch_errors and not write_errors) else 1


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Synchronisiere Sleeper-Liga-Avatare in die Supabase-Tabelle "
            "'leagues'. Es werden ausschließlich existierende Zeilen "
            "aktualisiert (UPDATE ... WHERE league_id = ?). Keine INSERTs, "
            "damit NOT-NULL-Constraints nicht verletzt werden."
        )
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximal N Ligen in diesem Lauf verarbeiten.",
    )
    p.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Anzahl der Ligen, die am Anfang übersprungen werden.",
    )
    p.add_argument(
        "--league-id",
        action="append",
        default=None,
        help="Nur diese Liga(n) synchronisieren. Mehrfach nutzbar. "
        "Deaktiviert --offset/--limit.",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Parallelität der Sleeper-API-Aufrufe (Default: 16).",
    )
    p.add_argument(
        "--clear-empty",
        action="store_true",
        help="Wenn Sleeper einen leeren Avatar liefert, den DB-Wert "
        "auf NULL setzen. Standard: bestehenden Wert behalten.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, was aktualisiert würde — nichts schreiben.",
    )
    p.add_argument(
        "--samples",
        type=int,
        default=10,
        help="Anzahl der Beispiel-Updates in der Ausgabe (Default: 10).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return sync_avatars(
        league_ids=args.league_id,
        offset=args.offset,
        limit=args.limit,
        workers=args.workers,
        clear_empty=args.clear_empty,
        dry_run=args.dry_run,
        samples=args.samples,
    )


if __name__ == "__main__":
    sys.exit(main())
