import reflex as rx
from app.states.community_state import CommunityState
from app.components.layout import layout


def trending_player_row(player: dict, index: int, is_add: bool) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.span(index + 1, class_name="text-gray-500 font-bold"),
            class_name="p-3 w-12 text-center border-b border-gray-100",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    player["full_name"].to(str),
                    class_name="font-bold text-gray-900 mr-2",
                ),
                rx.el.span(
                    player["position"].to(str),
                    class_name=rx.match(
                        player["position"].to(str),
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
                    player["team"].to(str),
                    class_name="text-xs font-semibold text-gray-500",
                ),
                class_name="flex items-center",
            ),
            class_name="p-3 border-b border-gray-100",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    player["count"].to_string(),
                    class_name="font-bold text-gray-700 mr-2",
                ),
                rx.cond(
                    is_add,
                    rx.icon("trending-up", class_name="w-4 h-4 text-emerald-500"),
                    rx.icon("trending-down", class_name="w-4 h-4 text-red-500"),
                ),
                class_name="flex items-center justify-end",
            ),
            class_name="p-3 border-b border-gray-100 text-right",
        ),
        class_name="hover:bg-gray-50 transition-colors",
    )


def trending_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h1(
                        rx.icon(
                            "flame", class_name="w-8 h-8 mr-3 text-orange-500 inline"
                        ),
                        "Trending Players",
                        class_name="text-3xl font-bold text-gray-900 mb-2 flex items-center",
                    ),
                    rx.el.p(
                        "The most added and dropped players across Sleeper leagues.",
                        class_name="text-gray-500 font-medium",
                    ),
                ),
                rx.el.div(
                    rx.el.button(
                        "24 Hours",
                        on_click=CommunityState.change_trending_timeframe("24h"),
                        class_name=rx.cond(
                            CommunityState.trending_timeframe == "24h",
                            "px-4 py-2 text-sm font-bold bg-emerald-600 text-white rounded-l-lg transition-colors",
                            "px-4 py-2 text-sm font-bold bg-white text-gray-600 border border-gray-200 rounded-l-lg hover:bg-gray-50 transition-colors",
                        ),
                    ),
                    rx.el.button(
                        "48 Hours",
                        on_click=CommunityState.change_trending_timeframe("48h"),
                        class_name=rx.cond(
                            CommunityState.trending_timeframe == "48h",
                            "px-4 py-2 text-sm font-bold bg-emerald-600 text-white rounded-r-lg transition-colors",
                            "px-4 py-2 text-sm font-bold bg-white text-gray-600 border border-gray-200 border-l-0 rounded-r-lg hover:bg-gray-50 transition-colors",
                        ),
                    ),
                    class_name="flex mt-4 md:mt-0 shadow-sm rounded-lg",
                ),
                class_name="flex flex-col md:flex-row md:justify-between md:items-end mb-8",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            rx.icon(
                                "arrow-up-right",
                                class_name="w-5 h-5 mr-2 text-emerald-500 inline",
                            ),
                            "Hot Adds",
                            class_name="text-lg font-bold text-gray-800 flex items-center",
                        ),
                        class_name="p-4 border-b border-gray-200 bg-emerald-50 rounded-t-2xl",
                    ),
                    rx.el.div(
                        rx.el.table(
                            rx.el.tbody(
                                rx.foreach(
                                    CommunityState.trending_adds,
                                    lambda player, idx: trending_player_row(
                                        player, idx, True
                                    ),
                                )
                            ),
                            class_name="w-full table-auto",
                        ),
                        class_name="overflow-x-auto p-2",
                    ),
                    class_name="bg-white rounded-2xl border border-gray-200 shadow-sm",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            rx.icon(
                                "arrow-down-right",
                                class_name="w-5 h-5 mr-2 text-red-500 inline",
                            ),
                            "Trending Drops",
                            class_name="text-lg font-bold text-gray-800 flex items-center",
                        ),
                        class_name="p-4 border-b border-gray-200 bg-red-50 rounded-t-2xl",
                    ),
                    rx.el.div(
                        rx.el.table(
                            rx.el.tbody(
                                rx.foreach(
                                    CommunityState.trending_drops,
                                    lambda player, idx: trending_player_row(
                                        player, idx, False
                                    ),
                                )
                            ),
                            class_name="w-full table-auto",
                        ),
                        class_name="overflow-x-auto p-2",
                    ),
                    class_name="bg-white rounded-2xl border border-gray-200 shadow-sm",
                ),
                class_name="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6",
            ),
            rx.el.p(
                "* Players sorted by Sleeper trending activity across all leagues.",
                class_name="text-xs text-gray-500 text-center italic mt-6",
            ),
        )
    )