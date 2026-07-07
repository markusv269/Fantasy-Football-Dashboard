import reflex as rx
from app.supabase_client import get_supabase_client
import logging


class LeagueDetailState(rx.State):
    show_modal: bool = False
    modal_league_id: str = ""
    modal_league_name: str = ""
    modal_league_type: str = ""
    modal_league_season: str = ""
    modal_standings: list[dict[str, str | int | float]] = []
    modal_recent_matchups: list[
        dict[str, str | int | float | bool | list[str]]
    ] = []
    modal_champion: dict[str, str | int | float | None] = {}
    modal_roster_positions: list[str] = []
    modal_loading: bool = False

    @rx.event
    async def open_league_modal(self, league_id: str):
        from app.states.app_state import AppState

        clean_id = str(league_id).strip('"').strip()
        self.show_modal = True
        self.modal_loading = True
        self.modal_league_id = clean_id
        self.modal_standings = []
        self.modal_recent_matchups = []
        self.modal_champion = {}
        self.modal_roster_positions = []
        self.modal_league_name = ""
        self.modal_league_type = ""
        self.modal_league_season = ""

        try:
            app_state = await self.get_state(AppState)
            lg_info = None
            for lg in app_state.leagues_data:
                if str(lg.get("league_id", "")) == clean_id:
                    lg_info = lg
                    break
            if lg_info:
                self.modal_league_name = str(lg_info.get("name", "") or "")
                self.modal_league_type = str(lg_info.get("status", "") or "")
                self.modal_league_season = str(lg_info.get("season", "") or "")

            client = get_supabase_client()
            if not client:
                return

            st: list[dict] = []
            paired_list: list[dict] = []
            champion_data: dict = {}
            roster_pos: list[str] = []

            max_res = (
                client.table("rosters")
                .select("week")
                .eq("league_id", clean_id)
                .order("week", desc=True)
                .limit(1)
                .execute()
            )
            latest_week = (
                max_res.data[0].get("week", 1)
                if (max_res and max_res.data)
                else 1
            )

            standings_res = (
                client.table("rosters")
                .select("*")
                .eq("league_id", clean_id)
                .eq("week", latest_week)
                .order("wins", desc=True)
                .order("fpts_for", desc=True)
                .execute()
            )
            managers_res = (
                client.table("managers")
                .select("*")
                .eq("league_id", clean_id)
                .execute()
            )
            mgr_map = {
                m.get("roster_id"): m
                for m in (managers_res.data if managers_res else [])
            }

            if standings_res and standings_res.data:
                for i, r in enumerate(standings_res.data):
                    rid = r.get("roster_id")
                    mgr = mgr_map.get(rid, {})
                    st.append(
                        {
                            "rank": i + 1,
                            "team_name": str(
                                mgr.get("team_name")
                                or mgr.get("display_name")
                                or f"Team {rid}"
                            ),
                            "display_name": str(
                                mgr.get("display_name") or f"Manager {rid}"
                            ),
                            "wins": int(r.get("wins") or 0),
                            "losses": int(r.get("losses") or 0),
                            "ties": int(r.get("ties") or 0),
                            "fpts_for": float(r.get("fpts_for") or 0.0),
                            "fpts_against": float(r.get("fpts_against") or 0.0),
                        }
                    )

            matchups_res = (
                client.table("matchup_week_stats")
                .select("*")
                .eq("league_id", clean_id)
                .eq("week", latest_week)
                .execute()
            )
            if matchups_res and matchups_res.data:
                pairs: dict = {}
                for m in matchups_res.data:
                    mid = m.get("matchup_id")
                    pairs.setdefault(mid, []).append(m)
                for mid, teams in pairs.items():
                    if len(teams) >= 2:
                        t1, t2 = teams[0], teams[1]
                        m1 = mgr_map.get(t1.get("roster_id"), {})
                        m2 = mgr_map.get(t2.get("roster_id"), {})
                        paired_list.append(
                            {
                                "matchup_id": int(mid)
                                if mid is not None
                                else 0,
                                "week": int(latest_week),
                                "team_a_name": str(
                                    m1.get("team_name")
                                    or m1.get("display_name")
                                    or f"Team {t1.get('roster_id')}"
                                ),
                                "team_a_points": float(t1.get("points") or 0.0),
                                "team_b_name": str(
                                    m2.get("team_name")
                                    or m2.get("display_name")
                                    or f"Team {t2.get('roster_id')}"
                                ),
                                "team_b_points": float(t2.get("points") or 0.0),
                            }
                        )

            try:
                champ_res = (
                    client.table("league_champion")
                    .select("*")
                    .eq("league_id", clean_id)
                    .limit(1)
                    .execute()
                )
                if champ_res and champ_res.data:
                    raw = champ_res.data[0]
                    champion_data = {
                        "team_name": str(
                            raw.get("team_name")
                            or raw.get("display_name")
                            or ""
                        ),
                        "display_name": str(raw.get("display_name") or ""),
                    }
            except Exception as e:
                logging.exception(f"Champion fetch failed: {e}")

            try:
                leagues_res = (
                    client.table("leagues")
                    .select("roster_positions")
                    .eq("league_id", clean_id)
                    .limit(1)
                    .execute()
                )
                if leagues_res and leagues_res.data:
                    rp = leagues_res.data[0].get("roster_positions") or []
                    roster_pos = [str(x) for x in rp]
            except Exception as e:
                logging.exception(f"Roster positions fetch failed: {e}")

            self.modal_standings = st
            self.modal_recent_matchups = paired_list
            self.modal_champion = champion_data
            self.modal_roster_positions = roster_pos
        except Exception as e:
            logging.exception(f"Error fetching league detail: {e}")
        finally:
            self.modal_loading = False

    @rx.event
    def close_league_modal(self):
        self.show_modal = False
        self.modal_league_id = ""
        self.modal_standings = []
        self.modal_recent_matchups = []
        self.modal_champion = {}
        self.modal_roster_positions = []
        self.modal_loading = False
