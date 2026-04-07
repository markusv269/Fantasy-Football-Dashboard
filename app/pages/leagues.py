import reflex as rx
from app.states.app_state import AppState
from app.states.league_detail_state import LeagueDetailState
from app.states.theme_state import ThemeState
from app.components.layout import layout
from app.components.league_modal import league_detail_modal
from app.pages.home import league_card


def leagues_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "All Leagues",
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-3xl font-bold text-white mb-8",
                        "text-3xl font-bold text-gray-900 mb-8",
                    ),
                ),
                rx.el.div(
                    rx.el.input(
                        placeholder="Enter Sleeper League ID",
                        on_change=AppState.set_new_league_id,
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "px-4 py-3 bg-[#0F1119] text-white border border-gray-700 rounded-xl focus:ring-2 focus:ring-[#DC2626] outline-none mr-4 w-full md:w-80 font-medium",
                            "px-4 py-3 bg-white text-gray-900 border border-gray-300 rounded-xl focus:ring-2 focus:ring-[#DC2626] outline-none mr-4 w-full md:w-80 font-medium",
                        ),
                        default_value=AppState.new_league_id,
                    ),
                    rx.el.button(
                        "Add League",
                        on_click=AppState.add_league_by_id,
                        class_name="bg-[#DC2626] hover:bg-[#B91C1C] text-white font-bold px-8 py-3 rounded-xl transition-colors shadow-sm whitespace-nowrap",
                    ),
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "flex flex-col md:flex-row items-center mb-10 bg-[#1C2033] p-6 rounded-3xl border border-gray-800 shadow-sm gap-4 md:gap-0",
                        "flex flex-col md:flex-row items-center mb-10 bg-white p-6 rounded-3xl border border-gray-200 shadow-sm gap-4 md:gap-0",
                    ),
                ),
                rx.el.div(
                    rx.foreach(
                        AppState.leagues_data,
                        lambda league: rx.el.div(
                            league_card(league),
                            rx.el.button(
                                rx.icon("trash-2", class_name="w-4 h-4"),
                                "Remove League",
                                on_click=lambda: AppState.remove_league(
                                    league["league_id"].to_string()
                                ),
                                class_name="mt-3 w-full flex items-center justify-center gap-2 py-2.5 text-sm font-semibold text-red-600 bg-red-50 hover:bg-red-100 rounded-xl transition-colors",
                            ),
                            class_name="flex flex-col",
                        ),
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8",
                ),
            ),
            league_detail_modal(),
        )
    )