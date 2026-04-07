import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.states.theme_state import ThemeState
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
                    rx.cond(
                        ThemeState.is_dark,
                        "w-8 h-8 rounded-full bg-gray-800 text-gray-400 font-bold flex items-center justify-center",
                        "w-8 h-8 rounded-full bg-gray-50 text-gray-600 font-bold flex items-center justify-center",
                    ),
                ),
            ),
            class_name="p-4",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.div(
                    team["team_name"],
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "font-bold text-white",
                        "font-bold text-gray-900",
                    ),
                ),
                rx.el.div(
                    team["owner_name"],
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-xs text-gray-400 font-medium",
                        "text-xs text-gray-500 font-medium",
                    ),
                ),
            ),
            class_name="p-4",
        ),
        rx.el.td(
            team["wins"],
            class_name=rx.cond(
                ThemeState.is_dark,
                "p-4 font-semibold text-gray-300 text-center",
                "p-4 font-semibold text-gray-700 text-center",
            ),
        ),
        rx.el.td(
            team["losses"],
            class_name=rx.cond(
                ThemeState.is_dark,
                "p-4 font-semibold text-gray-300 text-center",
                "p-4 font-semibold text-gray-700 text-center",
            ),
        ),
        rx.el.td(
            team["ties"],
            class_name=rx.cond(
                ThemeState.is_dark,
                "p-4 font-semibold text-gray-300 text-center",
                "p-4 font-semibold text-gray-700 text-center",
            ),
        ),
        rx.el.td(
            team["win_pct"],
            class_name=rx.cond(
                ThemeState.is_dark,
                "p-4 font-medium text-gray-500 text-center",
                "p-4 font-medium text-gray-500 text-center",
            ),
        ),
        rx.el.td(
            team["fpts"], class_name="p-4 font-semibold text-[#DC2626] text-right"
        ),
        rx.el.td(
            team["fpts_against"], class_name="p-4 font-medium text-[#5B7BA5] text-right"
        ),
        on_click=MatchupsState.view_roster(team["roster_id"].to(int)),
        class_name=rx.cond(
            ThemeState.is_dark,
            "border-b border-gray-800 hover:bg-[#161926] cursor-pointer transition-colors",
            "border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors",
        ),
    )


def standings_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Standings", class_name="text-3xl font-bold text-gray-900 mb-2"
                ),
                rx.el.p(
                    "League rankings, records, and points.",
                    class_name="text-gray-500 font-medium",
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
                        class_name="text-xl font-bold text-gray-700 mb-2",
                    ),
                    rx.el.p(
                        "Select a league to view standings.", class_name="text-gray-500"
                    ),
                    class_name="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-gray-200 border-dashed",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.table(
                            rx.el.thead(
                                rx.el.tr(
                                    rx.el.th(
                                        "Rank",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    rx.el.th(
                                        "Team",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    rx.el.th(
                                        "W",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    rx.el.th(
                                        "L",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    rx.el.th(
                                        "T",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    rx.el.th(
                                        "Pct",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    rx.el.th(
                                        "PF",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-right text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    rx.el.th(
                                        "PA",
                                        class_name=rx.cond(
                                            ThemeState.is_dark,
                                            "p-4 text-right text-xs font-bold text-gray-400 uppercase tracking-wider",
                                            "p-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider",
                                        ),
                                    ),
                                    class_name=rx.cond(
                                        ThemeState.is_dark,
                                        "bg-[#161926] border-b border-gray-800",
                                        "bg-gray-50 border-b border-gray-200",
                                    ),
                                )
                            ),
                            rx.el.tbody(
                                rx.foreach(MatchupsState.standings_data, standings_row)
                            ),
                            class_name="min-w-full table-auto",
                        ),
                        class_name="overflow-x-auto",
                    ),
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "bg-[#1C2033] rounded-2xl border border-gray-800 shadow-sm overflow-hidden",
                        "bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden",
                    ),
                ),
            ),
        )
    )