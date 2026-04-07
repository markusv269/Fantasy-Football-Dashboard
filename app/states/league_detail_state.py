import reflex as rx
from typing import Any
from app.supabase_client import get_supabase_client
import logging


class LeagueDetailState(rx.State):
    show_modal: bool = False
    modal_league_id: str = ""
    modal_league_name: str = ""
    modal_league_type: str = ""
    modal_league_season: str = ""
    modal_standings: list[dict[str, str | int | float]] = []
    modal_recent_matchups: list[dict[str, str | int | float | bool | list[str]]] = []
    modal_champion: dict[str, str] = {}
    modal_roster_positions: list[str] = []
    modal_loading: bool = False

    @rx.event(background=True)
    async def open_league_modal(self, league_id: str):
        async with self:
            self.show_modal = True
            self.modal_loading = True
            self.modal_league_id = league_id
            from app.states.app_state import AppState

            app_state = await self.get_state(AppState)
            lg_info = next(
                (
                    lg
                    for lg in app_state.leagues_data
                    if str(lg.get("league_id")) == league_id
                ),
                None,
            )
            if lg_info:
                self.modal_league_name = str(lg_info.get("name", ""))
                self.modal_league_type = str(lg_info.get("status", ""))
                self.modal_league_season = str(lg_info.get("season", ""))
            self.modal_standings = []
            self.modal_recent_matchups = []
            self.modal_champion = {}
            self.modal_roster_positions = []
        client = get_supabase_client()
        if not client:
            async with self:
                self.modal_loading = False
            return
        try:
            standings_data = (
                client.table("rosters")
                .select("*")
                .eq("league_id", league_id)
                .eq("week", 0)
                .order("wins", desc=True)
                .order("fpts_for", desc=True)
                .execute()
            )
            managers_data = (
                client.table("managers")
                .select("*")
                .eq("league_id", league_id)
                .execute()
            )
            mgr_map = {
                m.get("roster_id"): m
                for m in (managers_data.data if managers_data else [])
            }
            if standings_data and standings_data.data:
                st = []
                for i, r in enumerate(standings_data.data):
                    rid = r.get("roster_id")
                    mgr = mgr_map.get(rid, {})
                    st.append(
                        {
                            "rank": i + 1,
                            "team_name": mgr.get("team_name")
                            or mgr.get("display_name", f"Team {rid}"),
                            "display_name": mgr.get("display_name", f"Manager {rid}"),
                            "wins": r.get("wins", 0),
                            "losses": r.get("losses", 0),
                            "ties": r.get("ties", 0),
                            "fpts_for": r.get("fpts_for", 0.0),
                            "fpts_against": r.get("fpts_against", 0.0),
                        }
                    )
                async with self:
                    self.modal_standings = st
            max_week_res = (
                client.table("matchup_week_stats")
                .select("week")
                .eq("league_id", league_id)
                .order("week", desc=True)
                .limit(1)
                .execute()
            )
            if max_week_res and max_week_res.data:
                max_week = max_week_res.data[0].get("week")
                matchups_res = (
                    client.table("matchup_week_stats")
                    .select("*")
                    .eq("league_id", league_id)
                    .eq("week", max_week)
                    .execute()
                )
                if matchups_res and matchups_res.data:
                    pairs = {}
                    for m in matchups_res.data:
                        mid = m.get("matchup_id")
                        if mid not in pairs:
                            pairs[mid] = []
                        pairs[mid].append(m)
                    paired_list = []
                    for mid, teams in pairs.items():
                        if len(teams) >= 2:
                            t1, t2 = (teams[0], teams[1])
                            m1, m2 = (
                                mgr_map.get(t1.get("roster_id"), {}),
                                mgr_map.get(t2.get("roster_id"), {}),
                            )
                            paired_list.append(
                                {
                                    "matchup_id": mid,
                                    "week": max_week,
                                    "team_a_name": m1.get("team_name")
                                    or m1.get(
                                        "display_name", f"Team {t1.get('roster_id')}"
                                    ),
                                    "team_a_points": t1.get("points", 0),
                                    "team_b_name": m2.get("team_name")
                                    or m2.get(
                                        "display_name", f"Team {t2.get('roster_id')}"
                                    ),
                                    "team_b_points": t2.get("points", 0),
                                }
                            )
                    async with self:
                        self.modal_recent_matchups = paired_list
            champ_res = (
                client.table("league_champion")
                .select("*")
                .eq("league_id", league_id)
                .limit(1)
                .execute()
            )
            if champ_res and champ_res.data:
                async with self:
                    self.modal_champion = champ_res.data[0]
            leagues_res = (
                client.table("leagues")
                .select("roster_positions")
                .eq("league_id", league_id)
                .limit(1)
                .execute()
            )
            if leagues_res and leagues_res.data:
                rp = leagues_res.data[0].get("roster_positions")
                async with self:
                    self.modal_roster_positions = rp if isinstance(rp, list) else []
        except Exception as e:
            logging.exception(f"Error fetching league detail: {e}")
        finally:
            async with self:
                self.modal_loading = False

    @rx.event
    def close_league_modal(self):
        self.show_modal = False
        self.modal_league_id = ""
        self.modal_standings = []
        self.modal_recent_matchups = []
        self.modal_champion = {}
        self.modal_roster_positions = []