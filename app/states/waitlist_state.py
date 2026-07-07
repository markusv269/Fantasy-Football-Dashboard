import reflex as rx
import requests
import logging
from datetime import datetime
from app.supabase_client import get_supabase_client


class WaitlistState(rx.State):
    sleeper_name_input: str = ""
    discord_input: str = ""
    dynasty_checked: bool = False
    dynasty_idp_checked: bool = False
    dynasty_bb_checked: bool = False
    resolved_user_id: str = ""
    resolved_display_name: str = ""
    resolved_avatar: str = ""
    is_resolving: bool = False
    is_submitting: bool = False
    username_valid: bool = False
    username_error: str = ""
    submit_success: bool = False
    existing_entry: dict[str, str | bool] = {}
    total_dynasty: int = 0
    total_idp: int = 0
    total_bb: int = 0
    total_registrations: int = 0
    all_entries: list[dict[str, str | bool]] = []

    @rx.var
    def dynasty_entries(self) -> list[dict[str, str | bool]]:
        return [e for e in self.all_entries if e.get("dynasty")]

    @rx.var
    def dynasty_idp_entries(self) -> list[dict[str, str | bool]]:
        return [e for e in self.all_entries if e.get("dynasty_idp")]

    @rx.var
    def dynasty_bb_entries(self) -> list[dict[str, str | bool]]:
        return [e for e in self.all_entries if e.get("dynasty_bb")]

    @rx.event
    def set_sleeper_name_input(self, val: str):
        self.sleeper_name_input = val

    @rx.event
    def set_discord_input(self, val: str):
        self.discord_input = val

    @rx.event
    def toggle_dynasty(self):
        self.dynasty_checked = not self.dynasty_checked

    @rx.event
    def toggle_dynasty_idp(self):
        self.dynasty_idp_checked = not self.dynasty_idp_checked

    @rx.event
    def toggle_dynasty_bb(self):
        self.dynasty_bb_checked = not self.dynasty_bb_checked

    @rx.event
    def validate_sleeper_name(self):
        self.is_resolving = True
        yield
        try:
            name = self.sleeper_name_input.strip()
            if not name:
                self.username_valid = False
                self.username_error = "Bitte gib einen Namen ein."
                self.is_resolving = False
                return
            r = requests.get(
                f"https://api.sleeper.app/v1/user/{name}", timeout=10
            )
            if r.status_code == 200 and r.json():
                data = r.json()
                self.resolved_user_id = str(data.get("user_id", ""))
                self.resolved_display_name = data.get("display_name", name)
                self.resolved_avatar = data.get("avatar", "") or ""
                self.username_valid = True
                self.username_error = ""
                client = get_supabase_client()
                if client:
                    res = (
                        client.table("dynasty_waitinglist")
                        .select("*")
                        .eq("user_id", self.resolved_user_id)
                        .execute()
                    )
                    if res and res.data:
                        entry = res.data[0]
                        self.existing_entry = entry
                        self.dynasty_checked = bool(entry.get("dynasty", False))
                        self.dynasty_idp_checked = bool(
                            entry.get("dynasty_idp", False)
                        )
                        self.dynasty_bb_checked = bool(
                            entry.get("dynasty_bb", False)
                        )
                        self.discord_input = entry.get("discord") or ""
                    else:
                        self.existing_entry = {}
            else:
                self.username_valid = False
                self.username_error = "Sleeper-User nicht gefunden."
                self.resolved_user_id = ""
                self.resolved_display_name = ""
                self.resolved_avatar = ""
                self.existing_entry = {}
        except Exception as e:
            logging.exception(f"Error validating sleeper name: {e}")
            self.username_valid = False
            self.username_error = "Sleeper-User nicht gefunden."
            self.resolved_user_id = ""
            self.resolved_display_name = ""
            self.resolved_avatar = ""
            self.existing_entry = {}
        finally:
            self.is_resolving = False

    @rx.event
    def submit_waitlist(self):
        if not (
            self.dynasty_checked
            or self.dynasty_idp_checked
            or self.dynasty_bb_checked
        ):
            return rx.toast(
                "Bitte wähle mindestens eine Liga-Art aus.", duration=3000
            )
        if not self.username_valid:
            return rx.toast(
                "Bitte überprüfe zuerst deinen Sleeper-Namen.", duration=3000
            )

        discord_val = self.discord_input.strip()
        if not discord_val:
            return rx.toast(
                "Bitte gib deinen Discord-Namen ein.", duration=3000
            )

        self.is_submitting = True
        yield
        try:
            client = get_supabase_client()
            if client:
                client.table("dynasty_waitinglist").upsert(
                    {
                        "user_id": self.resolved_user_id,
                        "sleeper_name": self.resolved_display_name
                        or self.sleeper_name_input.strip(),
                        "dynasty": self.dynasty_checked,
                        "dynasty_idp": self.dynasty_idp_checked,
                        "dynasty_bb": self.dynasty_bb_checked,
                        "discord": discord_val,
                    },
                    on_conflict="user_id",
                ).execute()
                self.submit_success = True
                yield WaitlistState.load_waitlist_stats
                return rx.toast("Anmeldung erfolgreich!", duration=3000)
        except Exception as e:
            logging.exception(f"Error submitting waitlist: {e}")
            return rx.toast("Es ist ein Fehler aufgetreten.", duration=3000)
        finally:
            self.is_submitting = False

    @rx.event
    def reset_form(self):
        self.sleeper_name_input = ""
        self.discord_input = ""
        self.dynasty_checked = False
        self.dynasty_idp_checked = False
        self.dynasty_bb_checked = False
        self.resolved_user_id = ""
        self.resolved_display_name = ""
        self.resolved_avatar = ""
        self.is_resolving = False
        self.is_submitting = False
        self.username_valid = False
        self.username_error = ""
        self.submit_success = False
        self.existing_entry = {}

    @rx.event
    def load_waitlist_stats(self):
        client = get_supabase_client()
        if client:
            try:
                res = (
                    client.table("dynasty_waitinglist")
                    .select("*")
                    .order("created_at", desc=False)
                    .execute()
                )
                if res and res.data:
                    data = res.data
                    self.total_registrations = len(data)
                    self.total_dynasty = sum(
                        (1 for d in data if d.get("dynasty"))
                    )
                    self.total_idp = sum(
                        (1 for d in data if d.get("dynasty_idp"))
                    )
                    self.total_bb = sum(
                        (1 for d in data if d.get("dynasty_bb"))
                    )
                    entries = []
                    for d in data:
                        created = str(d.get("created_at") or "")
                        display = ""
                        if created:
                            try:
                                dt = datetime.fromisoformat(
                                    created.replace("Z", "+00:00")
                                )
                                display = dt.strftime("%d.%m.%Y %H:%M")
                            except Exception:
                                logging.exception("Failed to parse created_at")
                                display = created[:10]
                        entries.append(
                            {
                                "sleeper_name": str(d.get("sleeper_name", "")),
                                "dynasty": bool(d.get("dynasty", False)),
                                "dynasty_idp": bool(
                                    d.get("dynasty_idp", False)
                                ),
                                "dynasty_bb": bool(d.get("dynasty_bb", False)),
                                "discord": str(d.get("discord") or ""),
                                "created_at": created,
                                "created_at_display": display,
                            }
                        )
                    self.all_entries = entries
                else:
                    self.total_registrations = 0
                    self.total_dynasty = 0
                    self.total_idp = 0
                    self.total_bb = 0
                    self.all_entries = []
            except Exception as e:
                logging.exception(f"Error loading waitlist stats: {e}")

    @rx.event
    def init_waitlist(self):
        yield WaitlistState.load_waitlist_stats
