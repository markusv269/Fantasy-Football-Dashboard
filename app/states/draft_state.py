import reflex as rx
import logging
from datetime import datetime
from app.sleeper_api import get_draft, get_draft_picks
from app.supabase_client import get_supabase_client


ACTIVE_STATUSES = {"drafting", "paused"}
SCHEDULED_STATUSES = {"pre_draft"}
COMPLETED_STATUSES = {"complete", "completed"}


def _dtype_label(raw) -> str:
    val = str(raw or "").strip().lower()
    mapping = {
        "0": "Snake",
        "1": "Linear",
        "2": "Auction",
        "snake": "Snake",
        "linear": "Linear",
        "auction": "Auction",
    }
    return mapping.get(val, val.title() or "Unknown")


def _format_start_time(raw) -> tuple[str, int]:
    """Return (display_str, unix_ts_seconds) for a stored start_time value."""
    if raw is None or raw == "":
        return "", 0
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y · %H:%M"), int(dt.timestamp())
    except Exception:
        logging.exception("start_time parse failed")
        return str(raw)[:16], 0


def _detect_flags(league_name: str, league_type: str) -> dict:
    ln = (league_name or "").upper()
    lt = (league_type or "").lower()
    is_bestball = (
        ("BESTBALL" in ln) or ("BEST BALL" in ln) or (lt == "bestball")
    )
    is_idp = "IDP" in ln
    is_dynasty = lt == "dynasty"
    is_redraft = lt == "redraft"
    return {
        "is_dynasty": is_dynasty,
        "is_redraft": is_redraft,
        "is_bestball": is_bestball,
        "is_idp": is_idp,
    }


class DraftState(rx.State):
    is_loading: bool = False
    draft_filter: str = "All"
    show_all_completed: bool = False

    all_drafts: list[dict[str, str | int | float | bool | None]] = []
    active_drafts: list[dict[str, str | int | float | bool | None]] = []
    scheduled_drafts: list[dict[str, str | int | float | bool | None]] = []
    completed_drafts: list[dict[str, str | int | float | bool | None]] = []
    other_drafts: list[dict[str, str | int | float | bool | None]] = []
    season_breakdown: list[dict[str, str | int]] = []

    @rx.event
    def set_draft_filter(self, new_filter: str):
        self.draft_filter = new_filter

    @rx.event
    def toggle_completed(self):
        self.show_all_completed = not self.show_all_completed

    def _build_base_draft(self, d: dict, lg: dict) -> dict:
        lid = str(d.get("league_id", ""))
        league_name = str(lg.get("league_name") or f"League {lid}")
        league_type = str(lg.get("league_type") or "")
        flags = _detect_flags(league_name, league_type)
        start_display, start_ts = _format_start_time(d.get("start_time"))
        draft_id = str(d.get("draft_id") or "")
        status = str(d.get("status") or "unknown").lower()
        return {
            "draft_id": draft_id,
            "league_id": lid,
            "league_name": league_name,
            "league_avatar": str(lg.get("avatar") or ""),
            "league_type": league_type,
            "season": str(d.get("season") or ""),
            "draft_type": _dtype_label(d.get("draft_type")),
            "status": status,
            "status_label": self._status_label(status),
            "start_date_str": start_display,
            "start_time_ts": start_ts,
            "url": f"https://sleeper.com/draft/nfl/{draft_id}"
            if draft_id
            else "",
            "is_dynasty": flags["is_dynasty"],
            "is_redraft": flags["is_redraft"],
            "is_bestball": flags["is_bestball"],
            "is_idp": flags["is_idp"],
            # Live fields defaults (populated for active drafts).
            "is_live": False,
            "last_pick_no": 0,
            "last_round": 0,
            "last_player_name": "",
            "last_player_team": "",
            "last_player_pos": "",
            "next_pick_no": 0,
            "next_round": 0,
            "next_slot": 0,
            "next_roster_id": 0,
            "next_manager_name": "",
            "next_team_name": "",
            "total_picks": 0,
            "total_slots": 0,
            "progress_pct": 0,
            "progress_str": "",
            "rounds": 0,
            "teams": 0,
        }

    def _status_label(self, status: str) -> str:
        s = status.lower()
        if s == "drafting":
            return "LIVE"
        if s == "paused":
            return "PAUSED"
        if s == "pre_draft":
            return "SCHEDULED"
        if s in COMPLETED_STATUSES:
            return "COMPLETED"
        return s.upper() or "UNKNOWN"

    def _enrich_live_draft(self, base: dict, managers_by_league: dict) -> dict:
        """Fetch live Sleeper data and derive live fields."""
        draft_id = base["draft_id"]
        if not draft_id:
            return base
        try:
            live = get_draft(draft_id)
        except Exception as e:
            logging.exception(f"get_draft failed for {draft_id}: {e}")
            live = None
        try:
            picks = get_draft_picks(draft_id) or []
        except Exception as e:
            logging.exception(f"get_draft_picks failed for {draft_id}: {e}")
            picks = []
        if not live:
            return base

        settings = live.get("settings") or {}
        rounds = int(settings.get("rounds") or 0)
        teams = int(settings.get("teams") or 0)
        total_slots = rounds * teams if (rounds and teams) else 0
        slot_to_roster = live.get("slot_to_roster_id") or {}

        total_picks = len(picks)
        last_pick_no = 0
        last_round = 0
        last_name = ""
        last_team = ""
        last_pos = ""
        if picks:
            try:
                sorted_picks = sorted(
                    picks, key=lambda p: int(p.get("pick_no") or 0)
                )
                last = sorted_picks[-1]
                last_pick_no = int(last.get("pick_no") or 0)
                last_round = int(last.get("round") or 0)
                meta = last.get("metadata") or {}
                first = str(meta.get("first_name") or "")
                lname = str(meta.get("last_name") or "")
                last_name = f"{first} {lname}".strip() or str(
                    last.get("player_id") or ""
                )
                last_team = str(meta.get("team") or "")
                last_pos = str(meta.get("position") or "")
            except Exception as e:
                logging.exception(f"last pick parse failed: {e}")

        next_pick_no = last_pick_no + 1 if last_pick_no > 0 else 1
        next_round = 0
        next_slot = 0
        next_roster_id = 0
        if teams > 0 and rounds > 0 and next_pick_no <= total_slots:
            next_round = ((next_pick_no - 1) // teams) + 1
            pos_in_round = ((next_pick_no - 1) % teams) + 1
            dtype = str(live.get("type") or "").lower()
            if dtype == "snake" and next_round % 2 == 0:
                next_slot = teams - pos_in_round + 1
            else:
                next_slot = pos_in_round
            next_roster_id = int(
                slot_to_roster.get(next_slot)
                or slot_to_roster.get(next_slot)
                or 0
            )

        next_manager_name = ""
        next_team_name = ""
        if next_roster_id > 0:
            mgrs = managers_by_league.get(base["league_id"], {})
            m = mgrs.get(next_roster_id) or {}
            next_manager_name = str(m.get("display_name") or "")
            next_team_name = str(m.get("team_name") or next_manager_name or "")

        progress_pct = 0
        if total_slots > 0:
            progress_pct = int(round(total_picks * 100 / total_slots))
        progress_str = (
            f"{total_picks} / {total_slots}"
            if total_slots > 0
            else f"{total_picks} picks"
        )

        base.update(
            {
                "is_live": True,
                "rounds": rounds,
                "teams": teams,
                "total_picks": total_picks,
                "total_slots": total_slots,
                "last_pick_no": last_pick_no,
                "last_round": last_round,
                "last_player_name": last_name,
                "last_player_team": last_team,
                "last_player_pos": last_pos,
                "next_pick_no": next_pick_no
                if next_pick_no <= total_slots or total_slots == 0
                else 0,
                "next_round": next_round,
                "next_slot": next_slot,
                "next_roster_id": next_roster_id,
                "next_manager_name": next_manager_name,
                "next_team_name": next_team_name,
                "progress_pct": progress_pct,
                "progress_str": progress_str,
            }
        )
        return base

    @rx.event
    def init_drafts(self):
        self.is_loading = True
        yield
        try:
            client = get_supabase_client()
            if not client:
                self.is_loading = False
                return

            drafts_res = client.table("drafts").select("*").execute()
            drafts_rows = (
                drafts_res.data if drafts_res and drafts_res.data else []
            )

            leagues_res = (
                client.table("leagues")
                .select(
                    "league_id,league_name,league_type,league_season,"
                    "league_sort,avatar"
                )
                .execute()
            )
            leagues_rows = (
                leagues_res.data if leagues_res and leagues_res.data else []
            )
            league_map = {str(lg["league_id"]): lg for lg in leagues_rows}

            # Identify active drafts to fetch managers for.
            active_league_ids: set[str] = set()
            for d in drafts_rows:
                st = str(d.get("status") or "").lower()
                if st in ACTIVE_STATUSES:
                    lid = str(d.get("league_id") or "")
                    if lid:
                        active_league_ids.add(lid)

            managers_by_league: dict[str, dict[int, dict]] = {}
            if active_league_ids:
                try:
                    ids = list(active_league_ids)
                    batch = 100
                    for i in range(0, len(ids), batch):
                        chunk = ids[i : i + batch]
                        if not chunk:
                            continue
                        mres = (
                            client.table("managers")
                            .select(
                                "league_id,roster_id,display_name,team_name"
                            )
                            .in_("league_id", chunk)
                            .execute()
                        )
                        for m in mres.data or []:
                            lid = str(m.get("league_id") or "")
                            try:
                                rid = int(m.get("roster_id") or 0)
                            except Exception:
                                logging.exception("bad roster_id")
                                rid = 0
                            if lid and rid:
                                managers_by_league.setdefault(lid, {})[rid] = m
                except Exception as e:
                    logging.exception(f"managers fetch failed: {e}")

            active: list[dict] = []
            scheduled: list[dict] = []
            completed: list[dict] = []
            other: list[dict] = []
            all_entries: list[dict] = []

            for d in drafts_rows:
                lid = str(d.get("league_id") or "")
                lg = league_map.get(lid, {})
                base = self._build_base_draft(d, lg)
                st = base["status"]
                if st in ACTIVE_STATUSES:
                    enriched = self._enrich_live_draft(base, managers_by_league)
                    active.append(enriched)
                    all_entries.append(enriched)
                elif st in SCHEDULED_STATUSES:
                    scheduled.append(base)
                    all_entries.append(base)
                elif st in COMPLETED_STATUSES:
                    completed.append(base)
                    all_entries.append(base)
                else:
                    other.append(base)
                    all_entries.append(base)

            active.sort(key=lambda x: str(x.get("league_name") or "").lower())
            scheduled.sort(
                key=lambda x: (
                    x["start_time_ts"] == 0,
                    x["start_time_ts"],
                    str(x.get("league_name") or "").lower(),
                )
            )
            completed.sort(
                key=lambda x: (
                    -int(x.get("season") or 0)
                    if str(x.get("season") or "").lstrip("-").isdigit()
                    else 0,
                    -int(x.get("start_time_ts") or 0),
                    str(x.get("league_name") or "").lower(),
                )
            )
            other.sort(key=lambda x: str(x.get("league_name") or "").lower())

            season_counts: dict[str, int] = {}
            for entry in all_entries:
                s = str(entry.get("season") or "")
                if not s:
                    continue
                season_counts[s] = season_counts.get(s, 0) + 1
            breakdown = [
                {"season": s, "count": c}
                for s, c in sorted(
                    season_counts.items(),
                    key=lambda kv: (
                        -int(kv[0]) if kv[0].lstrip("-").isdigit() else 0
                    ),
                )
            ]

            self.active_drafts = active
            self.scheduled_drafts = scheduled
            self.completed_drafts = completed
            self.other_drafts = other
            self.all_drafts = all_entries
            self.season_breakdown = breakdown
        except Exception as e:
            logging.exception(f"init_drafts failed: {e}")
        finally:
            self.is_loading = False

    def _matches_filter(self, d: dict) -> bool:
        f = self.draft_filter
        if f == "All":
            return True
        if f == "Active":
            return d["status"] in ACTIVE_STATUSES
        if f == "Scheduled":
            return d["status"] in SCHEDULED_STATUSES
        if f == "Completed":
            return d["status"] in COMPLETED_STATUSES
        if f == "Dynasty":
            return bool(d.get("is_dynasty"))
        if f == "Redraft":
            return bool(d.get("is_redraft"))
        if f == "IDP":
            return bool(d.get("is_idp"))
        if f == "Bestball":
            return bool(d.get("is_bestball"))
        return True

    @rx.var
    def filtered_active(
        self,
    ) -> list[dict[str, str | int | float | bool | None]]:
        return [d for d in self.active_drafts if self._matches_filter(d)]

    @rx.var
    def filtered_scheduled(
        self,
    ) -> list[dict[str, str | int | float | bool | None]]:
        return [d for d in self.scheduled_drafts if self._matches_filter(d)]

    @rx.var
    def filtered_completed(
        self,
    ) -> list[dict[str, str | int | float | bool | None]]:
        return [d for d in self.completed_drafts if self._matches_filter(d)]

    @rx.var
    def filtered_other(
        self,
    ) -> list[dict[str, str | int | float | bool | None]]:
        return [d for d in self.other_drafts if self._matches_filter(d)]

    @rx.var
    def active_count(self) -> int:
        return len(self.active_drafts)

    @rx.var
    def scheduled_count(self) -> int:
        return len(self.scheduled_drafts)

    @rx.var
    def completed_count(self) -> int:
        return len(self.completed_drafts)

    @rx.var
    def total_count(self) -> int:
        return len(self.all_drafts)

    @rx.var
    def other_count(self) -> int:
        return len(self.other_drafts)
