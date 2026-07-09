import reflex as rx
import logging
from datetime import datetime
from app.supabase_client import get_supabase_client
from app.sleeper_api import (
    get_league,
    get_rosters,
    get_league_users,
    get_nfl_state,
    get_matchups,
    get_league_drafts,
    get_draft,
)


class AdminState(rx.State):
    leagues: list[dict[str, str | int | bool]] = []
    is_loading: bool = False
    is_syncing: bool = False
    sync_target: str = ""
    add_league_input: str = ""
    add_league_type: str = "dynasty"
    search_query: str = ""
    filter_type: str = "all"
    status_message: str = ""
    status_type: str = ""
    log_entries: list[dict[str, str]] = []
    last_sync_time: str = ""
    show_confirm_sync_all: bool = False

    @rx.var
    def total_leagues(self) -> int:
        return len(self.leagues)

    @rx.var
    def dynasty_count(self) -> int:
        return sum(
            1
            for lg in self.leagues
            if str(lg.get("league_type", "")) == "dynasty"
        )

    @rx.var
    def redraft_count(self) -> int:
        return sum(
            1
            for lg in self.leagues
            if str(lg.get("league_type", "")) == "redraft"
        )

    @rx.var
    def filtered_leagues(self) -> list[dict[str, str | int | bool]]:
        leagues = self.leagues
        if self.filter_type != "all":
            leagues = [
                lg
                for lg in leagues
                if str(lg.get("league_type", "")).lower() == self.filter_type
            ]
        if not self.search_query:
            return leagues
        q = self.search_query.lower()
        return [
            lg
            for lg in leagues
            if q in str(lg.get("league_name", "")).lower()
            or q in str(lg.get("league_id", "")).lower()
            or q in str(lg.get("league_season", "")).lower()
        ]

    @rx.var
    def bestball_count(self) -> int:
        return sum(
            1
            for lg in self.leagues
            if str(lg.get("league_type", "")) == "bestball"
        )

    @rx.var
    def unique_seasons(self) -> list[str]:
        seasons = {
            str(lg.get("league_season", ""))
            for lg in self.leagues
            if lg.get("league_season")
        }
        return sorted(seasons, reverse=True)

    @rx.event
    def set_filter_type(self, val: str):
        self.filter_type = val

    @rx.event
    def open_confirm_sync_all(self):
        self.show_confirm_sync_all = True

    @rx.event
    def close_confirm_sync_all(self):
        self.show_confirm_sync_all = False

    @rx.event
    def set_confirm_sync_all_open(self, val: bool):
        self.show_confirm_sync_all = val

    @rx.event
    def confirm_and_sync_all(self):
        self.show_confirm_sync_all = False
        yield AdminState.sync_all

    @rx.event
    def clear_log(self):
        self.log_entries = []

    def _log(self, msg: str, level: str = "info"):
        self.log_entries = [
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": msg,
                "level": level,
            }
        ] + self.log_entries[:49]

    def _set_status(self, msg: str, kind: str = "success"):
        self.status_message = msg
        self.status_type = kind

    @rx.event
    def set_add_league_input(self, val: str):
        self.add_league_input = val

    @rx.event
    def set_add_league_type(self, val: str):
        self.add_league_type = val

    @rx.event
    def set_search_query(self, val: str):
        self.search_query = val

    @rx.event
    def clear_status(self):
        self.status_message = ""
        self.status_type = ""

    @rx.event
    def load_leagues(self):
        self.is_loading = True
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                self.is_loading = False
                return
            res = (
                client.table("leagues")
                .select("*")
                .order("league_season", desc=True)
                .execute()
            )
            data = res.data if res and res.data else []
            leagues = []
            for lg in data:
                leagues.append(
                    {
                        "league_id": str(lg.get("league_id", "")),
                        "league_name": str(lg.get("league_name", "")),
                        "league_season": str(lg.get("league_season", "")),
                        "league_type": str(lg.get("league_type", "")),
                        "avatar": str(lg.get("avatar") or ""),
                    }
                )
            self.leagues = leagues
            self._log(f"{len(leagues)} Ligen geladen.")
        except Exception as e:
            logging.exception(f"Error loading admin leagues: {e}")
            self._set_status(f"Fehler beim Laden: {e}", "error")
        finally:
            self.is_loading = False

    def _sync_league_metadata(self, client, league_id: str) -> dict:
        data = get_league(league_id)
        if not data:
            raise Exception(f"Sleeper API: Liga {league_id} nicht gefunden.")
        payload = {
            "league_id": str(league_id),
            "league_name": data.get("name", ""),
            "league_season": int(data.get("season") or 0)
            if str(data.get("season", "")).isdigit()
            else data.get("season"),
            "avatar": data.get("avatar") or "",
            "roster_positions": data.get("roster_positions") or [],
        }
        try:
            client.table("leagues").upsert(
                payload, on_conflict="league_id"
            ).execute()
        except Exception as e:
            logging.exception(f"Metadata upsert failed: {e}")
            raise
        return data

    def _sync_managers(self, client, league_id: str) -> int:
        users = get_league_users(league_id) or []
        rosters = get_rosters(league_id) or []
        user_map = {u.get("user_id"): u for u in users}
        rows = []
        for r in rosters:
            owner_id = r.get("owner_id")
            u = user_map.get(owner_id, {})
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
                    "avatar": u.get("avatar") or "",
                }
            )
        if rows:
            try:
                client.table("managers").upsert(
                    rows, on_conflict="league_id,roster_id"
                ).execute()
            except Exception as e:
                logging.exception(f"Managers upsert failed: {e}")
                raise
        return len(rows)

    def _sync_rosters(self, client, league_id: str, week: int) -> int:
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
            try:
                client.table("rosters").upsert(
                    rows, on_conflict="league_id,roster_id,week"
                ).execute()
            except Exception as e:
                logging.exception(f"Rosters upsert failed: {e}")
                raise
        return len(rows)

    def _current_week(self) -> int:
        try:
            state = get_nfl_state() or {}
            w = int(state.get("week") or 0)
            return max(w, 1)
        except Exception:
            logging.exception("Failed to get NFL week")
            return 1

    def _sync_matchup_weeks(
        self, client, league_id: str, up_to_week: int
    ) -> int:
        """Sync matchup data for weeks 1..up_to_week into matchup_week_stats."""
        total_rows = 0
        for week in range(1, max(up_to_week, 1) + 1):
            try:
                data = get_matchups(league_id, week)
            except Exception as e:
                logging.exception(f"Matchups week {week} fetch failed: {e}")
                data = None
            if not data:
                continue
            rows = []
            for m in data:
                pts = m.get("points")
                try:
                    pts_val = float(pts) if pts is not None else 0.0
                except Exception:
                    logging.exception("Invalid matchup points")
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
                logging.exception(f"Matchups upsert failed w{week}: {e}")
        return total_rows

    def _sync_drafts(self, client, league_id: str) -> int:
        """Sync all drafts for a league into the drafts table."""
        try:
            drafts = get_league_drafts(league_id) or []
        except Exception as e:
            logging.exception(f"Get drafts failed: {e}")
            return 0
        if not drafts:
            return 0
        rows = []
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
            dtype_map = {"snake": "0", "linear": "1", "auction": "2"}
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
            client.table("drafts").upsert(
                rows, on_conflict="draft_id"
            ).execute()
        except Exception as e:
            logging.exception(f"Drafts upsert failed: {e}")
            return 0
        return len(rows)

    @rx.event
    def sync_league(self, league_id: str):
        self.is_syncing = True
        self.sync_target = league_id
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            self._log(f"Sync gestartet für Liga {league_id}…")
            self._sync_league_metadata(client, league_id)
            self._log(f"Metadaten aktualisiert ({league_id}).")
            mcount = self._sync_managers(client, league_id)
            self._log(f"{mcount} Manager aktualisiert ({league_id}).")
            week = self._current_week()
            rcount = self._sync_rosters(client, league_id, week)
            self._log(
                f"{rcount} Roster (Woche {week}) aktualisiert ({league_id})."
            )
            try:
                mucount = self._sync_matchup_weeks(client, league_id, week)
                self._log(
                    f"{mucount} Matchup-Einträge synchronisiert ({league_id})."
                )
            except Exception as e:
                logging.exception(f"Matchup sync failed for {league_id}: {e}")
                self._log(f"Matchup-Sync fehlgeschlagen: {e}", "error")
            try:
                dcount = self._sync_drafts(client, league_id)
                self._log(f"{dcount} Draft(s) synchronisiert ({league_id}).")
            except Exception as e:
                logging.exception(f"Draft sync failed for {league_id}: {e}")
                self._log(f"Draft-Sync fehlgeschlagen: {e}", "error")
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._set_status(
                f"Liga {league_id} erfolgreich synchronisiert.", "success"
            )
        except Exception as e:
            logging.exception(f"Sync failed for {league_id}: {e}")
            self._log(f"Fehler bei {league_id}: {e}", "error")
            self._set_status(f"Sync-Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_target = ""
            yield AdminState.load_leagues

    @rx.event
    def sync_all(self):
        self.is_syncing = True
        self.sync_target = "ALL"
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            week = self._current_week()
            ok = 0
            fail = 0
            self._log(f"Sync ALLER Ligen gestartet (Woche {week})…")
            for lg in list(self.leagues):
                lid = str(lg.get("league_id", ""))
                if not lid:
                    continue
                try:
                    self._sync_league_metadata(client, lid)
                    self._sync_managers(client, lid)
                    self._sync_rosters(client, lid, week)
                    ok += 1
                    self._log(f"OK: {lid}")
                except Exception as e:
                    fail += 1
                    logging.exception(f"Bulk sync failed for {lid}: {e}")
                    self._log(f"FEHLER: {lid} — {e}", "error")
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._set_status(
                f"Bulk-Sync abgeschlossen: {ok} OK, {fail} Fehler.",
                "success" if fail == 0 else "error",
            )
        except Exception as e:
            logging.exception(f"Bulk sync error: {e}")
            self._set_status(f"Sync-Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_target = ""
            yield AdminState.load_leagues

    @rx.event
    def add_league(self):
        raw = self.add_league_input.strip().strip('"')
        if not raw:
            self._set_status("Bitte gib eine Sleeper League-ID ein.", "error")
            return
        if not raw.isdigit() or len(raw) < 6:
            self._set_status(
                f"Ungültige League-ID „{raw}“. Erwartet wird eine numerische Sleeper-ID.",
                "error",
            )
            return
        allowed_types = {"dynasty", "redraft", "bestball"}
        if self.add_league_type not in allowed_types:
            self._set_status(
                f"Ungültiger Liga-Typ „{self.add_league_type}“.", "error"
            )
            return

        self.is_syncing = True
        self.sync_target = raw
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return

            existing = (
                client.table("leagues")
                .select("league_id, league_name, league_type")
                .eq("league_id", raw)
                .limit(1)
                .execute()
            )
            is_duplicate = bool(existing and existing.data)
            if is_duplicate:
                existing_name = str(
                    existing.data[0].get("league_name") or f"Liga {raw}"
                )
                self._log(
                    f"Liga {raw} („{existing_name}“) existiert bereits — führe vollständige Neuinitialisierung durch.",
                    "info",
                )
                self._set_status(
                    f"Liga {raw} ist bereits vorhanden. Aktualisiere Daten…",
                    "info",
                )

            self._log(f"Prüfe Liga {raw} bei Sleeper…")
            data = get_league(raw)
            if not data:
                self._set_status(
                    f"Liga {raw} bei Sleeper nicht gefunden. Bitte ID überprüfen.",
                    "error",
                )
                self._log(f"Sleeper API: Liga {raw} nicht gefunden.", "error")
                return

            season_raw = data.get("season", "")
            season_val = (
                int(season_raw) if str(season_raw).isdigit() else season_raw
            )
            payload = {
                "league_id": raw,
                "league_name": data.get("name", "") or f"Liga {raw}",
                "league_season": season_val,
                "league_type": self.add_league_type,
                "avatar": data.get("avatar") or "",
                "roster_positions": data.get("roster_positions") or [],
            }
            try:
                client.table("leagues").upsert(
                    payload, on_conflict="league_id"
                ).execute()
            except Exception as e:
                logging.exception(f"League upsert failed: {e}")
                self._set_status(
                    f"Fehler beim Speichern der Liga: {e}", "error"
                )
                self._log(f"DB-Fehler beim Speichern: {e}", "error")
                return

            league_name = str(data.get("name") or f"Liga {raw}")
            action_verb = "aktualisiert" if is_duplicate else "hinzugefügt"
            self._log(
                f"Metadaten {action_verb}: {league_name} (Saison {season_val})."
            )

            week = self._current_week()

            try:
                mcount = self._sync_managers(client, raw)
                self._log(f"{mcount} Manager synchronisiert.")
            except Exception as e:
                logging.exception(f"Manager sync failed for {raw}: {e}")
                self._log(f"Manager-Sync fehlgeschlagen: {e}", "error")
                mcount = 0

            try:
                rcount = self._sync_rosters(client, raw, week)
                self._log(f"{rcount} Roster (Woche {week}) synchronisiert.")
            except Exception as e:
                logging.exception(f"Roster sync failed for {raw}: {e}")
                self._log(f"Roster-Sync fehlgeschlagen: {e}", "error")
                rcount = 0

            try:
                mucount = self._sync_matchup_weeks(client, raw, week)
                self._log(
                    f"{mucount} Matchup-Einträge über {week} Woche(n) synchronisiert."
                )
            except Exception as e:
                logging.exception(f"Matchup sync failed for {raw}: {e}")
                self._log(f"Matchup-Sync fehlgeschlagen: {e}", "error")
                mucount = 0

            try:
                dcount = self._sync_drafts(client, raw)
                self._log(f"{dcount} Draft(s) synchronisiert.")
            except Exception as e:
                logging.exception(f"Draft sync failed for {raw}: {e}")
                self._log(f"Draft-Sync fehlgeschlagen: {e}", "error")
                dcount = 0

            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            summary = (
                f"„{league_name}“ {action_verb}: "
                f"{mcount} Manager · {rcount} Roster · "
                f"{mucount} Matchups · {dcount} Drafts."
            )
            self._log(f"Initial-Sync für {raw} abgeschlossen.")
            self._set_status(summary, "success")
            self.add_league_input = ""
        except Exception as e:
            logging.exception(f"Add league failed: {e}")
            self._set_status(f"Fehler beim Hinzufügen: {e}", "error")
            self._log(f"Unerwarteter Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_target = ""
            yield AdminState.load_leagues

    @rx.event
    def init_admin(self):
        yield AdminState.load_leagues
