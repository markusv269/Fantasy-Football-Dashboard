import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.states.theme_state import ThemeState
from app.theme import t, SELECT, H1, TEXT_SECONDARY, TEXT_PRIMARY, CARD, EMPTY_STATE
from app.components.layout import layout


def league_selector() -> rx.Component:
    return rx.el.div(
        rx.el.select(
            rx.el.option("Select a League", value="", disabled=True),
            rx.foreach(
                AppState.leagues_data,
                lambda lg: rx.el.option(lg["name"], value=lg["league_id"].to_string()),
            ),
            value=AppState.selected_league_id,
            on_change=lambda val: [
                AppState.select_league(val),
                MatchupsState.init_matchups(),
            ],
            class_name=rx.cond(
                ThemeState.is_dark,
                "appearance-none bg-[#1C2033] border border-gray-700 text-white text-sm rounded-lg focus:ring-[#DC2626] focus:border-[#DC2626] block w-full p-2.5 pr-10 outline-none font-medium",
                "appearance-none bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-[#DC2626] focus:border-[#DC2626] block w-full p-2.5 pr-10 outline-none font-medium",
            ),
        ),
        rx.el.div(
            rx.icon("chevron-down", class_name="h-4 w-4 text-gray-500"),
            class_name="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none",
        ),
        class_name="relative w-full md:w-64 mb-6 md:mb-0",
    )


def week_selector() -> rx.Component:
    return rx.el.div(
        rx.el.button(
            rx.icon("chevron-left", class_name="w-4 h-4"),
            on_click=MatchupsState.change_week(MatchupsState.selected_week - 1),
            class_name="p-2 text-gray-500 hover:text-[#DC2626] transition-colors",
        ),
        rx.el.div(
            rx.foreach(
                rx.Var.range(1, 19),
                lambda w: rx.el.button(
                    w,
                    on_click=MatchupsState.change_week(w),
                    class_name=rx.cond(
                        w == MatchupsState.selected_week,
                        "w-8 h-8 rounded-full bg-[#DC2626]/20 text-[#DC2626] font-bold text-sm flex items-center justify-center",
                        "w-8 h-8 rounded-full font-medium text-sm flex items-center justify-center transition-colors "
                        + t(
                            "text-gray-400 hover:bg-gray-800",
                            "text-gray-600 hover:bg-gray-100",
                        ),
                    ),
                ),
            ),
            class_name="flex gap-1 overflow-x-auto no-scrollbar mx-2",
        ),
        rx.el.button(
            rx.icon("chevron-right", class_name="w-4 h-4"),
            on_click=MatchupsState.change_week(MatchupsState.selected_week + 1),
            class_name="p-2 text-gray-500 hover:text-[#DC2626] transition-colors",
        ),
        class_name="flex items-center rounded-full px-2 py-1 shadow-sm w-full md:w-auto overflow-hidden "
        + t("bg-[#1C2033] border border-gray-800", "bg-white border border-gray-200"),
    )


def matchup_card(matchup: rx.Var) -> rx.Component:
    team_a = matchup["team_a"].to(dict)
    team_b = matchup["team_b"].to(dict)
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    team_a["team_name"].to(str),
                    class_name="font-semibold text-sm truncate max-w-[120px] "
                    + TEXT_PRIMARY,
                ),
                rx.el.span(
                    team_a["points"].to_string(),
                    class_name=rx.cond(
                        team_a["points"].to(float) > team_b["points"].to(float),
                        "font-bold text-lg text-[#DC2626]",
                        "font-semibold text-lg " + TEXT_SECONDARY,
                    ),
                ),
                class_name="flex flex-col items-center p-4 flex-1",
            ),
            rx.el.div(
                rx.el.span(
                    "VS",
                    class_name="text-xs font-bold px-2 py-1 rounded-full "
                    + t("text-gray-500 bg-gray-800", "text-gray-400 bg-gray-100"),
                ),
                class_name="flex items-center justify-center px-2",
            ),
            rx.el.div(
                rx.el.span(
                    team_b["team_name"].to(str),
                    class_name="font-semibold text-sm truncate max-w-[120px] "
                    + TEXT_PRIMARY,
                ),
                rx.el.span(
                    team_b["points"].to_string(),
                    class_name=rx.cond(
                        team_b["points"].to(float) > team_a["points"].to(float),
                        "font-bold text-lg text-[#DC2626]",
                        "font-semibold text-lg " + TEXT_SECONDARY,
                    ),
                ),
                class_name="flex flex-col items-center p-4 flex-1",
            ),
            class_name="flex justify-between items-center w-full",
        ),
        rx.el.div(
            rx.el.span(
                f"Matchup {matchup['matchup_id']}",
                class_name="text-[10px] uppercase font-bold text-gray-400",
            ),
            class_name="absolute top-2 left-3",
        ),
        class_name=CARD
        + " relative shadow-sm hover:shadow-md transition-shadow overflow-hidden",
    )


def matchups_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1("Matchups", class_name=H1 + " mb-2"),
                rx.el.p(
                    "View weekly scores and head-to-head results.",
                    class_name=TEXT_SECONDARY + " font-medium",
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                league_selector(),
                week_selector(),
                class_name="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4",
            ),
            rx.cond(
                AppState.selected_league_id == "",
                rx.el.div(
                    rx.icon("trophy", class_name="w-12 h-12 text-gray-300 mb-4"),
                    rx.el.h3(
                        "No League Selected",
                        class_name="text-xl font-bold mb-2 " + TEXT_PRIMARY,
                    ),
                    rx.el.p(
                        "Select a league to view matchups.", class_name=TEXT_SECONDARY
                    ),
                    class_name=EMPTY_STATE,
                ),
                rx.cond(
                    MatchupsState.paired_matchups.length() > 0,
                    rx.el.div(
                        rx.foreach(MatchupsState.paired_matchups, matchup_card),
                        class_name="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6",
                    ),
                    rx.el.div(
                        rx.icon(
                            "calendar-x", class_name="w-12 h-12 text-gray-300 mb-4"
                        ),
                        rx.el.h3(
                            "No Matchups",
                            class_name="text-xl font-bold mb-2 " + TEXT_PRIMARY,
                        ),
                        rx.el.p(
                            "No matchups available for this week.",
                            class_name=TEXT_SECONDARY,
                        ),
                        class_name=EMPTY_STATE,
                    ),
                ),
            ),
        )
    )