import reflex as rx
from app.states.app_state import AppState
from app.states.league_detail_state import LeagueDetailState
from app.components.layout import layout
from app.components.league_modal import league_detail_modal


def league_card(league: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.image(
                src=rx.cond(
                    league["avatar"] != "",
                    f"https://sleepercdn.com/avatars/{league['avatar']}",
                    "/placeholder.svg",
                ),
                class_name="w-14 h-14 rounded-full object-cover border border-gray-100 shadow-sm mr-4",
            ),
            rx.el.div(
                rx.el.h3(league["name"], class_name="font-bold text-lg text-gray-800"),
                rx.el.p(
                    f"{league['season']} Season",
                    class_name="text-sm font-medium text-gray-500",
                ),
            ),
            class_name="flex items-center mb-5",
        ),
        rx.el.div(
            rx.el.span(
                league["status"],
                class_name=rx.match(
                    league["status"],
                    (
                        "in_season",
                        "bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full text-xs font-bold uppercase",
                    ),
                    (
                        "complete",
                        "bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-bold uppercase",
                    ),
                    (
                        "drafting",
                        "bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-bold uppercase",
                    ),
                    (
                        "pre_draft",
                        "bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-xs font-bold uppercase",
                    ),
                    (
                        "redraft",
                        "bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-xs font-bold uppercase",
                    ),
                    (
                        "dynasty",
                        "bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-bold uppercase",
                    ),
                    "bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-xs font-bold uppercase",
                ),
            ),
            rx.cond(
                (league["total_rosters"].to(str) != "")
                & (league["total_rosters"].to(str) != "0"),
                rx.el.span(
                    f"{league['total_rosters']} Teams",
                    class_name="text-sm font-semibold text-gray-600",
                ),
                rx.fragment(),
            ),
            class_name="flex justify-between items-center",
        ),
        on_click=lambda: LeagueDetailState.open_league_modal(
            league["league_id"].to_string()
        ),
        class_name="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md hover:border-emerald-200 transition-all cursor-pointer",
    )


def home_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Welcome to Fantasy Football Community Hub",
                    class_name="text-3xl md:text-4xl font-bold text-gray-900 mb-3",
                ),
                rx.el.p(
                    "Manage your leagues, track matchups, follow trends, and engage with the podcast community seamlessly.",
                    class_name="text-lg text-gray-600 font-medium",
                ),
                class_name="mb-10 bg-white p-8 md:p-10 rounded-3xl border border-gray-200 shadow-sm",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            "Your Leagues",
                            class_name="text-2xl font-bold text-gray-800 mb-6",
                        ),
                        rx.cond(
                            AppState.leagues_data.length() > 0,
                            rx.el.div(
                                rx.foreach(AppState.leagues_data, league_card),
                                class_name="grid grid-cols-1 md:grid-cols-2 gap-6",
                            ),
                            rx.el.div(
                                rx.icon(
                                    "ghost", class_name="w-12 h-12 text-gray-400 mb-3"
                                ),
                                rx.el.p(
                                    "No leagues configured yet.",
                                    class_name="text-gray-500 font-medium",
                                ),
                                class_name="p-12 border-2 border-dashed border-gray-300 rounded-3xl text-center flex flex-col items-center justify-center bg-gray-50/50",
                            ),
                        ),
                    ),
                    class_name="col-span-1 lg:col-span-2 space-y-10",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.h3(
                            "Add League",
                            class_name="text-lg font-bold text-gray-800 mb-4",
                        ),
                        rx.el.div(
                            rx.el.input(
                                placeholder="Sleeper League ID",
                                on_change=AppState.set_new_league_id,
                                class_name="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none mb-4 font-medium",
                                default_value=AppState.new_league_id,
                            ),
                            rx.el.button(
                                "Add League",
                                on_click=AppState.add_league_by_id,
                                class_name="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl transition-colors shadow-sm",
                            ),
                        ),
                        class_name="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm mb-8",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.h3(
                                "Trending Adds",
                                class_name="text-lg font-bold text-gray-800",
                            ),
                            rx.icon("flame", class_name="w-5 h-5 text-orange-500"),
                            class_name="flex justify-between items-center mb-4",
                        ),
                        rx.el.div(
                            rx.foreach(
                                AppState.trending_adds,
                                lambda t: rx.el.div(
                                    rx.el.div(
                                        rx.el.span(
                                            t["full_name"].to(str),
                                            class_name="font-bold text-gray-800 mr-2",
                                        ),
                                        rx.el.span(
                                            t["position"].to(str),
                                            class_name=rx.match(
                                                t["position"].to(str),
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
                                            t["team"].to(str),
                                            class_name="text-xs font-semibold text-gray-500",
                                        ),
                                        class_name="flex items-center",
                                    ),
                                    rx.el.span(
                                        f"+{t['count']}",
                                        class_name="text-emerald-700 text-xs font-bold bg-emerald-50 px-2.5 py-1 rounded-md",
                                    ),
                                    class_name="flex justify-between items-center py-3 border-b border-gray-100 last:border-0",
                                ),
                            ),
                            class_name="bg-white p-2 rounded-xl",
                        ),
                        class_name="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm",
                    ),
                    class_name="col-span-1",
                ),
                class_name="grid grid-cols-1 lg:grid-cols-3 gap-8",
            ),
            league_detail_modal(),
        )
    )