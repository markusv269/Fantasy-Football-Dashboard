import reflex as rx
from app.states.draft_state import DraftState
from app.states.theme_state import ThemeState
from app.theme import (
    t,
    CARD,
    H1,
    H2,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BTN_PRIMARY,
    BADGE_SUBTLE,
    TABLE_CONTAINER,
    TABLE_HEADER_ROW,
    TABLE_HEADER_CELL,
    TABLE_ROW,
    EMPTY_STATE,
)
from app.components.layout import layout


def stat_card(
    title: str, value: rx.Var, icon_name: str, color_class: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    title,
                    class_name=t(
                        "text-sm font-bold text-gray-400 uppercase tracking-wide",
                        "text-sm font-bold text-gray-500 uppercase tracking-wide",
                    ),
                ),
                rx.el.span(
                    value,
                    class_name=t(
                        "text-3xl font-bold text-white mt-1 block",
                        "text-3xl font-bold text-gray-900 mt-1 block",
                    ),
                ),
            ),
            rx.el.div(
                rx.icon(icon_name, class_name=f"w-8 h-8 {color_class}"),
                class_name=f"p-3 rounded-xl {color_class.replace('text-', 'bg-').replace('500', '100').replace('600', '100')}",
            ),
            class_name="flex justify-between items-start",
        ),
        class_name=t(
            "bg-[#1C2033] p-6 rounded-2xl border border-gray-800 shadow-sm",
            "bg-white p-6 rounded-2xl border border-gray-200 shadow-sm",
        ),
    )


def draft_filter_tab(label: str) -> rx.Component:
    return rx.el.button(
        label,
        on_click=DraftState.set_draft_filter(label),
        class_name=rx.cond(
            DraftState.draft_filter == label,
            "px-4 py-2 rounded-full text-sm font-bold bg-[#DC2626]/20 text-[#DC2626] transition-colors shadow-sm",
            t(
                "px-4 py-2 rounded-full text-sm font-semibold bg-[#1C2033] text-gray-400 border border-gray-800 hover:bg-gray-800 transition-colors",
                "px-4 py-2 rounded-full text-sm font-semibold bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 transition-colors",
            ),
        ),
    )


def upcoming_draft_card(draft: dict) -> rx.Component:
    is_scheduled = draft["start_time"].to(int) > 0
    return rx.el.a(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    draft["league_name"].to(str),
                    class_name=t(
                        "font-bold text-lg text-white line-clamp-1",
                        "font-bold text-lg text-gray-900 line-clamp-1",
                    ),
                ),
                rx.el.div(
                    rx.el.span(
                        draft["status"].to(str).upper(),
                        class_name=rx.match(
                            draft["status"].to(str),
                            (
                                "pre_draft",
                                "bg-yellow-100 text-yellow-800 px-2 py-1 rounded-md text-xs font-bold",
                            ),
                            (
                                "drafting",
                                "bg-emerald-100 text-emerald-800 px-2 py-1 rounded-md text-xs font-bold animate-pulse",
                            ),
                            (
                                "paused",
                                "bg-orange-100 text-orange-800 px-2 py-1 rounded-md text-xs font-bold",
                            ),
                            "bg-gray-100 text-gray-700 px-2 py-1 rounded-md text-xs font-bold",
                        ),
                    ),
                    rx.el.span(
                        draft["draft_type"].to(str).title(),
                        class_name=rx.cond(
                            draft["draft_type"].to(str) == "linear",
                            "bg-blue-100 text-blue-700 px-2 py-1 rounded-md text-xs font-bold ml-2",
                            "bg-purple-100 text-purple-700 px-2 py-1 rounded-md text-xs font-bold ml-2",
                        ),
                    ),
                    rx.cond(
                        draft["is_idp"].to(bool),
                        rx.el.span(
                            "IDP",
                            class_name="bg-red-100 text-red-700 px-2 py-1 rounded-md text-xs font-bold ml-2",
                        ),
                    ),
                    rx.cond(
                        draft["is_bestball"].to(bool),
                        rx.el.span(
                            "BB",
                            class_name="bg-orange-100 text-orange-700 px-2 py-1 rounded-md text-xs font-bold ml-2",
                        ),
                    ),
                    class_name="flex items-center mt-2",
                ),
                class_name="flex-1",
            )
        ),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    rx.cond(is_scheduled, "calendar", "clock"),
                    class_name="w-4 h-4 mr-2 text-gray-400",
                ),
                rx.el.span(
                    rx.cond(is_scheduled, draft["start_date_str"].to(str), "TBD"),
                    class_name=rx.cond(
                        is_scheduled,
                        t(
                            "text-sm font-semibold text-gray-300",
                            "text-sm font-semibold text-gray-700",
                        ),
                        t(
                            "text-sm font-bold text-gray-500 italic",
                            "text-sm font-bold text-gray-500 italic",
                        ),
                    ),
                ),
                class_name="flex items-center mt-4 mb-4",
            ),
            rx.el.div(
                rx.el.span(
                    f"{draft['rounds'].to(str)} Rounds",
                    class_name=BADGE_SUBTLE + " mr-2",
                ),
                rx.el.span(f"{draft['teams'].to(str)} Teams", class_name=BADGE_SUBTLE),
                class_name="flex items-center",
            ),
        ),
        href=f"https://sleeper.com/draft/nfl/{draft['draft_id'].to(str)}",
        target="_blank",
        class_name=rx.cond(
            is_scheduled,
            t(
                "bg-[#1C2033] p-5 rounded-2xl shadow-sm border border-gray-800 border-l-4 border-l-emerald-400 hover:shadow-md transition-shadow block",
                "bg-white p-5 rounded-2xl shadow-sm border border-gray-200 border-l-4 border-l-emerald-400 hover:shadow-md transition-shadow block",
            ),
            t(
                "bg-[#1C2033] p-5 rounded-2xl shadow-sm border border-gray-800 border-l-4 border-l-gray-600 border-dashed hover:shadow-md transition-shadow block",
                "bg-white p-5 rounded-2xl shadow-sm border border-gray-200 border-l-4 border-l-gray-300 border-dashed hover:shadow-md transition-shadow block",
            ),
        ),
    )


def historical_draft_row(draft: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.span(
                    draft["league_name"].to(str),
                    class_name=t(
                        "font-bold text-white block", "font-bold text-gray-900 block"
                    ),
                ),
                rx.el.span(
                    f"Season {draft['season'].to(str)}",
                    class_name=t(
                        "text-xs text-gray-400 font-medium",
                        "text-xs text-gray-500 font-medium",
                    ),
                ),
            ),
            class_name="p-4 whitespace-nowrap",
        ),
        rx.el.td(
            rx.el.span(
                draft["draft_type"].to(str),
                class_name=rx.match(
                    draft["draft_type"].to(str),
                    (
                        "Linear",
                        "bg-blue-100 text-blue-700 px-2.5 py-1 rounded-md text-xs font-bold",
                    ),
                    (
                        "Snake",
                        "bg-purple-100 text-purple-700 px-2.5 py-1 rounded-md text-xs font-bold",
                    ),
                    (
                        "Auction",
                        "bg-orange-100 text-orange-700 px-2.5 py-1 rounded-md text-xs font-bold",
                    ),
                    "bg-gray-100 text-gray-700 px-2.5 py-1 rounded-md text-xs font-bold",
                ),
            ),
            class_name="p-4 whitespace-nowrap",
        ),
        rx.el.td(
            rx.cond(
                draft["league_type"].to(str) != "",
                rx.el.span(
                    draft["league_type"].to(str).title(),
                    class_name=t(
                        "bg-gray-800 border border-gray-700 text-gray-300 text-xs font-bold px-2 py-1 rounded-md",
                        "bg-gray-50 border border-gray-200 text-gray-600 text-xs font-bold px-2 py-1 rounded-md",
                    ),
                ),
                rx.el.span(""),
            ),
            class_name="p-4 whitespace-nowrap",
        ),
        rx.el.td(
            rx.el.span(
                draft["start_date_str"].to(str),
                class_name=t(
                    "text-sm text-gray-300 font-medium",
                    "text-sm text-gray-600 font-medium",
                ),
            ),
            class_name="p-4 whitespace-nowrap text-right",
        ),
        rx.el.td(
            rx.el.a(
                "View",
                href=f"https://sleeper.com/draft/nfl/{draft['draft_id'].to(str)}",
                target="_blank",
                class_name="text-xs font-bold text-emerald-500 bg-emerald-500/10 hover:bg-emerald-500/20 px-3 py-1.5 rounded-lg transition-colors",
            ),
            class_name="p-4 whitespace-nowrap text-center",
        ),
        class_name=TABLE_ROW,
    )


def drafts_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    rx.icon(
                        "calendar-days",
                        class_name="w-8 h-8 mr-3 text-emerald-600 inline",
                    ),
                    "Draft Center",
                    class_name=H1 + " flex items-center",
                ),
                rx.el.p(
                    "Overview of all upcoming 2026 drafts and past 2025 results.",
                    class_name=t(
                        "text-gray-400 font-medium", "text-gray-500 font-medium"
                    ),
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                stat_card(
                    "Total 2026 Drafts",
                    DraftState.upcoming_drafts.length().to_string(),
                    "list",
                    "text-emerald-600",
                ),
                stat_card(
                    "Scheduled",
                    DraftState.scheduled_count.to_string(),
                    "calendar-check",
                    "text-blue-500",
                ),
                stat_card(
                    "Unscheduled",
                    DraftState.unscheduled_count.to_string(),
                    "clock",
                    "text-amber-500",
                ),
                stat_card(
                    "Completed 2025",
                    DraftState.historical_drafts.length().to_string(),
                    "circle-check",
                    "text-gray-500",
                ),
                class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10",
            ),
            rx.el.div(
                rx.el.div(
                    draft_filter_tab("All"),
                    draft_filter_tab("Scheduled"),
                    draft_filter_tab("Unscheduled"),
                    draft_filter_tab("Dynasty"),
                    draft_filter_tab("Redraft"),
                    draft_filter_tab("IDP"),
                    class_name="flex flex-wrap gap-3",
                ),
                class_name=t(
                    "mb-8 bg-[#1C2033] p-4 rounded-2xl border border-gray-800 shadow-sm",
                    "mb-8 bg-white p-4 rounded-2xl border border-gray-200 shadow-sm",
                ),
            ),
            rx.el.div(
                rx.el.h2(
                    "Upcoming Drafts (2026)",
                    class_name=t(
                        "text-2xl font-bold text-white mb-2",
                        "text-2xl font-bold text-gray-800 mb-2",
                    ),
                ),
                rx.el.p(
                    "2026 Season — Dynasty & Redraft Rookie Drafts",
                    class_name=t(
                        "text-sm text-gray-400 font-medium mb-6",
                        "text-sm text-gray-500 font-medium mb-6",
                    ),
                ),
                rx.cond(
                    DraftState.is_loading,
                    rx.el.div(
                        rx.icon(
                            "loader",
                            class_name="w-8 h-8 animate-spin text-emerald-500 mx-auto",
                        ),
                        class_name="py-20 flex justify-center",
                    ),
                    rx.cond(
                        DraftState.filtered_upcoming.length() > 0,
                        rx.el.div(
                            rx.foreach(
                                DraftState.filtered_upcoming, upcoming_draft_card
                            ),
                            class_name="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6",
                        ),
                        rx.el.div(
                            rx.icon("ghost", class_name="w-12 h-12 text-gray-300 mb-4"),
                            rx.el.h3(
                                "No Drafts Found",
                                class_name=t(
                                    "text-lg font-bold text-gray-300",
                                    "text-lg font-bold text-gray-700",
                                ),
                            ),
                            class_name=EMPTY_STATE,
                        ),
                    ),
                ),
                class_name="mb-12",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Completed Drafts (2025)",
                        class_name=t(
                            "text-2xl font-bold text-gray-200 mb-2",
                            "text-2xl font-bold text-gray-800 mb-2",
                        ),
                    ),
                    rx.el.button(
                        rx.cond(
                            DraftState.show_all_historical, "Show Less", "Show All"
                        ),
                        on_click=DraftState.toggle_historical,
                        class_name="text-sm font-bold text-emerald-600 hover:text-emerald-700",
                    ),
                    class_name="flex justify-between items-center mb-6",
                ),
                rx.el.div(
                    rx.el.table(
                        rx.el.thead(
                            rx.el.tr(
                                rx.el.th(
                                    "League",
                                    class_name=t(
                                        "p-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider",
                                        "p-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider",
                                    ),
                                ),
                                rx.el.th(
                                    "Type",
                                    class_name=t(
                                        "p-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider",
                                        "p-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider",
                                    ),
                                ),
                                rx.el.th(
                                    "Format",
                                    class_name=t(
                                        "p-4 text-left text-xs font-bold text-gray-400 uppercase tracking-wider",
                                        "p-4 text-left text-xs font-bold text-gray-500 uppercase tracking-wider",
                                    ),
                                ),
                                rx.el.th(
                                    "Completed",
                                    class_name=t(
                                        "p-4 text-right text-xs font-bold text-gray-400 uppercase tracking-wider",
                                        "p-4 text-right text-xs font-bold text-gray-500 uppercase tracking-wider",
                                    ),
                                ),
                                rx.el.th(
                                    "Board",
                                    class_name=t(
                                        "p-4 text-center text-xs font-bold text-gray-400 uppercase tracking-wider",
                                        "p-4 text-center text-xs font-bold text-gray-500 uppercase tracking-wider",
                                    ),
                                ),
                                class_name=TABLE_HEADER_ROW,
                            )
                        ),
                        rx.el.tbody(
                            rx.foreach(
                                rx.cond(
                                    DraftState.show_all_historical,
                                    DraftState.historical_drafts,
                                    DraftState.historical_drafts[:12],
                                ),
                                historical_draft_row,
                            )
                        ),
                        class_name="min-w-full table-auto",
                    ),
                    class_name=TABLE_CONTAINER,
                ),
            ),
        )
    )