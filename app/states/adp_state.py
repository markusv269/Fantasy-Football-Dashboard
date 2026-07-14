import reflex as rx
import logging
from app.supabase_client import get_supabase_client


BOARD_SLOTS = 12
PICKS_PAGE_SIZE = 1000
DRAFT_ID_BATCH = 25
LEAGUE_ID_BATCH = 100


class AdpState(rx.State):
    is_loading: bool = False
    selected_season: str = "all"
    selected_format: str = "redraft"
    available_seasons: list[str] = []
    adp_players: list[dict[str, str | int | float]] = []
    board_cells: list[dict[str, str | int | float]] = []
    total_drafts: int = 0
    total_picks: int = 0
    total_players: int = 0

    # Session-scoped caches to avoid repeated full-table scans.
    _leagues_by_format_cache: dict[str, list[str]] = {}
    _seasons_loaded: bool = False
    # Cache of computed ADP results keyed by "format|season".
    # Each entry stores the full snapshot needed to repopulate the UI
    # without re-querying Supabase or re-aggregating picks.
    _results_cache: dict[str, dict[str, int | list]] = {}

    @rx.var
    def board_layout(self) -> str:
        return "linear" if self.selected_format != "redraft" else "snake"

    @rx.var
    def total_rounds(self) -> int:
        n = len(self.adp_players)
        if n == 0:
            return 0
        return (n + BOARD_SLOTS - 1) // BOARD_SLOTS

    @rx.var
    def round_range(self) -> list[int]:
        return list(range(1, self.total_rounds + 1))

    @rx.var
    def slot_range(self) -> list[int]:
        return list(range(1, BOARD_SLOTS + 1))

    def _cache_key(self) -> str:
        return f"{self.selected_format}|{self.selected_season}"

    def _apply_cached(self, entry: dict) -> None:
        self.total_drafts = int(entry.get("total_drafts", 0))
        self.total_picks = int(entry.get("total_picks", 0))
        self.total_players = int(entry.get("total_players", 0))
        self.adp_players = list(entry.get("adp_players", []))
        self.board_cells = list(entry.get("board_cells", []))

    def _store_cached(self) -> None:
        self._results_cache[self._cache_key()] = {
            "total_drafts": self.total_drafts,
            "total_picks": self.total_picks,
            "total_players": self.total_players,
            "adp_players": list(self.adp_players),
            "board_cells": list(self.board_cells),
        }

    @rx.event
    def set_selected_season(self, v: str):
        if v == self.selected_season:
            return
        self.selected_season = v
        cached = self._results_cache.get(self._cache_key())
        if cached is not None:
            self._apply_cached(cached)
            return
        self._recompute_adp()

    @rx.event
    def set_selected_format(self, v: str):
        if v == self.selected_format:
            return
        self.selected_format = v
        cached = self._results_cache.get(self._cache_key())
        if cached is not None:
            self._apply_cached(cached)
            return
        self._recompute_adp()

    @rx.event
    def init_adp(self):
        if not self._seasons_loaded:
            self._load_seasons_sync()
        cached = self._results_cache.get(self._cache_key())
        if cached is not None:
            self._apply_cached(cached)
            return
        self._recompute_adp()

    def _load_seasons_sync(self):
        """Load distinct completed-draft seasons once per session."""
        if self._seasons_loaded and self.available_seasons:
            return
        client = get_supabase_client()
        if not client:
            return
        try:
            res = (
                client.table("drafts")
                .select("season")
                .eq("status", "complete")
                .execute()
            )
            rows = res.data if res and res.data else []
            seasons = sorted(
                {str(r.get("season") or "") for r in rows if r.get("season")},
                reverse=True,
            )
            self.available_seasons = seasons
            self._seasons_loaded = True
        except Exception as e:
            logging.exception(f"load_seasons failed: {e}")

    @rx.event
    def load_seasons(self):
        self._load_seasons_sync()

    def _load_leagues_format_map(self, client) -> dict[str, list[str]]:
        """Build and cache a format -> [league_ids] mapping.

        Fetches the leagues table once per session and buckets by format.
        Subsequent format/season switches reuse this cache instead of
        re-scanning the leagues table.
        """
        if self._leagues_by_format_cache:
            return self._leagues_by_format_cache
        try:
            res = (
                client.table("leagues")
                .select("league_id,league_name,league_type")
                .execute()
            )
            rows = res.data if res and res.data else []
        except Exception as e:
            logging.exception(f"leagues fetch failed: {e}")
            return {}

        mapping: dict[str, list[str]] = {
            "dynasty": [],
            "dynasty_idp": [],
            "redraft": [],
        }
        for lg in rows:
            lid = str(lg.get("league_id") or "")
            if not lid:
                continue
            lname = str(lg.get("league_name") or "").upper()
            ltype = str(lg.get("league_type") or "").lower()
            is_idp = "IDP" in lname
            if ltype == "dynasty":
                if is_idp:
                    mapping["dynasty_idp"].append(lid)
                else:
                    mapping["dynasty"].append(lid)
            elif ltype == "redraft":
                mapping["redraft"].append(lid)
        self._leagues_by_format_cache = mapping
        return mapping

    def _get_matching_league_ids(self, client) -> list[str]:
        mapping = self._load_leagues_format_map(client)
        return list(mapping.get(self.selected_format, []))

    def _get_matching_draft_ids(
        self, client, league_ids: list[str]
    ) -> list[str]:
        """Return completed draft IDs for the given leagues + season filter.

        Server-side filters on league_id (batched IN), status=complete, and
        optionally season keep the returned dataset compact.
        """
        if not league_ids:
            return []
        draft_ids: list[str] = []
        try:
            for i in range(0, len(league_ids), LEAGUE_ID_BATCH):
                chunk = league_ids[i : i + LEAGUE_ID_BATCH]
                if not chunk:
                    continue
                q = (
                    client.table("drafts")
                    .select("draft_id")
                    .in_("league_id", chunk)
                    .eq("status", "complete")
                )
                if self.selected_season != "all":
                    season_val = self.selected_season
                    try:
                        if str(season_val).lstrip("-").isdigit():
                            season_val = int(season_val)
                    except Exception:
                        logging.exception("season parse")
                    q = q.eq("season", season_val)
                res = q.execute()
                rows = res.data if res and res.data else []
                for r in rows:
                    did = str(r.get("draft_id") or "")
                    if did:
                        draft_ids.append(did)
        except Exception as e:
            logging.exception(f"drafts fetch failed: {e}")
        return draft_ids

    def _fetch_picks(self, client, draft_ids: list[str]) -> list[dict]:
        """Fetch picks in bounded batches with pagination per batch.

        Uses small IN-batches of draft IDs to keep URL sizes safe, and
        pages each batch via range() until an empty or short page returns.
        Terminates cleanly on empty inputs or query errors.
        """
        all_picks: list[dict] = []
        if not draft_ids:
            return all_picks
        for i in range(0, len(draft_ids), DRAFT_ID_BATCH):
            chunk = draft_ids[i : i + DRAFT_ID_BATCH]
            if not chunk:
                continue
            offset = 0
            while True:
                try:
                    res = (
                        client.table("draft_picks")
                        .select("pick_no,player_id,metadata")
                        .in_("draft_id", chunk)
                        .range(offset, offset + PICKS_PAGE_SIZE - 1)
                        .execute()
                    )
                    rows = res.data if res and res.data else []
                except Exception as e:
                    logging.exception(f"picks page failed offset={offset}: {e}")
                    rows = []
                    break
                if not rows:
                    break
                all_picks.extend(rows)
                if len(rows) < PICKS_PAGE_SIZE:
                    break
                offset += PICKS_PAGE_SIZE
        return all_picks

    def _aggregate_picks(
        self, picks: list[dict]
    ) -> list[dict[str, str | int | float]]:
        agg: dict[str, dict] = {}
        for p in picks:
            pid = str(p.get("player_id") or "")
            if not pid:
                continue
            try:
                pick_no = int(p.get("pick_no") or 0)
            except Exception:
                logging.exception("bad pick_no")
                pick_no = 0
            if pick_no <= 0:
                continue
            meta = p.get("metadata") or {}
            if not isinstance(meta, dict):
                meta = {}
            first = str(meta.get("first_name") or "")
            last = str(meta.get("last_name") or "")
            full_name = f"{first} {last}".strip() or f"Player {pid}"
            pos = str(meta.get("position") or "")
            team = str(meta.get("team") or "")

            entry = agg.get(pid)
            if entry is None:
                entry = {
                    "player_id": pid,
                    "full_name": full_name,
                    "position": pos,
                    "team": team,
                    "picks": [],
                }
                agg[pid] = entry
            entry["picks"].append(pick_no)
            if not entry["full_name"] or entry["full_name"].startswith(
                "Player "
            ):
                entry["full_name"] = full_name
            if not entry["position"] and pos:
                entry["position"] = pos
            if not entry["team"] and team:
                entry["team"] = team

        players: list[dict] = []
        for pid, info in agg.items():
            pk = info["picks"]
            if not pk:
                continue
            count = len(pk)
            avg = sum(pk) / count
            avg_round = ((avg - 1) // BOARD_SLOTS) + 1
            avg_slot = ((avg - 1) % BOARD_SLOTS) + 1
            players.append(
                {
                    "player_id": pid,
                    "full_name": info["full_name"],
                    "position": info["position"] or "?",
                    "team": info["team"] or "FA",
                    "count": count,
                    "adp": round(avg, 2),
                    "adp_str": f"{avg:.1f}",
                    "min_pick": min(pk),
                    "max_pick": max(pk),
                    "avg_round": int(avg_round),
                    "avg_slot": round(avg_slot, 1),
                    "avg_display": (
                        f"{int(avg_round)}.{int(round(avg_slot)):02d}"
                    ),
                }
            )
        players.sort(key=lambda x: x["adp"])
        for i, p in enumerate(players):
            p["overall_rank"] = i + 1
        return players

    def _build_board_cells(
        self, players: list[dict]
    ) -> list[dict[str, str | int | float]]:
        layout = self.board_layout
        cells: list[dict] = []
        for i, p in enumerate(players):
            rnd = i // BOARD_SLOTS
            slot_in_round = i % BOARD_SLOTS
            if layout == "snake" and rnd % 2 == 1:
                col = BOARD_SLOTS - slot_in_round
            else:
                col = slot_in_round + 1
            cells.append(
                {
                    "player_id": p["player_id"],
                    "full_name": p["full_name"],
                    "position": p["position"],
                    "team": p["team"],
                    "adp": p["adp"],
                    "adp_str": p["adp_str"],
                    "count": p["count"],
                    "overall_rank": p["overall_rank"],
                    "round": rnd + 1,
                    "column": col,
                    "pick_notation": f"{rnd + 1}.{col:02d}",
                }
            )
        return cells

    def _reset_results(self):
        self.total_drafts = 0
        self.total_picks = 0
        self.total_players = 0
        self.adp_players = []
        self.board_cells = []

    def _recompute_adp(self):
        if self.is_loading:
            return
        self.is_loading = True
        try:
            client = get_supabase_client()
            if not client:
                self._reset_results()
                self._store_cached()
                return

            league_ids = self._get_matching_league_ids(client)
            if not league_ids:
                self._reset_results()
                self._store_cached()
                return

            draft_ids = self._get_matching_draft_ids(client, league_ids)
            if not draft_ids:
                self._reset_results()
                self._store_cached()
                return

            picks = self._fetch_picks(client, draft_ids)
            self.total_drafts = len(draft_ids)
            self.total_picks = len(picks)

            players = self._aggregate_picks(picks)
            self.adp_players = players
            self.total_players = len(players)
            self.board_cells = self._build_board_cells(players)
            self._store_cached()
        except Exception as e:
            logging.exception(f"load_adp failed: {e}")
            self._reset_results()
        finally:
            self.is_loading = False

    @rx.event
    def load_adp(self):
        cached = self._results_cache.get(self._cache_key())
        if cached is not None:
            self._apply_cached(cached)
            return
        self._recompute_adp()
