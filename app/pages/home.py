import reflex as rx
from app.states.app_state import AppState
from app.states.user_state import UserState
from app.states.league_detail_state import LeagueDetailState
from app.theme import t
from app.components.layout import layout
from app.components.league_modal import league_detail_modal


def _status_color(status: rx.Var) -> rx.Var:
    return rx.match(
        status,
        ("dynasty", "purple"),
        ("redraft", "blue"),
        ("in_season", "green"),
        ("complete", "gray"),
        ("drafting", "blue"),
        ("pre_draft", "yellow"),
        "gray",
    )


def league_card(league: dict) -> rx.Component:
    avatar_url = rx.cond(
        (league["avatar"] != None)
        & (league["avatar"] != "")
        & (league["avatar"] != "null"),
        f"https://sleepercdn.com/avatars/thumbs/{league['avatar']}",
        "https://sleepercdn.com/images/v2/icons/league/nfl/purple.png",
    )
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.image(
                    src=avatar_url,
                    width="56px",
                    height="56px",
                    border_radius="9999px",
                    class_name="object-cover",
                ),
                rx.vstack(
                    rx.heading(
                        league["name"],
                        size="4",
                        weight="bold",
                        line_height="1.2",
                    ),
                    rx.text(
                        f"Season {league['season']}",
                        size="1",
                        color_scheme="gray",
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                    min_width="0",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.hstack(
                rx.badge(
                    league["status"],
                    color_scheme=_status_color(league["status"]),
                    variant="soft",
                    radius="full",
                ),
                rx.spacer(),
                rx.cond(
                    (league["total_rosters"].to(str) != "")
                    & (league["total_rosters"].to(str) != "0"),
                    rx.text(
                        f"{league['total_rosters']} Teams",
                        size="1",
                        weight="medium",
                        color_scheme="gray",
                    ),
                ),
                width="100%",
                align="center",
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        on_click=LeagueDetailState.open_league_modal(
            league["league_id"].to(str)
        ),
        size="2",
        class_name="cursor-pointer hover:border-[#DC2626] transition-all "
        + t(
            "bg-[#12141C] border-white/10 shadow-lg",
            "bg-white border-gray-200 shadow-sm",
        ),
    )


def _section(title: str, count: rx.Var, leagues: rx.Var) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.heading(title, size="6", weight="bold"),
            rx.badge(
                count.to_string(), color_scheme="red", variant="soft", size="2"
            ),
            spacing="3",
            align="center",
        ),
        rx.cond(
            leagues.length() > 0,
            rx.grid(
                rx.foreach(leagues, league_card),
                columns=rx.breakpoints(initial="1", sm="1", md="2", lg="3"),
                spacing="4",
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.icon("inbox", size=32, color="gray"),
                    rx.text(
                        "Keine Ligen in dieser Kategorie.",
                        size="2",
                        color_scheme="gray",
                    ),
                    spacing="2",
                    align="center",
                    padding="32px",
                    width="100%",
                ),
                class_name="border-dashed",
            ),
        ),
        spacing="4",
        width="100%",
        align="stretch",
    )


def _login_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Melde dich mit Sleeper an", size="4", weight="bold"),
            rx.text(
                "Gib deinen Sleeper-Namen ein, um deine Ligen zu sehen.",
                size="2",
                color_scheme="gray",
            ),
            rx.hstack(
                rx.input(
                    placeholder="Sleeper Username",
                    on_change=UserState.set_username_input,
                    size="3",
                    flex="1",
                ),
                rx.button(
                    "Los geht's",
                    on_click=UserState.save_username,
                    size="3",
                    style={"background_color": "#DC2626"},
                ),
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "Willkommen bei Stoned Lack Sleeper Ligen",
                    size="7",
                    weight="bold",
                ),
                rx.spacer(),
                rx.cond(
                    AppState.current_season != "",
                    rx.badge(
                        f"Saison {AppState.current_season}",
                        color_scheme="red",
                        variant="solid",
                        size="2",
                    ),
                ),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            rx.text(
                "Dein Zugang zu allen aktuellen Ligen der Stoned Lack Army. Verfolge Matchups, entdecke Trends und werde Teil der Community.",
                size="3",
                color_scheme="gray",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _archive_cta() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.icon("archive", size=24, color="#DC2626"),
            rx.vstack(
                rx.heading("Archiv", size="3", weight="bold"),
                rx.text(
                    "Ältere Ligen und vergangene Saisons ansehen.",
                    size="2",
                    color_scheme="gray",
                ),
                spacing="1",
                align="start",
                flex="1",
            ),
            rx.link(
                rx.button(
                    "Ältere Ligen ansehen",
                    rx.icon("arrow-right", size=16),
                    variant="soft",
                    color_scheme="gray",
                ),
                href="/archive",
                underline="none",
            ),
            spacing="4",
            align="center",
            width="100%",
        ),
        size="2",
        width="100%",
    )


def _trending_sidebar() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("Trending Adds", size="4", weight="bold"),
                rx.spacer(),
                rx.icon("flame", size=18, color="orange"),
                width="100%",
                align="center",
            ),
            rx.vstack(
                rx.foreach(
                    AppState.trending_adds,
                    lambda p: rx.hstack(
                        rx.vstack(
                            rx.text(
                                p["full_name"].to(str), size="2", weight="bold"
                            ),
                            rx.hstack(
                                rx.badge(
                                    p["position"].to(str),
                                    color_scheme=rx.match(
                                        p["position"].to(str),
                                        ("QB", "red"),
                                        ("RB", "blue"),
                                        ("WR", "green"),
                                        ("TE", "orange"),
                                        ("K", "gray"),
                                        ("DEF", "purple"),
                                        "gray",
                                    ),
                                    size="1",
                                    variant="soft",
                                ),
                                rx.text(
                                    p["team"].to(str),
                                    size="1",
                                    color_scheme="gray",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.spacer(),
                        rx.badge(
                            f"+{p['count']}",
                            color_scheme="blue",
                            variant="soft",
                        ),
                        width="100%",
                        align="center",
                        padding_y="8px",
                        class_name="border-b last:border-0 "
                        + t("border-gray-800", "border-gray-100"),
                    ),
                ),
                spacing="0",
                width="100%",
                align="stretch",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="2",
        width="100%",
    )


def home_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            rx.cond(~UserState.has_username, _login_card()),
            rx.grid(
                rx.vstack(
                    _section(
                        f"Dynasty Ligen {AppState.current_season}",
                        AppState.current_dynasty_leagues.length(),
                        AppState.current_dynasty_leagues,
                    ),
                    _section(
                        f"Redraft Ligen {AppState.current_season}",
                        AppState.current_redraft_leagues.length(),
                        AppState.current_redraft_leagues,
                    ),
                    _archive_cta(),
                    spacing="6",
                    width="100%",
                    align="stretch",
                ),
                _trending_sidebar(),
                columns=rx.breakpoints(initial="1", sm="1", md="1", lg="3"),
                spacing="6",
                width="100%",
                template_columns=rx.breakpoints(
                    initial="1fr", sm="1fr", md="1fr", lg="2fr 1fr"
                ),
            ),
            league_detail_modal(),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
