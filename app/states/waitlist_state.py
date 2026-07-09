import reflex as rx
import requests
import logging
from datetime import datetime, timezone
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
    is_removing: bool = False
    username_valid: bool = False
    username_error: str = ""
    submit_success: bool = False
    existing_entry: dict[str, str | bool | None] = {}
    total_dynasty: int = 0
    total_idp: int = 0
    total_bb: int = 0
    total_registrations: int = 0
    all_entries: list[dict[str, str | bool]] = []

    def _sort_key(self, entry: dict, ts_field: str) -> str:
        """Helper to generate a stable sort key with fallback. Ensures empty strings/None handle gracefully."""
        ts = entry.get(ts_field)
        if ts and str(ts).strip():
            return str(ts)
        fallback = entry.get("created_at")
        if fallback and str(fallback).strip():
            return str(fallback)
        return ""  # Stable bottom fallback

    def _format_iso_to_display(self, iso_str: str | None) -> str:
        if not iso_str or not str(iso_str).strip():
            return ""
        try:
            dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            logging.exception("Unexpected error")
            return str(iso_str)[:10]

    @rx.var
    def dynasty_entries(self) -> list[dict[str, str | bool]]:
        entries = [e for e in self.all_entries if e.get("dynasty")]
        entries.sort(key=lambda e: self._sort_key(e, "registration_dyn"))
        formatted = []
        for e in entries:
            new_e = dict(e)
            reg_ts = e.get("registration_dyn")
            new_e["time_display"] = self._format_iso_to_display(
                reg_ts if reg_ts else e.get("created_at")
            )
            formatted.append(new_e)
        return formatted

    @rx.var
    def dynasty_idp_entries(self) -> list[dict[str, str | bool]]:
        entries = [e for e in self.all_entries if e.get("dynasty_idp")]
        entries.sort(key=lambda e: self._sort_key(e, "registration_idp"))
        formatted = []
        for e in entries:
            new_e = dict(e)
            reg_ts = e.get("registration_idp")
            new_e["time_display"] = self._format_iso_to_display(
                reg_ts if reg_ts else e.get("created_at")
            )
            formatted.append(new_e)
        return formatted

    @rx.var
    def dynasty_bb_entries(self) -> list[dict[str, str | bool]]:
        entries = [e for e in self.all_entries if e.get("dynasty_bb")]
        entries.sort(key=lambda e: self._sort_key(e, "registration_bb"))
        formatted = []
        for e in entries:
            new_e = dict(e)
            reg_ts = e.get("registration_bb")
            new_e["time_display"] = self._format_iso_to_display(
                reg_ts if reg_ts else e.get("created_at")
            )
            formatted.append(new_e)
        return formatted

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
                        raw_entry = res.data[0]
                        # Normalize row to match the declared state type and handle NULLs
                        entry = {
                            "user_id": str(raw_entry.get("user_id", "")),
                            "sleeper_name": str(
                                raw_entry.get("sleeper_name", "")
                            ),
                            "discord": str(raw_entry.get("discord", "") or ""),
                            "dynasty": bool(raw_entry.get("dynasty", False)),
                            "dynasty_idp": bool(
                                raw_entry.get("dynasty_idp", False)
                            ),
                            "dynasty_bb": bool(
                                raw_entry.get("dynasty_bb", False)
                            ),
                            "created_at": str(raw_entry.get("created_at", "")),
                            "registration_dyn": str(
                                raw_entry.get("registration_dyn") or ""
                            ),
                            "registration_idp": str(
                                raw_entry.get("registration_idp") or ""
                            ),
                            "registration_bb": str(
                                raw_entry.get("registration_bb") or ""
                            ),
                        }
                        self.existing_entry = entry
                        self.dynasty_checked = entry["dynasty"]
                        self.dynasty_idp_checked = entry["dynasty_idp"]
                        self.dynasty_bb_checked = entry["dynasty_bb"]
                        self.discord_input = entry["discord"]
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
                now_iso = datetime.now(timezone.utc).isoformat()
                existing_dyn = str(
                    self.existing_entry.get("registration_dyn") or ""
                )
                existing_idp = str(
                    self.existing_entry.get("registration_idp") or ""
                )
                existing_bb = str(
                    self.existing_entry.get("registration_bb") or ""
                )
                prev_dyn = bool(self.existing_entry.get("dynasty", False))
                prev_idp = bool(self.existing_entry.get("dynasty_idp", False))
                prev_bb = bool(self.existing_entry.get("dynasty_bb", False))

                if self.dynasty_checked:
                    reg_dyn = (
                        existing_dyn if (prev_dyn and existing_dyn) else now_iso
                    )
                else:
                    reg_dyn = None
                if self.dynasty_idp_checked:
                    reg_idp = (
                        existing_idp if (prev_idp and existing_idp) else now_iso
                    )
                else:
                    reg_idp = None
                if self.dynasty_bb_checked:
                    reg_bb = (
                        existing_bb if (prev_bb and existing_bb) else now_iso
                    )
                else:
                    reg_bb = None

                client.table("dynasty_waitinglist").upsert(
                    {
                        "user_id": self.resolved_user_id,
                        "sleeper_name": self.resolved_display_name
                        or self.sleeper_name_input.strip(),
                        "dynasty": self.dynasty_checked,
                        "dynasty_idp": self.dynasty_idp_checked,
                        "dynasty_bb": self.dynasty_bb_checked,
                        "discord": discord_val,
                        "registration_dyn": reg_dyn,
                        "registration_idp": reg_idp,
                        "registration_bb": reg_bb,
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
    def remove_from_waitlist(self):
        if not self.resolved_user_id:
            return rx.toast(
                "Keine bestehende Anmeldung gefunden.", duration=3000
            )
        self.is_removing = True
        yield
        try:
            client = get_supabase_client()
            if not client:
                return rx.toast("Datenbank nicht verfügbar.", duration=3000)
            client.table("dynasty_waitinglist").delete().eq(
                "user_id", self.resolved_user_id
            ).execute()

            # Atomic state reset after successful deletion
            self.sleeper_name_input = ""
            self.discord_input = ""
            self.dynasty_checked = False
            self.dynasty_idp_checked = False
            self.dynasty_bb_checked = False
            self.resolved_user_id = ""
            self.resolved_display_name = ""
            self.resolved_avatar = ""
            self.username_valid = False
            self.username_error = ""
            self.submit_success = False
            self.existing_entry = {}

            yield WaitlistState.load_waitlist_stats
            return rx.toast(
                "Du wurdest erfolgreich von der Warteliste entfernt.",
                duration=3000,
            )
        except Exception as e:
            logging.exception(f"Error removing from waitlist: {e}")
            return rx.toast(
                "Fehler beim Entfernen von der Warteliste.", duration=3000
            )
        finally:
            self.is_removing = False

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
                                "registration_dyn": str(
                                    d.get("registration_dyn") or ""
                                ),
                                "registration_idp": str(
                                    d.get("registration_idp") or ""
                                ),
                                "registration_bb": str(
                                    d.get("registration_bb") or ""
                                ),
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
