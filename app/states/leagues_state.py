import reflex as rx
import logging
from app.supabase_client import get_supabase_client


class LeaguesState(rx.State):
    is_loading: bool = False
    all_leagues: list[dict[str, str | int | list[str]]] = []
    available_seasons: list[str] = []
    available_types: list[str] = []
    available_managers: list[str] = []
    manager_to_leagues: dict[str, list[str]] = {}

    selected_season: str = "all"
    selected_type: str = "all"
    selected_manager: str = "all"
    selected_week: str = "all"
    selected_scope: str = "all"
    search_query: str = ""
    sort_by: str = "season_desc"

    @rx.event
    def load_leagues(self):
        self.is_loading = True
        yield
        try:
            client = get_supabase_client()
            if not client:
                self.is_loading = False
                return
            res = (
                client.table("leagues")
                .select("league_id,league_name,league_season,league_type")
                .order("league_season", desc=True)
                .execute()
            )
            leagues_rows = res.data if res and res.data else []
            all_ids = [str(lg.get("league_id", "")) for lg in leagues_rows]

            mgr_map: dict[str, list[dict]] = {}
            try:
                batch = 200
                for i in range(0, len(all_ids), batch):
                    chunk = all_ids[i : i + batch]
                    if not chunk:
                        continue
                    mres = (
                        client.table("managers")
                        .select("league_id,display_name,team_name")
                        .in_("league_id", chunk)
                        .execute()
                    )
                    if mres and mres.data:
                        for m in mres.data:
                            lid = str(m.get("league_id", ""))
                            mgr_map.setdefault(lid, []).append(m)
            except Exception as e:
                logging.exception(f"managers fetch failed: {e}")

            weeks_by_league: dict[str, set[int]] = {}
            try:
                batch = 100
                for i in range(0, len(all_ids), batch):
                    chunk = all_ids[i : i + batch]
                    if not chunk:
                        continue
                    try:
                        wres = (
                            client.table("matchup_week_stats")
                            .select("league_id,week")
                            .in_("league_id", chunk)
                            .execute()
                        )
                        if wres and wres.data:
                            for row in wres.data:
                                lid = str(row.get("league_id", ""))
                                w = row.get("week")
                                if w is not None:
                                    try:
                                        weeks_by_league.setdefault(
                                            lid, set()
                                        ).add(int(w))
                                    except Exception:
                                        logging.exception("bad week")
                    except Exception as e:
                        logging.exception(f"matchup weeks fetch failed: {e}")
                    try:
                        rres = (
                            client.table("rosters")
                            .select("league_id,week")
                            .in_("league_id", chunk)
                            .execute()
                        )
                        if rres and rres.data:
                            for row in rres.data:
                                lid = str(row.get("league_id", ""))
                                w = row.get("week")
                                if w is not None:
                                    try:
                                        weeks_by_league.setdefault(
                                            lid, set()
                                        ).add(int(w))
                                    except Exception:
                                        logging.exception("bad week r")
                    except Exception as e:
                        logging.exception(f"roster weeks fetch failed: {e}")
            except Exception as e:
                logging.exception(f"weeks batch loop failed: {e}")

            manager_to_leagues: dict[str, list[str]] = {}
            all_manager_names: set[str] = set()
            leagues_out: list[dict] = []
            for lg in leagues_rows:
                lid = str(lg.get("league_id", ""))
                mgrs = mgr_map.get(lid, [])
                names = []
                for m in mgrs:
                    n = str(
                        m.get("display_name") or m.get("team_name") or ""
                    ).strip()
                    if n:
                        names.append(n)
                unique_names = list(dict.fromkeys(names))
                for n in unique_names:
                    all_manager_names.add(n)
                    manager_to_leagues.setdefault(n, []).append(lid)
                weeks_set = weeks_by_league.get(lid, set())
                weeks_sorted = sorted(weeks_set)
                latest_week = max(weeks_sorted) if weeks_sorted else 0
                leagues_out.append(
                    {
                        "league_id": lid,
                        "league_name": str(
                            lg.get("league_name") or f"Liga {lid}"
                        ),
                        "season": str(lg.get("league_season") or ""),
                        "type": str(lg.get("league_type") or "unknown"),
                        "manager_count": len(unique_names),
                        "manager_sample": ", ".join(unique_names[:3]),
                        "manager_names": unique_names,
                        "available_weeks": [str(w) for w in weeks_sorted],
                        "latest_week": latest_week,
                    }
                )

            self.all_leagues = leagues_out
            self.manager_to_leagues = manager_to_leagues
            self.available_seasons = sorted(
                {lg["season"] for lg in leagues_out if lg["season"]},
                reverse=True,
            )
            self.available_types = sorted(
                {lg["type"] for lg in leagues_out if lg["type"]}
            )
            self.available_managers = sorted(
                all_manager_names, key=lambda x: x.lower()
            )
        except Exception as e:
            logging.exception(f"Error loading leagues page: {e}")
        finally:
            self.is_loading = False

    @rx.event
    def set_selected_season(self, val: str):
        self.selected_season = val

    @rx.event
    def set_selected_type(self, val: str):
        self.selected_type = val

    @rx.event
    def set_selected_manager(self, val: str):
        self.selected_manager = val

    @rx.event
    def set_selected_week(self, val: str):
        self.selected_week = val

    @rx.event
    def set_selected_scope(self, val: str):
        self.selected_scope = val

    @rx.event
    def set_search_query(self, val: str):
        self.search_query = val

    @rx.event
    def set_sort_by(self, val: str):
        self.sort_by = val

    @rx.event
    def reset_filters(self):
        self.selected_season = "all"
        self.selected_type = "all"
        self.selected_manager = "all"
        self.selected_week = "all"
        self.selected_scope = "all"
        self.search_query = ""
        self.sort_by = "season_desc"

    @rx.event
    def clear_season(self):
        self.selected_season = "all"

    @rx.event
    def clear_type(self):
        self.selected_type = "all"

    @rx.event
    def clear_manager(self):
        self.selected_manager = "all"

    @rx.event
    def clear_week(self):
        self.selected_week = "all"

    @rx.event
    def clear_scope(self):
        self.selected_scope = "all"

    @rx.event
    def clear_search(self):
        self.search_query = ""

    @rx.var
    def has_active_filters(self) -> bool:
        return (
            self.selected_season != "all"
            or self.selected_type != "all"
            or self.selected_manager != "all"
            or self.selected_week != "all"
            or self.selected_scope != "all"
            or self.search_query != ""
        )

    @rx.var
    def active_filter_count(self) -> int:
        n = 0
        if self.selected_season != "all":
            n += 1
        if self.selected_type != "all":
            n += 1
        if self.selected_manager != "all":
            n += 1
        if self.selected_week != "all":
            n += 1
        if self.selected_scope != "all":
            n += 1
        if self.search_query != "":
            n += 1
        return n

    @rx.var
    def total_count(self) -> int:
        return len(self.all_leagues)

    async def _get_user_league_ids(self) -> set[str]:
        try:
            from app.states.user_state import UserState

            u = await self.get_state(UserState)
            return {str(x) for x in u.user_league_ids}
        except Exception as e:
            logging.exception(f"user leagues fetch failed: {e}")
            return set()

    async def _is_logged_in(self) -> bool:
        try:
            from app.states.user_state import UserState

            u = await self.get_state(UserState)
            return bool(u.is_logged_in)
        except Exception:
            logging.exception("login check failed")
            return False

    @rx.var
    async def filtered_leagues(self) -> list[dict[str, str | int]]:
        user_ids: set[str] = set()
        logged_in = await self._is_logged_in()
        if logged_in and self.selected_scope != "all":
            user_ids = await self._get_user_league_ids()

        q = self.search_query.lower().strip()
        mgr_league_ids: set[str] = set()
        if self.selected_manager != "all":
            mgr_league_ids = set(
                self.manager_to_leagues.get(self.selected_manager, [])
            )
        try:
            week_int = (
                int(self.selected_week) if self.selected_week != "all" else None
            )
        except Exception:
            logging.exception("bad week filter")
            week_int = None

        result = []
        for lg in self.all_leagues:
            if (
                self.selected_season != "all"
                and lg["season"] != self.selected_season
            ):
                continue
            if self.selected_type != "all" and lg["type"] != self.selected_type:
                continue
            if (
                self.selected_manager != "all"
                and lg["league_id"] not in mgr_league_ids
            ):
                continue
            if week_int is not None:
                weeks = lg.get("available_weeks", [])
                if str(week_int) not in weeks:
                    continue
            if logged_in and self.selected_scope == "mine":
                if lg["league_id"] not in user_ids:
                    continue
            if logged_in and self.selected_scope == "others":
                if lg["league_id"] in user_ids:
                    continue
            if q:
                names_str = " ".join(lg.get("manager_names", [])).lower()
                haystack = (
                    f"{lg['league_name']} {lg['season']} {lg['type']} "
                    f"{lg['league_id']} {names_str}"
                ).lower()
                if q not in haystack:
                    continue
            result.append(lg)

        def _season_int(x):
            s = str(x.get("season") or "0")
            try:
                return int(s) if s.isdigit() else 0
            except Exception:
                logging.exception("bad season sort")
                return 0

        sort_by = self.sort_by
        if sort_by == "season_desc":
            result.sort(
                key=lambda x: (
                    -_season_int(x),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "season_asc":
            result.sort(
                key=lambda x: (
                    _season_int(x),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "name_asc":
            result.sort(key=lambda x: str(x.get("league_name") or "").lower())
        elif sort_by == "name_desc":
            result.sort(
                key=lambda x: str(x.get("league_name") or "").lower(),
                reverse=True,
            )
        elif sort_by == "managers_desc":
            result.sort(
                key=lambda x: (
                    -int(x.get("manager_count") or 0),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "managers_asc":
            result.sort(
                key=lambda x: (
                    int(x.get("manager_count") or 0),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "week_desc":
            result.sort(
                key=lambda x: (
                    -int(x.get("latest_week") or 0),
                    -_season_int(x),
                )
            )
        elif sort_by == "week_asc":
            result.sort(
                key=lambda x: (
                    int(x.get("latest_week") or 0)
                    if int(x.get("latest_week") or 0) > 0
                    else 9999,
                    -_season_int(x),
                )
            )
        return result

    @rx.var
    async def result_count(self) -> int:
        rows = await self.filtered_leagues
        return len(rows)
