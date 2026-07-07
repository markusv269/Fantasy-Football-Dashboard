import reflex as rx
from app.states.draft_state import DraftState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


def stat_card(
    title: str, value: rx.Var, icon_name: str, color: str
) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(
                    title,
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                rx.heading(value, size="7", weight="bold"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.icon(icon_name, size=32, color=color),
            width="100%",
            align="center",
        ),
        size="3",
        width="100%",
    )


def draft_filter_tab(label: str) -> rx.Component:
    return rx.button(
        label,
        on_click=DraftState.set_draft_filter(label),
        variant=rx.cond(DraftState.draft_filter == label, "solid", "soft"),
        color_scheme=rx.cond(DraftState.draft_filter == label, "red", "gray"),
        size="2",
        radius="full",
    )


def upcoming_draft_card(draft: dict) -> rx.Component:
    is_scheduled = draft["start_time"].to(int) > 0
    return rx.link(
        rx.card(
            rx.vstack(
                rx.heading(
                    draft["league_name"].to(str),
                    size="4",
                    weight="bold",
                    class_name="line-clamp-1",
                ),
                rx.hstack(
                    rx.badge(
                        draft["status"].to(str).upper(),
                        color_scheme=rx.match(
                            draft["status"].to(str),
                            ("pre_draft", "yellow"),
                            ("drafting", "green"),
                            ("paused", "orange"),
                            "gray",
                        ),
                        variant="soft",
                    ),
                    rx.badge(
                        draft["draft_type"].to(str).title(),
                        color_scheme=rx.cond(
                            draft["draft_type"].to(str) == "linear",
                            "blue",
                            "purple",
                        ),
                        variant="soft",
                    ),
                    rx.cond(
                        draft["is_idp"].to(bool),
                        rx.badge("IDP", color_scheme="red", variant="soft"),
                    ),
                    rx.cond(
                        draft["is_bestball"].to(bool),
                        rx.badge("BB", color_scheme="orange", variant="soft"),
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.hstack(
                    rx.icon(
                        rx.cond(is_scheduled, "calendar", "clock"),
                        size=16,
                        color="gray",
                    ),
                    rx.text(
                        rx.cond(
                            is_scheduled,
                            draft["start_date_str"].to(str),
                            "TBD",
                        ),
                        size="2",
                        weight="medium",
                        class_name=rx.cond(
                            is_scheduled,
                            TEXT_PRIMARY,
                            "italic " + TEXT_SECONDARY,
                        ),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.badge(
                        f"{draft['rounds'].to(str)} Rounds",
                        color_scheme="gray",
                        variant="soft",
                    ),
                    rx.badge(
                        f"{draft['teams'].to(str)} Teams",
                        color_scheme="gray",
                        variant="soft",
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="3",
                align="stretch",
                width="100%",
            ),
            size="3",
            width="100%",
            class_name=rx.cond(
                is_scheduled,
                "border-l-4 border-l-emerald-400 hover:shadow-md transition-shadow",
                "border-l-4 border-l-gray-300 border-dashed hover:shadow-md transition-shadow",
            ),
        ),
        href=f"https://sleeper.com/draft/nfl/{draft['draft_id'].to(str)}",
        is_external=True,
        underline="none",
        width="100%",
    )


def historical_draft_row(draft: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.vstack(
                rx.text(
                    draft["league_name"].to(str),
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.text(
                    f"Season {draft['season'].to(str)}",
                    size="1",
                    class_name=TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
            ),
        ),
        rx.table.cell(
            rx.badge(
                draft["draft_type"].to(str),
                color_scheme=rx.match(
                    draft["draft_type"].to(str),
                    ("Linear", "blue"),
                    ("Snake", "purple"),
                    ("Auction", "orange"),
                    "gray",
                ),
                variant="soft",
            ),
        ),
        rx.table.cell(
            rx.cond(
                draft["league_type"].to(str) != "",
                rx.badge(
                    draft["league_type"].to(str).title(),
                    color_scheme="gray",
                    variant="soft",
                ),
                rx.text(""),
            ),
        ),
        rx.table.cell(
            rx.text(
                draft["start_date_str"].to(str),
                size="2",
                weight="medium",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.link(
                rx.button(
                    "View",
                    size="1",
                    variant="soft",
                    color_scheme="green",
                ),
                href=f"https://sleeper.com/draft/nfl/{draft['draft_id'].to(str)}",
                is_external=True,
                underline="none",
            ),
        ),
    )


def drafts_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("calendar-days", size=28, color="#10B981"),
                    rx.heading("Draft Center", size="7", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Overview of all upcoming 2026 drafts and past 2025 results.",
                    size="3",
                    color_scheme="gray",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.grid(
                stat_card(
                    "Total 2026 Drafts",
                    DraftState.upcoming_drafts.length().to_string(),
                    "list",
                    "#10B981",
                ),
                stat_card(
                    "Scheduled",
                    DraftState.scheduled_count.to_string(),
                    "calendar-check",
                    "#3B82F6",
                ),
                stat_card(
                    "Unscheduled",
                    DraftState.unscheduled_count.to_string(),
                    "clock",
                    "#F59E0B",
                ),
                stat_card(
                    "Completed 2025",
                    DraftState.historical_drafts.length().to_string(),
                    "circle-check",
                    "#6B7280",
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                spacing="4",
                width="100%",
            ),
            rx.card(
                rx.hstack(
                    draft_filter_tab("All"),
                    draft_filter_tab("Scheduled"),
                    draft_filter_tab("Unscheduled"),
                    draft_filter_tab("Dynasty"),
                    draft_filter_tab("Redraft"),
                    draft_filter_tab("IDP"),
                    spacing="2",
                    wrap="wrap",
                ),
                size="2",
                width="100%",
            ),
            rx.vstack(
                rx.heading("Upcoming Drafts (2026)", size="6", weight="bold"),
                rx.text(
                    "2026 Season — Dynasty & Redraft Rookie Drafts",
                    size="2",
                    color_scheme="gray",
                ),
                rx.cond(
                    DraftState.is_loading,
                    rx.center(
                        rx.spinner(size="3"),
                        padding_y="80px",
                        width="100%",
                    ),
                    rx.cond(
                        DraftState.filtered_upcoming.length() > 0,
                        rx.grid(
                            rx.foreach(
                                DraftState.filtered_upcoming,
                                upcoming_draft_card,
                            ),
                            columns=rx.breakpoints(initial="1", md="2", xl="3"),
                            spacing="4",
                            width="100%",
                        ),
                        rx.card(
                            rx.vstack(
                                rx.icon("ghost", size=40, color="gray"),
                                rx.heading(
                                    "No Drafts Found",
                                    size="4",
                                    weight="bold",
                                ),
                                spacing="2",
                                align="center",
                                padding="48px",
                                width="100%",
                            ),
                            class_name="border-dashed",
                            width="100%",
                        ),
                    ),
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "Completed Drafts (2025)", size="6", weight="bold"
                    ),
                    rx.spacer(),
                    rx.button(
                        rx.cond(
                            DraftState.show_all_historical,
                            "Show Less",
                            "Show All",
                        ),
                        on_click=DraftState.toggle_historical,
                        variant="ghost",
                        color_scheme="green",
                        size="2",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("League"),
                                rx.table.column_header_cell("Type"),
                                rx.table.column_header_cell("Format"),
                                rx.table.column_header_cell("Completed"),
                                rx.table.column_header_cell("Board"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                rx.cond(
                                    DraftState.show_all_historical,
                                    DraftState.historical_drafts,
                                    DraftState.historical_drafts[:12],
                                ),
                                historical_draft_row,
                            )
                        ),
                        variant="surface",
                        size="2",
                    ),
                    width="100%",
                    overflow_x="auto",
                    border_radius="12px",
                    class_name="border "
                    + t("border-gray-800", "border-gray-200"),
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
