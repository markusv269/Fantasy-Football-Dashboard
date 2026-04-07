import reflex as rx
import logging
from datetime import datetime
from app.sleeper_api import get_league, get_league_drafts
from app.supabase_client import get_supabase_client


class DraftState(rx.State):
    dynasty_league_ids_2026: list[str] = []
    redraft_league_ids_2026: list[str] = []
    upcoming_drafts: list[dict[str, str | int | float | bool | None]] = []
    historical_drafts: list[dict[str, str | int | float | bool | None]] = []
    is_loading: bool = False
    draft_filter: str = "All"
    show_all_historical: bool = False

    @rx.event
    def init_drafts(self):
        self.is_loading = True
        try:
            client = get_supabase_client()
            if client:
                dynasty_res = (
                    client.table("leagues")
                    .select("league_id")
                    .eq("league_season", 2026)
                    .eq("league_type", "dynasty")
                    .execute()
                )
                if dynasty_res and dynasty_res.data:
                    self.dynasty_league_ids_2026 = [
                        str(lg["league_id"]) for lg in dynasty_res.data
                    ]
                redraft_res = (
                    client.table("leagues")
                    .select("league_id")
                    .eq("league_season", 2026)
                    .eq("league_type", "redraft")
                    .execute()
                )
                if redraft_res and redraft_res.data:
                    self.redraft_league_ids_2026 = [
                        str(lg["league_id"]) for lg in redraft_res.data
                    ]
            all_2026_ids = self.dynasty_league_ids_2026 + self.redraft_league_ids_2026
            upcoming = []
            for lid in all_2026_ids:
                league = get_league(lid)
                league_name = (
                    league.get("name", f"League {lid}") if league else f"League {lid}"
                )
                drafts = get_league_drafts(lid)
                if drafts:
                    for d in drafts:
                        start = d.get("start_time")
                        dt_str = (
                            datetime.fromtimestamp(start / 1000).strftime(
                                "%b %d, %Y · %H:%M"
                            )
                            if start
                            else ""
                        )
                        upcoming.append(
                            {
                                "league_id": lid,
                                "league_name": league_name,
                                "draft_id": d.get("draft_id"),
                                "draft_type": d.get("type", ""),
                                "status": d.get("status", ""),
                                "start_time": int(start) if start else 0,
                                "start_date_str": dt_str,
                                "rounds": d.get("settings", {}).get("rounds", 0),
                                "teams": d.get("settings", {}).get("teams", 0),
                                "metadata_name": d.get("metadata", {}).get("name", ""),
                                "is_dynasty": lid in self.dynasty_league_ids_2026,
                                "is_idp": "IDP" in league_name.upper()
                                or "IDP"
                                in d.get("metadata", {}).get("name", "").upper(),
                                "is_bestball": "BESTBALL" in league_name.upper()
                                or "BB" in league_name.upper(),
                            }
                        )
            upcoming.sort(
                key=lambda x: (x["start_time"] == 0, x["start_time"], x["league_name"])
            )
            self.upcoming_drafts = upcoming
            client = get_supabase_client()
            historical = []
            if client:
                drafts_res = client.table("drafts").select("*").execute()
                leagues_res = (
                    client.table("leagues")
                    .select("league_id, league_name, league_type")
                    .execute()
                )
                league_map = {
                    str(lg["league_id"]): lg
                    for lg in (leagues_res.data if leagues_res else [])
                }
                if drafts_res and drafts_res.data:
                    for d in drafts_res.data:
                        lid = str(d.get("league_id", ""))
                        lg = league_map.get(lid, {})
                        start_ts = d.get("start_time")
                        start_date_str = ""
                        if start_ts:
                            try:
                                dt = datetime.fromisoformat(
                                    start_ts.replace("Z", "+00:00")
                                )
                                start_date_str = dt.strftime("%b %d, %Y")
                            except:
                                logging.exception("Unexpected error")
                                start_date_str = start_ts[:10]
                        raw_dt_type = d.get("draft_type")
                        dt_type = str(raw_dt_type) if raw_dt_type is not None else ""
                        type_str = (
                            "Snake"
                            if dt_type == "0"
                            else "Linear"
                            if dt_type == "1"
                            else "Auction"
                            if dt_type == "2"
                            else "Unknown"
                        )
                        historical.append(
                            {
                                "draft_id": d.get("draft_id"),
                                "league_id": lid,
                                "league_name": lg.get("league_name", f"League {lid}"),
                                "league_type": lg.get("league_type", ""),
                                "season": d.get("season", ""),
                                "draft_type": type_str,
                                "status": d.get("status", ""),
                                "start_time": start_ts if start_ts else "",
                                "start_date_str": start_date_str,
                            }
                        )
                historical.sort(key=lambda x: x["start_time"], reverse=True)
                self.historical_drafts = historical
        except Exception as e:
            logging.exception(f"Error initializing drafts: {e}")
        finally:
            self.is_loading = False

    @rx.event
    def set_draft_filter(self, new_filter: str):
        self.draft_filter = new_filter

    @rx.event
    def toggle_historical(self):
        self.show_all_historical = not self.show_all_historical

    @rx.var
    def filtered_upcoming(self) -> list[dict[str, str | int | float | bool | None]]:
        res = []
        for d in self.upcoming_drafts:
            if self.draft_filter == "Scheduled" and int(d["start_time"]) == 0:
                continue
            if self.draft_filter == "Unscheduled" and int(d["start_time"]) > 0:
                continue
            if self.draft_filter == "Dynasty" and (not d["is_dynasty"]):
                continue
            if self.draft_filter == "Redraft" and d["is_dynasty"]:
                continue
            if self.draft_filter == "IDP" and (not d["is_idp"]):
                continue
            res.append(d)
        return res

    @rx.var
    def scheduled_count(self) -> int:
        return sum((1 for d in self.upcoming_drafts if int(d["start_time"]) > 0))

    @rx.var
    def unscheduled_count(self) -> int:
        return sum((1 for d in self.upcoming_drafts if int(d["start_time"]) == 0))