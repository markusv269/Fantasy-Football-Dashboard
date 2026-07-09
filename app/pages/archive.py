import reflex as rx
from app.states.app_state import AppState
from app.theme import t
from app.components.layout import layout
from app.pages.home import league_card


def _section(
    title: str, leagues: rx.Var, icon: str, color: str
) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(icon, size=20, color=color),
            rx.heading(title, size="5", weight="bold"),
            rx.badge(
                leagues.length().to_string(),
                color_scheme="gray",
                variant="soft",
                size="2",
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
                rx.text(
                    "Keine Ligen in dieser Kategorie.",
                    size="2",
                    color_scheme="gray",
                ),
                class_name="border-dashed",
            ),
        ),
        spacing="4",
        width="100%",
        align="stretch",
    )


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("archive", size=28, color="#DC2626"),
                rx.heading("Liga-Archiv", size="7", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"{AppState.archived_leagues.length()} Ligen",
                    color_scheme="red",
                    variant="solid",
                    size="2",
                ),
                spacing="3",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.text(
                "Ältere Ligen und vergangene Saisons der Stoned Lack Army.",
                size="3",
                color_scheme="gray",
            ),
            rx.link(
                rx.button(
                    rx.icon("arrow-left", size=16),
                    "Zur aktuellen Saison",
                    variant="soft",
                    color_scheme="red",
                    size="2",
                ),
                href="/",
                underline="none",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _empty_state() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon("inbox", size=40, color="gray"),
            rx.heading("Kein Archiv vorhanden", size="4", weight="bold"),
            rx.text(
                "Es gibt derzeit keine älteren Ligen im Archiv.",
                size="2",
                color_scheme="gray",
            ),
            rx.link(
                rx.button(
                    "Zurück zur Startseite",
                    style={"background_color": "#DC2626"},
                ),
                href="/",
                underline="none",
            ),
            spacing="3",
            align="center",
            padding="48px",
            width="100%",
        ),
        width="100%",
    )


def archive_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            rx.cond(
                AppState.archived_leagues.length() > 0,
                rx.vstack(
                    _section(
                        "Archivierte Dynasty Ligen",
                        AppState.archived_dynasty_leagues,
                        "crown",
                        "purple",
                    ),
                    _section(
                        "Archivierte Redraft Ligen",
                        AppState.archived_redraft_leagues,
                        "trophy",
                        "blue",
                    ),
                    rx.cond(
                        AppState.archived_other_leagues.length() > 0,
                        _section(
                            "Weitere archivierte Ligen",
                            AppState.archived_other_leagues,
                            "folder",
                            "gray",
                        ),
                    ),
                    spacing="8",
                    width="100%",
                    align="stretch",
                ),
                _empty_state(),
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
