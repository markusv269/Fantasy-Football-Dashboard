import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.components.layout import layout
from app.pages.matchups import league_selector


def roster_card(roster: rx.Var) -> rx.Component:
    roster_settings = roster["settings"].to(dict)
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                roster["team_name"].to(str),
                class_name="font-bold text-lg text-gray-900 truncate",
            ),
            rx.el.p(
                roster["owner_name"].to(str),
                class_name="text-sm text-gray-500 font-medium truncate",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    "W-L-T",
                    class_name="text-xs text-gray-400 font-bold uppercase block",
                ),
                rx.el.span(
                    f"{roster_settings['wins']}-{roster_settings['losses']}-{roster_settings['ties']}",
                    class_name="font-semibold text-gray-700",
                ),
            ),
            rx.el.div(
                rx.el.span(
                    "PF", class_name="text-xs text-gray-400 font-bold uppercase block"
                ),
                rx.el.span(
                    roster_settings["fpts"].to_string(),
                    class_name="font-semibold text-emerald-600",
                ),
            ),
            class_name="flex justify-between items-center bg-gray-50 p-3 rounded-xl",
        ),
        on_click=MatchupsState.view_roster(roster["roster_id"].to(int)),
        class_name="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md cursor-pointer transition-all hover:border-emerald-200",
    )


def roster_detail() -> rx.Component:
    roster = MatchupsState.selected_roster
    roster_settings = roster["settings"].to(dict)
    return rx.el.div(
        rx.el.button(
            rx.icon("arrow-left", class_name="w-4 h-4 mr-2"),
            "Back to Rosters",
            on_click=MatchupsState.clear_selected_roster,
            class_name="flex items-center text-sm font-medium text-gray-500 hover:text-emerald-600 transition-colors mb-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    roster["team_name"].to(str),
                    class_name="text-2xl font-bold text-gray-900",
                ),
                rx.el.p(
                    roster["owner_name"].to(str), class_name="text-gray-500 font-medium"
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "Record",
                        class_name="text-xs text-gray-400 font-bold uppercase block",
                    ),
                    rx.el.span(
                        f"{roster_settings['wins']}-{roster_settings['losses']}-{roster_settings['ties']}",
                        class_name="text-lg font-bold text-gray-800",
                    ),
                    class_name="text-center px-4 border-r border-gray-200",
                ),
                rx.el.div(
                    rx.el.span(
                        "Waiver",
                        class_name="text-xs text-gray-400 font-bold uppercase block",
                    ),
                    rx.el.span(
                        f"${roster_settings['waiver_budget_used']}",
                        class_name="text-lg font-bold text-gray-800",
                    ),
                    class_name="text-center px-4",
                ),
                class_name="flex items-center bg-gray-50 rounded-xl py-2",
            ),
            class_name="flex justify-between items-center bg-white p-6 rounded-2xl border border-gray-200 shadow-sm mb-6",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    "Starters",
                    class_name="font-bold text-gray-800 mb-4 flex items-center gap-2",
                ),
                rx.el.div(
                    rx.foreach(
                        roster["starters"].to(list[dict[str, str]]),
                        lambda p: rx.el.div(
                            rx.el.span(
                                p["full_name"],
                                class_name="font-bold text-sm text-gray-900",
                            ),
                            rx.el.div(
                                rx.el.span(
                                    p["position"],
                                    class_name=rx.match(
                                        p["position"],
                                        (
                                            "QB",
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-100 text-red-700 mr-1",
                                        ),
                                        (
                                            "RB",
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 mr-1",
                                        ),
                                        (
                                            "WR",
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 mr-1",
                                        ),
                                        (
                                            "TE",
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 mr-1",
                                        ),
                                        (
                                            "K",
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-200 text-gray-700 mr-1",
                                        ),
                                        (
                                            "DEF",
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 mr-1",
                                        ),
                                        "text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 mr-1",
                                    ),
                                ),
                                rx.el.span(
                                    p["team"],
                                    class_name="text-xs font-semibold text-gray-500",
                                ),
                                class_name="flex items-center",
                            ),
                            class_name="flex justify-between items-center p-3 border-b border-gray-100 last:border-0 hover:bg-gray-50",
                        ),
                    ),
                    class_name="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm",
                ),
                class_name="flex-1",
            ),
            rx.el.div(
                rx.el.h3(
                    "Reserve / IR",
                    class_name="font-bold text-gray-800 mb-4 flex items-center gap-2",
                ),
                rx.cond(
                    roster["reserve"].to(list[dict[str, str]]).length() > 0,
                    rx.el.div(
                        rx.foreach(
                            roster["reserve"].to(list[dict[str, str]]),
                            lambda p: rx.el.div(
                                rx.el.span(
                                    p["full_name"],
                                    class_name="font-bold text-sm text-gray-900",
                                ),
                                rx.el.div(
                                    rx.el.span(
                                        p["position"],
                                        class_name=rx.match(
                                            p["position"],
                                            (
                                                "QB",
                                                "text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-100 text-red-700 mr-1",
                                            ),
                                            (
                                                "RB",
                                                "text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 mr-1",
                                            ),
                                            (
                                                "WR",
                                                "text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 mr-1",
                                            ),
                                            (
                                                "TE",
                                                "text-[10px] font-bold px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 mr-1",
                                            ),
                                            (
                                                "K",
                                                "text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-200 text-gray-700 mr-1",
                                            ),
                                            (
                                                "DEF",
                                                "text-[10px] font-bold px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 mr-1",
                                            ),
                                            "text-[10px] font-bold px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 mr-1",
                                        ),
                                    ),
                                    rx.el.span(
                                        p["team"],
                                        class_name="text-xs font-semibold text-gray-500",
                                    ),
                                    class_name="flex items-center",
                                ),
                                class_name="flex justify-between items-center p-3 border-b border-gray-100 last:border-0 hover:bg-gray-50",
                            ),
                        ),
                        class_name="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm",
                    ),
                    rx.el.p(
                        "No players on reserve/IR.",
                        class_name="text-sm text-gray-500 italic p-4 bg-gray-50 rounded-xl border border-gray-200 border-dashed",
                    ),
                ),
                class_name="flex-1",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 gap-6",
        ),
    )


def rosters_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1("Rosters", class_name="text-3xl font-bold text-gray-900 mb-2"),
                rx.el.p(
                    "Explore team rosters and player details.",
                    class_name="text-gray-500 font-medium",
                ),
                class_name="mb-8",
            ),
            rx.cond(
                MatchupsState.selected_roster.contains("roster_id"),
                roster_detail(),
                rx.el.div(
                    rx.el.div(league_selector(), class_name="mb-8"),
                    rx.cond(
                        AppState.selected_league_id == "",
                        rx.el.div(
                            rx.icon("users", class_name="w-12 h-12 text-gray-300 mb-4"),
                            rx.el.h3(
                                "No League Selected",
                                class_name="text-xl font-bold text-gray-700 mb-2",
                            ),
                            rx.el.p(
                                "Select a league to view rosters.",
                                class_name="text-gray-500",
                            ),
                            class_name="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-gray-200 border-dashed",
                        ),
                        rx.el.div(
                            rx.foreach(MatchupsState.standings_data, roster_card),
                            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6",
                        ),
                    ),
                ),
            ),
        )
    )