import reflex as rx
import logging
from app.supabase_client import get_supabase_client
from app.league_types import (
    add_types_col,
    is_missing_league_types_column_error,
    normalize_league_types,
)


BOARD_SLOTS = 12

# Module-level cache keyed by (season, format, draft_type) — persists across
# state instances within the same process. Each cache value is a dict with the
# fully-computed result payload so setter events can restore results
# synchronously without re-querying Supabase.
_ADP_RESULTS_CACHE: dict[tuple[str, str, str], dict] = {}


class AdpState(rx.State):
    is_loading: bool = False
    selected_season: str = ""
    selected_format: str = "redraft"
    selected_draft_type: str = "0"  # 0=Alle Spieler, 1=Rookies, 2=Veterans
    available_seasons: list[str] = []

    # Search + position filters for the ADP table
    table_search: str = ""
    table_position: str = "all"

    # Minimum pick count threshold (filters both board and rankings table)
    min_pick_count: int = 1
    min_pick_reset_counter: int = 0

    adp_players: list[dict[str, str | int | float]] = []
    board_cells: list[dict[str, str | int | float]] = []
    total_drafts: int = 0
    total_picks: int = 0
    total_players: int = 0

    @rx.var
    def max_pick_count(self) -> int:
        m = 1
        for p in self.adp_players:
            try:
                c = int(p.get("count") or 0)
                if c > m:
                    m = c
            except Exception:
                logging.exception("bad count")
        return m

    @rx.var
    def players_meeting_threshold(self) -> list[dict[str, str | int | float]]:
        thr = max(1, int(self.min_pick_count))
        out = [p for p in self.adp_players if int(p.get("count") or 0) >= thr]
        return out

    def _build_board_cells(
        self, players: list[dict[str, str | int | float]]
    ) -> list[dict[str, str | int | float]]:
        """Build board positions from ADP order for both full and filtered views."""
        layout = self.board_layout
        cells: list[dict[str, str | int | float]] = []
        for index, player in enumerate(players):
            round_index = index // BOARD_SLOTS
            slot_index = index % BOARD_SLOTS
            display_column = (
                BOARD_SLOTS - slot_index
                if layout == "snake" and round_index % 2 == 1
                else slot_index + 1
            )
            cells.append(
                {
                    "player_id": player.get("player_id", ""),
                    "full_name": player.get("full_name", ""),
                    "position": player.get("position", ""),
                    "team": player.get("team", ""),
                    "adp": player.get("adp", 0.0),
                    "adp_str": player.get("adp_str", ""),
                    "count": player.get("count", 0),
                    "overall_rank": player.get("overall_rank", 0),
                    "overall_pick_rank": player.get("overall_pick_rank", ""),
                    "positional_pick_rank": player.get(
                        "positional_pick_rank", ""
                    ),
                    "round": round_index + 1,
                    "column": display_column,
                    "display_column": display_column,
                    "pick_notation": (
                        f"{round_index + 1}.{slot_index + 1}"
                        if layout == "snake"
                        else f"{round_index + 1}.{display_column}"
                    ),
                }
            )
        return cells

    @rx.var
    def filtered_board_cells(self) -> list[dict[str, str | int | float]]:
        threshold = max(1, int(self.min_pick_count))
        eligible = [
            player
            for player in self.adp_players
            if int(player.get("count") or 0) >= threshold
        ]
        return self._build_board_cells(eligible)

    @rx.var
    def filtered_total_rounds(self) -> int:
        n = len(self.players_meeting_threshold)
        if n == 0:
            return 0
        return (n + BOARD_SLOTS - 1) // BOARD_SLOTS

    @rx.var
    def filtered_round_range(self) -> list[int]:
        return list(range(1, self.filtered_total_rounds + 1))

    @rx.var
    def board_layout(self) -> str:
        # Redraft always snake.
        if self.selected_format == "redraft":
            return "snake"
        # Dynasty / Dynasty IDP: rookie drafts are linear, all-player and
        # veteran drafts are snake.
        if self.selected_draft_type == "1":
            return "linear"
        return "snake"

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

    @rx.var
    def available_positions(self) -> list[str]:
        seen: set[str] = set()
        for p in self.adp_players:
            pos = str(p.get("position") or "").strip()
            if pos and pos != "?":
                seen.add(pos)
        return sorted(seen)

    @rx.var
    def filtered_players(self) -> list[dict[str, str | int | float]]:
        q = self.table_search.strip().lower()
        pos = self.table_position
        thr = max(1, int(self.min_pick_count))
        out: list[dict] = []
        for p in self.adp_players:
            if int(p.get("count") or 0) < thr:
                continue
            if pos != "all" and str(p.get("position") or "") != pos:
                continue
            if q:
                hay = (
                    f"{p.get('full_name', '')} {p.get('team', '')} "
                    f"{p.get('position', '')}"
                ).lower()
                if q not in hay:
                    continue
            out.append(p)
        return out

    @rx.var
    def filtered_count(self) -> int:
        return len(self.filtered_players)

    @rx.var
    def has_table_filters(self) -> bool:
        return (
            self.table_search.strip() != ""
            or self.table_position != "all"
            or int(self.min_pick_count) > 1
        )

    @rx.event
    def set_min_pick_count(self, val: int | str):
        try:
            v = int(val)
        except (ValueError, TypeError):
            return
        mx = self.max_pick_count
        if v < 1:
            v = 1
        if v > mx:
            v = mx
        self.min_pick_count = v

    @rx.event
    def reset_min_pick_count(self):
        self.min_pick_count = 1
        self.min_pick_reset_counter += 1

    @rx.event
    def set_selected_season(self, v: str):
        if not v:
            return
        self.selected_season = v
        self._clear_table_filters()
        self._recompute_adp()

    @rx.event
    def set_selected_format(self, v: str):
        self.selected_format = v
        self._clear_table_filters()
        self._recompute_adp()

    @rx.event
    def set_selected_draft_type(self, v: str):
        self.selected_draft_type = v
        self._clear_table_filters()
        self._recompute_adp()

    def _clear_table_filters(self):
        self.table_search = ""
        self.table_position = "all"
        self.min_pick_count = 1
        self.min_pick_reset_counter += 1

    def _cache_key(self) -> tuple[str, str, str]:
        return (
            str(self.selected_season),
            str(self.selected_format),
            str(self.selected_draft_type),
        )

    def _apply_cached(self, payload: dict) -> None:
        self.adp_players = payload.get("adp_players", [])
        self.board_cells = payload.get("board_cells", [])
        self.total_drafts = int(payload.get("total_drafts", 0))
        self.total_picks = int(payload.get("total_picks", 0))
        self.total_players = int(payload.get("total_players", 0))

    def _recompute_adp(self) -> None:
        """Synchronous recompute: use cache if available, otherwise load."""
        if not self.selected_season:
            return
        key = self._cache_key()
        cached = _ADP_RESULTS_CACHE.get(key)
        if cached is not None:
            self._apply_cached(cached)
            return
        self._load_adp_sync()

    @rx.event
    def set_table_search(self, v: str):
        self.table_search = v

    @rx.event
    def set_table_position(self, v: str):
        self.table_position = v

    @rx.event
    def clear_table_filters(self):
        self.table_search = ""
        self.table_position = "all"
        self.min_pick_count = 1
        self.min_pick_reset_counter += 1

    @rx.event
    def init_adp(self):
        yield AdpState.load_seasons
        yield AdpState.load_adp

    @rx.event
    def load_seasons(self):
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
            # Default to newest season if not set or if current selection is
            # no longer valid.
            if seasons and (
                not self.selected_season or self.selected_season not in seasons
            ):
                self.selected_season = seasons[0]
        except Exception as e:
            logging.exception(f"load_seasons failed: {e}")

    def _get_matching_league_ids(self, client) -> list[str]:
        """Get league IDs matching the selected format filter."""
        base_cols = "league_id,league_name,league_type"
        try:
            try:
                res = (
                    client.table("leagues")
                    .select(add_types_col(base_cols))
                    .execute()
                )
            except Exception as e:
                if is_missing_league_types_column_error(e):
                    # Expected fallback: `league_types` column not yet
                    # deployed. Retry without it silently.
                    res = client.table("leagues").select(base_cols).execute()
                else:
                    logging.exception(f"adp leagues select failed: {e}")
                    raise
            rows = res.data if res and res.data else []
        except Exception as e:
            logging.exception(f"leagues fetch failed: {e}")
            return []

        fmt = self.selected_format
        matching: list[str] = []
        for lg in rows:
            lname = str(lg.get("league_name") or "").upper()
            primary, types_list = normalize_league_types(
                lg.get("league_types"), lg.get("league_type")
            )
            norm_types = {str(t).lower() for t in types_list}
            # Backwards-compat: when only the legacy scalar is present,
            # ensure it participates in membership checks.
            legacy = str(lg.get("league_type") or "").lower()
            if legacy and not norm_types:
                norm_types.add(legacy)
            structured_idp = ("idp" in norm_types) or ("idp_only" in norm_types)
            is_idp = structured_idp or "IDP" in lname
            if fmt == "dynasty":
                if "dynasty" in norm_types and not is_idp:
                    matching.append(lg.get("league_id") or "")
            elif fmt == "dynasty_idp":
                if "dynasty" in norm_types and is_idp:
                    matching.append(lg.get("league_id") or "")
            elif fmt == "redraft":
                if "redraft" in norm_types:
                    matching.append(lg.get("league_id") or "")
            elif fmt == "bestball":
                if "bestball" in norm_types:
                    matching.append(lg.get("league_id") or "")
        return [x for x in matching if x]

    def _get_matching_draft_ids(
        self, client, league_ids: list[str]
    ) -> list[str]:
        """Get completed draft IDs for the matching leagues + season + draft_type."""
        if not league_ids or not self.selected_season:
            return []
        draft_ids: list[str] = []
        try:
            batch = 100
            for i in range(0, len(league_ids), batch):
                chunk = league_ids[i : i + batch]
                q = (
                    client.table("drafts")
                    .select("draft_id,season,league_id,status,draft_type")
                    .in_("league_id", chunk)
                    .eq("status", "complete")
                    .eq("season", self.selected_season)
                    .eq("draft_type", self.selected_draft_type)
                )
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
        """Fetch all picks for the given draft IDs."""
        all_picks: list[dict] = []
        if not draft_ids:
            return all_picks
        try:
            batch = 50
            for i in range(0, len(draft_ids), batch):
                chunk = draft_ids[i : i + batch]
                offset = 0
                page = 1000
                while True:
                    try:
                        res = (
                            client.table("draft_picks")
                            .select("draft_id,pick_no,round,player_id,metadata")
                            .in_("draft_id", chunk)
                            .range(offset, offset + page - 1)
                            .execute()
                        )
                        rows = res.data if res and res.data else []
                    except Exception as e:
                        logging.exception(f"picks page failed: {e}")
                        rows = []
                        break
                    if not rows:
                        break
                    all_picks.extend(rows)
                    if len(rows) < page:
                        break
                    offset += page
        except Exception as e:
            logging.exception(f"picks fetch failed: {e}")
        return all_picks

    @rx.event
    def load_adp(self):
        self.is_loading = True
        yield
        self._load_adp_sync()

    def _load_adp_sync(self) -> None:
        self.is_loading = True
        try:
            client = get_supabase_client()
            if not client:
                self.is_loading = False
                return

            league_ids = self._get_matching_league_ids(client)
            draft_ids = self._get_matching_draft_ids(client, league_ids)
            picks = self._fetch_picks(client, draft_ids)

            self.total_drafts = len(draft_ids)
            self.total_picks = len(picks)

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

                if pid not in agg:
                    agg[pid] = {
                        "player_id": pid,
                        "full_name": full_name,
                        "position": pos,
                        "team": team,
                        "picks": [],
                    }
                agg[pid]["picks"].append(pick_no)
                if not agg[pid]["full_name"] or agg[pid][
                    "full_name"
                ].startswith("Player "):
                    agg[pid]["full_name"] = full_name
                if not agg[pid]["position"]:
                    agg[pid]["position"] = pos
                if not agg[pid]["team"]:
                    agg[pid]["team"] = team

            players: list[dict] = []
            for pid, info in agg.items():
                pk = info["picks"]
                if not pk:
                    continue
                count = len(pk)
                avg = sum(pk) / count
                mn = min(pk)
                mx = max(pk)
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
                        "min_pick": mn,
                        "max_pick": mx,
                        "avg_round": int(avg_round),
                        "avg_slot": round(avg_slot, 1),
                        "avg_display": f"{int(avg_round)}.{int(round(avg_slot)):02d}",
                    }
                )

            players.sort(key=lambda x: x["adp"])

            # Positional ranking based on ADP order within position.
            pos_counter: dict[str, int] = {}
            for i, p in enumerate(players):
                p["overall_rank"] = i + 1
                p["overall_pick_rank"] = f"#{i + 1}"
                pos = str(p.get("position") or "?")
                pos_counter[pos] = pos_counter.get(pos, 0) + 1
                p["positional_rank"] = pos_counter[pos]
                p["positional_pick_rank"] = f"{pos}#{pos_counter[pos]}"

            self.adp_players = players
            self.total_players = len(players)

            self.board_cells = self._build_board_cells(players)

            _ADP_RESULTS_CACHE[self._cache_key()] = {
                "adp_players": list(self.adp_players),
                "board_cells": list(self.board_cells),
                "total_drafts": self.total_drafts,
                "total_picks": self.total_picks,
                "total_players": self.total_players,
            }
        except Exception as e:
            logging.exception(f"load_adp failed: {e}")
        finally:
            self.is_loading = False
