"""Shared helpers for normalizing league type data across the app.

Background
----------
Historically, the Supabase ``leagues`` table exposed a single text column
``league_type`` with one of ``redraft``, ``dynasty``, ``bestball``. A newer
schema adds a ``league_types`` column that can be either a plain text
value like ``"dynasty"`` or a list such as ``["dynasty", "idp"]``. The
full set of supported forms is::

    redraft, dynasty, bestball, idp, idp_only

These helpers normalize either source into a canonical
``(primary_type, types_list)`` pair so downstream UI/filter code can rely
on a backwards-compatible single label AND the complete set of forms.

Callers reading the ``leagues`` table with explicit column lists should
add ``league_types`` via :func:`add_types_col` and, when the column does
not exist yet in the deployed schema, retry the same query without it
using :func:`is_missing_league_types_column_error` to detect the case.
"""

from __future__ import annotations

from collections.abc import Callable
import json
import logging

SUPPORTED_TYPES: tuple[str, ...] = (
    "redraft",
    "dynasty",
    "bestball",
    "idp",
    "idp_only",
)
_TYPE_SET = frozenset(SUPPORTED_TYPES)

# "Primary/backwards-compatible" values — the pre-existing single-string
# categorization used across the app. IDP flavors are treated as
# modifiers layered on top of a base format.
_BASE_FORMATS: tuple[str, ...] = ("redraft", "dynasty", "bestball")
_BASE_FORMAT_SET = frozenset(_BASE_FORMATS)


def _clean(v) -> str:
    """Lowercase/strip a raw value and return it only if it is a
    supported league type; otherwise return an empty string."""
    if v is None:
        return ""
    s = str(v).strip().lower()
    if not s or s == "null":
        return ""
    return s if s in _TYPE_SET else ""


def _scan_tokens(s: str) -> list[str]:
    """Last-resort scanner: extract every supported token that appears
    as a substring inside ``s``, matched longest-first so ``idp_only``
    wins over ``idp`` and their spans don't double-match. Returns tokens
    in the order they occur in the source string.
    """
    if not s:
        return []
    low = s.lower()
    consumed = [False] * len(low)
    ordered = sorted(SUPPORTED_TYPES, key=lambda t: -len(t))
    matches: list[tuple[int, str]] = []
    for tok in ordered:
        start = 0
        tlen = len(tok)
        while True:
            idx = low.find(tok, start)
            if idx < 0:
                break
            if not any(consumed[idx : idx + tlen]):
                matches.append((idx, tok))
                for i in range(idx, idx + tlen):
                    consumed[i] = True
            start = idx + tlen
    matches.sort(key=lambda x: x[0])
    out: list[str] = []
    for _, tok in matches:
        if tok not in out:
            out.append(tok)
    return out


def _extract_list(raw) -> list[str]:
    """Coerce a raw league-types value into a de-duplicated list of
    supported forms. Accepts:

    - ``None`` → ``[]``
    - ``list`` → each element cleaned
    - ``str`` — plain (``"dynasty"``), JSON (``'["dynasty","idp"]'``),
      comma-separated (``"dynasty, idp"``), or malformed text
      containing supported tokens (``'dynasty["dynasty","bestball"]'``).

    Values that don't contain any supported token (e.g. ``"empty"``,
    ``"unknown"``, raw legacy strings) collapse to ``[]`` so nothing
    unsupported can leak into UI filters or badges.
    """
    out: list[str] = []
    if raw is None:
        return out
    if isinstance(raw, list):
        for x in raw:
            c = _clean(x)
            if c and c not in out:
                out.append(c)
        # If the list contained no directly-supported values, but its
        # str-cast items still embed supported tokens (e.g. a list of
        # JSON-encoded strings), fall through to a substring scan of
        # the joined representation as a robustness net.
        if not out:
            joined = ",".join(str(x) for x in raw if x is not None)
            for tok in _scan_tokens(joined):
                if tok not in out:
                    out.append(tok)
        return out
    if isinstance(raw, str):
        s = raw.strip()
        if not s or s.lower() == "null":
            return out
        # Plain supported token.
        c = _clean(s)
        if c:
            out.append(c)
            return out
        # JSON list of tokens.
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    for x in parsed:
                        cc = _clean(x)
                        if cc and cc not in out:
                            out.append(cc)
                    if out:
                        return out
            except Exception:
                logging.exception("league_types JSON parse failed")
        # Comma-separated tokens.
        for part in s.split(","):
            cc = _clean(part)
            if cc and cc not in out:
                out.append(cc)
        if out:
            return out
        # Last resort: scan for supported tokens embedded in malformed
        # text like ``'dynasty["dynasty", "bestball"]'``.
        for tok in _scan_tokens(s):
            if tok not in out:
                out.append(tok)
    return out


def normalize_league_types(
    new_val=None, legacy_val=None
) -> tuple[str, list[str]]:
    """Normalize league type data from the two possible sources.

    Parameters
    ----------
    new_val
        The value from the new ``league_types`` column (list or text)
        when present, or ``None`` when the column is missing.
    legacy_val
        The value from the legacy ``league_type`` column. May be a
        clean scalar (``"dynasty"``), a JSON-list string, a
        comma-separated string, or even malformed text — all forms are
        routed through :func:`_extract_list` to yield only supported
        tokens.

    Returns
    -------
    ``(primary_type, types_list)``
        ``primary_type`` preserves current behavior: when the legacy
        source cleanly resolves to a base format (``redraft`` /
        ``dynasty`` / ``bestball``), it wins; otherwise the first base
        format from the merged list is used, falling back to the first
        entry of the list, then any legacy token, then ``""``.

        ``types_list`` is a de-duplicated, order-stable list containing
        every applicable supported form drawn from BOTH sources, with
        legacy tokens inserted at the front so the primary base format
        leads the list. Values that resolve to nothing supported (raw
        JSON echoes, ``"empty"``, ``"unknown"``, etc.) are dropped.
    """
    types = _extract_list(new_val)
    legacy_tokens = _extract_list(legacy_val)

    # Preserve back-compat: when the legacy source resolves to a base
    # format, that value wins as the primary.
    legacy_primary = ""
    for lt in legacy_tokens:
        if lt in _BASE_FORMAT_SET:
            legacy_primary = lt
            break

    # Merge legacy tokens to the front in original order so the primary
    # base format leads the list.
    for lt in reversed(legacy_tokens):
        if lt not in types:
            types.insert(0, lt)

    if legacy_primary:
        primary = legacy_primary
    else:
        primary = ""
        for t in types:
            if t in _BASE_FORMAT_SET:
                primary = t
                break
        if not primary and types:
            primary = types[0]
    return primary, types


def is_missing_league_types_column_error(exc: Exception) -> bool:
    """Return True if the given Supabase/Postgrest error indicates that
    the ``league_types`` column does not exist in the target table.

    Callers can use this to detect the "column not yet deployed" case
    and retry the same query without selecting/filtering the column.
    """
    msg = str(exc)
    if "league_types" not in msg:
        return False
    lower = msg.lower()
    return (
        "does not exist" in lower or "42703" in msg or "could not find" in lower
    )


def add_types_col(select_cols: str) -> str:
    """Return ``select_cols`` extended with ``league_types`` if absent.

    Handles both empty and non-empty select strings, and avoids
    duplicating the column when the caller already included it.
    """
    if not select_cols:
        return "league_types"
    parts = [p.strip() for p in select_cols.split(",") if p.strip()]
    if "league_types" in parts:
        return select_cols
    return select_cols + ",league_types"


def is_missing_optional_column_error(exc: Exception, column: str) -> bool:
    """Return whether a PostgREST error reports a missing optional column."""
    message = str(exc).lower()
    column_name = column.lower()
    return column_name in message and (
        "does not exist" in message
        or "42703" in message
        or "could not find" in message
    )


def fetch_optional_league_rows(
    query_builder: Callable[[str], object], base_cols: str
) -> list[dict]:
    """Fetch league rows while tolerating optional schema columns.

    The deployed database may omit either ``league_types`` or ``invite_link``.
    Keep retrying only for those schema errors and preserve every column that
    is available by trying both optional columns, then each reduced shape.
    """
    typed_cols = add_types_col(base_cols)
    attempts = (
        (f"{base_cols},invite_link", "base+invite"),
        (typed_cols, "typed"),
        (base_cols, "base"),
    )
    last_error: Exception | None = None
    for columns, attempt_name in attempts:
        try:
            response = query_builder(columns).execute()
            raw_rows = getattr(response, "data", [])
            if not isinstance(raw_rows, list):
                return []
            rows: list[dict] = []
            for row in raw_rows:
                if isinstance(row, dict):
                    rows.append(row)
            return rows
        except Exception as exc:
            last_error = exc
            types_missing = is_missing_optional_column_error(
                exc, "league_types"
            )
            invite_missing = is_missing_optional_column_error(
                exc, "invite_link"
            )
            if not (types_missing or invite_missing):
                logging.exception(
                    f"League select failed during {attempt_name} attempt: {exc}"
                )
                raise
            logging.exception(
                f"League select {attempt_name} missing optional column: {exc}"
            )
    if last_error is not None:
        raise last_error
    raise RuntimeError("No league select fallback attempt was configured.")


def has_type(types: list[str], form: str) -> bool:
    """Convenience predicate: True iff ``form`` appears in ``types``."""
    return _clean(form) in {t for t in types if t}
