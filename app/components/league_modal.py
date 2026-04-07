import reflex as rx
from app.states.league_detail_state import LeagueDetailState
from app.states.theme_state import ThemeState


def standing_row(team: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.span(
                team["rank"].to(str),
                class_name=rx.match(
                    team["rank"].to(int),
                    (
                        1,
                        "w-6 h-6 rounded-full bg-yellow-100 text-yellow-700 font-bold flex items-center justify-center",
                    ),
                    (
                        2,
                        "w-6 h-6 rounded-full bg-gray-200 text-gray-700 font-bold flex items-center justify-center",
                    ),
                    (
                        3,
                        "w-6 h-6 rounded-full bg-orange-100 text-orange-700 font-bold flex items-center justify-center",
                    ),
                    rx.cond(
                        ThemeState.is_dark,
                        "w-6 h-6 rounded-full bg-gray-800 text-gray-400 font-bold flex items-center justify-center",
                        "w-6 h-6 rounded-full bg-gray-50 text-gray-600 font-bold flex items-center justify-center",
                    ),
                ),
            ),
            class_name="p-3",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    team["team_name"].to(str),
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "font-bold text-white block",
                        "font-bold text-gray-900 block",
                    ),
                ),
                rx.el.span(
                    team["display_name"].to(str),
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-xs text-gray-400 font-medium",
                        "text-xs text-gray-500 font-medium",
                    ),
                ),
            ),
            class_name="p-3",
        ),
        rx.el.td(
            team["wins"].to(str),
            class_name=rx.cond(
                ThemeState.is_dark,
                "p-3 text-center font-medium text-gray-300",
                "p-3 text-center font-medium text-gray-700",
            ),
        ),
        rx.el.td(
            team["losses"].to(str),
            class_name=rx.cond(
                ThemeState.is_dark,
                "p-3 text-center font-medium text-gray-300",
                "p-3 text-center font-medium text-gray-700",
            ),
        ),
        rx.el.td(
            team["ties"].to(str),
            class_name=rx.cond(
                ThemeState.is_dark,
                "p-3 text-center font-medium text-gray-300",
                "p-3 text-center font-medium text-gray-700",
            ),
        ),
        rx.el.td(
            team["fpts_for"].to(str),
            class_name="p-3 text-right font-bold text-emerald-500",
        ),
        rx.el.td(
            team["fpts_against"].to(str),
            class_name="p-3 text-right font-medium text-red-500",
        ),
        class_name=rx.cond(
            ThemeState.is_dark,
            "border-b border-gray-800 hover:bg-[#161926]",
            "border-b border-gray-100 hover:bg-gray-50",
        ),
    )


def matchup_card(matchup: dict) -> rx.Component:
    a_pts = matchup["team_a_points"].to(float)
    b_pts = matchup["team_b_points"].to(float)
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                matchup["team_a_name"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "font-medium truncate max-w-[100px] text-sm text-gray-300",
                    "font-medium truncate max-w-[100px] text-sm text-gray-700",
                ),
            ),
            rx.el.span(
                matchup["team_a_points"].to(str),
                class_name=rx.cond(
                    a_pts > b_pts,
                    "font-bold text-emerald-500",
                    rx.cond(
                        ThemeState.is_dark,
                        "font-medium text-gray-500",
                        "font-medium text-gray-600",
                    ),
                ),
            ),
            class_name="flex justify-between items-center mb-1",
        ),
        rx.el.div(
            rx.el.span(
                matchup["team_b_name"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "font-medium truncate max-w-[100px] text-sm text-gray-300",
                    "font-medium truncate max-w-[100px] text-sm text-gray-700",
                ),
            ),
            rx.el.span(
                matchup["team_b_points"].to(str),
                class_name=rx.cond(
                    b_pts > a_pts,
                    "font-bold text-emerald-500",
                    rx.cond(
                        ThemeState.is_dark,
                        "font-medium text-gray-500",
                        "font-medium text-gray-600",
                    ),
                ),
            ),
            class_name="flex justify-between items-center",
        ),
        class_name=rx.cond(
            ThemeState.is_dark,
            "bg-[#161926] border border-gray-700 p-3 rounded-xl",
            "bg-gray-50 border border-gray-200 p-3 rounded-xl",
        ),
    )


def league_detail_modal() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.cond(
                    LeagueDetailState.modal_loading,
                    rx.el.div(
                        rx.icon(
                            "loader",
                            class_name="w-8 h-8 animate-spin text-emerald-500 mx-auto",
                        ),
                        class_name="py-20 flex justify-center",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.radix.primitives.dialog.title(
                                    LeagueDetailState.modal_league_name,
                                    class_name=rx.cond(
                                        ThemeState.is_dark,
                                        "text-2xl font-bold text-white",
                                        "text-2xl font-bold text-gray-900",
                                    ),
                                ),
                                rx.el.div(
                                    rx.el.span(
                                        LeagueDetailState.modal_league_type.upper(),
                                        class_name="bg-blue-100 text-blue-800 text-[10px] px-2 py-0.5 rounded-full font-bold",
                                    ),
                                    rx.el.span(
                                        LeagueDetailState.modal_league_season,
                                        class_name="bg-gray-100 text-gray-600 text-[10px] px-2 py-0.5 rounded-full font-bold",
                                    ),
                                    class_name="flex items-center gap-2 mt-1",
                                ),
                            ),
                            rx.radix.primitives.dialog.close(
                                rx.el.button(
                                    rx.icon("x", class_name="w-5 h-5 text-gray-500"),
                                    on_click=LeagueDetailState.close_league_modal,
                                    class_name=rx.cond(
                                        ThemeState.is_dark,
                                        "p-2 hover:bg-gray-800 rounded-full transition-colors",
                                        "p-2 hover:bg-gray-100 rounded-full transition-colors",
                                    ),
                                )
                            ),
                            class_name="flex justify-between items-start mb-6",
                        ),
                        rx.cond(
                            LeagueDetailState.modal_champion.contains("team_name"),
                            rx.el.div(
                                rx.icon(
                                    "trophy", class_name="w-5 h-5 text-yellow-600 mr-2"
                                ),
                                rx.el.span(
                                    "League Champion: ",
                                    class_name="font-medium text-yellow-800",
                                ),
                                rx.el.span(
                                    f"{LeagueDetailState.modal_champion['team_name'].to(str)} ({LeagueDetailState.modal_champion['display_name'].to(str)})",
                                    class_name="font-bold text-yellow-900 ml-1",
                                ),
                                class_name="flex items-center bg-yellow-50 border border-yellow-200 p-4 rounded-xl mb-6",
                            ),
                        ),
                        rx.el.div(
                            rx.el.h3(
                                "Standings",
                                class_name=rx.cond(
                                    ThemeState.is_dark,
                                    "text-lg font-bold text-gray-200 mb-3",
                                    "text-lg font-bold text-gray-800 mb-3",
                                ),
                            ),
                            rx.el.div(
                                rx.el.table(
                                    rx.el.thead(
                                        rx.el.tr(
                                            rx.el.th(
                                                "Rank",
                                                class_name=rx.cond(
                                                    ThemeState.is_dark,
                                                    "p-2 text-left text-xs font-bold text-gray-400",
                                                    "p-2 text-left text-xs font-bold text-gray-500",
                                                ),
                                            ),
                                            rx.el.th(
                                                "Team",
                                                class_name=rx.cond(
                                                    ThemeState.is_dark,
                                                    "p-2 text-left text-xs font-bold text-gray-400",
                                                    "p-2 text-left text-xs font-bold text-gray-500",
                                                ),
                                            ),
                                            rx.el.th(
                                                "W",
                                                class_name=rx.cond(
                                                    ThemeState.is_dark,
                                                    "p-2 text-center text-xs font-bold text-gray-400",
                                                    "p-2 text-center text-xs font-bold text-gray-500",
                                                ),
                                            ),
                                            rx.el.th(
                                                "L",
                                                class_name=rx.cond(
                                                    ThemeState.is_dark,
                                                    "p-2 text-center text-xs font-bold text-gray-400",
                                                    "p-2 text-center text-xs font-bold text-gray-500",
                                                ),
                                            ),
                                            rx.el.th(
                                                "T",
                                                class_name=rx.cond(
                                                    ThemeState.is_dark,
                                                    "p-2 text-center text-xs font-bold text-gray-400",
                                                    "p-2 text-center text-xs font-bold text-gray-500",
                                                ),
                                            ),
                                            rx.el.th(
                                                "PF",
                                                class_name=rx.cond(
                                                    ThemeState.is_dark,
                                                    "p-2 text-right text-xs font-bold text-gray-400",
                                                    "p-2 text-right text-xs font-bold text-gray-500",
                                                ),
                                            ),
                                            rx.el.th(
                                                "PA",
                                                class_name=rx.cond(
                                                    ThemeState.is_dark,
                                                    "p-2 text-right text-xs font-bold text-gray-400",
                                                    "p-2 text-right text-xs font-bold text-gray-500",
                                                ),
                                            ),
                                            class_name=rx.cond(
                                                ThemeState.is_dark,
                                                "bg-[#161926]",
                                                "bg-gray-50",
                                            ),
                                        )
                                    ),
                                    rx.el.tbody(
                                        rx.foreach(
                                            LeagueDetailState.modal_standings,
                                            standing_row,
                                        )
                                    ),
                                    class_name="w-full table-auto",
                                ),
                                class_name=rx.cond(
                                    ThemeState.is_dark,
                                    "overflow-x-auto border border-gray-800 rounded-xl",
                                    "overflow-x-auto border border-gray-200 rounded-xl",
                                ),
                            ),
                            class_name="mb-6",
                        ),
                        rx.el.div(
                            rx.el.h3(
                                "Recent Matchups",
                                class_name=rx.cond(
                                    ThemeState.is_dark,
                                    "text-lg font-bold text-gray-200 mb-3",
                                    "text-lg font-bold text-gray-800 mb-3",
                                ),
                            ),
                            rx.cond(
                                LeagueDetailState.modal_recent_matchups.length() > 0,
                                rx.el.div(
                                    rx.foreach(
                                        LeagueDetailState.modal_recent_matchups,
                                        matchup_card,
                                    ),
                                    class_name="grid grid-cols-1 md:grid-cols-2 gap-4",
                                ),
                                rx.el.p(
                                    "No matchup data available.",
                                    class_name=rx.cond(
                                        ThemeState.is_dark,
                                        "text-gray-500 text-sm italic",
                                        "text-gray-500 text-sm italic",
                                    ),
                                ),
                            ),
                            class_name="mb-6",
                        ),
                        rx.el.div(
                            rx.el.h3(
                                "Roster Settings",
                                class_name=rx.cond(
                                    ThemeState.is_dark,
                                    "text-lg font-bold text-gray-200 mb-3",
                                    "text-lg font-bold text-gray-800 mb-3",
                                ),
                            ),
                            rx.cond(
                                LeagueDetailState.modal_roster_positions.length() > 0,
                                rx.el.div(
                                    rx.foreach(
                                        LeagueDetailState.modal_roster_positions,
                                        lambda pos: rx.el.span(
                                            pos,
                                            class_name=rx.cond(
                                                ThemeState.is_dark,
                                                "px-2 py-1 bg-gray-800 text-gray-300 text-xs font-bold rounded-md",
                                                "px-2 py-1 bg-gray-100 text-gray-700 text-xs font-bold rounded-md",
                                            ),
                                        ),
                                    ),
                                    class_name="flex flex-wrap gap-2",
                                ),
                                rx.el.p(
                                    "No roster info.",
                                    class_name="text-gray-500 text-sm",
                                ),
                            ),
                        ),
                    ),
                ),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#1C2033] rounded-2xl shadow-2xl p-6 w-full max-w-4xl max-h-[85vh] overflow-y-auto z-50 text-white",
                    "fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-2xl p-6 w-full max-w-4xl max-h-[85vh] overflow-y-auto z-50 text-gray-900",
                ),
            ),
        ),
        open=LeagueDetailState.show_modal,
        on_open_change=lambda _: LeagueDetailState.close_league_modal(),
    )