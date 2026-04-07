import reflex as rx
from app.states.app_state import AppState
from app.components.layout import layout
from app.pages.home import league_card


def leagues_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "All Leagues", class_name="text-3xl font-bold text-gray-900 mb-8"
                ),
                rx.el.div(
                    rx.el.input(
                        placeholder="Enter Sleeper League ID",
                        on_change=AppState.set_new_league_id,
                        class_name="px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none mr-4 w-full md:w-80 font-medium",
                        default_value=AppState.new_league_id,
                    ),
                    rx.el.button(
                        "Add League",
                        on_click=AppState.add_league_by_id,
                        class_name="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-8 py-3 rounded-xl transition-colors shadow-sm whitespace-nowrap",
                    ),
                    class_name="flex flex-col md:flex-row items-center mb-10 bg-white p-6 rounded-3xl border border-gray-200 shadow-sm gap-4 md:gap-0",
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
            )
        )
    )