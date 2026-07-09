import reflex as rx
import logging
from app.supabase_client import get_supabase_client


class LeaguePageState(rx.State):
    loading: bool = True
    not_found: bool = False
    error_message: str = ""
    league_id: str = ""
    league_name: str = ""
    league_type: str = ""
    league_season: str = ""
    league_avatar: str = ""
    total_rosters: int = 0
    manager_count: int = 0
    latest_week: int = 0
    roster_positions: list[str] = []
    champion: dict[str, str] = {}
    top_standings: list[dict[str, str | int | float]] = []
    full_standings: list[dict[str, str | int | float]] = []
    matchup_pairs: list[dict[str, str | int | float]] = []
    manager_cards: list[dict[str, str | int]] = []
    roster_cards: list[dict[str, str | int | float]] = []
    trades: list[dict[str, str]] = []
    trades_available: bool = False
    drafts: list[dict[str, str | int]] = []

    def _reset_state(self):
        self.loading = True
        self.not_found = False
        self.error_message = ""
        self.league_id = ""
        self.league_name = ""
        self.league_type = ""
        self.league_season = ""
        self.league_avatar = ""
        self.total_rosters = 0
        self.manager_count = 0
        self.latest_week = 0
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
            self.league_type = str(lg.get("league_type") or "")
            self.league_season = str(lg.get("league_season") or "")
            rp = lg.get("roster_positions") or []
            self.roster_positions = [str(x) for x in rp]

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

            # Matchup pairs (latest week)
            try:
                if latest_week > 0:
                    mres = (
                        client.table("matchup_week_stats")
                        .select("*")
                        .eq("league_id", clean_id)
                        .eq("week", latest_week)
                        .execute()
                    )
                    mrows = mres.data if mres and mres.data else []
                    pairs: dict = {}
                    for m in mrows:
                        mid = m.get("matchup_id")
                        pairs.setdefault(mid, []).append(m)
                    paired = []
                    for mid, teams in pairs.items():
                        if len(teams) >= 2:
                            t1, t2 = teams[0], teams[1]
                            m1 = mgr_map.get(t1.get("roster_id"), {})
                            m2 = mgr_map.get(t2.get("roster_id"), {})
                            paired.append(
                                {
                                    "matchup_id": int(mid)
                                    if mid is not None
                                    else 0,
                                    "team_a_name": str(
                                        m1.get("team_name")
                                        or m1.get("display_name")
                                        or f"Team {t1.get('roster_id')}"
                                    ),
                                    "team_a_manager": str(
                                        m1.get("display_name") or ""
                                    ),
                                    "team_a_points": round(
                                        float(t1.get("points") or 0.0), 2
                                    ),
                                    "team_b_name": str(
                                        m2.get("team_name")
                                        or m2.get("display_name")
                                        or f"Team {t2.get('roster_id')}"
                                    ),
                                    "team_b_manager": str(
                                        m2.get("display_name") or ""
                                    ),
                                    "team_b_points": round(
                                        float(t2.get("points") or 0.0), 2
                                    ),
                                }
                            )
                        elif len(teams) == 1:
                            t1 = teams[0]
                            m1 = mgr_map.get(t1.get("roster_id"), {})
                            paired.append(
                                {
                                    "matchup_id": int(mid)
                                    if mid is not None
                                    else 0,
                                    "team_a_name": str(
                                        m1.get("team_name")
                                        or m1.get("display_name")
                                        or f"Team {t1.get('roster_id')}"
                                    ),
                                    "team_a_manager": str(
                                        m1.get("display_name") or ""
                                    ),
                                    "team_a_points": round(
                                        float(t1.get("points") or 0.0), 2
                                    ),
                                    "team_b_name": "BYE",
                                    "team_b_manager": "",
                                    "team_b_points": 0.0,
                                }
                            )
                    self.matchup_pairs = paired
            except Exception as e:
                logging.exception(f"Matchup pairs fetch failed: {e}")

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

            # Roster cards using json_data
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
                            jd.get("players") if isinstance(jd, dict) else None
                        )
                        starters = (
                            jd.get("starters") if isinstance(jd, dict) else None
                        )
                        players_count = (
                            len(players) if isinstance(players, list) else 0
                        )
                        starters_count = (
                            len(starters) if isinstance(starters, list) else 0
                        )
                        bench_count = max(players_count - starters_count, 0)
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
                                "players_count": players_count,
                                "starters_count": starters_count,
                                "bench_count": bench_count,
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
