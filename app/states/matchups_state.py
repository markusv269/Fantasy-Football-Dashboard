import reflex as rx
from app.states.app_state import AppState
from app.sleeper_api import get_matchups, get_rosters, get_league_users
from app.player_cache import enrich_roster_players


class MatchupsState(rx.State):
    selected_week: int = 1
    matchups_data: list[dict[str, str | int | float | list | dict | None]] = []
    paired_matchups: list[dict[str, str | int | float | list | dict | None]] = []
    league_users: list[dict[str, str | int | float | list | dict | None]] = []
    league_rosters: list[dict[str, str | int | float | list | dict | None]] = []
    standings_data: list[
        dict[str, str | int | float | list | dict | list[str] | None]
    ] = []
    selected_roster: dict[str, str | int | float | list | dict | list[str] | None] = {}

    @rx.event
    async def init_matchups(self):
        app_state = await self.get_state(AppState)
        week = app_state.nfl_state.get("week", 1)
        if str(week) == "0":
            week = 1
        self.selected_week = int(week)
        if app_state.selected_league_id:
            yield MatchupsState.fetch_league_detail
            yield MatchupsState.fetch_matchups(self.selected_week)

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
    def change_week(self, week: int):
        self.selected_week = week
        yield MatchupsState.fetch_matchups(week)

    @rx.event
    async def fetch_matchups(self, week: int):
        app_state = await self.get_state(AppState)
        league_id = app_state.selected_league_id
        if not league_id:
            return
        if not self.league_users or not self.league_rosters:
            users = get_league_users(league_id)
            rosters = get_rosters(league_id)
            if users:
                self.league_users = users
            if rosters:
                self.league_rosters = rosters
        matchups = get_matchups(league_id, week)
        if not matchups:
            self.matchups_data = []
            self.paired_matchups = []
            return
        self.matchups_data = matchups
        user_map = {u.get("user_id"): u for u in self.league_users}
        roster_map = {r.get("roster_id"): r for r in self.league_rosters}
        pairs = {}
        for m in matchups:
            mid = m.get("matchup_id")
            if mid not in pairs:
                pairs[mid] = []
            roster_id = m.get("roster_id")
            roster = roster_map.get(roster_id, {})
            owner_id = roster.get("owner_id")
            owner = user_map.get(owner_id, {})
            team_name = owner.get("metadata", {}).get("team_name")
            display_name = owner.get("display_name", f"Team {roster_id}")
            m_enriched = m.copy()
            m_enriched["team_name"] = team_name if team_name else display_name
            m_enriched["owner_name"] = display_name
            m_enriched["avatar"] = owner.get("avatar", "")
            pairs[mid].append(m_enriched)
        paired_list = []
        for mid, teams in pairs.items():
            if len(teams) == 2:
                paired_list.append(
                    {"matchup_id": mid, "team_a": teams[0], "team_b": teams[1]}
                )
            elif len(teams) == 1:
                paired_list.append(
                    {"matchup_id": mid, "team_a": teams[0], "team_b": None}
                )
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
            fpts = settings.get("fpts", 0) + settings.get("fpts_decimal", 0) / 100
            fpts_against = (
                settings.get("fpts_against", 0)
                + settings.get("fpts_against_decimal", 0) / 100
            )
            total_games = wins + losses + ties
            win_pct = wins / total_games if total_games > 0 else 0
            team_name = owner.get("metadata", {}).get("team_name")
            display_name = owner.get("display_name", f"Team {r.get('roster_id')}")
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