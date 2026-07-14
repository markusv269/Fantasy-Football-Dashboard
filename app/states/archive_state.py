import reflex as rx
import logging
from app.supabase_client import get_supabase_client


class ArchiveState(rx.State):
    is_loading: bool = False
    all_leagues: list[dict[str, str | int]] = []
    manager_counts: dict[str, int] = {}
    manager_samples: dict[str, list[str]] = {}
    available_seasons: list[str] = []
    available_types: list[str] = []
    available_managers: list[str] = []
    manager_to_leagues: dict[str, list[str]] = {}
    current_season: str = ""

    selected_season: str = "all"
    selected_type: str = "all"
    selected_manager: str = "all"
    search_query: str = ""

    @rx.event
    def load_archive(self):
        self.is_loading = True
        yield
        try:
            client = get_supabase_client()
            if not client:
                self.is_loading = False
                return
            res = (
                client.table("leagues")
                .select(
                    "league_id,league_name,league_season,league_type,league_sort,avatar"
                )
                .order("league_season", desc=True)
                .order("league_sort", desc=False)
                .execute()
            )
            leagues_rows = res.data if res and res.data else []
            seasons_int: list[int] = []
            for lg in leagues_rows:
                s = lg.get("league_season")
                if s is None:
                    continue
                try:
                    seasons_int.append(int(s))
                except Exception:
                    logging.exception("bad season")
            current_season = str(max(seasons_int)) if seasons_int else ""
            self.current_season = current_season

            all_league_ids = [
                str(lg.get("league_id", "")) for lg in leagues_rows
            ]

            mgr_map: dict[str, list[dict]] = {}
            try:
                batch = 200
                for i in range(0, len(all_league_ids), batch):
                    chunk = all_league_ids[i : i + batch]
                    if not chunk:
                        continue
                    mres = (
                        client.table("managers")
                        .select("league_id,display_name,team_name")
                        .in_("league_id", chunk)
                        .execute()
                    )
                    if mres and mres.data:
                        for m in mres.data:
                            lid = str(m.get("league_id", ""))
                            mgr_map.setdefault(lid, []).append(m)
            except Exception as e:
                logging.exception(f"managers fetch failed: {e}")

            counts: dict[str, int] = {}
            samples: dict[str, list[str]] = {}
            manager_to_leagues: dict[str, list[str]] = {}
            all_manager_names: set[str] = set()

            for lid, mgrs in mgr_map.items():
                names = []
                for m in mgrs:
                    n = str(m.get("display_name") or m.get("team_name") or "")
                    n = n.strip()
                    if n:
                        names.append(n)
                unique_names = list(dict.fromkeys(names))
                counts[lid] = len(unique_names)
                samples[lid] = unique_names[:3]
                for n in unique_names:
                    all_manager_names.add(n)
                    manager_to_leagues.setdefault(n, []).append(lid)

            archived = []
            for lg in leagues_rows:
                season_str = str(lg.get("league_season") or "")
                if season_str == current_season:
                    continue
                lid = str(lg.get("league_id", ""))
                raw_sort = lg.get("league_sort")
                try:
                    ls_val = int(raw_sort) if raw_sort is not None else -1
                except Exception:
                    logging.exception("Unexpected error")
                    ls_val = -1
                archived.append(
                    {
                        "league_id": lid,
                        "league_name": str(
                            lg.get("league_name") or f"Liga {lid}"
                        ),
                        "season": season_str,
                        "type": str(lg.get("league_type") or "unknown"),
                        "league_sort": ls_val,
                        "avatar": str(lg.get("avatar") or ""),
                    }
                )

            self.all_leagues = archived
            self.manager_counts = counts
            self.manager_samples = samples
            self.manager_to_leagues = manager_to_leagues

            seasons = sorted(
                {lg["season"] for lg in archived if lg["season"]},
                reverse=True,
            )
            types = sorted({lg["type"] for lg in archived if lg["type"]})
            managers_in_archive: set[str] = set()
            archive_ids = {lg["league_id"] for lg in archived}
            for name, lids in manager_to_leagues.items():
                if any(l in archive_ids for l in lids):
                    managers_in_archive.add(name)
            self.available_seasons = seasons
            self.available_types = types
            self.available_managers = sorted(
                managers_in_archive, key=lambda x: x.lower()
            )
        except Exception as e:
            logging.exception(f"Error loading archive: {e}")
        finally:
            self.is_loading = False

    @rx.event
    def set_selected_season(self, val: str):
        self.selected_season = val

    @rx.event
    def set_selected_type(self, val: str):
        self.selected_type = val

    @rx.event
    def set_selected_manager(self, val: str):
        self.selected_manager = val

    @rx.event
    def set_search_query(self, val: str):
        self.search_query = val

    @rx.event
    def reset_filters(self):
        self.selected_season = "all"
        self.selected_type = "all"
        self.selected_manager = "all"
        self.search_query = ""

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
    def clear_search(self):
        self.search_query = ""

    @rx.var
    def has_active_filters(self) -> bool:
        return (
            self.selected_season != "all"
            or self.selected_type != "all"
            or self.selected_manager != "all"
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
        if self.search_query != "":
            n += 1
        return n

    @rx.var
    def filtered_leagues(self) -> list[dict[str, str | int]]:
        result = []
        q = self.search_query.lower().strip()
        manager_league_ids: set[str] = set()
        if self.selected_manager != "all":
            manager_league_ids = set(
                self.manager_to_leagues.get(self.selected_manager, [])
            )
        for lg in self.all_leagues:
            if (
                self.selected_season != "all"
                and lg["season"] != self.selected_season
            ):
                continue
            if self.selected_type != "all" and lg["type"] != self.selected_type:
                continue
            if (
                self.selected_manager != "all"
                and lg["league_id"] not in manager_league_ids
            ):
                continue
            if q:
                haystack = (
                    f"{lg['league_name']} {lg['season']} {lg['type']} "
                    f"{lg['league_id']}"
                ).lower()
                sample_names = " ".join(
                    self.manager_samples.get(lg["league_id"], [])
                ).lower()
                if q not in haystack and q not in sample_names:
                    continue
            lid = lg["league_id"]
            result.append(
                {
                    "league_id": lid,
                    "league_name": lg["league_name"],
                    "season": lg["season"],
                    "type": lg["type"],
                    "manager_count": self.manager_counts.get(lid, 0),
                    "manager_sample": ", ".join(
                        self.manager_samples.get(lid, [])
                    ),
                    "league_sort": lg.get("league_sort", -1),
                    "avatar": lg.get("avatar", ""),
                }
            )

        def _ls_key(x) -> tuple:
            v = x.get("league_sort")
            try:
                iv = int(v) if v is not None else None
            except Exception:
                logging.exception("Unexpected error")
                iv = None
            is_null = iv is None or iv < 0
            return (is_null, iv if iv is not None else 10**9)

        result.sort(
            key=lambda x: (
                -int(x["season"]) if str(x["season"]).isdigit() else 0,
                *_ls_key(x),
                str(x["league_name"]).lower(),
            )
        )
        return result

    @rx.var
    def result_count(self) -> int:
        return len(self.filtered_leagues)

    @rx.var
    def total_archive_count(self) -> int:
        return len(self.all_leagues)
