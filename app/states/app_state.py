import reflex as rx
from app.sleeper_api import get_nfl_state, get_league, get_trending_players
from app.player_cache import enrich_trending
import logging
from app.supabase_client import get_supabase_client


def league_sort_key(lg: dict) -> tuple:
    """Consistent league ordering: season DESC, league_sort ASC (nulls last), name ASC.

    Works for both AppState-normalized dicts (season/name/league_sort keys)
    and Supabase raw rows (league_season/league_name/league_sort).
    """
    season_raw = lg.get("season", lg.get("league_season", ""))
    try:
        season_int = int(season_raw)
    except Exception:
        logging.exception("Unexpected error")
        season_int = 0
    ls_raw = lg.get("league_sort")
    try:
        ls_int = int(ls_raw) if ls_raw is not None else None
    except Exception:
        logging.exception("Unexpected error")
        ls_int = None
    is_null = ls_int is None or ls_int < 0
    name = str(lg.get("name", lg.get("league_name", "")) or "").lower()
    return (-season_int, is_null, ls_int if ls_int is not None else 10**9, name)


class AppState(rx.State):
    configured_league_ids: list[str] = []
    nfl_state: dict[str, str | int | bool] = {}
    leagues_data: list[dict[str, str | int | dict | list | None]] = []
    selected_league_id: str = ""
    trending_adds: list[dict[str, str | int]] = []
    is_loading: bool = False
    is_full_loaded: bool = False
    search_query: str = ""
    filter_type: str = "All"

    @rx.event
    def fetch_nfl_state(self):
        state = get_nfl_state()
        if state:
            cleaned = {}
            for k, v in state.items():
                if v is None:
                    cleaned[k] = ""
                else:
                    cleaned[k] = v
            self.nfl_state = cleaned

    @rx.event
    def fetch_trending(self):
        trending = get_trending_players(limit=5)
        if trending:
            self.trending_adds = enrich_trending(trending)

    def _normalize_league(
        self, lg: dict, live_data: dict | None = None
    ) -> dict:
        """Normalize a Supabase league row to the shape the UI expects.

        The Supabase `leagues` table has no `avatar` column — we tolerate
        its absence and rely on the UI's placeholder fallback. When live
        Sleeper data is available (small sets only), we opportunistically
        enrich the row with the live avatar and total_rosters.
        """
        raw_id = str(lg.get("league_id", "") or "")
        league_id = raw_id.strip('"').strip()
        name = str(
            lg.get("league_name") or lg.get("name") or f"League {league_id}"
        )
        season = str(lg.get("league_season") or lg.get("season") or "")
        status = str(lg.get("league_type") or lg.get("status") or "unknown")
        avatar = ""
        total_rosters = ""
        raw_sort = lg.get("league_sort")
        try:
            league_sort = int(raw_sort) if raw_sort is not None else -1
        except Exception:
            logging.exception("Unexpected error")
            league_sort = -1
        if live_data:
            name = str(live_data.get("name") or name)
            live_season = live_data.get("season")
            if live_season not in (None, ""):
                season = str(live_season)
            live_status = live_data.get("status")
            if live_status:
                status = str(live_status)
            avatar = str(live_data.get("avatar") or "")
            live_total = live_data.get("total_rosters")
            if live_total not in (None, ""):
                total_rosters = str(live_total)
        return {
            "league_id": league_id,
            "name": name,
            "season": season,
            "status": status,
            "total_rosters": total_rosters,
            "avatar": avatar,
            "league_sort": league_sort,
        }

    @rx.event
    def fetch_all_leagues_data(self):
        self.is_loading = True
        yield
        client = get_supabase_client()
        if client:
            try:
                result = client.table("leagues").select("*").execute()
                if result and result.data:
                    raw_leagues = result.data
                    use_live = len(raw_leagues) <= 10
                    normalized = []
                    for lg in raw_leagues:
                        live_data = None
                        if use_live:
                            try:
                                live_data = get_league(lg.get("league_id", ""))
                            except Exception as e:
                                logging.exception(
                                    f"Failed to fetch live league data: {e}"
                                )
                        normalized.append(self._normalize_league(lg, live_data))
                    normalized.sort(key=league_sort_key)
                    self.leagues_data = normalized
                    self.configured_league_ids = [
                        lg["league_id"] for lg in normalized
                    ]
                    self.is_full_loaded = True
                else:
                    self.leagues_data = []
                    self.configured_league_ids = []
            except Exception as e:
                logging.exception(f"Error fetching leagues from Supabase: {e}")
        self.is_loading = False

    @rx.event
    def fetch_current_season_leagues(self):
        """Load only the leagues of the current (max) season. Fast initial load."""
        self.is_loading = True
        yield
        client = get_supabase_client()
        if client:
            try:
                max_res = (
                    client.table("leagues")
                    .select("league_season")
                    .order("league_season", desc=True)
                    .limit(1)
                    .execute()
                )
                max_season = None
                if max_res and max_res.data:
                    max_season = max_res.data[0].get("league_season")
                if max_season is not None:
                    res = (
                        client.table("leagues")
                        .select("*")
                        .eq("league_season", max_season)
                        .execute()
                    )
                    raw_leagues = res.data if res and res.data else []
                    normalized = [
                        self._normalize_league(lg) for lg in raw_leagues
                    ]
                    normalized.sort(key=league_sort_key)
                    self.leagues_data = normalized
                    self.configured_league_ids = [
                        lg["league_id"] for lg in normalized
                    ]
                    self.is_full_loaded = False
            except Exception as e:
                logging.exception(f"Error fetching current season: {e}")
        self.is_loading = False

    @rx.event
    def ensure_all_leagues_loaded(self):
        """Trigger full load if not already loaded."""
        if not self.is_full_loaded:
            yield AppState.fetch_all_leagues_data

    @rx.event
    def select_league(self, league_id: str):
        self.selected_league_id = league_id.strip('"')

    @rx.event
    def init_app(self):
        yield AppState.fetch_nfl_state
        yield AppState.fetch_trending
        yield AppState.fetch_current_season_leagues

    @rx.var
    def current_season(self) -> str:
        seasons: list[int] = []
        for lg in self.leagues_data:
            s = str(lg.get("season", ""))
            if s.isdigit():
                seasons.append(int(s))
        if seasons:
            return str(max(seasons))
        nfl_season = self.nfl_state.get("season", "")
        if nfl_season:
            return str(nfl_season)
        return ""

    @rx.var
    def current_dynasty_leagues(
        self,
    ) -> list[dict[str, str | int | dict | list | None]]:
        cs = self.current_season
        return [
            lg
            for lg in self.leagues_data
            if str(lg.get("season", "")) == cs
            and str(lg.get("status", "")).lower() == "dynasty"
        ]

    @rx.var
    def current_redraft_leagues(
        self,
    ) -> list[dict[str, str | int | dict | list | None]]:
        cs = self.current_season
        return [
            lg
            for lg in self.leagues_data
            if str(lg.get("season", "")) == cs
            and str(lg.get("status", "")).lower() == "redraft"
        ]

    @rx.var
    def archived_leagues(
        self,
    ) -> list[dict[str, str | int | dict | list | None]]:
        cs = self.current_season
        return [
            lg for lg in self.leagues_data if str(lg.get("season", "")) != cs
        ]

    @rx.var
    def archive_seasons(self) -> list[str]:
        seasons = {str(lg.get("season", "")) for lg in self.archived_leagues}
        seasons.discard("")
        return sorted(seasons, reverse=True)

    @rx.var
    def archived_dynasty_leagues(
        self,
    ) -> list[dict[str, str | int | dict | list | None]]:
        return [
            lg
            for lg in self.archived_leagues
            if str(lg.get("status", "")).lower() == "dynasty"
        ]

    @rx.var
    def archived_redraft_leagues(
        self,
    ) -> list[dict[str, str | int | dict | list | None]]:
        return [
            lg
            for lg in self.archived_leagues
            if str(lg.get("status", "")).lower() == "redraft"
        ]

    @rx.var
    def archived_other_leagues(
        self,
    ) -> list[dict[str, str | int | dict | list | None]]:
        return [
            lg
            for lg in self.archived_leagues
            if str(lg.get("status", "")).lower() not in ("dynasty", "redraft")
        ]
