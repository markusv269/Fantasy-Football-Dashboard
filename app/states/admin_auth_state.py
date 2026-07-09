import reflex as rx
import os
import hashlib
import hmac
import time
import logging

_SALT = b"stoned_lack_admin_v1_salt"
_ITERATIONS = 200_000
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 60


def _hash_password(password: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _SALT, _ITERATIONS
    )
    return dk.hex()


def _expected_hash() -> str:
    env_hash = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
    if env_hash:
        return env_hash.lower()
    env_plain = os.environ.get("ADMIN_PASSWORD", "").strip()
    if env_plain:
        return _hash_password(env_plain)
    # Fallback default for local app when no env var is set.
    return _hash_password("stonedlack2026")


class AdminAuthState(rx.State):
    is_authenticated: bool = False
    password_input: str = ""
    error_message: str = ""
    failed_attempts: int = 0
    locked_until: float = 0.0
    is_checking: bool = False

    @rx.var
    def is_locked(self) -> bool:
        return self.locked_until > time.time()

    @rx.var
    def lockout_remaining(self) -> int:
        remaining = int(self.locked_until - time.time())
        return remaining if remaining > 0 else 0

    @rx.event
    def set_password_input(self, val: str):
        self.password_input = val

    @rx.event
    def submit_login(self):
        self.is_checking = True
        yield
        try:
            if self.locked_until > time.time():
                self.error_message = "Zu viele Fehlversuche. Bitte warte kurz."
                return
            candidate = self.password_input
            if not candidate:
                self.error_message = "Bitte Passwort eingeben."
                return
            try:
                candidate_hash = _hash_password(candidate)
                expected = _expected_hash()
                is_valid = hmac.compare_digest(candidate_hash, expected)
            except Exception as e:
                logging.exception(f"Password hashing failed: {e}")
                is_valid = False
            if is_valid:
                self.is_authenticated = True
                self.error_message = ""
                self.failed_attempts = 0
                self.locked_until = 0.0
                self.password_input = ""
            else:
                self.failed_attempts += 1
                self.password_input = ""
                if self.failed_attempts >= _MAX_ATTEMPTS:
                    self.locked_until = time.time() + _LOCKOUT_SECONDS
                    self.error_message = f"Zu viele Fehlversuche. Gesperrt für {_LOCKOUT_SECONDS}s."
                    self.failed_attempts = 0
                else:
                    self.error_message = "Ungültige Anmeldedaten."
        finally:
            self.is_checking = False

    @rx.event
    def logout(self):
        self.is_authenticated = False
        self.password_input = ""
        self.error_message = ""
