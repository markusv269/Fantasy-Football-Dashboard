import reflex as rx
import logging
from datetime import datetime
from app.sleeper_api import get_draft, get_draft_picks, get_league
from app.supabase_client import get_supabase_client
from app.league_types import (
    add_types_col,
    is_missing_league_types_column_error,
    normalize_league_types,
)


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


def _detect_flags(
    league_name: str,
    league_type: str,
    types_list: list[str] | None = None,
) -> dict:
    """Detect league form flags using the normalized ``types_list`` with
    membership semantics, falling back to the legacy scalar ``league_type``
    only when the normalized list is empty. League-name heuristics remain
    as a last-resort signal for bestball / IDP forms so historical rows
    without structured type data still surface correctly.
    """
    ln = (league_name or "").upper()
    lt = (league_type or "").strip().lower()
    norm_types = {
        str(t).strip().lower() for t in (types_list or []) if str(t).strip()
    }
    if not norm_types and lt:
        norm_types = {lt}
    is_dynasty = "dynasty" in norm_types
    is_redraft = "redraft" in norm_types
    is_bestball = (
        "bestball" in norm_types or "BESTBALL" in ln or "BEST BALL" in ln
    )
    is_idp = "idp" in norm_types or "idp_only" in norm_types or "IDP" in ln
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

    all_drafts: list[
        dict[str, str | int | float | bool | list[str] | None]
    ] = []
    active_drafts: list[
        dict[str, str | int | float | bool | list[str] | None]
    ] = []
    scheduled_drafts: list[
        dict[str, str | int | float | bool | list[str] | None]
    ] = []
    completed_drafts: list[
        dict[str, str | int | float | bool | list[str] | None]
    ] = []
    other_drafts: list[
        dict[str, str | int | float | bool | list[str] | None]
    ] = []
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
        primary, types_list = normalize_league_types(
            lg.get("league_types"), lg.get("league_type")
        )
        league_type = primary or str(lg.get("league_type") or "")
        # Multi-form leagues (e.g. ['dynasty','bestball']) surface in every
        # applicable filter/badge context via the normalized types list.
        flags = _detect_flags(league_name, league_type, types_list)
        start_display, start_ts = _format_start_time(d.get("start_time"))
        draft_id = str(d.get("draft_id") or "")
        status = str(d.get("status") or "unknown").lower()
        return {
            "draft_id": draft_id,
            "league_id": lid,
            "league_name": league_name,
            "league_avatar": str(lg.get("avatar") or ""),
            "league_invite_link": str(lg.get("invite_link") or ""),
            "league_type": league_type,
            "league_types": types_list,
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
            "next_user_id": "",
            "on_clock_source": "",
            "last_picked_by_user_id": "",
            "last_picked_by_manager": "",
            "last_picked_by_team": "",
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

    def _enrich_live_draft(
        self,
        base: dict,
        managers_by_league: dict,
        managers_by_user: dict,
    ) -> dict:
        """Fetch live Sleeper data and derive live fields.

        For active drafts, prefer `metadata.on_the_clock_user_id` from the
        Sleeper league endpoint to identify the on-clock manager, and use
        `picked_by` from the final pick to identify who made the last pick.
        Fall back to slot/roster calculation when on_the_clock_user_id is
        unavailable.
        """
        draft_id = base["draft_id"]
        league_id = base["league_id"]
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
        league_live = {}
        if league_id:
            try:
                league_live = get_league(league_id) or {}
            except Exception as e:
                logging.exception(f"get_league failed for {league_id}: {e}")
                league_live = {}
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
        last_picked_by = ""
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
                last_picked_by = str(last.get("picked_by") or "")
            except Exception as e:
                logging.exception(f"last pick parse failed: {e}")

        # Resolve last picked-by manager via Supabase managers (by user_id).
        last_picked_by_manager = ""
        last_picked_by_team = ""
        if last_picked_by:
            users_by_uid = managers_by_user.get(league_id, {})
            m = users_by_uid.get(last_picked_by) or {}
            last_picked_by_manager = str(m.get("display_name") or "")
            last_picked_by_team = str(
                m.get("team_name") or last_picked_by_manager or ""
            )

        # Preferred on-clock resolution: league metadata.on_the_clock_user_id.
        on_clock_user_id = ""
        league_meta = league_live.get("metadata") or {}
        if isinstance(league_meta, dict):
            on_clock_user_id = str(
                league_meta.get("on_the_clock_user_id") or ""
            )

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
            next_roster_id = int(slot_to_roster.get(next_slot) or 0)

        next_manager_name = ""
        next_team_name = ""
        on_clock_source = ""

        if on_clock_user_id:
            users_by_uid = managers_by_user.get(league_id, {})
            m = users_by_uid.get(on_clock_user_id) or {}
            if m:
                next_manager_name = str(m.get("display_name") or "")
                next_team_name = str(
                    m.get("team_name") or next_manager_name or ""
                )
                try:
                    rid = int(m.get("roster_id") or 0)
                    if rid > 0:
                        next_roster_id = rid
                except Exception:
                    logging.exception("bad roster_id from managers")
                on_clock_source = "on_the_clock_user_id"

        if not next_manager_name and next_roster_id > 0:
            mgrs = managers_by_league.get(league_id, {})
            m = mgrs.get(next_roster_id) or {}
            next_manager_name = str(m.get("display_name") or "")
            next_team_name = str(m.get("team_name") or next_manager_name or "")
            if next_manager_name and not on_clock_source:
                on_clock_source = "slot_calculation"

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
                "last_picked_by_user_id": last_picked_by,
                "last_picked_by_manager": last_picked_by_manager,
                "last_picked_by_team": last_picked_by_team,
                "next_pick_no": next_pick_no
                if next_pick_no <= total_slots or total_slots == 0
                else 0,
                "next_round": next_round,
                "next_slot": next_slot,
                "next_roster_id": next_roster_id,
                "next_manager_name": next_manager_name,
                "next_team_name": next_team_name,
                "next_user_id": on_clock_user_id,
                "on_clock_source": on_clock_source,
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

            base_cols = (
                "league_id,league_name,league_type,league_season,"
                "league_sort,avatar"
            )
            typed_cols = add_types_col(base_cols)
            invite_cols = f"{typed_cols},invite_link"
            try:
                leagues_res = (
                    client.table("leagues").select(invite_cols).execute()
                )
            except Exception as e:
                error_text = str(e).lower()
                invite_missing = "invite_link" in error_text and (
                    "does not exist" in error_text
                    or "could not find" in error_text
                    or "pgrst204" in error_text
                )
                if is_missing_league_types_column_error(e) or invite_missing:
                    # Optional columns may be absent on older deployments.
                    fallback_cols = base_cols if invite_missing else typed_cols
                    leagues_res = (
                        client.table("leagues").select(fallback_cols).execute()
                    )
                else:
                    logging.exception(f"drafts leagues select failed: {e}")
                    raise
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
            managers_by_user: dict[str, dict[str, dict]] = {}
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
                                "league_id,roster_id,user_id,"
                                "display_name,team_name"
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
                            uid = str(m.get("user_id") or "")
                            if lid and rid:
                                managers_by_league.setdefault(lid, {})[rid] = m
                            if lid and uid:
                                managers_by_user.setdefault(lid, {})[uid] = m
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
                    enriched = self._enrich_live_draft(
                        base, managers_by_league, managers_by_user
                    )
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
