import reflex as rx
import json
from app.states.app_state import AppState
from app.states.user_state import UserState
from app.states.league_detail_state import LeagueDetailState
from app.theme import (
    t,
    CARD,
    H1,
    H2,
    H3,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BTN_PRIMARY,
    INPUT,
    PAGE_BG,
)
from app.components.layout import layout
from app.components.league_modal import league_detail_modal


def league_card(league: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.image(
                src=rx.cond(
                    league["avatar"] != None,
                    f"https://sleepercdn.com/avatars/{league['avatar']}",
                    "/placeholder.svg",
                ),
                class_name="w-14 h-14 rounded-full object-cover border shadow-sm mr-4 "
                + t("border-gray-700", "border-gray-100"),
            ),
            rx.el.div(
                rx.el.h3(
                    league["name"], class_name=TEXT_PRIMARY + " font-bold text-lg"
                ),
                rx.el.p(
                    f"{league['season']} Season",
                    class_name=TEXT_SECONDARY + " text-sm font-medium",
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
                    class_name=TEXT_SECONDARY + " text-sm font-semibold",
                ),
                rx.fragment(),
            ),
            class_name="flex justify-between items-center",
        ),
        on_click=lambda: LeagueDetailState.open_league_modal(
            league["league_id"].to_string()
        ),
        class_name=CARD + " p-6 hover:border-[#DC2626] cursor-pointer transition-all",
    )


def home_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1("Willkommen bei Stoned Lack Sleeper Ligen", class_name=H1 + " mb-3"),
                rx.el.p(
                    "Das ist dein Zugang zu allen Ligen der Stoned Lack Army: verfolge Matchups, entdecke Trends und werde Teil der Stoned Lack Community.",
                    class_name=TEXT_SECONDARY + " text-lg font-medium",
                ),
                rx.cond(
                    ~UserState.has_username,
                    rx.el.div(
                        rx.el.p(
                            "Gib deinen Sleeper-Namen ein, um deine Ligen zu sehen:",
                            class_name="font-bold mb-2 " + TEXT_PRIMARY,
                        ),
                        rx.el.div(
                            rx.el.input(
                                placeholder="Sleeper Username",
                                on_change=UserState.set_username_input,
                                class_name=INPUT,
                            ),
                            rx.el.button(
                                "Los geht's",
                                on_click=UserState.save_username,
                                class_name=BTN_PRIMARY + " whitespace-nowrap px-8",
                            ),
                            class_name="flex gap-3",
                        ),
                        class_name="mt-6 p-6 rounded-2xl "
                        + t(
                            "bg-gray-800/50 border border-gray-700",
                            "bg-gray-50 border border-gray-200",
                        ),
                    ),
                ),
                class_name="mb-10 border-l-4 border-l-[#DC2626] p-8 md:p-10 rounded-3xl shadow-sm "
                + t("bg-[#1C2033] border-gray-800", "bg-white border-gray-200"),
            ),
            rx.el.div(
                rx.el.div(
                    rx.cond(
                        UserState.is_logged_in,
                        rx.el.div(
                            rx.el.h2("Meine Ligen", class_name=H2 + " mb-6"),
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
                                class_name="grid grid-cols-1 md:grid-cols-2 gap-6",
                            ),
                            class_name="mb-10",
                        ),
                    ),
                    rx.el.div(
                        rx.el.h2("Alle Ligen", class_name=H2 + " mb-6"),
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
                            class_name="grid grid-cols-1 md:grid-cols-2 gap-6",
                        ),
                    ),
                    class_name="col-span-1 lg:col-span-2 space-y-10",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.h3("Trending Adds", class_name=H3),
                            rx.icon("flame", class_name="w-5 h-5 text-orange-500"),
                            class_name="flex justify-between items-center mb-4",
                        ),
                        rx.el.div(
                            rx.foreach(
                                AppState.trending_adds,
                                lambda t_player: rx.el.div(
                                    rx.el.div(
                                        rx.el.span(
                                            t_player["full_name"].to(str),
                                            class_name="font-bold mr-2 " + TEXT_PRIMARY,
                                        ),
                                        rx.el.span(
                                            t_player["position"].to(str),
                                            class_name=rx.match(
                                                t_player["position"].to(str),
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
                                            t_player["team"].to(str),
                                            class_name=TEXT_SECONDARY
                                            + " text-xs font-semibold",
                                        ),
                                        class_name="flex items-center",
                                    ),
                                    rx.el.span(
                                        f"+{t_player['count']}",
                                        class_name="text-[#5B7BA5] text-xs font-bold bg-[#5B7BA5]/10 px-2.5 py-1 rounded-md",
                                    ),
                                    class_name="flex justify-between items-center py-3 border-b last:border-0 "
                                    + t("border-gray-800", "border-gray-100"),
                                ),
                            ),
                            class_name="p-2 rounded-xl "
                            + t("bg-[#161926]", "bg-white"),
                        ),
                        class_name=CARD + " p-6",
                    ),
                    class_name="col-span-1",
                ),
                class_name="grid grid-cols-1 lg:grid-cols-3 gap-8",
            ),
            league_detail_modal(),
        )
    )