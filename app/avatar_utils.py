"""Utilities for resolving Sleeper league avatar URLs."""

PLACEHOLDER_URL = "https://sleepercdn.com/images/v2/icons/league/nfl/purple.png"


def league_avatar_url(avatar: str | None) -> str:
    """Return a display URL for a league avatar value.

    - Full URL (http/https): returned as-is.
    - Sleeper avatar id (opaque token): resolved via the Sleeper CDN thumbs.
    - Empty/None/'null': falls back to the shared Sleeper league placeholder.
    """
    if avatar is None:
        return PLACEHOLDER_URL
    val = str(avatar).strip()
    if not val or val.lower() == "null":
        return PLACEHOLDER_URL
    if val.startswith("http://") or val.startswith("https://"):
        return val
    return f"https://sleepercdn.com/avatars/thumbs/{val}"


"""Utilities for resolving Sleeper league avatar URLs."""

import reflex as rx

PLACEHOLDER_URL = "https://sleepercdn.com/images/v2/icons/league/nfl/purple.png"


def league_avatar_url(avatar: str | None) -> str:
    """Return a display URL for a league avatar value (Python string).

    - Full URL (http/https): returned as-is.
    - Sleeper avatar id (opaque token): resolved via the Sleeper CDN thumbs.
    - Empty/None/'null': falls back to the shared Sleeper league placeholder.
    """
    if avatar is None:
        return PLACEHOLDER_URL
    val = str(avatar).strip()
    if not val or val.lower() == "null":
        return PLACEHOLDER_URL
    if val.startswith("http://") or val.startswith("https://"):
        return val
    return f"https://sleepercdn.com/avatars/thumbs/{val}"


def league_avatar_src(avatar) -> rx.Var:
    """Reflex Var expression resolving a league avatar to a URL.

    Accepts a state Var or a str-castable value. Uses the same fallback
    logic as `league_avatar_url` but compiles to JS on the frontend.
    """
    av = rx.cond(
        hasattr(avatar, "to"), avatar.to(str), (avatar | "").to_string()
    )
    return rx.cond(
        (av == "") | (av == "null"),
        PLACEHOLDER_URL,
        rx.cond(
            av.startswith("http"),
            av,
            "https://sleepercdn.com/avatars/thumbs/" + av,
        ),
    )


def league_avatar_image(avatar, size: str = "40px", **kwargs) -> rx.Component:
    """Render a rounded league avatar image with robust fallback."""
    return rx.image(
        src=league_avatar_src(avatar),
        width=size,
        height=size,
        border_radius="9999px",
        class_name="object-cover shrink-0",
        **kwargs,
    )
