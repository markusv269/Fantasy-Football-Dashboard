import reflex as rx
import requests
import logging
from app.supabase_client import get_supabase_client


class UserState(rx.State):
    sleeper_username: str = rx.LocalStorage("", name="sl_sleeper_username")
    sleeper_user_id: str = ""
    sleeper_display_name: str = ""
    sleeper_avatar: str = ""
    user_league_ids: list[str] = []
    my_leagues_data: list[dict[str, str | int]] = []
    is_resolving: bool = False
    is_loading_my_leagues: bool = False
    username_input: str = ""

    @rx.event
    def set_username_input(self, val: str):
        self.username_input = val

    @rx.event
    def save_username(self):
        """Save the username and resolve user identity from Sleeper API + Supabase managers table."""
        username = self.username_input.strip()
        if not username:
            return rx.toast("Bitte gib deinen Sleeper-Namen ein.")
        self.sleeper_username = username
        self.is_resolving = True
        yield UserState.resolve_user

    @rx.event
    def resolve_user(self):
        """Lookup Sleeper user_id from username, then find their leagues in our DB."""
        if not self.sleeper_username:
            self.is_resolving = False
            return
        try:
            r = requests.get(
                f"https://api.sleeper.app/v1/user/{self.sleeper_username}",
                timeout=10,
            )
            if r.status_code == 200 and r.json():
                data = r.json()
                self.sleeper_user_id = str(data.get("user_id", ""))
                self.sleeper_display_name = data.get(
                    "display_name", self.sleeper_username
                )
                self.sleeper_avatar = data.get("avatar", "") or ""
            else:
                self.sleeper_user_id = ""
                self.sleeper_display_name = self.sleeper_username
                self.sleeper_avatar = ""
                self.user_league_ids = []
                self.is_resolving = False
                return rx.toast("Sleeper-User nicht gefunden.", duration=3000)
            if self.sleeper_user_id:
                client = get_supabase_client()
                if client:
                    res = (
                        client.table("managers")
                        .select("league_id")
                        .eq("user_id", self.sleeper_user_id)
                        .execute()
                    )
                    if res and res.data:
                        self.user_league_ids = list(
                            set((str(m["league_id"]) for m in res.data))
                        )
                    else:
                        self.user_league_ids = []
                    self._load_my_leagues_data(client)
        except Exception as e:
            logging.exception(f"Error resolving user: {e}")
        finally:
            self.is_resolving = False

    def _load_my_leagues_data(self, client):
        """Load full league data for the user's leagues regardless of season."""
        if not self.user_league_ids:
            self.my_leagues_data = []
            return
        try:
            all_rows: list[dict] = []
            batch = 100
            ids = list(self.user_league_ids)
            for i in range(0, len(ids), batch):
                chunk = ids[i : i + batch]
                if not chunk:
                    continue
                res = (
                    client.table("leagues")
                    .select(
                        "league_id,league_name,league_season,league_type,league_sort"
                    )
                    .in_("league_id", chunk)
                    .execute()
                )
                if res and res.data:
                    all_rows.extend(res.data)
            normalized = []
            for lg in all_rows:
                lid = str(lg.get("league_id", "") or "").strip('"').strip()
                raw_sort = lg.get("league_sort")
                try:
                    ls_val = int(raw_sort) if raw_sort is not None else -1
                except Exception:
                    logging.exception("Unexpected error")
                    ls_val = -1
                normalized.append(
                    {
                        "league_id": lid,
                        "name": str(lg.get("league_name") or f"Liga {lid}"),
                        "season": str(lg.get("league_season") or ""),
                        "status": str(lg.get("league_type") or "unknown"),
                        "total_rosters": "",
                        "avatar": "",
                        "league_sort": ls_val,
                    }
                )

            def _season_key(x):
                s = str(x.get("season") or "0")
                return int(s) if s.isdigit() else 0

            def _ls_key(x) -> tuple:
                v = x.get("league_sort")
                try:
                    iv = int(v) if v is not None else None
                except Exception:
                    logging.exception("Unexpected error")
                    iv = None
                is_null = iv is None or iv < 0
                return (is_null, iv if iv is not None else 10**9)

            normalized.sort(
                key=lambda x: (
                    -_season_key(x),
                    *_ls_key(x),
                    str(x.get("name") or "").lower(),
                )
            )
            self.my_leagues_data = normalized
        except Exception as e:
            logging.exception(f"Error loading my_leagues_data: {e}")
            self.my_leagues_data = []

    @rx.event
    def init_user(self):
        """Called on app load to resolve the persisted username."""
        if self.sleeper_username:
            yield UserState.resolve_user

    @rx.event
    def clear_username(self):
        """Clear user identity."""
        self.sleeper_username = ""
        self.sleeper_user_id = ""
        self.sleeper_display_name = ""
        self.sleeper_avatar = ""
        self.user_league_ids = []
        self.my_leagues_data = []
        self.username_input = ""

    @rx.var
    def my_leagues_count(self) -> int:
        return len(self.my_leagues_data)

    @rx.var
    def my_dynasty_leagues(self) -> list[dict[str, str | int]]:
        return [
            lg
            for lg in self.my_leagues_data
            if str(lg.get("status", "")).lower() == "dynasty"
        ]

    @rx.var
    def my_redraft_leagues(self) -> list[dict[str, str | int]]:
        return [
            lg
            for lg in self.my_leagues_data
            if str(lg.get("status", "")).lower() == "redraft"
        ]

    @rx.var
    def my_other_leagues(self) -> list[dict[str, str | int]]:
        return [
            lg
            for lg in self.my_leagues_data
            if str(lg.get("status", "")).lower() not in ("dynasty", "redraft")
        ]

    @rx.var
    def is_logged_in(self) -> bool:
        return self.sleeper_username != "" and self.sleeper_user_id != ""

    @rx.var
    def has_username(self) -> bool:
        return self.sleeper_username != ""
