import reflex as rx
import logging
from app.supabase_client import get_supabase_client
from app.league_types import (
    SUPPORTED_TYPES,
    add_types_col,
    is_missing_league_types_column_error,
    normalize_league_types,
)


def _lg_sort_key(lg: dict) -> tuple:
    """Season DESC, league_sort ASC (nulls last), name ASC."""
    s = str(lg.get("season", "") or "0")
    try:
        season_int = int(s) if s.lstrip("-").isdigit() else 0
    except Exception:
        logging.exception("Unexpected error")
        season_int = 0
    ls_raw = lg.get("league_sort")
    try:
        ls_int = int(ls_raw) if ls_raw is not None else None
    except Exception:
        logging.exception("Unexpected error")
        ls_int = None
    is_null = ls_int is None or ls_int < 0
    name = str(lg.get("league_name") or "").lower()
    return (-season_int, is_null, ls_int if ls_int is not None else 10**9, name)


PAGE_SIZE = 1000


def _paginated_in_query(
    client,
    table: str,
    select_cols: str,
    filter_col: str,
    filter_values: list[str],
    extra_eq: dict | None = None,
    id_batch: int = 100,
) -> list[dict]:
    """Fetch all rows matching an IN (...) filter, paginating past Supabase's
    default row limit. Batches the IN clause to avoid overly large lists and
    uses range() to page through each chunk until an empty page is returned.
    """
    out: list[dict] = []
    if not filter_values:
        return out
    for i in range(0, len(filter_values), id_batch):
        chunk = filter_values[i : i + id_batch]
        if not chunk:
            continue
        offset = 0
        while True:
            try:
                q = (
                    client.table(table)
                    .select(select_cols)
                    .in_(filter_col, chunk)
                )
                if extra_eq:
                    for k, v in extra_eq.items():
                        q = q.eq(k, v)
                res = q.range(offset, offset + PAGE_SIZE - 1).execute()
                rows = res.data if res and res.data else []
            except Exception as e:
                logging.exception(
                    f"paginated fetch failed table={table} offset={offset}: {e}"
                )
                rows = []
                break
            if not rows:
                break
            out.extend(rows)
            if len(rows) < PAGE_SIZE:
                break
            offset += PAGE_SIZE
    return out


class LeaguesState(rx.State):
    is_loading: bool = False
    is_full_loaded: bool = False
    current_season: str = ""
    all_leagues: list[dict[str, str | int | list[str]]] = []
    available_seasons: list[str] = []
    available_types: list[str] = []
    available_managers: list[str] = []
    manager_to_leagues: dict[str, list[str]] = {}

    selected_season: str = "all"
    selected_type: str = "all"
    selected_manager: str = "all"
    selected_week: str = "all"
    selected_scope: str = "all"
    search_query: str = ""
    sort_by: str = "season_desc"

    @rx.event
    def load_leagues(self):
        """Initial load: only current season. Full data loads on demand."""
        self.is_loading = True
        yield
        try:
            client = get_supabase_client()
            if not client:
                self.is_loading = False
                return
            max_res = (
                client.table("leagues")
                .select("league_season")
                .order("league_season", desc=True)
                .limit(1)
                .execute()
            )
            current_season_val = None
            if max_res and max_res.data:
                current_season_val = max_res.data[0].get("league_season")
            if current_season_val is None:
                self.is_loading = False
                return
            self.current_season = str(current_season_val)
            base_cols = (
                "league_id,league_name,league_season,league_type,"
                "league_sort,avatar"
            )
            try:
                res = (
                    client.table("leagues")
                    .select(add_types_col(base_cols))
                    .eq("league_season", current_season_val)
                    .execute()
                )
            except Exception as e:
                if is_missing_league_types_column_error(e):
                    # Expected fallback: `league_types` column not yet
                    # deployed. Retry without it silently.
                    res = (
                        client.table("leagues")
                        .select(base_cols)
                        .eq("league_season", current_season_val)
                        .execute()
                    )
                else:
                    logging.exception(
                        f"leagues select (current season) failed: {e}"
                    )
                    raise
            leagues_rows = res.data if res and res.data else []
            self._populate_from_rows(client, leagues_rows)
            self.is_full_loaded = False
        except Exception as e:
            logging.exception(f"Error loading current-season leagues: {e}")
        finally:
            self.is_loading = False

    def _populate_from_rows(
        self,
        client,
        leagues_rows: list[dict],
        include_week_metadata: bool = True,
    ):
        """Populate all state fields from a list of league rows.

        When ``include_week_metadata`` is False, skip the expensive
        per-week availability scan across all 19 weeks × all leagues.
        Week availability is then loaded lazily on demand when the
        user selects a specific week filter.
        """
        try:
            all_ids = [str(lg.get("league_id", "")) for lg in leagues_rows]

            # Paginate managers query so all rows are loaded (Supabase's
            # default row cap is 1000 per request).
            mgr_map: dict[str, list[dict]] = {}
            mgr_rows = _paginated_in_query(
                client,
                "managers",
                "league_id,display_name,team_name",
                "league_id",
                all_ids,
                id_batch=100,
            )
            for m in mgr_rows:
                lid = str(m.get("league_id", ""))
                mgr_map.setdefault(lid, []).append(m)

            # Build week availability using a bounded per-week existence
            # strategy. Only executed when include_week_metadata is True
            # (current-season fast path). For broad full loads, this is
            # skipped entirely to avoid timeouts; week metadata is loaded
            # lazily on demand.
            weeks_by_league: dict[str, set[int]] = {}
            if include_week_metadata:
                self._collect_week_availability(
                    client, "matchup_week_stats", all_ids, weeks_by_league
                )
                self._collect_week_availability(
                    client, "rosters", all_ids, weeks_by_league
                )

            manager_to_leagues: dict[str, list[str]] = {}
            all_manager_names: set[str] = set()
            leagues_out: list[dict] = []
            for lg in leagues_rows:
                lid = str(lg.get("league_id", ""))
                mgrs = mgr_map.get(lid, [])
                names = []
                for m in mgrs:
                    n = str(
                        m.get("display_name") or m.get("team_name") or ""
                    ).strip()
                    if n:
                        names.append(n)
                unique_names = list(dict.fromkeys(names))
                for n in unique_names:
                    all_manager_names.add(n)
                    manager_to_leagues.setdefault(n, []).append(lid)
                weeks_set = weeks_by_league.get(lid, set())
                weeks_sorted = sorted(weeks_set)
                latest_week = max(weeks_sorted) if weeks_sorted else 0
                raw_sort = lg.get("league_sort")
                try:
                    league_sort_val = (
                        int(raw_sort) if raw_sort is not None else -1
                    )
                except Exception:
                    logging.exception("Unexpected error")
                    league_sort_val = -1
                primary, types_list = normalize_league_types(
                    lg.get("league_types"), lg.get("league_type")
                )
                leagues_out.append(
                    {
                        "league_id": lid,
                        "league_name": str(
                            lg.get("league_name") or f"Liga {lid}"
                        ),
                        "season": str(lg.get("league_season") or ""),
                        "type": primary,
                        "types": types_list,
                        "manager_count": len(unique_names),
                        "manager_sample": ", ".join(unique_names[:3]),
                        "manager_names": unique_names,
                        "available_weeks": [str(w) for w in weeks_sorted],
                        "latest_week": latest_week,
                        "league_sort": league_sort_val,
                        "avatar": str(lg.get("avatar") or ""),
                    }
                )
            leagues_out.sort(key=_lg_sort_key)

            self.all_leagues = leagues_out
            self.manager_to_leagues = manager_to_leagues
            self.available_seasons = sorted(
                {lg["season"] for lg in leagues_out if lg["season"]},
                reverse=True,
            )
            type_set: set[str] = set()
            for lg in leagues_out:
                for t in lg.get("types") or []:
                    ts = str(t).strip().lower()
                    if ts in SUPPORTED_TYPES:
                        type_set.add(ts)
                primary = str(lg.get("type") or "").strip().lower()
                if primary in SUPPORTED_TYPES:
                    type_set.add(primary)
            self.available_types = sorted(type_set)
            self.available_managers = sorted(
                all_manager_names, key=lambda x: x.lower()
            )
        except Exception as e:
            logging.exception(f"Error populating leagues: {e}")

    def _collect_week_availability(
        self,
        client,
        table: str,
        league_ids: list[str],
        weeks_by_league: dict[str, set[int]],
    ) -> None:
        """Populate weeks_by_league using a bounded per-week query.

        For each week in 0..18, query the given table filtered by
        (league_id IN chunk) AND (week = w), selecting only
        league_id,week. This keeps the returned row volume small and
        avoids scanning per-roster/per-matchup detail rows. Pages
        through with range() until fewer than PAGE_SIZE rows are
        returned in a page.
        """
        if not league_ids:
            return
        id_batch = 100
        for w in range(0, 19):
            for i in range(0, len(league_ids), id_batch):
                chunk = league_ids[i : i + id_batch]
                if not chunk:
                    continue
                offset = 0
                while True:
                    try:
                        res = (
                            client.table(table)
                            .select("league_id,week")
                            .in_("league_id", chunk)
                            .eq("week", w)
                            .range(offset, offset + PAGE_SIZE - 1)
                            .execute()
                        )
                        rows = res.data if res and res.data else []
                    except Exception as e:
                        logging.exception(
                            f"week availability fetch failed {table} w={w}: {e}"
                        )
                        rows = []
                        break
                    if not rows:
                        break
                    for r in rows:
                        lid = str(r.get("league_id", ""))
                        if not lid:
                            continue
                        weeks_by_league.setdefault(lid, set()).add(w)
                    if len(rows) < PAGE_SIZE:
                        break
                    offset += PAGE_SIZE

    def _load_full_leagues_sync(self) -> None:
        """Synchronous helper: load ALL seasons + full paginated metadata.

        Called inline from setter events so filters that require the full
        dataset (search, non-current season, specific manager) get the data
        loaded within the same event tick rather than a yielded follow-up.
        Idempotent — no-op when full data is already loaded.

        Week availability is intentionally skipped here — computing it
        across all historical leagues and all 19 weeks times out on
        large inventories. It is loaded lazily via
        :py:meth:`set_selected_week` when a specific week filter is
        applied.
        """
        if self.is_full_loaded:
            return
        self.is_loading = True
        try:
            client = get_supabase_client()
            if not client:
                return
            base_cols = (
                "league_id,league_name,league_season,league_type,"
                "league_sort,avatar"
            )
            try:
                res = (
                    client.table("leagues")
                    .select(add_types_col(base_cols))
                    .order("league_season", desc=True)
                    .order("league_sort", desc=False)
                    .execute()
                )
            except Exception as e:
                if is_missing_league_types_column_error(e):
                    # Expected fallback: `league_types` column not yet
                    # deployed. Retry without it silently.
                    res = (
                        client.table("leagues")
                        .select(base_cols)
                        .order("league_season", desc=True)
                        .order("league_sort", desc=False)
                        .execute()
                    )
                else:
                    logging.exception(f"leagues select (full) failed: {e}")
                    raise
            leagues_rows = res.data if res and res.data else []
            self._populate_from_rows(
                client, leagues_rows, include_week_metadata=False
            )
            self.is_full_loaded = True
        except Exception as e:
            logging.exception(f"Error loading full leagues (sync): {e}")
        finally:
            self.is_loading = False

    def _ensure_week_metadata_for_selected(self, week: int) -> None:
        """Lazy-load week availability for a specific week across all
        currently loaded leagues that don't yet have any week metadata.

        This queries only the selected week (from matchup_week_stats and
        rosters) filtered to the currently loaded league IDs — a cheap
        bounded query — instead of the full 19-week × N-league scan.
        """
        if not self.all_leagues:
            return
        try:
            w = int(week)
        except Exception:
            logging.exception("bad week")
            return
        # Consider a league as "missing week metadata" if its
        # available_weeks list is empty. Under the lazy-load regime,
        # historical leagues will start empty and only accrue weeks as
        # the user selects them.
        missing_ids = [
            str(lg.get("league_id", ""))
            for lg in self.all_leagues
            if not lg.get("available_weeks")
        ]
        if not missing_ids:
            return
        client = get_supabase_client()
        if not client:
            return
        found: set[str] = set()
        for table in ("matchup_week_stats", "rosters"):
            id_batch = 100
            for i in range(0, len(missing_ids), id_batch):
                chunk = missing_ids[i : i + id_batch]
                if not chunk:
                    continue
                offset = 0
                while True:
                    try:
                        res = (
                            client.table(table)
                            .select("league_id,week")
                            .in_("league_id", chunk)
                            .eq("week", w)
                            .range(offset, offset + PAGE_SIZE - 1)
                            .execute()
                        )
                        rows = res.data if res and res.data else []
                    except Exception as e:
                        logging.exception(
                            f"lazy week metadata fetch failed {table}: {e}"
                        )
                        rows = []
                        break
                    if not rows:
                        break
                    for r in rows:
                        lid = str(r.get("league_id", ""))
                        if lid:
                            found.add(lid)
                    if len(rows) < PAGE_SIZE:
                        break
                    offset += PAGE_SIZE
        if not found:
            return
        # Update each matching league row with the newly discovered week.
        w_str = str(w)
        updated = []
        for lg in self.all_leagues:
            lid = str(lg.get("league_id", ""))
            if lid in found:
                new_lg = dict(lg)
                weeks = list(new_lg.get("available_weeks") or [])
                if w_str not in weeks:
                    weeks.append(w_str)
                    try:
                        weeks_sorted = sorted(
                            weeks,
                            key=lambda x: int(x) if str(x).isdigit() else 0,
                        )
                    except Exception:
                        logging.exception("weeks sort")
                        weeks_sorted = weeks
                    new_lg["available_weeks"] = weeks_sorted
                cur_latest = int(new_lg.get("latest_week") or 0)
                if w > cur_latest:
                    new_lg["latest_week"] = w
                updated.append(new_lg)
            else:
                updated.append(lg)
        self.all_leagues = updated

    @rx.event
    def load_full_leagues(self):
        """Load ALL seasons and full manager/week metadata. Idempotent."""
        if self.is_full_loaded:
            return
        yield
        self._load_full_leagues_sync()

    def _needs_full_data(self) -> bool:
        """Any filter that could reference non-current-season data."""
        if self.is_full_loaded:
            return False
        if (
            self.selected_season != "all"
            and self.selected_season != self.current_season
        ):
            return True
        if self.selected_manager != "all":
            return True
        if self.search_query.strip() != "":
            return True
        return False

    @rx.event
    def set_selected_season(self, val: str):
        self.selected_season = val
        if (
            val != "all"
            and val != self.current_season
            and not self.is_full_loaded
        ):
            self._load_full_leagues_sync()

    @rx.event
    def set_selected_type(self, val: str):
        self.selected_type = val

    @rx.event
    def set_selected_manager(self, val: str):
        self.selected_manager = val
        if val != "all" and not self.is_full_loaded:
            self._load_full_leagues_sync()

    @rx.event
    def set_selected_week(self, val: str):
        self.selected_week = val
        if val and val != "all":
            try:
                w = int(val)
            except Exception:
                logging.exception("bad selected week")
                return
            self._ensure_week_metadata_for_selected(w)

    @rx.event
    def set_selected_scope(self, val: str):
        self.selected_scope = val

    @rx.event
    def set_search_query(self, val: str):
        self.search_query = val
        if val.strip() != "" and not self.is_full_loaded:
            self._load_full_leagues_sync()

    @rx.event
    def set_sort_by(self, val: str):
        self.sort_by = val

    @rx.event
    def ensure_full_loaded(self):
        if not self.is_full_loaded:
            self._load_full_leagues_sync()

    @rx.event
    def reset_filters(self):
        self.selected_season = "all"
        self.selected_type = "all"
        self.selected_manager = "all"
        self.selected_week = "all"
        self.selected_scope = "all"
        self.search_query = ""
        self.sort_by = "season_desc"

    @rx.event
    def clear_season(self):
        self.selected_season = "all"

    @rx.event
    def clear_type(self):
        self.selected_type = "all"

    @rx.event
    def clear_manager(self):
        self.selected_manager = "all"

    @rx.event
    def clear_week(self):
        self.selected_week = "all"

    @rx.event
    def clear_scope(self):
        self.selected_scope = "all"

    @rx.event
    def clear_search(self):
        self.search_query = ""

    @rx.var
    def has_active_filters(self) -> bool:
        return (
            self.selected_season != "all"
            or self.selected_type != "all"
            or self.selected_manager != "all"
            or self.selected_week != "all"
            or self.selected_scope != "all"
            or self.search_query != ""
        )

    @rx.var
    def active_filter_count(self) -> int:
        n = 0
        if self.selected_season != "all":
            n += 1
        if self.selected_type != "all":
            n += 1
        if self.selected_manager != "all":
            n += 1
        if self.selected_week != "all":
            n += 1
        if self.selected_scope != "all":
            n += 1
        if self.search_query != "":
            n += 1
        return n

    @rx.var
    def total_count(self) -> int:
        return len(self.all_leagues)

    async def _get_user_league_ids(self) -> set[str]:
        try:
            from app.states.user_state import UserState

            u = await self.get_state(UserState)
            return {str(x) for x in u.user_league_ids}
        except Exception as e:
            logging.exception(f"user leagues fetch failed: {e}")
            return set()

    async def _is_logged_in(self) -> bool:
        try:
            from app.states.user_state import UserState

            u = await self.get_state(UserState)
            return bool(u.is_logged_in)
        except Exception:
            logging.exception("login check failed")
            return False

    @rx.var
    async def filtered_leagues(self) -> list[dict[str, str | int]]:
        user_ids: set[str] = set()
        logged_in = await self._is_logged_in()
        if logged_in and self.selected_scope != "all":
            user_ids = await self._get_user_league_ids()

        q = self.search_query.lower().strip()
        mgr_league_ids: set[str] = set()
        if self.selected_manager != "all":
            mgr_league_ids = set(
                self.manager_to_leagues.get(self.selected_manager, [])
            )
        try:
            week_int = (
                int(self.selected_week) if self.selected_week != "all" else None
            )
        except Exception:
            logging.exception("bad week filter")
            week_int = None

        result = []
        for lg in self.all_leagues:
            if (
                self.selected_season != "all"
                and lg["season"] != self.selected_season
            ):
                continue
            if self.selected_type != "all":
                lg_types = [str(t).lower() for t in (lg.get("types") or [])]
                if not lg_types and lg.get("type"):
                    lg_types = [str(lg.get("type")).lower()]
                if self.selected_type.lower() not in lg_types:
                    continue
            if (
                self.selected_manager != "all"
                and lg["league_id"] not in mgr_league_ids
            ):
                continue
            if week_int is not None:
                weeks = lg.get("available_weeks", [])
                if str(week_int) not in weeks:
                    continue
            if logged_in and self.selected_scope == "mine":
                if lg["league_id"] not in user_ids:
                    continue
            if logged_in and self.selected_scope == "others":
                if lg["league_id"] in user_ids:
                    continue
            if q:
                names_str = " ".join(lg.get("manager_names", [])).lower()
                haystack = (
                    f"{lg['league_name']} {lg['season']} {lg['type']} "
                    f"{lg['league_id']} {names_str}"
                ).lower()
                if q not in haystack:
                    continue
            result.append(lg)

        def _season_int(x):
            s = str(x.get("season") or "0")
            try:
                return int(s) if s.isdigit() else 0
            except Exception:
                logging.exception("bad season sort")
                return 0

        def _ls_key(x) -> tuple:
            v = x.get("league_sort")
            try:
                iv = int(v) if v is not None else None
            except Exception:
                logging.exception("Unexpected error")
                iv = None
            is_null = iv is None or iv < 0
            return (is_null, iv if iv is not None else 10**9)

        sort_by = self.sort_by
        if sort_by == "season_desc":
            result.sort(
                key=lambda x: (
                    -_season_int(x),
                    *_ls_key(x),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "season_asc":
            result.sort(
                key=lambda x: (
                    _season_int(x),
                    *_ls_key(x),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "name_asc":
            result.sort(key=lambda x: str(x.get("league_name") or "").lower())
        elif sort_by == "name_desc":
            result.sort(
                key=lambda x: str(x.get("league_name") or "").lower(),
                reverse=True,
            )
        elif sort_by == "managers_desc":
            result.sort(
                key=lambda x: (
                    -int(x.get("manager_count") or 0),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "managers_asc":
            result.sort(
                key=lambda x: (
                    int(x.get("manager_count") or 0),
                    str(x.get("league_name") or "").lower(),
                )
            )
        elif sort_by == "week_desc":
            result.sort(
                key=lambda x: (
                    -int(x.get("latest_week") or 0),
                    -_season_int(x),
                )
            )
        elif sort_by == "week_asc":
            result.sort(
                key=lambda x: (
                    int(x.get("latest_week") or 0)
                    if int(x.get("latest_week") or 0) > 0
                    else 9999,
                    -_season_int(x),
                )
            )
        return result

    @rx.var
    async def result_count(self) -> int:
        rows = await self.filtered_leagues
        return len(rows)
