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
    is_resolving: bool = False
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
                f"https://api.sleeper.app/v1/user/{self.sleeper_username}", timeout=10
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
        except Exception as e:
            logging.exception(f"Error resolving user: {e}")
        finally:
            self.is_resolving = False

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
        self.username_input = ""

    @rx.var
    def is_logged_in(self) -> bool:
        return self.sleeper_username != "" and self.sleeper_user_id != ""

    @rx.var
    def has_username(self) -> bool:
        return self.sleeper_username != ""