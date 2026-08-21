import reflex as rx
import requests
import logging
import json
import re
import secrets
import string
from datetime import datetime, timezone
from app.supabase_client import get_supabase_client


PRIMARY_TABLE = "redraft_registration_2026"
FALLBACK_TABLE = "user_registration"

# Die Ligen sind bereits erstellt: 85 Ligen mit je 12 Spielern = 1.020 Plätze.
FIXED_LEAGUE_COUNT = 85
PLAYERS_IN_LEAGUES = 1020

# Optional columns that may or may not exist on the target table.
# We attempt to write them, and silently drop them from the payload
# on PGRST204 errors ("Could not find the 'X' column"). The
# `Doppelanmeldung` column is intentionally spelled with a capital D
# to match the actual Supabase schema.
_OPTIONAL_COLUMNS = ("commish", "Doppelanmeldung")


def _gen_code(n: int = 10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


def _normalize_name(s: str) -> str:
    return str(s or "").strip().lower()


def _make_index(sleeper: str, user_id: str) -> str:
    """Build a stable, privacy-friendly index value for the row.

    Mirrors the existing `user_registration.index` convention
    (lowercased sleeper name, alnum + a few safe chars). Falls back
    to the user_id (or a random token) when the sleeper name is empty
    or would collapse to an empty slug.
    """
    base = _normalize_name(sleeper)
    slug = re.sub(r"[^a-z0-9_.-]+", "", base)
    if slug:
        return slug[:64]
    uid = str(user_id or "").strip()
    if uid:
        return f"uid_{uid}"[:64]
    return f"anon_{secrets.token_hex(6)}"


class RedraftRegistrationState(rx.State):
    sleeper_input: str = ""
    discord_input: str = ""
    email_input: str = ""
    teammate1_input: str = ""
    teammate2_input: str = ""
    teammate3_input: str = ""
    edit_code_input: str = ""
    commish_input: bool = False

    resolved_user_id: str = ""
    resolved_display_name: str = ""
    resolved_avatar: str = ""
    is_resolving: bool = False
    username_valid: bool = False
    username_error: str = ""

    is_submitting: bool = False
    submit_success: bool = False
    generated_code: str = ""
    status_message: str = ""
    status_type: str = ""

    table_missing: bool = False
    using_fallback: bool = False

    entries: list[dict[str, str | list[str]]] = []
    is_loading: bool = False

    existing_entry: dict[str, str] = {}

    @rx.event
    def set_sleeper_input(self, v: str):
        self.sleeper_input = v

    @rx.event
    def set_discord_input(self, v: str):
        self.discord_input = v

    @rx.event
    def set_email_input(self, v: str):
        self.email_input = v

    @rx.event
    def set_teammate1_input(self, v: str):
        self.teammate1_input = v

    @rx.event
    def set_teammate2_input(self, v: str):
        self.teammate2_input = v

    @rx.event
    def set_teammate3_input(self, v: str):
        self.teammate3_input = v

    @rx.event
    def set_edit_code_input(self, v: str):
        self.edit_code_input = v

    @rx.event
    def set_commish_input(self, v: bool):
        self.commish_input = bool(v)

    @rx.event
    def set_commish_yes(self):
        self.commish_input = True

    @rx.event
    def set_commish_no(self):
        self.commish_input = False

    def _set_status(self, msg: str, kind: str = "info"):
        self.status_message = msg
        self.status_type = kind

    def _clear_status(self):
        self.status_message = ""
        self.status_type = ""

    @rx.event
    def clear_status(self):
        self._clear_status()

    def _fetch_from_table(self, client, table: str) -> list[dict]:
        """Load all rows from Supabase in batches.

        Supabase/PostgREST commonly limits a single response to 1000 rows.
        We therefore page through the result set explicitly.
        """
        batch_size = 1000
        rows: list[dict] = []
        offset = 0

        while True:
            res = (
                client.table(table)
                .select(
                    "user_id,sleeper,discord,email,mitspieler,key,created_at,commish"
                )
                .order("created_at", desc=False, nullsfirst=False)
                .range(offset, offset + batch_size - 1)
                .execute()
            )

            batch = res.data if res and res.data else []
            rows.extend(batch)

            if len(batch) < batch_size:
                break

            offset += batch_size

        logging.info(
            "Loaded %d rows from %s in batches of %d",
            len(rows),
            table,
            batch_size,
        )
        return rows

    def _parse_mates(self, raw) -> list[str]:
        """Normalize the ``mitspieler`` column into a list of names.

        Supports rows stored as a Python list, a JSON-encoded string, or
        a comma-separated string. Returns an empty list on any failure.
        """
        if raw is None:
            return []
        if isinstance(raw, list):
            return [str(m).strip() for m in raw if str(m).strip()]
        if isinstance(raw, str):
            s = raw.strip()
            if not s:
                return []
            if s.startswith("[") and s.endswith("]"):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [
                            str(m).strip() for m in parsed if str(m).strip()
                        ]
                except Exception:
                    logging.exception("mitspieler JSON parse failed")
            return [m.strip() for m in s.split(",") if m.strip()]
        return []

    @rx.event
    def load_entries(self):
        self.is_loading = True
        yield
        try:
            client = get_supabase_client()
            if not client:
                self._set_status("Datenbank nicht verfügbar.", "error")
                self.is_loading = False
                return
            rows: list[dict] = []
            self.table_missing = False
            self.using_fallback = False
            try:
                rows = self._fetch_from_table(client, PRIMARY_TABLE)
            except Exception as e:
                # Primary table not available — silently try fallback.
                # Avoid noisy stack traces; this is an expected path.
                logging.debug(f"Primary table read failed: {e}")
                self.table_missing = True
                try:
                    rows = self._fetch_from_table(client, FALLBACK_TABLE)
                    self.using_fallback = True
                except Exception as e2:
                    logging.exception("Unexpected error")
                    logging.debug(f"Fallback table read failed: {e2}")
                    rows = []

            # Stable client-side sort by created_at ascending (early -> late),
            # with a safe fallback for rows without created_at.
            def _sort_key(r: dict) -> str:
                v = r.get("created_at")
                if v:
                    return str(v)
                # Fallback: sort missing timestamps last but stably.
                return "9999-12-31T23:59:59"

            rows = sorted(rows, key=_sort_key)

            # Build normalized-name -> sleeper name map for reciprocity check
            name_map: dict[str, str] = {}
            for r in rows:
                s = str(r.get("sleeper") or "").strip()
                if s:
                    name_map[_normalize_name(s)] = s

            # Build reverse index: who mentions each normalized name?
            mentioned_by: dict[str, list[str]] = {}
            for r in rows:
                mates_list = self._parse_mates(r.get("mitspieler"))
                who = str(r.get("sleeper") or "").strip()
                if not who:
                    continue
                for m in mates_list:
                    key = _normalize_name(m)
                    if key:
                        mentioned_by.setdefault(key, []).append(who)

            entries = []
            for r in rows:
                sleeper = str(r.get("sleeper") or "").strip()
                if not sleeper:
                    continue
                mates_list = self._parse_mates(r.get("mitspieler"))

                mates_display: list[str] = []
                mutual_count = 0
                for m in mates_list:
                    m_norm = _normalize_name(m)
                    reciprocal = False
                    # Reciprocal if the mentioned person also mentions this sleeper
                    others_mentioning = mentioned_by.get(
                        _normalize_name(sleeper), []
                    )
                    if any(
                        _normalize_name(o) == m_norm for o in others_mentioning
                    ):
                        reciprocal = True
                        mutual_count += 1
                    marker = " ✓" if reciprocal else ""
                    mates_display.append(f"{m}{marker}")

                created = str(r.get("created_at") or "")
                display = ""
                if created:
                    try:
                        dt = datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        )
                        display = dt.strftime("%d.%m.%Y %H:%M")
                    except Exception:
                        logging.exception("bad created_at")
                        display = created[:10]

                entries.append(
                    {
                        "sleeper": sleeper,
                        "discord": str(r.get("discord") or ""),
                        "mates_display": ", ".join(mates_display)
                        if mates_display
                        else "—",
                        "mutual_count": str(mutual_count),
                        "created_display": display,
                        "commish": bool(r.get("commish") or False),
                    }
                )
            self.entries = entries
        except Exception as e:
            logging.exception(f"load_entries failed: {e}")
            self._set_status(f"Fehler beim Laden: {e}", "error")
        finally:
            self.is_loading = False

    @rx.event
    def init_page(self):
        yield RedraftRegistrationState.load_entries

    @rx.event
    def validate_sleeper(self):
        self.is_resolving = True
        self._clear_status()
        yield
        try:
            name = self.sleeper_input.strip()
            if not name:
                self.username_valid = False
                self.username_error = "Bitte gib einen Sleeper-Namen ein."
                return
            try:
                r = requests.get(
                    f"https://api.sleeper.app/v1/user/{name}", timeout=10
                )
            except Exception as e:
                logging.exception(f"Sleeper lookup failed: {e}")
                self.username_valid = False
                self.username_error = "Sleeper-API nicht erreichbar."
                return
            if r.status_code != 200 or not r.json():
                self.username_valid = False
                self.username_error = f"Sleeper-User „{name}“ nicht gefunden."
                self.resolved_user_id = ""
                self.resolved_display_name = ""
                self.resolved_avatar = ""
                return
            data = r.json()
            self.resolved_user_id = str(data.get("user_id") or "")
            self.resolved_display_name = str(data.get("display_name") or name)
            self.resolved_avatar = str(data.get("avatar") or "")
            self.username_valid = True
            self.username_error = ""

            # Look up existing registration by user_id (canonical key).
            # Including the 'key' (edit code) for internal validation.
            client = get_supabase_client()
            self.existing_entry = {}
            if client and self.resolved_user_id:
                try:
                    res = (
                        client.table(PRIMARY_TABLE)
                        .select("user_id,sleeper,discord,email,key,commish")
                        .eq("user_id", self.resolved_user_id)
                        .limit(1)
                        .execute()
                    )
                    if res and res.data:
                        row = res.data[0]
                        self.existing_entry = {
                            "user_id": str(row.get("user_id") or ""),
                            "sleeper": str(row.get("sleeper") or ""),
                            "discord": str(row.get("discord") or ""),
                            "email": str(row.get("email") or ""),
                            "key": str(row.get("key") or ""),
                        }
                        # Preload commish state from existing entry
                        self.commish_input = bool(row.get("commish") or False)
                except Exception as e:
                    logging.exception(f"Existing entry lookup failed: {e}")
                    self.existing_entry = {}
        finally:
            self.is_resolving = False

    def _normalize_mates(self) -> list[str]:
        """Return all non-empty teammate inputs, trimmed.

        Preserves self-wishes and duplicates so the subsequent validation
        step can reject them with clear error messages instead of silently
        dropping them.
        """
        raw = [
            self.teammate1_input,
            self.teammate2_input,
            self.teammate3_input,
        ]
        result: list[str] = []
        for m in raw:
            n = str(m or "").strip()
            if not n:
                continue
            result.append(n)
        return result

    def _resolve_teammates(
        self, mates: list[str]
    ) -> tuple[list[str], list[str], str]:
        """Validate teammate names against the Sleeper user endpoint.

        Returns a tuple of (display_names, user_ids, error_message). If any
        teammate cannot be resolved via Sleeper, the error message is
        populated and the caller should abort the save.

        - Names are normalized case-insensitively.
        - Self-wishes are rejected (compared to the current user's
          resolved user_id AND normalized display name / input).
        - Duplicates (by user_id or normalized name) are rejected.
        """
        display_names: list[str] = []
        user_ids: list[str] = []
        seen_ids: set[str] = set()
        seen_norm: set[str] = set()
        my_id = str(self.resolved_user_id or "").strip()
        my_norm = _normalize_name(
            self.resolved_display_name or self.sleeper_input
        )
        # First pass: detect self-wishes and duplicates locally BEFORE any
        # external Sleeper API lookups. This ensures fast, clear errors and
        # avoids unnecessary network calls.
        pre_seen: set[str] = set()
        my_input_norm = _normalize_name(self.sleeper_input)
        for m in mates:
            name = str(m or "").strip()
            if not name:
                continue
            norm = _normalize_name(name)
            if norm and (norm == my_norm or norm == my_input_norm):
                return (
                    [],
                    [],
                    f"„{name}“ ist dein eigener Sleeper-Name. "
                    "Bitte gib einen anderen Mitspieler an.",
                )
            if norm in pre_seen:
                return (
                    [],
                    [],
                    f"„{name}“ wurde mehrfach eingegeben. "
                    "Bitte gib jeden Mitspieler nur einmal an.",
                )
            pre_seen.add(norm)

        for m in mates:
            name = str(m or "").strip()
            if not name:
                continue
            norm = _normalize_name(name)
            if norm == my_norm:
                return (
                    [],
                    [],
                    f"„{name}“ ist dein eigener Sleeper-Name. "
                    "Bitte gib einen anderen Mitspieler an.",
                )
            if norm in seen_norm:
                return (
                    [],
                    [],
                    f"„{name}“ wurde mehrfach eingegeben. "
                    "Bitte gib jeden Mitspieler nur einmal an.",
                )
            try:
                r = requests.get(
                    f"https://api.sleeper.app/v1/user/{name}", timeout=10
                )
            except Exception as e:
                logging.exception(f"Sleeper teammate lookup failed: {e}")
                return (
                    [],
                    [],
                    "Sleeper-API nicht erreichbar. Bitte versuche es später erneut.",
                )
            if r.status_code != 200 or not r.json():
                return (
                    [],
                    [],
                    f"Mitspieler „{name}“ konnte auf Sleeper nicht gefunden werden.",
                )
            data = r.json() or {}
            uid = str(data.get("user_id") or "").strip()
            disp = str(data.get("display_name") or name).strip() or name
            if not uid:
                return (
                    [],
                    [],
                    f"Mitspieler „{name}“ liefert keine gültige Sleeper-User-ID.",
                )
            if uid == my_id:
                return (
                    [],
                    [],
                    f"„{name}“ ist dein eigener Sleeper-Account. "
                    "Bitte gib einen anderen Mitspieler an.",
                )
            if uid in seen_ids:
                return (
                    [],
                    [],
                    f"Mitspieler „{disp}“ wurde mehrfach eingegeben. "
                    "Bitte gib jeden Mitspieler nur einmal an.",
                )
            seen_ids.add(uid)
            seen_norm.add(_normalize_name(disp))
            seen_norm.add(norm)
            display_names.append(disp)
            user_ids.append(uid)
        return display_names, user_ids, ""

    @rx.event
    def submit_registration(self):
        self._clear_status()
        if not self.username_valid or not self.resolved_user_id:
            self._set_status(
                "Bitte prüfe zuerst deinen Sleeper-Namen.", "error"
            )
            return
        discord = self.discord_input.strip()
        if not discord:
            self._set_status("Discord-Name ist ein Pflichtfeld.", "error")
            return
        email = self.email_input.strip()
        if email and "@" not in email:
            self._set_status("Ungültige E-Mail-Adresse.", "error")
            return

        mates_raw = self._normalize_mates()
        new_code = _gen_code(10)
        self.is_submitting = True
        yield
        try:
            mates, mates_ids, mates_err = self._resolve_teammates(mates_raw)
            if mates_err:
                self._set_status(mates_err, "error")
                return
            client = get_supabase_client()
            if not client:
                self._set_status("Datenbank nicht verfügbar.", "error")
                return

            # 1) Check for existing entry using both the database and the internal state.
            # We prefer the state-resident 'existing_entry' populated during validate_sleeper.
            existing_found = bool(
                self.existing_entry
                and self.existing_entry.get("user_id") == self.resolved_user_id
            )
            existing_code = self.existing_entry.get("key", "")

            # Double check database if state looks empty but we are on an update flow
            if not existing_found and self.edit_code_input.strip():
                try:
                    res = (
                        client.table(PRIMARY_TABLE)
                        .select("user_id,key")
                        .eq("user_id", self.resolved_user_id)
                        .limit(1)
                        .execute()
                    )
                    if res and res.data:
                        existing_found = True
                        existing_code = str(res.data[0].get("key") or "")
                except Exception as e:
                    logging.exception(f"Redraft table validation failed: {e}")
                    self._set_status(
                        "Die Ziel-Tabelle „redraft_registration_2026“ existiert "
                        "noch nicht oder ist nicht lesbar.",
                        "error",
                    )
                    self.table_missing = True
                    return

            # 2) STRICT edit-code enforcement: block ALL writes when an
            #    existing entry is present unless the correct code is given.
            provided_code = self.edit_code_input.strip()
            final_code = new_code
            is_update = False
            if existing_found:
                if not provided_code:
                    self._set_status(
                        "Für diesen Sleeper-User existiert bereits eine "
                        "Anmeldung. Bitte gib deinen Änderungscode ein, "
                        "um sie zu aktualisieren. Ohne gültigen Code "
                        "kann keine Änderung gespeichert werden.",
                        "error",
                    )
                    return
                if not existing_code or provided_code != existing_code:
                    self._set_status(
                        "Der eingegebene Änderungscode ist ungültig. "
                        "Es wurde nichts gespeichert.",
                        "error",
                    )
                    return
                # Valid code — perform an update, preserve the code.
                final_code = existing_code
                is_update = True

            sleeper_name = (
                self.resolved_display_name or self.sleeper_input.strip()
            )
            index_val = _make_index(sleeper_name, self.resolved_user_id)
            base_payload = {
                "index": index_val,
                "user_id": self.resolved_user_id,
                "sleeper": sleeper_name,
                "discord": discord,
                "email": email,
                "mitspieler": mates,
                "mitspieler_user_ids": mates_ids,
                "key": final_code,
            }
            # Optional columns are attempted with safe defaults
            optional_defaults: dict[str, bool] = {
                "commish": bool(self.commish_input),
                "Doppelanmeldung": False,
            }
            payload = {**base_payload, **optional_defaults}

            # Persist the registration timestamp only on INSERT. On updates,
            # the original created_at must be preserved (never overwritten).
            if not is_update:
                payload["created_at"] = datetime.now(timezone.utc).isoformat()

            def _extract_missing_column(msg: str) -> str:
                m = re.search(r"Could not find the '([^']+)' column", msg)
                if m:
                    return m.group(1)
                m = re.search(r"column \"([^\"]+)\" of relation", msg)
                if m:
                    return m.group(1)
                return ""

            def _write(current_payload: dict) -> tuple[bool, str]:
                attempt = dict(current_payload)
                last_err = ""
                # Allow enough retries to strip any optional columns +
                # the optional created_at column if the schema lacks it.
                for _ in range(len(optional_defaults) + 3):
                    try:
                        if is_update:
                            update_payload = {
                                k: v
                                for k, v in attempt.items()
                                if k != "user_id" and k != "created_at"
                            }
                            client.table(PRIMARY_TABLE).update(
                                update_payload
                            ).eq("user_id", self.resolved_user_id).execute()
                        else:
                            client.table(PRIMARY_TABLE).insert(
                                attempt
                            ).execute()
                        return True, ""
                    except Exception as err:
                        logging.exception("Unexpected error")
                        logging.debug(f"Write attempt failed: {err}")
                        msg = str(err)
                        last_err = msg
                        col = _extract_missing_column(msg)
                        # Never drop these required columns
                        required = {
                            "index",
                            "user_id",
                            "sleeper",
                            "discord",
                            "email",
                            "mitspieler",
                            "mitspieler_user_ids",
                            "key",
                        }
                        if col and col in attempt and col not in required:
                            attempt.pop(col, None)
                            continue
                        return False, msg
                return False, last_err or "Too many schema retries."

            ok, err_msg = _write(payload)
            if not ok:
                if 'null value in column "index"' in err_msg:
                    self._set_status(
                        "Die Spalte „index“ konnte nicht befüllt werden.",
                        "error",
                    )
                else:
                    self._set_status(
                        "Fehler beim Speichern. Die Ziel-Tabelle existiert "
                        "eventuell nicht.",
                        "error",
                    )
                return

            # 3) Success — update local state and refresh overview
            self.generated_code = final_code
            self.submit_success = True
            # Update internal existing entry state with the latest values
            self.existing_entry = {
                "user_id": self.resolved_user_id,
                "sleeper": sleeper_name,
                "discord": discord,
                "email": email,
                "key": final_code,
            }
            action = "aktualisiert" if is_update else "gespeichert"
            self._set_status(f"Anmeldung erfolgreich {action}.", "success")
            yield RedraftRegistrationState.load_entries
        finally:
            self.is_submitting = False

    @rx.event
    def reset_form(self):
        self.sleeper_input = ""
        self.discord_input = ""
        self.email_input = ""
        self.teammate1_input = ""
        self.teammate2_input = ""
        self.teammate3_input = ""
        self.edit_code_input = ""
        self.commish_input = False
        self.resolved_user_id = ""
        self.resolved_display_name = ""
        self.resolved_avatar = ""
        self.username_valid = False
        self.username_error = ""
        self.submit_success = False
        self.generated_code = ""
        self.existing_entry = {}
        self._clear_status()

    @rx.var
    def total_entries(self) -> int:
        return len(self.entries)

    @rx.var
    def commish_count(self) -> int:
        return sum(1 for e in self.entries if e.get("commish"))

    @rx.var
    def full_leagues_count(self) -> int:
        return len(self.entries) // 12

    @rx.var
    def remaining_for_next_league(self) -> int:
        rem = 12 - (len(self.entries) % 12)
        return rem if rem != 12 else 0

    @rx.var
    def fixed_league_count(self) -> int:
        return FIXED_LEAGUE_COUNT

    @rx.var
    def players_in_leagues(self) -> int:
        return PLAYERS_IN_LEAGUES

    @rx.var
    def waitlist_count(self) -> int:
        return max(len(self.entries) - PLAYERS_IN_LEAGUES, 0)

    @rx.var
    def waitlist_entries(self) -> list[dict[str, str | list[str]]]:
        # load_entries sortiert nach Eingangszeit; die ersten 1.020 sind
        # den bereits erstellten Ligen zugeordnet.
        return self.entries[PLAYERS_IN_LEAGUES:]

    @rx.var
    def league_status_text(self) -> str:
        if self.waitlist_count > 0:
            return (
                f"{self.waitlist_count} Nachrücker auf der Warteliste. "
                "Neue Anmeldungen werden hinten angehängt."
            )
        return "Noch keine Nachrücker. Neue Anmeldungen werden auf die Warteliste gesetzt."
