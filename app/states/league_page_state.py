import reflex as rx
import logging
from app.supabase_client import get_supabase_client
from app.player_cache import enrich_roster_players
from app.league_types import normalize_league_types


class LeaguePageState(rx.State):
    loading: bool = True
    not_found: bool = False
    error_message: str = ""
    league_id: str = ""
    league_name: str = ""
    league_type: str = ""
    league_types: list[str] = []
    league_season: str = ""
    league_avatar: str = ""
    # league_avatar populated from leagues.avatar (Sleeper id or full URL).
    total_rosters: int = 0
    manager_count: int = 0
    latest_week: int = 0
    available_weeks: list[int] = []
    selected_matchup_week: int = 0
    roster_positions: list[str] = []
    champion: dict[str, str] = {}
    top_standings: list[dict[str, str | int | float]] = []
    full_standings: list[dict[str, str | int | float]] = []
    matchup_pairs: list[
        dict[str, str | int | float | bool | list[dict[str, str | float]]]
    ] = []
    manager_cards: list[dict[str, str | int]] = []
    roster_cards: list[dict[str, str | int | float | list[dict[str, str]]]] = []
    trades: list[dict[str, str]] = []
    trades_available: bool = False
    drafts: list[dict[str, str | int]] = []
    predecessor: dict[str, str] = {}

    def _reset_state(self):
        self.loading = True
        self.not_found = False
        self.error_message = ""
        self.league_id = ""
        self.league_name = ""
        self.league_type = ""
        self.league_types = []
        self.league_season = ""
        self.league_avatar = ""
        self.total_rosters = 0
        self.manager_count = 0
        self.latest_week = 0
        self.available_weeks = []
        self.selected_matchup_week = 0
        self.roster_positions = []
        self.champion = {}
        self.top_standings = []
        self.full_standings = []
        self.matchup_pairs = []
        self.manager_cards = []
        self.roster_cards = []
        self.trades = []
        self.trades_available = False
        self.drafts = []
        self.predecessor = {}

    def _extract_route_id(self) -> str:
        """Extract the dynamic route id, supporting both `lid` and legacy `league_id`."""
        params: dict = {}
        try:
            params = dict(self.router.page.params or {})
        except Exception:
            logging.exception("Failed to read router.page.params")
            params = {}
        try:
            url_params = getattr(self.router.url, "query_parameters", None)
            if url_params:
                for k, v in dict(url_params).items():
                    params.setdefault(k, v)
        except Exception:
            logging.exception("Failed to read router.url query_parameters")
        for key in ("lid", "league_id"):
            val = params.get(key, "")
            if val:
                if isinstance(val, list):
                    val = val[0] if val else ""
                return str(val).strip('"').strip()
        return ""

    @rx.event
    async def load_league(self):
        self._reset_state()
        yield
        clean_id = self._extract_route_id()
        if not clean_id:
            self.not_found = True
            self.loading = False
            return
        yield LeaguePageState.load_league_by_id(clean_id)

    @rx.event
    async def load_league_by_id(self, lid: str):
        """Testable path: load a league detail page by explicit id."""
        self._reset_state()
        clean_id = str(lid).strip('"').strip()
        if not clean_id:
            self.not_found = True
            self.loading = False
            return

        self.league_id = clean_id
        client = get_supabase_client()
        if not client:
            self.error_message = "Datenbank nicht verfügbar."
            self.loading = False
            return

        try:
            lg_res = (
                client.table("leagues")
                .select("*")
                .eq("league_id", clean_id)
                .limit(1)
                .execute()
            )
            if not lg_res or not lg_res.data:
                self.not_found = True
                self.loading = False
                return
            lg = lg_res.data[0]
            self.league_name = str(lg.get("league_name") or f"Liga {clean_id}")
            primary, types_list = normalize_league_types(
                lg.get("league_types"), lg.get("league_type")
            )
            self.league_type = primary or str(lg.get("league_type") or "")
            self.league_types = types_list
            self.league_season = str(lg.get("league_season") or "")
            self.league_avatar = str(lg.get("avatar") or "")
            rp = lg.get("roster_positions") or []
            self.roster_positions = [str(x) for x in rp]

            # Load predecessor (previous league) information
            raw_prev = lg.get("previous_league_id")
            prev_id = (
                str(raw_prev).strip()
                if raw_prev not in (None, "", "0", "null")
                else ""
            )
            if prev_id:
                try:
                    p_res = (
                        client.table("leagues")
                        .select("league_name,league_season")
                        .eq("league_id", prev_id)
                        .limit(1)
                        .execute()
                    )
                    if p_res and p_res.data:
                        p_data = p_res.data[0]
                        self.predecessor = {
                            "league_id": prev_id,
                            "name": str(p_data.get("league_name") or ""),
                            "season": str(p_data.get("league_season") or ""),
                        }
                    else:
                        # ID exists but no row found in DB
                        self.predecessor = {"league_id": prev_id}
                except Exception as e:
                    logging.exception(
                        f"Predecessor lookup failed for {prev_id}: {e}"
                    )
                    self.predecessor = {"league_id": prev_id}

            try:
                mgr_res = (
                    client.table("managers")
                    .select("*")
                    .eq("league_id", clean_id)
                    .execute()
                )
                mgrs = mgr_res.data if mgr_res and mgr_res.data else []
                self.manager_count = len(mgrs)
                mgr_map = {m.get("roster_id"): m for m in mgrs}
            except Exception as e:
                logging.exception(f"Manager fetch failed: {e}")
                mgr_map = {}

            try:
                max_res = (
                    client.table("rosters")
                    .select("week")
                    .eq("league_id", clean_id)
                    .order("week", desc=True)
                    .limit(1)
                    .execute()
                )
                latest_week = 0
                if max_res and max_res.data:
                    latest_week = int(max_res.data[0].get("week") or 0)
                self.latest_week = latest_week
            except Exception as e:
                logging.exception(f"Latest week fetch failed: {e}")
                latest_week = 0

            try:
                if latest_week > 0:
                    st_res = (
                        client.table("rosters")
                        .select("*")
                        .eq("league_id", clean_id)
                        .eq("week", latest_week)
                        .order("wins", desc=True)
                        .order("fpts_for", desc=True)
                        .execute()
                    )
                    rows = st_res.data if st_res and st_res.data else []
                    self.total_rosters = len(rows)
                    top = []
                    for i, r in enumerate(rows[:5]):
                        rid = r.get("roster_id")
                        mgr = mgr_map.get(rid, {})
                        top.append(
                            {
                                "rank": i + 1,
                                "team_name": str(
                                    mgr.get("team_name")
                                    or mgr.get("display_name")
                                    or f"Team {rid}"
                                ),
                                "display_name": str(
                                    mgr.get("display_name") or ""
                                ),
                                "wins": int(r.get("wins") or 0),
                                "losses": int(r.get("losses") or 0),
                                "ties": int(r.get("ties") or 0),
                                "fpts_for": float(r.get("fpts_for") or 0.0),
                            }
                        )
                    self.top_standings = top
            except Exception as e:
                logging.exception(f"Standings fetch failed: {e}")

            try:
                champ_res = (
                    client.table("league_champion")
                    .select("*")
                    .eq("league_id", clean_id)
                    .limit(1)
                    .execute()
                )
                if champ_res and champ_res.data:
                    c = champ_res.data[0]
                    self.champion = {
                        "team_name": str(c.get("team_name") or ""),
                        "display_name": str(c.get("display_name") or ""),
                    }
            except Exception as e:
                logging.exception(f"Champion fetch failed: {e}")

            # Full standings (all rows, latest week)
            try:
                if latest_week > 0:
                    all_res = (
                        client.table("rosters")
                        .select("*")
                        .eq("league_id", clean_id)
                        .eq("week", latest_week)
                        .order("wins", desc=True)
                        .order("fpts_for", desc=True)
                        .execute()
                    )
                    all_rows = all_res.data if all_res and all_res.data else []
                    full = []
                    for i, r in enumerate(all_rows):
                        rid = r.get("roster_id")
                        mgr = mgr_map.get(rid, {})
                        wins = int(r.get("wins") or 0)
                        losses = int(r.get("losses") or 0)
                        ties = int(r.get("ties") or 0)
                        games = wins + losses + ties
                        win_pct = (wins / games) if games > 0 else 0.0
                        full.append(
                            {
                                "rank": i + 1,
                                "roster_id": int(rid) if rid is not None else 0,
                                "team_name": str(
                                    mgr.get("team_name")
                                    or mgr.get("display_name")
                                    or f"Team {rid}"
                                ),
                                "display_name": str(
                                    mgr.get("display_name") or f"Manager {rid}"
                                ),
                                "wins": wins,
                                "losses": losses,
                                "ties": ties,
                                "fpts_for": round(
                                    float(r.get("fpts_for") or 0.0), 2
                                ),
                                "fpts_against": round(
                                    float(r.get("fpts_against") or 0.0), 2
                                ),
                                "win_pct": round(win_pct, 3),
                                "win_pct_str": f"{win_pct * 100:.1f}%",
                            }
                        )
                    self.full_standings = full
            except Exception as e:
                logging.exception(f"Full standings fetch failed: {e}")

            # Available matchup weeks + matchup pairs for latest available
            try:
                weeks_res = (
                    client.table("matchup_week_stats")
                    .select("week")
                    .eq("league_id", clean_id)
                    .execute()
                )
                weeks_rows = (
                    weeks_res.data if weeks_res and weeks_res.data else []
                )
                weeks_set = {
                    int(x.get("week"))
                    for x in weeks_rows
                    if x.get("week") is not None
                }
                available_weeks = sorted(weeks_set)
                self.available_weeks = available_weeks
                if available_weeks:
                    selected = max(available_weeks)
                    self.selected_matchup_week = selected
                    self.matchup_pairs = self._fetch_matchup_pairs(
                        client, clean_id, selected, mgr_map
                    )
                else:
                    self.selected_matchup_week = 0
                    self.matchup_pairs = []
            except Exception as e:
                logging.exception(f"Matchup pairs fetch failed: {e}")
                self.available_weeks = []
                self.selected_matchup_week = 0
                self.matchup_pairs = []

            # Manager cards
            try:
                mgr_cards = []
                for m in mgr_map.values():
                    rid = m.get("roster_id")
                    mgr_cards.append(
                        {
                            "roster_id": int(rid) if rid is not None else 0,
                            "team_name": str(
                                m.get("team_name")
                                or m.get("display_name")
                                or f"Team {rid}"
                            ),
                            "display_name": str(m.get("display_name") or ""),
                            "user_id": str(m.get("user_id") or ""),
                        }
                    )
                mgr_cards.sort(key=lambda x: x["roster_id"])
                self.manager_cards = mgr_cards
            except Exception as e:
                logging.exception(f"Manager cards build failed: {e}")

            # Roster cards using json_data + real player lists
            try:
                if latest_week > 0:
                    rc_res = (
                        client.table("rosters")
                        .select("*")
                        .eq("league_id", clean_id)
                        .eq("week", latest_week)
                        .execute()
                    )
                    rc_rows = rc_res.data if rc_res and rc_res.data else []
                    cards = []
                    for r in rc_rows:
                        rid = r.get("roster_id")
                        mgr = mgr_map.get(rid, {})
                        jd = r.get("json_data") or {}
                        players = (
                            jd.get("players") if isinstance(jd, dict) else []
                        ) or []
                        starters = (
                            jd.get("starters") if isinstance(jd, dict) else []
                        ) or []
                        reserve = (
                            jd.get("reserve") if isinstance(jd, dict) else []
                        ) or []
                        players = [
                            str(p) for p in players if p not in (None, "0", 0)
                        ]
                        starters = [
                            str(p) for p in starters if p not in (None, "0", 0)
                        ]
                        reserve = [
                            str(p) for p in reserve if p not in (None, "0", 0)
                        ]
                        bench = [
                            p
                            for p in players
                            if p not in starters and p not in reserve
                        ]
                        starter_players = enrich_roster_players(starters)
                        bench_players = enrich_roster_players(bench)
                        reserve_players = enrich_roster_players(reserve)
                        cards.append(
                            {
                                "roster_id": int(rid) if rid is not None else 0,
                                "team_name": str(
                                    mgr.get("team_name")
                                    or mgr.get("display_name")
                                    or f"Team {rid}"
                                ),
                                "display_name": str(
                                    mgr.get("display_name") or ""
                                ),
                                "players_count": len(players),
                                "starters_count": len(starters),
                                "bench_count": len(bench),
                                "reserve_count": len(reserve),
                                "starter_players": starter_players,
                                "bench_players": bench_players,
                                "reserve_players": reserve_players,
                                "wins": int(r.get("wins") or 0),
                                "losses": int(r.get("losses") or 0),
                                "ties": int(r.get("ties") or 0),
                                "fpts_for": round(
                                    float(r.get("fpts_for") or 0.0), 2
                                ),
                            }
                        )
                    cards.sort(key=lambda x: x["roster_id"])
                    self.roster_cards = cards
            except Exception as e:
                logging.exception(f"Roster cards fetch failed: {e}")

            # Trades / transactions — no table exists in Supabase per validation
            self.trades = []
            self.trades_available = False

            # Drafts for this league
            try:
                from datetime import datetime as _dt

                drafts_res = (
                    client.table("drafts")
                    .select("*")
                    .eq("league_id", clean_id)
                    .execute()
                )
                draft_rows = (
                    drafts_res.data if drafts_res and drafts_res.data else []
                )
                dtype_map = {
                    "0": "Snake",
                    "1": "Linear",
                    "2": "Auction",
                    "snake": "Snake",
                    "linear": "Linear",
                    "auction": "Auction",
                }
                drafts_out = []
                for d in draft_rows:
                    draft_id = str(d.get("draft_id") or "")
                    if not draft_id:
                        continue
                    raw_type = str(d.get("draft_type") or "").lower()
                    type_str = dtype_map.get(raw_type, raw_type.title() or "—")
                    status = str(d.get("status") or "unknown")
                    season = str(d.get("season") or "")
                    start_raw = d.get("start_time")
                    start_display = ""
                    start_ts = 0
                    if start_raw:
                        try:
                            dt = _dt.fromisoformat(
                                str(start_raw).replace("Z", "+00:00")
                            )
                            start_display = dt.strftime("%d.%m.%Y · %H:%M")
                            start_ts = int(dt.timestamp())
                        except Exception:
                            logging.exception("Draft start_time parse failed")
                            start_display = str(start_raw)[:16]
                    drafts_out.append(
                        {
                            "draft_id": draft_id,
                            "season": season,
                            "draft_type": type_str,
                            "status": status,
                            "start_time_display": start_display,
                            "start_time_ts": start_ts,
                            "url": f"https://sleeper.com/draft/nfl/{draft_id}",
                        }
                    )
                drafts_out.sort(
                    key=lambda x: (x["season"], x["start_time_ts"]),
                    reverse=True,
                )
                self.drafts = drafts_out
            except Exception as e:
                logging.exception(f"Drafts fetch failed: {e}")
                self.drafts = []

        except Exception as e:
            logging.exception(f"Error loading league: {e}")
            self.error_message = "Fehler beim Laden der Liga."
        finally:
            self.loading = False

    def _build_lineup(self, row: dict) -> dict:
        """Extract starters, bench, and reserve/IR lineups with points."""
        jd = row.get("json_data") or {}
        if not isinstance(jd, dict):
            jd = {}
        starters = [
            str(p)
            for p in (jd.get("starters") or [])
            if p not in (None, "0", 0)
        ]
        players = [
            str(p) for p in (jd.get("players") or []) if p not in (None, "0", 0)
        ]
        reserve = [
            str(p) for p in (jd.get("reserve") or []) if p not in (None, "0", 0)
        ]
        taxi = [
            str(p) for p in (jd.get("taxi") or []) if p not in (None, "0", 0)
        ]
        reserve_all: list[str] = []
        for pid in reserve + taxi:
            if pid not in reserve_all:
                reserve_all.append(pid)
        starter_set = set(starters)
        reserve_set = set(reserve_all)
        bench = [
            p for p in players if p not in starter_set and p not in reserve_set
        ]

        # Points sources per Sleeper: players_points (primary),
        # starters_points (list matching starters order), custom_points.
        players_points_raw = jd.get("players_points")
        players_points: dict[str, float] = {}
        if isinstance(players_points_raw, dict):
            for k, v in players_points_raw.items():
                try:
                    players_points[str(k)] = float(v or 0)
                except Exception:
                    logging.exception("bad players_points value")

        starters_points_list = jd.get("starters_points") or []
        starter_pts_map: dict[str, float] = {}
        if isinstance(starters_points_list, list):
            for i, sid in enumerate(starters):
                if i < len(starters_points_list):
                    try:
                        starter_pts_map[sid] = float(
                            starters_points_list[i] or 0
                        )
                    except Exception:
                        logging.exception("bad starters_points value")

        custom_points_raw = jd.get("custom_points")
        custom_points: dict[str, float] = {}
        if isinstance(custom_points_raw, dict):
            for k, v in custom_points_raw.items():
                try:
                    custom_points[str(k)] = float(v or 0)
                except Exception:
                    logging.exception("bad custom_points value")

        def _get_pts(pid: str) -> float:
            if pid in players_points:
                return round(players_points[pid], 2)
            if pid in starter_pts_map:
                return round(starter_pts_map[pid], 2)
            if pid in custom_points:
                return round(custom_points[pid], 2)
            return 0.0

        def _enrich(pids: list[str]) -> list[dict]:
            base = enrich_roster_players(pids)
            out = []
            for p in base:
                pid = str(p.get("player_id", ""))
                out.append(
                    {
                        "player_id": pid,
                        "full_name": str(p.get("full_name", "")),
                        "position": str(p.get("position", "") or "?"),
                        "team": str(p.get("team", "") or "FA"),
                        "points": _get_pts(pid),
                    }
                )
            return out

        return {
            "starters": _enrich(starters),
            "bench": _enrich(bench),
            "reserve": _enrich(reserve_all),
        }

    def _fetch_matchup_pairs(
        self, client, league_id: str, week: int, mgr_map: dict
    ) -> list[dict]:
        """Load and pair matchups for a given week, including lineups."""
        try:
            mres = (
                client.table("matchup_week_stats")
                .select("*")
                .eq("league_id", league_id)
                .eq("week", int(week))
                .execute()
            )
            mrows = mres.data if mres and mres.data else []
            pairs: dict = {}
            for m in mrows:
                mid = m.get("matchup_id")
                pairs.setdefault(mid, []).append(m)
            paired = []

            def _team_entry(row: dict, prefix: str, mgr: dict) -> dict:
                lineup = self._build_lineup(row)
                return {
                    f"{prefix}_name": str(
                        mgr.get("team_name")
                        or mgr.get("display_name")
                        or f"Team {row.get('roster_id')}"
                    ),
                    f"{prefix}_manager": str(mgr.get("display_name") or ""),
                    f"{prefix}_points": round(
                        float(row.get("points") or 0.0), 2
                    ),
                    f"{prefix}_starters": lineup["starters"],
                    f"{prefix}_bench": lineup["bench"],
                    f"{prefix}_reserve": lineup["reserve"],
                }

            for mid, teams in pairs.items():
                if len(teams) >= 2:
                    t1, t2 = teams[0], teams[1]
                    m1 = mgr_map.get(t1.get("roster_id"), {})
                    m2 = mgr_map.get(t2.get("roster_id"), {})
                    entry = {
                        "matchup_id": int(mid) if mid is not None else 0,
                        "is_bye": False,
                    }
                    entry.update(_team_entry(t1, "team_a", m1))
                    entry.update(_team_entry(t2, "team_b", m2))
                    paired.append(entry)
                elif len(teams) == 1:
                    t1 = teams[0]
                    m1 = mgr_map.get(t1.get("roster_id"), {})
                    entry = {
                        "matchup_id": int(mid) if mid is not None else 0,
                        "is_bye": True,
                    }
                    entry.update(_team_entry(t1, "team_a", m1))
                    entry.update(
                        {
                            "team_b_name": "BYE",
                            "team_b_manager": "",
                            "team_b_points": 0.0,
                            "team_b_starters": [],
                            "team_b_bench": [],
                            "team_b_reserve": [],
                        }
                    )
                    paired.append(entry)
            paired.sort(key=lambda x: x["matchup_id"])
            return paired
        except Exception as e:
            logging.exception(f"Fetch matchups for week {week} failed: {e}")
            return []

    @rx.event
    def change_matchup_week(self, week: int):
        """Update only the selected week and its matchup pairs."""
        try:
            w = int(week)
        except Exception:
            logging.exception("Invalid week arg")
            return
        if w not in self.available_weeks:
            return
        client = get_supabase_client()
        if not client or not self.league_id:
            self.selected_matchup_week = w
            return
        try:
            mgr_res = (
                client.table("managers")
                .select("*")
                .eq("league_id", self.league_id)
                .execute()
            )
            mgrs = mgr_res.data if mgr_res and mgr_res.data else []
            mgr_map = {m.get("roster_id"): m for m in mgrs}
        except Exception as e:
            logging.exception(f"Manager map reload failed: {e}")
            mgr_map = {}
        self.selected_matchup_week = w
        self.matchup_pairs = self._fetch_matchup_pairs(
            client, self.league_id, w, mgr_map
        )
