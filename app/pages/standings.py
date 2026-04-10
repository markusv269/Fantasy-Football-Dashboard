import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.states.theme_state import ThemeState
from app.states.user_state import UserState
from app.theme import (
    t,
    H1,
    TEXT_SECONDARY,
    TEXT_PRIMARY,
    EMPTY_STATE,
    TABLE_CONTAINER,
    TABLE_HEADER_ROW,
    TABLE_HEADER_CELL,
    TABLE_ROW,
)
from app.components.layout import layout
from app.pages.matchups import league_selector


def standings_row(team: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.span(
                team["rank"],
                class_name=rx.match(
                    team["rank"].to(int),
                    (
                        1,
                        "w-8 h-8 rounded-full bg-yellow-100 text-yellow-700 font-bold flex items-center justify-center",
                    ),
                    (
                        2,
                        "w-8 h-8 rounded-full bg-gray-200 text-gray-700 font-bold flex items-center justify-center",
                    ),
                    (
                        3,
                        "w-8 h-8 rounded-full bg-orange-100 text-orange-700 font-bold flex items-center justify-center",
                    ),
                    "w-8 h-8 rounded-full font-bold flex items-center justify-center "
                    + t("bg-gray-800 text-gray-400", "bg-gray-50 text-gray-600"),
                ),
            ),
            class_name="p-4",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.div(team["team_name"], class_name="font-bold " + TEXT_PRIMARY),
                rx.el.div(
                    team["owner_name"],
                    class_name="text-xs font-medium " + TEXT_SECONDARY,
                ),
            ),
            class_name="p-4",
        ),
        rx.el.td(
            team["wins"],
            class_name="p-4 font-semibold text-center "
            + t("text-gray-300", "text-gray-700"),
        ),
        rx.el.td(
            team["losses"],
            class_name="p-4 font-semibold text-center "
            + t("text-gray-300", "text-gray-700"),
        ),
        rx.el.td(
            team["ties"],
            class_name="p-4 font-semibold text-center "
            + t("text-gray-300", "text-gray-700"),
        ),
        rx.el.td(
            team["win_pct"], class_name="p-4 font-medium text-center " + TEXT_SECONDARY
        ),
        rx.el.td(
            team["fpts"], class_name="p-4 font-semibold text-[#DC2626] text-right"
        ),
        rx.el.td(
            team["fpts_against"], class_name="p-4 font-medium text-[#5B7BA5] text-right"
        ),
        on_click=MatchupsState.view_roster(team["roster_id"].to(int)),
        class_name=TABLE_ROW + " cursor-pointer",
    )


def standings_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1("Standings", class_name=H1 + " mb-2"),
                rx.el.p(
                    "League rankings, records, and points.",
                    class_name=TEXT_SECONDARY + " font-medium",
                ),
                class_name="mb-8",
            ),
            rx.el.div(league_selector(), class_name="mb-8"),
            rx.cond(
                AppState.selected_league_id == "",
                rx.el.div(
                    rx.icon("list-ordered", class_name="w-12 h-12 text-gray-300 mb-4"),
                    rx.el.h3(
                        "No League Selected",
                        class_name="text-xl font-bold mb-2 " + TEXT_PRIMARY,
                    ),
                    rx.el.p(
                        "Select a league to view standings.", class_name=TEXT_SECONDARY
                    ),
                    class_name=EMPTY_STATE,
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    rx.el.th(
                                        "Rank",
                                        class_name=TABLE_HEADER_CELL + " p-4 text-left",
                                    ),
                                    rx.el.th(
                                        "Team",
                                        class_name=TABLE_HEADER_CELL + " p-4 text-left",
                                    ),
                                    rx.el.th(
                                        "W",
                                        class_name=TABLE_HEADER_CELL
                                        + " p-4 text-center",
                                    ),
                                    rx.el.th(
                                        "L",
                                        class_name=TABLE_HEADER_CELL
                                        + " p-4 text-center",
                                    ),
                                    rx.el.th(
                                        "T",
                                        class_name=TABLE_HEADER_CELL
                                        + " p-4 text-center",
                                    ),
                                    rx.el.th(
                                        "Pct",
                                        class_name=TABLE_HEADER_CELL
                                        + " p-4 text-center",
                                    ),
                                    rx.el.th(
                                        "PF",
                                        class_name=TABLE_HEADER_CELL
                                        + " p-4 text-right",
                                    ),
                                    rx.el.th(
                                        "PA",
                                        class_name=TABLE_HEADER_CELL
                                        + " p-4 text-right",
                                    ),
                                    class_name=TABLE_HEADER_ROW,
                                )
                            ),
                            rx.el.tbody(
                                rx.foreach(MatchupsState.standings_data, standings_row)
                            ),
                            class_name="min-w-full table-auto",
                        ),
                        class_name="overflow-x-auto",
                    ),
                    class_name=TABLE_CONTAINER,
                ),
            ),
        )
    )