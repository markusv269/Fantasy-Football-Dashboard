import reflex as rx
import logging
from app.states.app_state import AppState
from app.sleeper_api import get_rosters, get_league_users
from app.player_cache import enrich_roster_players
from app.supabase_client import get_supabase_client


class MatchupsState(rx.State):
    selected_week: int = 1
    is_loading: bool = False
    matchups_by_league: dict[
        str, list[dict[str, str | int | float | list | dict | None]]
    ] = {}
    league_names: dict[str, str] = {}

    # Season/week context
    current_season: str = ""
    current_nfl_week: int = 0
    available_weeks: list[int] = []
    current_league_ids: list[str] = []
    current_leagues_meta: list[dict[str, str]] = []

    # Fields for filtered view
    matchups_data: list[dict[str, str | int | float | list | dict | None]] = []
    paired_matchups: list[
        dict[str, str | int | float | list | dict | None]
    ] = []
    league_users: list[dict[str, str | int | float | list | dict | None]] = []
    league_rosters: list[dict[str, str | int | float | list | dict | None]] = []
    standings_data: list[
        dict[str, str | int | float | list | dict | list[str] | None]
    ] = []
    selected_roster: dict[
        str, str | int | float | list | dict | list[str] | None
    ] = {}

    @rx.var
    def week_options(self) -> list[str]:
        return [str(w) for w in self.available_weeks]

    @rx.var
    def current_league_options(self) -> list[dict[str, str]]:
        return self.current_leagues_meta

    def _determine_current_season(self, app_state: AppState) -> str:
        seasons: list[int] = []
        for lg in app_state.leagues_data:
            s = str(lg.get("season", ""))
            if s.isdigit():
                seasons.append(int(s))
        if seasons:
            return str(max(seasons))
        nfl_season = app_state.nfl_state.get("season", "")
        return str(nfl_season) if nfl_season else ""

    def _load_current_leagues_from_supabase(
        self,
    ) -> tuple[str, list[str], list[dict[str, str]]]:
        """Load current-season leagues directly from Supabase.

        Used as a fallback when cross-state AppState hydration is not
        available (e.g. in isolated event tests). Returns
        (current_season, current_league_ids, current_leagues_meta).
        """
        client = get_supabase_client()
        if not client:
            return "", [], []
        try:
            res = (
                client.table("leagues")
                .select("league_id,league_name,league_season")
                .execute()
            )
            rows = res.data if res and res.data else []
        except Exception as e:
            logging.exception(f"leagues fetch failed: {e}")
            return "", [], []
        seasons: list[int] = []
        for lg in rows:
            s = lg.get("league_season")
            try:
                if s is not None and str(s).lstrip("-").isdigit():
                    seasons.append(int(s))
            except Exception:
                logging.exception("bad season")
        if not seasons:
            return "", [], []
        current = str(max(seasons))
        current_leagues = [
            lg for lg in rows if str(lg.get("league_season", "")) == current
        ]
        ids = [str(lg.get("league_id", "")) for lg in current_leagues]
        meta = [
            {
                "league_id": str(lg.get("league_id", "")),
                "name": str(
                    lg.get("league_name", "")
                    or f"Liga {lg.get('league_id', '')}"
                ),
            }
            for lg in current_leagues
        ]
        return current, ids, meta

    @rx.event
    async def init_matchups(self):
        self.is_loading = True
        yield
        try:
            app_state = await self.get_state(AppState)

            if app_state.leagues_data:
                season = self._determine_current_season(app_state)
                self.current_season = season
                current_leagues = [
                    lg
                    for lg in app_state.leagues_data
                    if str(lg.get("season", "")) == season
                ]
                self.current_league_ids = [
                    str(lg["league_id"]) for lg in current_leagues
                ]
                self.current_leagues_meta = [
                    {
                        "league_id": str(lg["league_id"]),
                        "name": str(
                            lg.get("name", "") or f"Liga {lg['league_id']}"
                        ),
                    }
                    for lg in current_leagues
                ]
            else:
                # Fallback: load current-season leagues directly from Supabase.
                # This keeps init_matchups usable in isolated tests and any
                # context where AppState was not pre-hydrated.
                season, ids, meta = self._load_current_leagues_from_supabase()
                self.current_season = season
                self.current_league_ids = ids
                self.current_leagues_meta = meta

            # Current NFL week from Sleeper state
            nfl_week_raw = app_state.nfl_state.get("week", 0)
            try:
                cur_week = int(nfl_week_raw) if nfl_week_raw else 0
            except Exception:
                logging.exception("bad nfl week")
                cur_week = 0
            self.current_nfl_week = max(cur_week, 0)

            # If selected league is not part of current season, clear it
            if app_state.selected_league_id and (
                app_state.selected_league_id not in self.current_league_ids
            ):
                app_state.selected_league_id = ""

            # Load available weeks from Supabase for current-season leagues
            self.available_weeks = self._load_available_weeks(
                self.current_league_ids
            )

            # Pick initial week: current NFL week if available in matchup data,
            # otherwise the next available week (smallest week >= current NFL
            # week). Fall back to max available week if no week is >= current.
            initial_week = 0
            if self.available_weeks:
                if (
                    self.current_nfl_week > 0
                    and self.current_nfl_week in self.available_weeks
                ):
                    initial_week = self.current_nfl_week
                else:
                    upcoming = [
                        w
                        for w in self.available_weeks
                        if w >= self.current_nfl_week
                    ]
                    if upcoming:
                        initial_week = min(upcoming)
                    else:
                        initial_week = max(self.available_weeks)
            self.selected_week = initial_week

            # Load matchups synchronously here so init_matchups leaves the
            # state fully populated, without depending on yielded events
            # re-hydrating AppState in isolated test contexts.
            if not app_state.selected_league_id:
                await self._load_all_matchups_for_current_season()
            else:
                yield MatchupsState.fetch_league_detail
                yield MatchupsState.fetch_matchups(self.selected_week)
        finally:
            self.is_loading = False

    async def _load_all_matchups_for_current_season(self):
        """Populate matchups_by_league for the current season using self.current_league_ids.
        Does NOT depend on cross-state AppState hydration.
        """
        league_ids = list(self.current_league_ids)
        if not league_ids or self.selected_week <= 0:
            self.matchups_by_league = {}
            self.league_names = {
                item["league_id"]: item["name"]
                for item in self.current_leagues_meta
            }
            return
        client = get_supabase_client()
        if not client:
            self.matchups_by_league = {}
            return
        names: dict[str, str] = {
            item["league_id"]: item["name"]
            for item in self.current_leagues_meta
        }
        mgr_map = self._load_managers_map(client, league_ids)
        rows: list[dict] = []
        try:
            batch = 100
            for i in range(0, len(league_ids), batch):
                chunk = league_ids[i : i + batch]
                if not chunk:
                    continue
                res = (
                    client.table("matchup_week_stats")
                    .select("league_id,week,matchup_id,roster_id,points")
                    .in_("league_id", chunk)
                    .eq("week", int(self.selected_week))
                    .execute()
                )
                data = res.data if res and res.data else []
                rows.extend(data)
        except Exception as e:
            logging.exception(f"all matchups fetch failed: {e}")
            rows = []

        grouped: dict[str, dict[int, list[dict]]] = {}
        for r in rows:
            lid = str(r.get("league_id", ""))
            mid_raw = r.get("matchup_id")
            try:
                mid = int(mid_raw) if mid_raw is not None else 0
            except Exception:
                logging.exception("bad mid")
                mid = 0
            grouped.setdefault(lid, {}).setdefault(mid, []).append(r)

        all_paired: dict[str, list[dict]] = {}
        for lid, matchup_dict in grouped.items():
            paired_list = []
            for mid, teams in matchup_dict.items():
                if len(teams) >= 2:
                    paired_list.append(
                        self._build_pair_entry(
                            mid, teams[0], teams[1], mgr_map, lid
                        )
                    )
                elif len(teams) == 1:
                    paired_list.append(
                        self._build_pair_entry(
                            mid, teams[0], None, mgr_map, lid
                        )
                    )
            paired_list.sort(key=lambda x: x["matchup_id"])
            if paired_list:
                all_paired[lid] = paired_list

        self.matchups_by_league = all_paired
        self.league_names = names

    def _load_available_weeks(self, league_ids: list[str]) -> list[int]:
        if not league_ids:
            return []
        client = get_supabase_client()
        if not client:
            return []
        weeks: set[int] = set()
        try:
            batch = 100
            for i in range(0, len(league_ids), batch):
                chunk = league_ids[i : i + batch]
                if not chunk:
                    continue
                res = (
                    client.table("matchup_week_stats")
                    .select("week")
                    .in_("league_id", chunk)
                    .execute()
                )
                data = res.data if res and res.data else []
                for row in data:
                    w = row.get("week")
                    if w is not None:
                        try:
                            weeks.add(int(w))
                        except Exception:
                            logging.exception("bad week")
        except Exception as e:
            logging.exception(f"available weeks fetch failed: {e}")
        return sorted(weeks)

    def _load_managers_map(self, client, league_ids: list[str]) -> dict:
        """Return {(league_id, roster_id): manager_row}."""
        mgr_map: dict = {}
        if not league_ids:
            return mgr_map
        try:
            batch = 100
            for i in range(0, len(league_ids), batch):
                chunk = league_ids[i : i + batch]
                if not chunk:
                    continue
                res = (
                    client.table("managers")
                    .select("league_id,roster_id,display_name,team_name")
                    .in_("league_id", chunk)
                    .execute()
                )
                data = res.data if res and res.data else []
                for m in data:
                    key = (
                        str(m.get("league_id", "")),
                        int(m.get("roster_id") or 0),
                    )
                    mgr_map[key] = m
        except Exception as e:
            logging.exception(f"managers fetch failed: {e}")
        return mgr_map

    def _build_pair_entry(
        self,
        matchup_id: int,
        team_a_row: dict,
        team_b_row: dict | None,
        mgr_map: dict,
        league_id: str,
    ) -> dict:
        @rx.event
        def team_dict(row: dict) -> dict:
            rid = int(row.get("roster_id") or 0)
            mgr = mgr_map.get((league_id, rid), {})
            team_name = (
                mgr.get("team_name") or mgr.get("display_name") or f"Team {rid}"
            )
            display_name = mgr.get("display_name") or f"Manager {rid}"
            pts_raw = row.get("points")
            try:
                pts = float(pts_raw) if pts_raw is not None else 0.0
            except Exception:
                logging.exception("bad points")
                pts = 0.0
            return {
                "roster_id": rid,
                "team_name": str(team_name),
                "owner_name": str(display_name),
                "points": round(pts, 2),
                "avatar": "",
            }

        a = team_dict(team_a_row)
        b = team_dict(team_b_row) if team_b_row else None

        return {
            "matchup_id": matchup_id,
            "team_a": a,
            "team_b": b,
        }

    @rx.event
    async def fetch_all_matchups(self):
        self.is_loading = True
        yield
        try:
            await self._load_all_matchups_for_current_season()
        finally:
            self.is_loading = False

    @rx.event
    async def init_standings(self):
        app_state = await self.get_state(AppState)
        if app_state.selected_league_id:
            yield MatchupsState.fetch_standings

    @rx.event
    async def init_rosters(self):
        app_state = await self.get_state(AppState)
        if app_state.selected_league_id:
            yield MatchupsState.fetch_league_detail

    @rx.event
    async def fetch_league_detail(self):
        app_state = await self.get_state(AppState)
        league_id = app_state.selected_league_id
        if not league_id:
            return
        users = get_league_users(league_id)
        rosters = get_rosters(league_id)
        if users:
            self.league_users = users
        if rosters:
            self.league_rosters = rosters

    @rx.event
    async def change_week(self, week: int):
        try:
            w = int(week)
        except (TypeError, ValueError):
            return
        if self.available_weeks and w not in self.available_weeks:
            return
        self.selected_week = w
        from app.states.app_state import AppState

        app_state = await self.get_state(AppState)
        if not app_state.selected_league_id:
            await self._load_all_matchups_for_current_season()
        else:
            yield MatchupsState.fetch_matchups(w)

    @rx.event
    async def change_week_str(self, val: str):
        s = str(val).strip() if val is not None else ""
        if not s or not s.lstrip("-").isdigit():
            return
        try:
            w = int(s)
        except (TypeError, ValueError):
            return
        if self.available_weeks and w not in self.available_weeks:
            return
        self.selected_week = w
        from app.states.app_state import AppState

        app_state = await self.get_state(AppState)
        if not app_state.selected_league_id:
            await self._load_all_matchups_for_current_season()
        else:
            yield MatchupsState.fetch_matchups(w)

    @rx.event
    async def fetch_matchups(self, week: int):
        app_state = await self.get_state(AppState)
        league_id = app_state.selected_league_id
        if not league_id:
            # All-leagues view
            yield MatchupsState.fetch_all_matchups
            return
        try:
            w = int(week)
        except Exception:
            logging.exception("bad week")
            return
        client = get_supabase_client()
        if not client:
            self.matchups_data = []
            self.paired_matchups = []
            return
        try:
            mgr_map = self._load_managers_map(client, [league_id])
            res = (
                client.table("matchup_week_stats")
                .select("league_id,week,matchup_id,roster_id,points")
                .eq("league_id", league_id)
                .eq("week", w)
                .execute()
            )
            rows = res.data if res and res.data else []
        except Exception as e:
            logging.exception(f"fetch matchups failed: {e}")
            rows = []

        pairs: dict[int, list[dict]] = {}
        for m in rows:
            mid_raw = m.get("matchup_id")
            try:
                mid = int(mid_raw) if mid_raw is not None else 0
            except Exception:
                logging.exception("bad mid")
                mid = 0
            pairs.setdefault(mid, []).append(m)

        paired_list = []
        for mid, teams in pairs.items():
            if len(teams) >= 2:
                paired_list.append(
                    self._build_pair_entry(
                        mid, teams[0], teams[1], mgr_map, league_id
                    )
                )
            elif len(teams) == 1:
                paired_list.append(
                    self._build_pair_entry(
                        mid, teams[0], None, mgr_map, league_id
                    )
                )
        paired_list.sort(key=lambda x: x["matchup_id"])
        self.matchups_data = rows
        self.paired_matchups = paired_list

    @rx.event
    async def fetch_standings(self):
        app_state = await self.get_state(AppState)
        league_id = app_state.selected_league_id
        if not league_id:
            return
        users = get_league_users(league_id)
        rosters = get_rosters(league_id)
        if users:
            self.league_users = users
        if rosters:
            self.league_rosters = rosters
        user_map = {u.get("user_id"): u for u in self.league_users}
        standings = []
        for r in self.league_rosters:
            owner_id = r.get("owner_id")
            owner = user_map.get(owner_id, {})
            settings = r.get("settings", {})
            wins = settings.get("wins", 0)
            losses = settings.get("losses", 0)
            ties = settings.get("ties", 0)
            fpts = (
                settings.get("fpts", 0) + settings.get("fpts_decimal", 0) / 100
            )
            fpts_against = (
                settings.get("fpts_against", 0)
                + settings.get("fpts_against_decimal", 0) / 100
            )
            total_games = wins + losses + ties
            win_pct = wins / total_games if total_games > 0 else 0
            team_name = owner.get("metadata", {}).get("team_name")
            display_name = owner.get(
                "display_name", f"Team {r.get('roster_id')}"
            )
            standings.append(
                {
                    "roster_id": r.get("roster_id"),
                    "team_name": team_name if team_name else display_name,
                    "owner_name": display_name,
                    "avatar": owner.get("avatar", ""),
                    "wins": wins,
                    "losses": losses,
                    "ties": ties,
                    "win_pct": round(win_pct, 3),
                    "fpts": round(fpts, 2),
                    "fpts_against": round(fpts_against, 2),
                }
            )
        standings.sort(key=lambda x: (x["wins"], x["fpts"]), reverse=True)
        for i, s in enumerate(standings):
            s["rank"] = i + 1
        self.standings_data = standings

    @rx.event
    def view_roster(self, roster_id: int):
        for r in self.league_rosters:
            if r.get("roster_id") == roster_id:
                user_map = {u.get("user_id"): u for u in self.league_users}
                owner_id = r.get("owner_id")
                owner = user_map.get(owner_id, {})
                r_enriched = r.copy()
                team_name = owner.get("metadata", {}).get("team_name")
                r_enriched["team_name"] = (
                    team_name
                    if team_name
                    else owner.get("display_name", f"Team {roster_id}")
                )
                r_enriched["owner_name"] = owner.get("display_name", "Unknown")
                r_enriched["starters"] = enrich_roster_players(
                    r_enriched.get("starters", [])
                )
                r_enriched["reserve"] = enrich_roster_players(
                    r_enriched.get("reserve", [])
                )
                self.selected_roster = r_enriched
                return rx.redirect("/rosters")

    @rx.event
    def clear_selected_roster(self):
        self.selected_roster = {}
