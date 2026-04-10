import reflex as rx
from app.states.app_state import AppState
from app.states.user_state import UserState
from app.states.league_detail_state import LeagueDetailState
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
from app.components.league_modal import league_detail_modal
from app.pages.home import league_card


def leagues_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.cond(
                UserState.is_logged_in,
                rx.el.div(
                    rx.el.h1("Meine Ligen", class_name=H1 + " mb-8"),
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
                        class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8",
                    ),
                    class_name="mb-16",
                ),
            ),
            rx.el.div(
                rx.el.h1("Alle Ligen", class_name=H1 + " mb-4"),
                rx.cond(
                    ~UserState.has_username,
                    rx.el.p(
                        "Melde dich mit deinem Sleeper-Namen an, um deine Ligen zu sehen.",
                        class_name=TEXT_SECONDARY + " mb-8 font-medium",
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
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8",
                ),
            ),
            league_detail_modal(),
        )
    )