import json
import logging
from decimal import Decimal, InvalidOperation
from typing import TypedDict

import reflex as rx

from app.sleeper_api import get_league, get_league_users, get_rosters
from app.supabase_client import get_supabase_client


class FantasyBoerseEntry(TypedDict):
    id: str
    created_at: str
    entry_type: str
    league_id: str
    roster_id: int
    buyin: float
    invite_link: str
    contact_sleeper: str
    contact_discord: str
    description: str
    status: str
    league_name: str
    league_size: int
    league_form: str
    roster_positions: list[str]
    roster_structure: str
    scoring_settings: dict[str, float]
    scoring_summary: str
    team_name: str
    owner_user_id: str
    raw_league: str
    raw_roster: str
    live_error: str


class FantasyBoerseState(rx.State):
    entries: list[FantasyBoerseEntry] = []
    is_loading: bool = False
    error_message: str = ""
    form_filter: str = "all"
    size_filter: str = "all"
    buyin_filter: str = "all"
    status_filter: str = "all"
    entry_type: str = "manager_spot"
    is_submitting: bool = False
    form_message: str = ""
    form_message_type: str = ""
    form_reset_counter: int = 0

    @rx.event
    def load_entries(self):
        self.is_loading = True
        self.error_message = ""
        yield
        try:
            client = get_supabase_client()
            if client is None:
                self.error_message = (
                    "Die Fantasybörse ist derzeit nicht verfügbar."
                )
                return
            result = (
                client.table("fantasy_boerse_entries")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            normalized: list[FantasyBoerseEntry] = []
            for raw_row in result.data or []:
                if not isinstance(raw_row, dict):
                    continue
                entry = self._normalize_entry(raw_row)
                live = self._fetch_live_entry(
                    entry["entry_type"],
                    entry["league_id"],
                    entry["roster_id"],
                    entry["league_form"],
                )
                normalized.append(self._apply_live_entry(entry, live))
                self._persist_live_entry(client, entry["id"], live)
            self.entries = normalized
        except Exception as exc:
            logging.exception(f"Error loading Fantasybörse entries: {exc}")
            self.entries = []
            self.error_message = "Die Einträge konnten nicht geladen werden. Bitte versuche es später erneut."
        finally:
            self.is_loading = False

    @rx.event
    def set_entry_type(self, value: str):
        if value in {"manager_spot", "whole_league"}:
            self.entry_type = value

    def _reset_entry_form(self):
        self.entry_type = "manager_spot"
        self.form_reset_counter += 1

    @staticmethod
    def _as_mapping(value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return {str(key): item for key, item in value.items()}
        return {}

    @staticmethod
    def _as_int(value: object, default: int = 0) -> int:
        try:
            return int(value or default)
        except (TypeError, ValueError):
            logging.exception(f"Invalid integer value: {value}")
            return default

    @staticmethod
    def _json_string(value: object) -> str:
        try:
            return json.dumps(
                value if value is not None else {},
                default=str,
                sort_keys=True,
            )
        except (TypeError, ValueError):
            logging.exception(f"Could not serialize live Sleeper data: {value}")
            return "{}"

    @staticmethod
    def _numeric_settings(value: object) -> dict[str, float]:
        raw = FantasyBoerseState._as_mapping(value)
        result: dict[str, float] = {}
        for key, item in raw.items():
            if isinstance(item, bool):
                continue
            try:
                result[key] = float(item)
            except (TypeError, ValueError):
                logging.exception(f"Invalid scoring value for {key}: {item}")
        return result

    @staticmethod
    def _infer_form(
        stored_form: object,
        league: dict[str, object],
        settings: dict[str, object],
    ) -> str:
        stored = str(stored_form or "").strip().lower().replace(" ", "_")
        if "idp" in stored:
            return "idp"
        if "bestball" in stored or "best_ball" in stored:
            return "bestball"
        if stored in {"dynasty", "redraft"}:
            return stored

        parts = [
            str(league.get(key) or "")
            for key in ("name", "type", "status", "draft_type")
        ]
        parts.append(settings or {})
        searchable = " ".join(parts).lower()
        if "idp" in searchable:
            return "idp"
        if "bestball" in searchable or "best_ball" in searchable:
            return "bestball"
        if "redraft" in searchable:
            return "redraft"
        if "dynasty" in searchable:
            return "dynasty"
        return "unknown"

    @staticmethod
    def _scoring_summary(scoring: dict[str, float]) -> str:
        reception = scoring.get("rec", 0.0)
        if reception == 1:
            parts = ["PPR"]
        elif reception == 0.5:
            parts = ["Half-PPR"]
        elif reception > 0:
            parts = [f"Rec {reception:g}"]
        else:
            parts = ["Standard"]

        labels = (
            ("pass_td", "Pass TD"),
            ("rush_td", "Rush TD"),
            ("rec_td", "Rec TD"),
            ("pass_int", "Pass INT"),
            ("sack", "Sack"),
            ("fum_lost", "Fumble lost"),
        )
        for key, label in labels:
            if key in scoring:
                parts.append(f"{label} {scoring[key]:g}")
        return " · ".join(parts)

    @staticmethod
    def _user_team_name(
        user: dict[str, object], roster: dict[str, object]
    ) -> str:
        metadata = user.get("metadata") or {}
        roster_metadata = roster.get("metadata") or {}
        team_name = str(
            metadata.get("team_name") or roster_metadata.get("team_name") or ""
        ).strip()
        display_name = str(user.get("display_name") or "").strip()
        if (
            team_name
            and display_name
            and team_name.lower() != display_name.lower()
        ):
            return f"{team_name} · {display_name}"
        return team_name or display_name

    def _fetch_live_entry(
        self, entry_type: str, league_id: str, roster_id: int, stored_form: str
    ) -> dict[str, object]:
        try:
            league = self._as_mapping(get_league(league_id))
            if not league or not league.get("name"):
                return {
                    "valid": False,
                    "persist_safe": False,
                    "error": f"Sleeper-Liga {league_id} wurde nicht gefunden.",
                }

            rosters_raw = get_rosters(league_id) or []
            users_raw = get_league_users(league_id) or []
            rosters = [
                self._as_mapping(row)
                for row in rosters_raw
                if isinstance(row, dict)
            ]
            users = [
                self._as_mapping(row)
                for row in users_raw
                if isinstance(row, dict)
            ]
            settings = self._as_mapping(league.get("settings"))
            scoring = self._numeric_settings(league.get("scoring_settings"))
            positions = [
                str(position)
                for position in (league.get("roster_positions") or [])
            ]
            league_size = self._as_int(
                league.get("total_rosters"), len(rosters)
            )
            if league_size <= 0:
                league_size = len(rosters)
            form = self._infer_form(stored_form, league, settings)

            selected_roster: dict[str, object] = {}
            owner_user_id = ""
            team_name = ""
            live_error = ""
            status = "open"

            if entry_type == "manager_spot":
                for roster in rosters:
                    if self._as_int(roster.get("roster_id")) == roster_id:
                        selected_roster = roster
                        break
                if not selected_roster:
                    live_error = f"Roster-Spot {roster_id} wurde in Liga {league_id} nicht gefunden."
                else:
                    owner_user_id = str(
                        selected_roster.get("owner_id") or ""
                    ).strip()
                    owner: dict[str, object] = {}
                    for user in users:
                        if (
                            str(user.get("user_id") or "").strip()
                            == owner_user_id
                        ):
                            owner = user
                            break
                    if owner_user_id:
                        team_name = (
                            self._user_team_name(owner, selected_roster)
                            or f"User {owner_user_id}"
                        )
                        status = "filled"
            else:
                claimed_ids: set[str] = set()
                for roster in rosters:
                    owner_id = str(roster.get("owner_id") or "").strip()
                    if owner_id:
                        claimed_ids.add(owner_id)
                for user in users:
                    user_id = str(user.get("user_id") or "").strip()
                    if user_id:
                        claimed_ids.add(user_id)
                if league_size > 0 and len(claimed_ids) >= league_size:
                    status = "filled"

            return {
                "valid": True,
                "persist_safe": not live_error,
                "league_name": str(league.get("name") or f"Liga {league_id}"),
                "league_size": league_size,
                "league_form": form,
                "roster_positions": positions,
                "roster_structure": (
                    " · ".join(positions)
                    if positions
                    else "Keine Roster-Struktur verfügbar"
                ),
                "scoring_settings": scoring,
                "scoring_summary": self._scoring_summary(scoring),
                "team_name": team_name,
                "owner_user_id": owner_user_id,
                "status": status,
                "raw_league": league,
                "raw_roster": selected_roster,
                "error": live_error,
            }
        except Exception as exc:
            logging.exception(
                f"Sleeper enrichment failed for league {league_id}: {exc}"
            )
            return {
                "valid": False,
                "persist_safe": False,
                "error": f"Live-Daten für Liga {league_id} konnten nicht geladen werden.",
            }

    def _apply_live_entry(
        self, entry: FantasyBoerseEntry, live: dict[str, object]
    ) -> FantasyBoerseEntry:
        updated: FantasyBoerseEntry = dict(entry)
        if bool(live.get("valid")):
            updated["league_name"] = str(
                live.get("league_name") or entry["league_name"]
            )
            updated["league_size"] = self._as_int(
                live.get("league_size"), entry["league_size"]
            )
            updated["league_form"] = str(
                live.get("league_form") or entry["league_form"]
            )
            updated["roster_positions"] = [
                str(item) for item in (live.get("roster_positions") or [])
            ]
            updated["roster_structure"] = str(
                live.get("roster_structure") or ""
            )
            updated["scoring_settings"] = self._numeric_settings(
                live.get("scoring_settings")
            )
            updated["scoring_summary"] = str(
                live.get("scoring_summary") or "Scoringdaten nicht verfügbar"
            )
            updated["team_name"] = str(live.get("team_name") or "")
            updated["owner_user_id"] = str(live.get("owner_user_id") or "")
            updated["status"] = str(live.get("status") or "open")
            updated["raw_league"] = self._json_string(live.get("raw_league"))
            updated["raw_roster"] = self._json_string(live.get("raw_roster"))
        updated["live_error"] = str(live.get("error") or "")
        return updated

    def _persist_live_entry(
        self, client, entry_id: str, live: dict[str, object]
    ) -> None:
        if not entry_id or not bool(live.get("persist_safe")):
            return
        payload = {
            "league_name": str(live.get("league_name") or ""),
            "league_size": self._as_int(live.get("league_size")),
            "league_form": str(live.get("league_form") or ""),
            "roster_positions": live.get("roster_positions") or [],
            "scoring_settings": live.get("scoring_settings") or {},
            "team_name": str(live.get("team_name") or ""),
            "owner_user_id": str(live.get("owner_user_id") or ""),
            "status": str(live.get("status") or "open"),
            "raw_league": live.get("raw_league") or {},
            "raw_roster": live.get("raw_roster") or {},
        }
        try:
            client.table("fantasy_boerse_entries").update(payload).eq(
                "id", entry_id
            ).execute()
        except Exception as exc:
            logging.exception(
                f"Fantasybörse live write-back failed for {entry_id}: {exc}"
            )

    @rx.event
    def submit_entry(self, form_data: dict[str, str]):
        self.is_submitting = True
        self.form_message = ""
        self.form_message_type = ""
        yield
        try:
            entry_type = str(form_data.get("entry_type", "")).strip()
            league_id = str(form_data.get("league_id", "")).strip()
            roster_raw = str(form_data.get("roster_id", "")).strip()
            buyin_raw = str(form_data.get("buyin", "")).strip()
            invite_link = str(form_data.get("invite_link", "")).strip()
            contact_sleeper = str(form_data.get("contact_sleeper", "")).strip()
            contact_discord = str(form_data.get("contact_discord", "")).strip()
            description = str(form_data.get("description", "")).strip()

            if entry_type not in {"manager_spot", "whole_league"}:
                self.form_message = "Bitte wähle eine gültige Angebotsart aus."
                self.form_message_type = "error"
                return
            if not league_id:
                self.form_message = "Bitte gib eine Sleeper League-ID ein."
                self.form_message_type = "error"
                return
            if not league_id.isdigit():
                self.form_message = "Die League-ID muss numerisch sein."
                self.form_message_type = "error"
                return
            if entry_type == "manager_spot":
                if not roster_raw or not roster_raw.isdigit():
                    self.form_message = "Für einen Managerposten ist ein numerischer Roster-Spot erforderlich."
                    self.form_message_type = "error"
                    return
                roster_id = int(roster_raw)
                if roster_id <= 0:
                    self.form_message = (
                        "Der Roster-Spot muss größer als 0 sein."
                    )
                    self.form_message_type = "error"
                    return
            else:
                roster_id = None

            if not buyin_raw:
                buyin = 0.0
            else:
                try:
                    buyin_decimal = Decimal(buyin_raw)
                except (InvalidOperation, ValueError):
                    logging.exception("Invalid buy-in value")
                    self.form_message = "Der Buy-in muss eine Zahl ab 0 sein."
                    self.form_message_type = "error"
                    return
                if not buyin_decimal.is_finite() or buyin_decimal < 0:
                    self.form_message = "Der Buy-in muss 0 oder größer sein."
                    self.form_message_type = "error"
                    return
                buyin = float(buyin_decimal)

            if not contact_sleeper:
                self.form_message = "Bitte gib deinen Sleeper-Namen an."
                self.form_message_type = "error"
                return
            if not contact_discord:
                self.form_message = "Bitte gib deinen Discord-Namen an."
                self.form_message_type = "error"
                return
            if len(description) < 20:
                self.form_message = (
                    "Bitte beschreibe das Angebot mit mindestens 20 Zeichen."
                )
                self.form_message_type = "error"
                return
            if len(description) > 500:
                self.form_message = (
                    "Die Beschreibung darf höchstens 500 Zeichen lang sein."
                )
                self.form_message_type = "error"
                return

            client = get_supabase_client()
            if client is None:
                self.form_message = "Die Datenbank ist derzeit nicht verfügbar."
                self.form_message_type = "error"
                return

            live = self._fetch_live_entry(
                entry_type, league_id, roster_id or 0, ""
            )
            if not bool(live.get("valid")) or (
                entry_type == "manager_spot" and str(live.get("error") or "")
            ):
                self.form_message = str(
                    live.get("error")
                    or "Die Sleeper-Liga konnte nicht geprüft werden."
                )
                self.form_message_type = "error"
                return

            payload: dict[
                str, str | int | float | list[str] | dict[str, object] | None
            ] = {
                "entry_type": entry_type,
                "league_id": league_id,
                "roster_id": roster_id,
                "buyin": buyin,
                "invite_link": invite_link or None,
                "contact_sleeper": contact_sleeper,
                "contact_discord": contact_discord,
                "description": description,
                "status": str(live.get("status") or "open"),
                "league_name": str(live.get("league_name") or ""),
                "league_size": self._as_int(live.get("league_size")),
                "league_form": str(live.get("league_form") or "unknown"),
                "roster_positions": live.get("roster_positions") or [],
                "scoring_settings": live.get("scoring_settings") or {},
                "team_name": str(live.get("team_name") or ""),
                "owner_user_id": str(live.get("owner_user_id") or ""),
                "raw_league": live.get("raw_league") or {},
                "raw_roster": live.get("raw_roster") or {},
            }
            client.table("fantasy_boerse_entries").insert(payload).execute()
            self.form_message = "Dein Angebot wurde erfolgreich veröffentlicht."
            self.form_message_type = "success"
            self._reset_entry_form()
            yield FantasyBoerseState.load_entries
        except Exception as exc:
            logging.exception(f"Error submitting Fantasybörse entry: {exc}")
            self.form_message = "Der Eintrag konnte nicht gespeichert werden. Bitte versuche es erneut."
            self.form_message_type = "error"
        finally:
            self.is_submitting = False

    def _normalize_entry(self, row: dict[str, object]) -> FantasyBoerseEntry:
        raw_buyin = row.get("buyin", 0)
        try:
            buyin = float(raw_buyin or 0)
        except (TypeError, ValueError):
            logging.exception(f"Invalid buyin value: {raw_buyin}")
            buyin = 0.0

        raw_roster_id = row.get("roster_id", 0)
        try:
            roster_id = int(raw_roster_id or 0)
        except (TypeError, ValueError):
            logging.exception(f"Invalid roster_id value: {raw_roster_id}")
            roster_id = 0

        raw_size = row.get("league_size", 0)
        try:
            league_size = int(raw_size or 0)
        except (TypeError, ValueError):
            logging.exception(f"Invalid league_size value: {raw_size}")
            league_size = 0

        scoring_settings = self._numeric_settings(row.get("scoring_settings"))
        raw_positions = row.get("roster_positions") or []
        roster_positions = [str(item) for item in raw_positions]
        roster_structure = (
            " · ".join(roster_positions)
            if roster_positions
            else "Keine Roster-Struktur verfügbar"
        )
        return {
            "id": str(row.get("id") or ""),
            "created_at": str(row.get("created_at") or ""),
            "entry_type": str(row.get("entry_type") or "manager_spot"),
            "league_id": str(row.get("league_id") or ""),
            "roster_id": roster_id,
            "buyin": buyin,
            "invite_link": str(row.get("invite_link") or ""),
            "contact_sleeper": str(row.get("contact_sleeper") or ""),
            "contact_discord": str(row.get("contact_discord") or ""),
            "description": str(row.get("description") or ""),
            "status": str(row.get("status") or "open"),
            "league_name": str(row.get("league_name") or "Unbenannte Liga"),
            "league_size": league_size,
            "league_form": str(row.get("league_form") or ""),
            "roster_positions": roster_positions,
            "roster_structure": roster_structure,
            "scoring_settings": scoring_settings,
            "scoring_summary": self._scoring_summary(scoring_settings),
            "team_name": str(row.get("team_name") or ""),
            "owner_user_id": str(row.get("owner_user_id") or ""),
            "raw_league": self._json_string(row.get("raw_league")),
            "raw_roster": self._json_string(row.get("raw_roster")),
            "live_error": str(row.get("live_error") or ""),
        }

    @rx.event
    def set_form_filter(self, value: str):
        self.form_filter = value

    @rx.event
    def set_size_filter(self, value: str):
        self.size_filter = value

    @rx.event
    def set_buyin_filter(self, value: str):
        self.buyin_filter = value

    @rx.event
    def set_status_filter(self, value: str):
        self.status_filter = value

    @rx.event
    def clear_filters(self):
        self.form_filter = "all"
        self.size_filter = "all"
        self.buyin_filter = "all"
        self.status_filter = "all"

    @rx.var
    def league_size_options(self) -> list[str]:
        sizes: set[int] = set()
        for entry in self.entries:
            if entry["league_size"] > 0:
                sizes.add(entry["league_size"])
        return [str(size) for size in sorted(sizes)]

    def _matches_filters(self, entry: FantasyBoerseEntry) -> bool:
        if self.form_filter != "all":
            form_matches = (
                entry["entry_type"] == self.form_filter
                or entry["league_form"].strip().lower() == self.form_filter
            )
            if not form_matches:
                return False
        if (
            self.size_filter != "all"
            and str(entry["league_size"]) != self.size_filter
        ):
            return False
        if self.buyin_filter == "free" and entry["buyin"] > 0:
            return False
        if self.buyin_filter == "up_to_25" and not 0 < entry["buyin"] <= 25:
            return False
        if self.buyin_filter == "25_to_50" and not 25 < entry["buyin"] <= 50:
            return False
        if self.buyin_filter == "over_50" and entry["buyin"] <= 50:
            return False
        if (
            self.status_filter != "all"
            and entry["status"] != self.status_filter
        ):
            return False
        return True

    @rx.var
    def filtered_entries(self) -> list[FantasyBoerseEntry]:
        return [entry for entry in self.entries if self._matches_filters(entry)]

    @rx.var
    def has_active_filters(self) -> bool:
        return any(
            filter_value != "all"
            for filter_value in (
                self.form_filter,
                self.size_filter,
                self.buyin_filter,
                self.status_filter,
            )
        )

    @rx.var
    def active_filter_count(self) -> int:
        return sum(
            filter_value != "all"
            for filter_value in (
                self.form_filter,
                self.size_filter,
                self.buyin_filter,
                self.status_filter,
            )
        )

    @rx.var
    def total_count(self) -> int:
        return len(self.entries)

    @rx.var
    def open_count(self) -> int:
        return sum(entry["status"] == "open" for entry in self.entries)

    @rx.var
    def manager_spot_count(self) -> int:
        return sum(
            entry["entry_type"] == "manager_spot" for entry in self.entries
        )

    @rx.var
    def whole_league_count(self) -> int:
        return sum(
            entry["entry_type"] == "whole_league" for entry in self.entries
        )

    @rx.var
    def display_state(self) -> str:
        if self.is_loading:
            return "loading"
        if self.error_message:
            return "error"
        if not self.filtered_entries:
            return "empty"
        return "ready"


def _safe_infer_form(
    stored_form: object,
    league: dict[str, object],
    settings: dict[str, object],
) -> str:
    stored = str(stored_form or "").strip().lower().replace(" ", "_")
    if "idp" in stored:
        return "idp"
    if "bestball" in stored or "best_ball" in stored:
        return "bestball"
    if stored in {"dynasty", "redraft"}:
        return stored

    parts = [
        str(league.get(key) or "")
        for key in ("name", "type", "status", "draft_type")
    ]
    parts.append(settings or {})
    searchable = " ".join(parts).lower()
    if "idp" in searchable:
        return "idp"
    if "bestball" in searchable or "best_ball" in searchable:
        return "bestball"
    if "redraft" in searchable:
        return "redraft"
    if "dynasty" in searchable:
        return "dynasty"
    return "unknown"


def _safe_user_team_name(
    user: dict[str, object], roster: dict[str, object]
) -> str:
    metadata = user.get("metadata") or {}
    roster_metadata = roster.get("metadata") or {}
    team_name = str(
        metadata.get("team_name") or roster_metadata.get("team_name") or ""
    ).strip()
    display_name = str(user.get("display_name") or "").strip()
    if team_name and display_name and team_name.lower() != display_name.lower():
        return f"{team_name} · {display_name}"
    return team_name or display_name


FantasyBoerseState._infer_form = staticmethod(_safe_infer_form)
FantasyBoerseState._user_team_name = staticmethod(_safe_user_team_name)


def _safe_infer_form_v2(
    stored_form: object,
    league: dict[str, object],
    settings: dict[str, object],
) -> str:
    stored = str(stored_form or "").strip().lower().replace(" ", "_")
    if "idp" in stored:
        return "idp"
    if "bestball" in stored or "best_ball" in stored:
        return "bestball"
    if stored in {"dynasty", "redraft"}:
        return stored

    parts = [
        str(league.get(key) or "")
        for key in ("name", "type", "status", "draft_type")
    ]
    parts.append(settings or "")
    searchable = " ".join(parts).lower()
    if "idp" in searchable:
        return "idp"
    if "bestball" in searchable or "best_ball" in searchable:
        return "bestball"
    if "redraft" in searchable:
        return "redraft"
    if "dynasty" in searchable:
        return "dynasty"
    return "unknown"


FantasyBoerseState._infer_form = staticmethod(_safe_infer_form_v2)


def _safe_infer_form_v3(stored_form, league, settings):
    stored = str(stored_form or "").strip().lower().replace(" ", "_")
    if "idp" in stored:
        return "idp"
    if "bestball" in stored or "best_ball" in stored:
        return "bestball"
    if stored in {"dynasty", "redraft"}:
        return stored

    parts = [
        str(league.get(key) or "")
        for key in ("name", "type", "status", "draft_type")
    ]
    parts.append(settings or {})
    searchable = " ".join(str(part) for part in parts).lower()
    if "idp" in searchable:
        return "idp"
    if "bestball" in searchable or "best_ball" in searchable:
        return "bestball"
    if "redraft" in searchable:
        return "redraft"
    if "dynasty" in searchable:
        return "dynasty"
    return "unknown"


FantasyBoerseState._infer_form = staticmethod(_safe_infer_form_v3)
