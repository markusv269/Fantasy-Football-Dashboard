import reflex as rx
import logging
from datetime import datetime, timezone
from app.supabase_client import get_supabase_client
from app.sleeper_api import (
    get_league,
    get_rosters,
    get_league_users,
    get_nfl_state,
    get_matchups,
    get_league_drafts,
    get_draft,
    get_draft_picks,
    get_all_nfl_players,
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

    # New: bulk data update controls
    week_mode: str = "single"  # 'single' | 'range' | 'all'
    week_single: int = 1
    week_start: int = 1
    week_end: int = 18
    target_league_id: str = ""  # empty => all leagues
    sync_operation: str = ""  # human-readable current op

    @rx.event
    def set_week_mode(self, val: str):
        self.week_mode = val

    @rx.event
    def set_week_single(self, val: str):
        try:
            self.week_single = max(0, min(18, int(val)))
        except Exception:
            logging.exception("bad week single")

    @rx.event
    def set_week_start(self, val: str):
        try:
            self.week_start = max(0, min(18, int(val)))
        except Exception:
            logging.exception("bad week start")

    @rx.event
    def set_week_end(self, val: str):
        try:
            self.week_end = max(0, min(18, int(val)))
        except Exception:
            logging.exception("bad week end")

    @rx.event
    def set_target_league_id(self, val: str):
        self.target_league_id = "" if val == "__ALL__" else val

    @rx.var
    def target_league_display(self) -> str:
        if not self.target_league_id:
            return "__ALL__"
        return self.target_league_id

    def _resolve_weeks(self) -> list[int]:
        if self.week_mode == "single":
            return [int(self.week_single)]
        if self.week_mode == "range":
            lo = min(self.week_start, self.week_end)
            hi = max(self.week_start, self.week_end)
            return list(range(lo, hi + 1))
        return list(range(0, 19))

    def _resolve_league_ids(self) -> list[str]:
        if self.target_league_id:
            return [self.target_league_id]
        return [str(lg.get("league_id", "")) for lg in self.leagues]

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

    async def _require_auth(self) -> bool:
        from app.states.admin_auth_state import AdminAuthState

        auth = await self.get_state(AdminAuthState)
        return bool(auth.is_authenticated)

    @rx.event
    async def load_leagues(self):
        if not await self._require_auth():
            return
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
                # `avatar` is intentionally not read from Supabase — the
                # column does not exist. UI fallbacks handle the missing
                # value via a default Sleeper league placeholder.
                leagues.append(
                    {
                        "league_id": str(lg.get("league_id", "")),
                        "league_name": str(lg.get("league_name", "")),
                        "league_season": str(lg.get("league_season", "")),
                        "league_type": str(lg.get("league_type", "")),
                        "avatar": "",
                    }
                )
            self.leagues = leagues
            self._log(f"{len(leagues)} Ligen geladen.")
        except Exception as e:
            logging.exception(f"Error loading admin leagues: {e}")
            self._set_status(f"Fehler beim Laden: {e}", "error")

    @rx.event
    async def init_admin(self):
        if not await self._require_auth():
            return
        yield AdminState.load_leagues

    def _sync_league_metadata(self, client, league_id: str) -> dict:
        data = get_league(league_id)
        if not data:
            raise Exception(f"Sleeper API: Liga {league_id} nicht gefunden.")
        season_raw = data.get("season", "")
        season_val = (
            int(season_raw) if str(season_raw).isdigit() else season_raw
        )
        # Preserve existing league_type — the leagues.league_type column is
        # NOT NULL on many rows and Sleeper does not return it. Fall back
        # to a safe default only when the row is brand new.
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
            logging.exception(f"Existing league_type lookup failed: {e}")
        safe_type = existing_type or "dynasty"
        payload = {
            "league_id": str(league_id),
            "league_name": data.get("name", "") or f"Liga {league_id}",
            "league_season": season_val,
            "league_type": safe_type,
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
            # Only include columns that exist on the `managers` table.
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
    async def sync_league(self, league_id: str):
        if not await self._require_auth():
            return
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
    async def sync_all(self):
        if not await self._require_auth():
            return
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

    # =========================================================
    # New bulk sync operations (Phase 2)
    # =========================================================

    def _sync_draft_picks_for_draft(self, client, draft_id: str) -> int:
        picks = get_draft_picks(draft_id) or []
        try:
            client.table("draft_picks").delete().eq(
                "draft_id", str(draft_id)
            ).execute()
        except Exception as e:
            logging.exception(f"draft_picks delete failed {draft_id}: {e}")
            raise
        if not picks:
            return 0
        rows = []
        for p in picks:
            rows.append(
                {
                    "draft_id": str(draft_id),
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
        # Batch insert
        try:
            batch = 500
            for i in range(0, len(rows), batch):
                client.table("draft_picks").insert(
                    rows[i : i + batch]
                ).execute()
        except Exception as e:
            logging.exception(f"draft_picks insert failed {draft_id}: {e}")
            raise
        return len(rows)

    @rx.event
    async def sync_all_drafts(self):
        if not await self._require_auth():
            return
        self.is_syncing = True
        self.sync_operation = "Drafts scannen"
        self.sync_target = "DRAFTS"
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            league_ids = self._resolve_league_ids()
            self._log(f"Draft-Scan gestartet für {len(league_ids)} Liga(en)…")
            total = 0
            ok = 0
            fail = 0
            dtype_map = {"snake": "0", "linear": "1", "auction": "2"}
            for lid in league_ids:
                try:
                    drafts = get_league_drafts(lid) or []
                    if not drafts:
                        continue
                    rows = []
                    for d in drafts:
                        did = str(d.get("draft_id") or "")
                        if not did:
                            continue
                        start_iso = ""
                        start = d.get("start_time")
                        if start:
                            try:
                                start_iso = datetime.fromtimestamp(
                                    int(start) / 1000
                                ).isoformat()
                            except Exception:
                                logging.exception("bad start")
                        dtype_raw = d.get("type", "")
                        dtype_val = dtype_map.get(
                            str(dtype_raw).lower(), dtype_raw
                        )
                        rows.append(
                            {
                                "draft_id": did,
                                "league_id": str(lid),
                                "season": str(d.get("season") or ""),
                                "draft_type": dtype_val,
                                "status": str(d.get("status") or ""),
                                "start_time": start_iso,
                                "json_data": d,
                            }
                        )
                    if rows:
                        client.table("drafts").upsert(
                            rows, on_conflict="draft_id"
                        ).execute()
                        total += len(rows)
                    ok += 1
                except Exception as e:
                    fail += 1
                    logging.exception(f"drafts sync failed {lid}: {e}")
                    self._log(f"FEHLER Drafts {lid}: {e}", "error")
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._log(
                f"Draft-Scan fertig: {total} Drafts aus {ok} Ligen ({fail} Fehler)."
            )
            self._set_status(
                f"{total} Drafts synchronisiert aus {ok} Liga(en).",
                "success" if fail == 0 else "error",
            )
        except Exception as e:
            logging.exception(f"sync_all_drafts error: {e}")
            self._set_status(f"Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_operation = ""
            self.sync_target = ""

    @rx.event
    async def sync_all_draft_picks(self):
        if not await self._require_auth():
            return
        self.is_syncing = True
        self.sync_operation = "Draftpicks importieren"
        self.sync_target = "PICKS"
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            # Load all drafts (optionally filter to target league)
            query = client.table("drafts").select("draft_id,league_id")
            if self.target_league_id:
                query = query.eq("league_id", self.target_league_id)
            res = query.execute()
            drafts = res.data if res and res.data else []
            self._log(f"Draftpicks-Import: {len(drafts)} Draft(s)…")
            total = 0
            ok = 0
            fail = 0
            for i, d in enumerate(drafts, 1):
                did = str(d.get("draft_id") or "")
                if not did:
                    continue
                try:
                    n = self._sync_draft_picks_for_draft(client, did)
                    total += n
                    ok += 1
                    if i % 10 == 0:
                        self._log(f"Fortschritt: {i}/{len(drafts)} Drafts.")
                except Exception as e:
                    fail += 1
                    logging.exception(f"draft picks {did} failed: {e}")
                    self._log(f"FEHLER Picks {did}: {e}", "error")
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._log(
                f"Draftpicks-Import fertig: {total} Picks ({ok} OK, {fail} Fehler)."
            )
            self._set_status(
                f"{total} Draftpicks importiert.",
                "success" if fail == 0 else "error",
            )
        except Exception as e:
            logging.exception(f"sync_all_draft_picks error: {e}")
            self._set_status(f"Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_operation = ""
            self.sync_target = ""

    @rx.event
    async def sync_all_managers(self):
        if not await self._require_auth():
            return
        self.is_syncing = True
        self.sync_operation = "Manager aktualisieren"
        self.sync_target = "MANAGERS"
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            league_ids = self._resolve_league_ids()
            self._log(f"Manager-Sync für {len(league_ids)} Liga(en)…")
            total = 0
            ok = 0
            fail = 0
            for i, lid in enumerate(league_ids, 1):
                try:
                    n = self._sync_managers(client, lid)
                    total += n
                    ok += 1
                    if i % 20 == 0:
                        self._log(f"Fortschritt: {i}/{len(league_ids)}")
                except Exception as e:
                    fail += 1
                    logging.exception(f"managers sync {lid} failed: {e}")
                    self._log(f"FEHLER Manager {lid}: {e}", "error")
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._log(
                f"Manager-Sync fertig: {total} Rows ({ok} OK, {fail} Fehler)."
            )
            self._set_status(
                f"{total} Manager aktualisiert in {ok} Liga(en).",
                "success" if fail == 0 else "error",
            )
        except Exception as e:
            logging.exception(f"sync_all_managers error: {e}")
            self._set_status(f"Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_operation = ""
            self.sync_target = ""

    @rx.event
    async def sync_nfl_players(self):
        if not await self._require_auth():
            return
        self.is_syncing = True
        self.sync_operation = "NFL-Spieler synchronisieren"
        self.sync_target = "PLAYERS"
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            self._log("Lade Sleeper NFL-Spielerkatalog…")
            data = get_all_nfl_players()
            if not data:
                self._set_status(
                    "Sleeper-API lieferte keine Spielerdaten.", "error"
                )
                return
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
            self._log(f"Upsert {len(rows)} NFL-Spieler in nfl_players…")
            batch = 500
            for i in range(0, len(rows), batch):
                chunk = rows[i : i + batch]
                try:
                    client.table("nfl_players").upsert(
                        chunk, on_conflict="player_id"
                    ).execute()
                except Exception as e:
                    logging.exception(f"nfl_players batch failed: {e}")
                    self._log(
                        f"FEHLER Batch {i}: {e}",
                        "error",
                    )
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._log(f"NFL-Spieler-Sync abgeschlossen ({len(rows)} Rows).")
            self._set_status(
                f"{len(rows)} NFL-Spieler synchronisiert.", "success"
            )
        except Exception as e:
            logging.exception(f"sync_nfl_players error: {e}")
            self._set_status(f"Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_operation = ""
            self.sync_target = ""

    def _sync_matchups_for_week(self, client, league_id: str, week: int) -> int:
        try:
            data = get_matchups(league_id, week)
        except Exception as e:
            logging.exception(f"matchups fetch {league_id} w{week}: {e}")
            return 0
        if not data:
            return 0
        rows = []
        for m in data:
            pts = m.get("points")
            try:
                pts_val = float(pts) if pts is not None else 0.0
            except Exception:
                logging.exception("bad pts")
                pts_val = 0.0
            rows.append(
                {
                    "league_id": str(league_id),
                    "week": int(week),
                    "matchup_id": int(m.get("matchup_id") or 0),
                    "roster_id": int(m.get("roster_id") or 0),
                    "points": round(pts_val, 2),
                    "json_data": m,
                }
            )
        if not rows:
            return 0
        try:
            client.table("matchup_week_stats").upsert(
                rows, on_conflict="league_id,week,roster_id"
            ).execute()
        except Exception as e:
            logging.exception(f"matchups upsert {league_id} w{week}: {e}")
            raise
        return len(rows)

    @rx.event
    async def sync_matchups_bulk(self):
        if not await self._require_auth():
            return
        self.is_syncing = True
        self.sync_operation = "Matchups synchronisieren"
        self.sync_target = "MATCHUPS"
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            league_ids = self._resolve_league_ids()
            weeks = self._resolve_weeks()
            self._log(
                f"Matchup-Sync: {len(league_ids)} Liga(en) × {len(weeks)} Woche(n)…"
            )
            total = 0
            ok = 0
            fail = 0
            for lid in league_ids:
                for w in weeks:
                    try:
                        n = self._sync_matchups_for_week(client, lid, w)
                        total += n
                        ok += 1
                    except Exception as e:
                        fail += 1
                        logging.exception(f"matchup err {lid} w{w}: {e}")
                        self._log(f"FEHLER Matchup {lid} W{w}: {e}", "error")
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._log(
                f"Matchup-Sync fertig: {total} Rows ({ok} OK, {fail} Fehler)."
            )
            self._set_status(
                f"{total} Matchup-Einträge synchronisiert.",
                "success" if fail == 0 else "error",
            )
        except Exception as e:
            logging.exception(f"sync_matchups_bulk error: {e}")
            self._set_status(f"Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_operation = ""
            self.sync_target = ""

    def _sync_rosters_for_week(self, client, league_id: str, week: int) -> int:
        rosters = get_rosters(league_id) or []
        if not rosters:
            return 0
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
            ppts = (
                float(settings.get("ppts", 0) or 0)
                + float(settings.get("ppts_decimal", 0) or 0) / 100.0
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
                    "ppts": round(ppts, 2),
                    "json_data": {
                        "players": r.get("players") or [],
                        "starters": r.get("starters") or [],
                        "reserve": r.get("reserve") or [],
                        "taxi": r.get("taxi") or [],
                        "settings": settings,
                    },
                }
            )
        try:
            client.table("rosters").upsert(
                rows, on_conflict="league_id,roster_id,week"
            ).execute()
        except Exception as e:
            logging.exception(f"rosters upsert {league_id} w{week}: {e}")
            raise
        return len(rows)

    @rx.event
    async def sync_rosters_bulk(self):
        if not await self._require_auth():
            return
        self.is_syncing = True
        self.sync_operation = "Roster synchronisieren"
        self.sync_target = "ROSTERS"
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Supabase nicht verfügbar.", "error")
                return
            league_ids = self._resolve_league_ids()
            weeks = self._resolve_weeks()
            self._log(
                f"Roster-Sync: {len(league_ids)} Liga(en) × {len(weeks)} Woche(n)…"
            )
            total = 0
            ok = 0
            fail = 0
            for lid in league_ids:
                for w in weeks:
                    try:
                        n = self._sync_rosters_for_week(client, lid, w)
                        total += n
                        ok += 1
                    except Exception as e:
                        fail += 1
                        logging.exception(f"roster err {lid} w{w}: {e}")
                        self._log(f"FEHLER Roster {lid} W{w}: {e}", "error")
            self.last_sync_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            self._log(
                f"Roster-Sync fertig: {total} Rows ({ok} OK, {fail} Fehler)."
            )
            self._set_status(
                f"{total} Roster-Einträge synchronisiert.",
                "success" if fail == 0 else "error",
            )
        except Exception as e:
            logging.exception(f"sync_rosters_bulk error: {e}")
            self._set_status(f"Fehler: {e}", "error")
        finally:
            self.is_syncing = False
            self.sync_operation = ""
            self.sync_target = ""

    @rx.event
    async def add_league(self):
        if not await self._require_auth():
            return
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
                .select("league_id,league_name,league_type")
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
            # Only include columns present in the `leagues` schema.
            payload = {
                "league_id": raw,
                "league_name": data.get("name", "") or f"Liga {raw}",
                "league_season": season_val,
                "league_type": self.add_league_type,
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
