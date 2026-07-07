import reflex as rx
from app.sleeper_api import get_nfl_state, get_league, get_trending_players
from app.player_cache import enrich_trending
import logging
from app.supabase_client import get_supabase_client


class AppState(rx.State):
    configured_league_ids: list[str] = []
    nfl_state: dict[str, str | int | bool] = {}
    leagues_data: list[dict[str, str | int | dict | list | None]] = []
    selected_league_id: str = ""
    trending_adds: list[dict[str, str | int]] = []
    is_loading: bool = False
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
        """Normalize a Supabase league row to the shape the UI expects."""
        raw_id = str(lg.get("league_id", ""))
        league_id = raw_id.strip('"').strip()
        name = lg.get("league_name", f"League {league_id}")
        season = str(lg.get("league_season", ""))
        status = lg.get("league_type", "unknown")
        avatar = lg.get("avatar", "") or ""
        total_rosters = ""
        if live_data:
            name = live_data.get("name", name)
            season = str(live_data.get("season", season))
            status = live_data.get("status", status)
            avatar = live_data.get("avatar", "") or ""
            total_rosters = str(live_data.get("total_rosters", ""))
        return {
            "league_id": league_id,
            "name": name,
            "season": season,
            "status": status,
            "total_rosters": total_rosters,
            "avatar": avatar,
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
                    use_live = (
                        len(raw_leagues) <= 10
                    )  # Nur bei 10 oder weniger Ligen Live-Daten abrufen, um Performance zu schonen
                    # use_live = True  # Immer Live-Daten verwenden, um die Genauigkeit zu gewährleisten
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
                    self.leagues_data = normalized
                    self.configured_league_ids = [
                        lg["league_id"] for lg in normalized
                    ]
                else:
                    self.leagues_data = []
                    self.configured_league_ids = []
            except Exception as e:
                logging.exception(f"Error fetching leagues from Supabase: {e}")
        self.is_loading = False

    @rx.event
    def select_league(self, league_id: str):
        self.selected_league_id = league_id.strip(
            '"'
        )  # Remove extra quotes if present

    @rx.event
    def init_app(self):
        yield AppState.fetch_nfl_state
        yield AppState.fetch_trending
        yield AppState.fetch_all_leagues_data

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
