import reflex as rx
import logging
from datetime import datetime
from app.supabase_client import get_supabase_client

RUNS_TABLE = "redraft_assignment_runs_2026"
PLAYERS_TABLE = "redraft_assignment_players_2026"
WAITLIST_TABLE = "redraft_assignment_waitlist_2026"


def _fmt_dt(raw) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        logging.exception("bad timestamp")
        return str(raw)[:16]


class RedraftAuslosungState(rx.State):
    """Public, read-only view of the active Redraft 2026 assignment."""

    is_loading: bool = False
    error_message: str = ""
    has_active_run: bool = False

    run: dict[str, str | int] = {
        "id": "",
        "name": "",
        "season": 0,
        "generated_display": "",
        "generated_by": "",
        "notes": "",
        "total_registrations": 0,
        "total_leagues": 0,
        "total_assigned": 0,
        "total_nachruecker": 0,
        "total_commish": 0,
    }

    leagues: list[
        dict[str, str | int | bool | list[dict[str, str | int | bool]]]
    ] = []
    waitlist: list[dict[str, str | int]] = []

    total_leagues: int = 0
    total_assigned: int = 0
    joined_count: int = 0
    open_count: int = 0
    mapped_leagues_count: int = 0
    manager_search_query: str = ""

    @rx.var
    def waitlist_count(self) -> int:
        return len(self.waitlist)

    @rx.var
    def filtered_league_count(self) -> int:
        return len(self.filtered_leagues)

    @rx.var
    def filtered_leagues(
        self,
    ) -> list[dict[str, str | int | bool | list[dict[str, str | int | bool]]]]:
        query = self.manager_search_query.strip().lower()
        if not query:
            return self.leagues

        filtered: list[
            dict[str, str | int | bool | list[dict[str, str | int | bool]]]
        ] = []
        for league in self.leagues:
            league_text = " ".join(
                [
                    str(league.get("league_name") or ""),
                    str(league.get("league_number") or ""),
                ]
            ).lower()
            if query in league_text:
                filtered.append(league)
                continue

            players = league.get("players") or []
            for player in players:
                player_text = " ".join(
                    [
                        str(player.get("sleeper_username") or ""),
                        str(player.get("discord") or ""),
                        str(player.get("team_name") or ""),
                    ]
                ).lower()
                if query in player_text:
                    filtered.append(league)
                    break
        return filtered

    @rx.event
    def set_manager_search(self, value: str):
        self.manager_search_query = str(value or "").strip()

    @rx.event
    def clear_manager_search(self):
        self.manager_search_query = ""

    @rx.var
    def has_players(self) -> bool:
        return self.total_assigned > 0

    @rx.var
    def has_league_mapping(self) -> bool:
        return self.mapped_leagues_count > 0

    @rx.var
    def joined_pct_str(self) -> str:
        if self.total_assigned <= 0:
            return "0.0%"
        return f"{self.joined_count * 100 / self.total_assigned:.1f}%"

    @rx.event
    def init_page(self):
        yield RedraftAuslosungState.load_assignment

    def _reset(self):
        self.error_message = ""
        self.has_active_run = False
        self.leagues = []
        self.waitlist = []
        self.total_leagues = 0
        self.total_assigned = 0
        self.joined_count = 0
        self.open_count = 0
        self.mapped_leagues_count = 0

    def _fetch_players(self, client, run_id: str) -> list[dict]:
        rows: list[dict] = []
        offset = 0
        page = 1000
        while True:
            try:
                res = (
                    client.table(PLAYERS_TABLE)
                    .select("*")
                    .eq("assignment_run_id", run_id)
                    .order("league_number", desc=False)
                    .order("roster_position", desc=False)
                    .range(offset, offset + page - 1)
                    .execute()
                )
                chunk = res.data if res and res.data else []
            except Exception as e:
                logging.exception(f"players fetch failed: {e}")
                break
            if not chunk:
                break
            rows.extend(chunk)
            if len(chunk) < page:
                break
            offset += page
        return rows

    def _fetch_waitlist(self, client, run_id: str) -> list[dict]:
        try:
            res = (
                client.table(WAITLIST_TABLE)
                .select("*")
                .eq("assignment_run_id", run_id)
                .order("waitlist_position", desc=False)
                .execute()
            )
            return res.data if res and res.data else []
        except Exception as e:
            logging.exception(f"waitlist fetch failed: {e}")
            return []

    def _fetch_league_meta(self, client) -> tuple[dict, dict]:
        """Return (by_id, by_normalized_name) maps of leagues rows."""
        by_id: dict[str, dict] = {}
        by_name: dict[str, dict] = {}
        try:
            res = (
                client.table("leagues")
                .select("league_id,league_name,league_season,avatar")
                .execute()
            )
            rows = res.data if res and res.data else []
        except Exception as e:
            logging.exception(f"leagues fetch failed: {e}")
            rows = []
        for lg in rows:
            lid = str(lg.get("league_id") or "").strip()
            if lid:
                by_id[lid] = lg
            nm = str(lg.get("league_name") or "").strip().lower()
            if nm and nm not in by_name:
                by_name[nm] = lg
        return by_id, by_name

    def _fetch_managers(self, client, league_ids: list[str]) -> dict:
        """Return {league_id: {user_id: manager_row}}."""
        out: dict[str, dict[str, dict]] = {}
        if not league_ids:
            return out
        batch = 100
        for i in range(0, len(league_ids), batch):
            chunk = league_ids[i : i + batch]
            try:
                res = (
                    client.table("managers")
                    .select(
                        "league_id,roster_id,user_id,display_name,team_name"
                    )
                    .in_("league_id", chunk)
                    .execute()
                )
                rows = res.data if res and res.data else []
            except Exception as e:
                logging.exception(f"managers fetch failed: {e}")
                rows = []
            for m in rows:
                lid = str(m.get("league_id") or "")
                uid = str(m.get("user_id") or "")
                if lid and uid:
                    out.setdefault(lid, {})[uid] = m
        return out

    def _fetch_roster_counts(self, client, league_ids: list[str]) -> dict:
        """Return {league_id: number_of_distinct_roster_ids}."""
        out: dict[str, set] = {}
        if not league_ids:
            return {}
        batch = 100
        for i in range(0, len(league_ids), batch):
            chunk = league_ids[i : i + batch]
            try:
                res = (
                    client.table("rosters")
                    .select("league_id,roster_id")
                    .in_("league_id", chunk)
                    .execute()
                )
                rows = res.data if res and res.data else []
            except Exception as e:
                logging.exception(f"rosters fetch failed: {e}")
                rows = []
            for r in rows:
                lid = str(r.get("league_id") or "")
                rid = r.get("roster_id")
                if lid and rid is not None:
                    out.setdefault(lid, set()).add(int(rid))
        return {k: len(v) for k, v in out.items()}

    @rx.event
    def load_assignment(self):
        self.is_loading = True
        self._reset()
        yield
        try:
            client = get_supabase_client()
            if not client:
                self.error_message = (
                    "Datenbank nicht verfügbar. Bitte später erneut versuchen."
                )
                return
            try:
                run_res = (
                    client.table(RUNS_TABLE)
                    .select("*")
                    .eq("is_active", True)
                    .order("generated_at", desc=True)
                    .limit(1)
                    .execute()
                )
                run_rows = run_res.data if run_res and run_res.data else []
            except Exception as e:
                logging.exception(f"active run fetch failed: {e}")
                self.error_message = f"Fehler beim Laden der Auslosung: {e}"
                return
            if not run_rows:
                self.has_active_run = False
                return

            r = run_rows[0]
            run_id = str(r.get("id") or "")
            self.run = {
                "id": run_id,
                "name": str(r.get("name") or "Aktive Auslosung"),
                "season": int(r.get("season") or 0),
                "generated_display": _fmt_dt(r.get("generated_at")),
                "generated_by": str(r.get("generated_by") or ""),
                "notes": str(r.get("notes") or ""),
                "total_registrations": int(r.get("total_registrations") or 0),
                "total_leagues": int(r.get("total_leagues") or 0),
                "total_assigned": int(r.get("total_assigned") or 0),
                "total_nachruecker": int(r.get("total_nachruecker") or 0),
                "total_commish": int(r.get("total_commish") or 0),
            }
            self.has_active_run = True

            players = self._fetch_players(client, run_id)
            waitlist_rows = self._fetch_waitlist(client, run_id)

            self.waitlist = [
                {
                    "position": int(w.get("waitlist_position") or 0),
                    "sleeper_username": str(w.get("sleeper_username") or ""),
                    "sleeper_user_id": str(w.get("sleeper_user_id") or ""),
                    "discord": str(w.get("discord") or ""),
                    "created_display": _fmt_dt(
                        w.get("source_registration_created_at")
                    ),
                }
                for w in waitlist_rows
            ]

            if not players:
                self.total_assigned = 0
                return

            lg_by_id, lg_by_name = self._fetch_league_meta(client)

            # Group players by (league_number, league_name).
            groups: dict[tuple[int, str], list[dict]] = {}
            for p in players:
                try:
                    num = int(p.get("league_number") or 0)
                except Exception:
                    logging.exception("bad league_number")
                    num = 0
                name = str(p.get("league_name") or f"Liga {num}")
                groups.setdefault((num, name), []).append(p)

            # Resolve real league mapping per group.
            resolved: dict[tuple[int, str], dict] = {}
            for key, rows in groups.items():
                lid = ""
                invite = ""
                for row in rows:
                    if not lid:
                        cand = str(row.get("league_id") or "").strip()
                        if cand:
                            lid = cand
                    if not invite:
                        cand_i = str(
                            row.get("league_invite_link") or ""
                        ).strip()
                        if cand_i:
                            invite = cand_i
                meta = {}
                if lid and lid in lg_by_id:
                    meta = lg_by_id[lid]
                elif not lid:
                    meta = lg_by_name.get(key[1].strip().lower(), {})
                    if meta:
                        lid = str(meta.get("league_id") or "")
                resolved[key] = {
                    "league_id": lid,
                    "invite": invite,
                    "meta": meta,
                }

            mapped_ids = [
                v["league_id"] for v in resolved.values() if v["league_id"]
            ]
            managers_map = self._fetch_managers(client, mapped_ids)
            roster_counts = self._fetch_roster_counts(client, mapped_ids)

            leagues_out: list[dict] = []
            total_joined = 0
            total_open = 0
            total_assigned = 0
            for key in sorted(groups.keys(), key=lambda k: (k[0], k[1])):
                num, name = key
                rows = groups[key]
                info = resolved[key]
                lid = str(info["league_id"] or "")
                mgrs = managers_map.get(lid, {})
                players_out: list[dict] = []
                joined_here = 0
                for row in sorted(
                    rows, key=lambda x: int(x.get("roster_position") or 0)
                ):
                    uid = str(row.get("sleeper_user_id") or "")
                    m = mgrs.get(uid) if uid else None
                    joined = bool(m)
                    if joined:
                        joined_here += 1
                    players_out.append(
                        {
                            "slot": int(row.get("roster_position") or 0),
                            "draft_position": int(
                                row.get("draft_position") or 0
                            ),
                            "sleeper_username": str(
                                row.get("sleeper_username") or ""
                            ),
                            "sleeper_user_id": uid,
                            "discord": str(row.get("discord") or ""),
                            "commish": bool(row.get("commish") or False),
                            "joined": joined,
                            "roster_id": int((m or {}).get("roster_id") or 0)
                            if joined
                            else 0,
                            "team_name": str(
                                (m or {}).get("team_name")
                                or (m or {}).get("display_name")
                                or ""
                            )
                            if joined
                            else "",
                        }
                    )
                size = len(players_out)
                total_assigned += size
                total_joined += joined_here
                total_open += size - joined_here
                meta = info["meta"] or {}
                leagues_out.append(
                    {
                        "league_number": num,
                        "league_name": name,
                        "league_id": lid,
                        "invite_link": str(info["invite"] or ""),
                        "has_invite": bool(info["invite"]),
                        "is_mapped": bool(lid),
                        "real_league_name": str(meta.get("league_name") or ""),
                        "avatar": str(meta.get("avatar") or ""),
                        "roster_count": int(roster_counts.get(lid, 0) or 0),
                        "size": size,
                        "joined_count": joined_here,
                        "open_count": size - joined_here,
                        "is_complete": size > 0 and joined_here == size,
                        "players": players_out,
                    }
                )

            self.leagues = leagues_out
            self.total_leagues = len(leagues_out)
            self.total_assigned = total_assigned
            self.joined_count = total_joined
            self.open_count = total_open
            self.mapped_leagues_count = sum(
                1 for lg in leagues_out if lg["is_mapped"]
            )
        except Exception as e:
            logging.exception(f"load_assignment failed: {e}")
            self.error_message = f"Unerwarteter Fehler: {e}"
        finally:
            self.is_loading = False
