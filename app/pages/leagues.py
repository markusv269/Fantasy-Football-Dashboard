import reflex as rx
from app.states.app_state import AppState
from app.states.user_state import UserState
from app.theme import (
    t,
    H1,
    H2,
    TEXT_SECONDARY,
    TEXT_PRIMARY,
    INPUT,
    BTN_PRIMARY,
    PAGE_BG,
)
from app.components.layout import layout
from app.pages.home import league_card


def leagues_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.cond(
                UserState.is_logged_in,
                rx.el.div(
                    rx.el.h1("Meine Ligen", class_name=H1 + " mb-6"),
                    rx.el.div(
                        rx.foreach(
                            AppState.leagues_data,
                            lambda league: rx.cond(
                                UserState.user_league_ids.contains(
                                    league["league_id"].to(str)
                                ),
                                league_card(league),
                                rx.fragment(),
                            ),
                        ),
                        class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                    ),
                    class_name="mb-12",
                ),
            ),
            rx.el.div(
                rx.el.h1("Alle Ligen", class_name=H1 + " mb-2"),
                rx.cond(
                    ~UserState.has_username,
                    rx.el.p(
                        "Melde dich mit deinem Sleeper-Namen an, um deine Ligen zu sehen.",
                        class_name=TEXT_SECONDARY + " mb-6 font-medium",
                    ),
                    rx.el.p(
                        "Übersicht aller verfügbaren Ligen.",
                        class_name=TEXT_SECONDARY + " mb-6 font-medium",
                    ),
                ),
                rx.el.div(
                    rx.foreach(
                        AppState.leagues_data,
                        lambda league: rx.cond(
                            ~UserState.user_league_ids.contains(
                                league["league_id"].to(str)
                            ),
                            league_card(league),
                            rx.fragment(),
                        ),
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                ),
            ),
        )
    )
