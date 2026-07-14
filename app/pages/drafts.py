import reflex as rx
from app.states.draft_state import DraftState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout
from app.avatar_utils import league_avatar_image


def _stat_card(
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
            rx.icon(icon_name, size=28, color=color),
            width="100%",
            align="center",
        ),
        size="3",
        width="100%",
    )


def _filter_tab(label: str) -> rx.Component:
    return rx.button(
        label,
        on_click=DraftState.set_draft_filter(label),
        variant=rx.cond(DraftState.draft_filter == label, "solid", "soft"),
        color_scheme=rx.cond(DraftState.draft_filter == label, "red", "gray"),
        size="2",
        radius="full",
    )


def _type_badges(draft: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.badge(
            draft["draft_type"].to(str),
            color_scheme="purple",
            variant="soft",
            size="1",
        ),
        rx.cond(
            draft["is_dynasty"].to(bool),
            rx.badge(
                "Dynasty", color_scheme="purple", variant="soft", size="1"
            ),
        ),
        rx.cond(
            draft["is_redraft"].to(bool),
            rx.badge("Redraft", color_scheme="blue", variant="soft", size="1"),
        ),
        rx.cond(
            draft["is_idp"].to(bool),
            rx.badge("IDP", color_scheme="red", variant="soft", size="1"),
        ),
        rx.cond(
            draft["is_bestball"].to(bool),
            rx.badge(
                "Bestball", color_scheme="orange", variant="soft", size="1"
            ),
        ),
        spacing="2",
        align="center",
        wrap="wrap",
    )


def _active_draft_card(draft: rx.Var) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                league_avatar_image(draft["league_avatar"], size="52px"),
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            draft["league_name"].to(str),
                            size="5",
                            weight="bold",
                            class_name="line-clamp-1 " + TEXT_PRIMARY,
                        ),
                        rx.badge(
                            rx.hstack(
                                rx.box(
                                    class_name="w-2 h-2 rounded-full bg-white animate-pulse",
                                ),
                                rx.text(
                                    draft["status_label"].to(str),
                                    size="1",
                                    weight="bold",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            color_scheme="red",
                            variant="solid",
                            size="2",
                        ),
                        spacing="3",
                        align="center",
                        wrap="wrap",
                    ),
                    _type_badges(draft),
                    spacing="2",
                    align="start",
                    flex="1",
                    min_width="0",
                ),
                rx.spacer(),
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=14),
                        "Sleeper Board",
                        size="2",
                        style={"background_color": "#DC2626"},
                    ),
                    href=draft["url"].to(str),
                    is_external=True,
                    underline="none",
                ),
                spacing="3",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Fortschritt",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.spacer(),
                    rx.text(
                        f"{draft['progress_str']} · {draft['progress_pct']}%",
                        size="2",
                        weight="bold",
                        class_name="text-[#DC2626] tabular-nums",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.box(
                    rx.box(
                        class_name="h-full rounded-full bg-[#DC2626] transition-all duration-500",
                        style={"width": f"{draft['progress_pct']}%"},
                    ),
                    class_name="h-2 w-full rounded-full overflow-hidden "
                    + t("bg-white/10", "bg-gray-200"),
                ),
                spacing="1",
                width="100%",
                align="stretch",
            ),
            rx.grid(
                rx.vstack(
                    rx.hstack(
                        rx.icon("history", size=14, color="#94A3B8"),
                        rx.text(
                            "Letzter Pick",
                            size="1",
                            weight="bold",
                            class_name="uppercase tracking-wide "
                            + TEXT_SECONDARY,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        draft["last_pick_no"].to(int) > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.badge(
                                    f"Pick {draft['last_pick_no']}",
                                    color_scheme="gray",
                                    variant="soft",
                                    size="1",
                                ),
                                rx.badge(
                                    f"Runde {draft['last_round']}",
                                    color_scheme="gray",
                                    variant="soft",
                                    size="1",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.text(
                                draft["last_player_name"].to(str),
                                size="3",
                                weight="bold",
                                class_name=TEXT_PRIMARY,
                            ),
                            rx.hstack(
                                rx.cond(
                                    draft["last_player_pos"].to(str) != "",
                                    rx.badge(
                                        draft["last_player_pos"].to(str),
                                        color_scheme="red",
                                        variant="soft",
                                        size="1",
                                    ),
                                ),
                                rx.cond(
                                    draft["last_player_team"].to(str) != "",
                                    rx.text(
                                        draft["last_player_team"].to(str),
                                        size="1",
                                        weight="medium",
                                        class_name=TEXT_SECONDARY,
                                    ),
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.cond(
                                draft["last_picked_by_manager"].to(str) != "",
                                rx.hstack(
                                    rx.icon(
                                        "user-round",
                                        size=12,
                                        color="#94A3B8",
                                    ),
                                    rx.text(
                                        "von",
                                        size="1",
                                        class_name=TEXT_SECONDARY,
                                    ),
                                    rx.text(
                                        draft["last_picked_by_team"].to(str),
                                        size="1",
                                        weight="bold",
                                        class_name=TEXT_PRIMARY,
                                    ),
                                    rx.cond(
                                        (
                                            draft["last_picked_by_manager"].to(
                                                str
                                            )
                                            != draft["last_picked_by_team"].to(
                                                str
                                            )
                                        )
                                        & (
                                            draft["last_picked_by_manager"].to(
                                                str
                                            )
                                            != ""
                                        ),
                                        rx.text(
                                            "("
                                            + draft[
                                                "last_picked_by_manager"
                                            ].to(str)
                                            + ")",
                                            size="1",
                                            class_name=TEXT_SECONDARY,
                                        ),
                                    ),
                                    spacing="1",
                                    align="center",
                                    wrap="wrap",
                                ),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.text(
                            "Noch keine Picks",
                            size="2",
                            class_name="italic " + TEXT_SECONDARY,
                        ),
                    ),
                    spacing="2",
                    align="start",
                    padding="14px",
                    border_radius="10px",
                    height="100%",
                    class_name="border "
                    + t(
                        "bg-[#08090D] border-white/5",
                        "bg-gray-50 border-gray-200",
                    ),
                ),
                rx.vstack(
                    rx.hstack(
                        rx.icon("circle_arrow_right", size=14, color="#DC2626"),
                        rx.text(
                            "Als Nächstes",
                            size="1",
                            weight="bold",
                            class_name="uppercase tracking-wide "
                            + TEXT_SECONDARY,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.cond(
                        draft["next_pick_no"].to(int) > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.badge(
                                    f"Pick {draft['next_pick_no']}",
                                    color_scheme="red",
                                    variant="solid",
                                    size="1",
                                ),
                                rx.badge(
                                    f"Runde {draft['next_round']}",
                                    color_scheme="red",
                                    variant="soft",
                                    size="1",
                                ),
                                rx.cond(
                                    draft["next_slot"].to(int) > 0,
                                    rx.badge(
                                        f"Slot {draft['next_slot']}",
                                        color_scheme="gray",
                                        variant="soft",
                                        size="1",
                                    ),
                                ),
                                spacing="2",
                                align="center",
                                wrap="wrap",
                            ),
                            rx.cond(
                                draft["next_team_name"].to(str) != "",
                                rx.vstack(
                                    rx.text(
                                        draft["next_team_name"].to(str),
                                        size="3",
                                        weight="bold",
                                        class_name=TEXT_PRIMARY,
                                    ),
                                    rx.cond(
                                        draft["next_manager_name"].to(str)
                                        != "",
                                        rx.text(
                                            draft["next_manager_name"].to(str),
                                            size="1",
                                            weight="medium",
                                            class_name=TEXT_SECONDARY,
                                        ),
                                    ),
                                    spacing="0",
                                    align="start",
                                ),
                                rx.cond(
                                    draft["next_roster_id"].to(int) > 0,
                                    rx.text(
                                        f"Roster #{draft['next_roster_id']}",
                                        size="2",
                                        weight="medium",
                                        class_name=TEXT_SECONDARY,
                                    ),
                                    rx.text(
                                        "Unbekannt",
                                        size="2",
                                        class_name="italic " + TEXT_SECONDARY,
                                    ),
                                ),
                            ),
                            spacing="1",
                            align="start",
                        ),
                        rx.text(
                            "Draft abgeschlossen",
                            size="2",
                            class_name="italic " + TEXT_SECONDARY,
                        ),
                    ),
                    spacing="2",
                    align="start",
                    padding="14px",
                    border_radius="10px",
                    height="100%",
                    class_name="border "
                    + t(
                        "bg-[#DC2626]/5 border-[#DC2626]/30",
                        "bg-red-50 border-red-200",
                    ),
                ),
                rx.vstack(
                    rx.hstack(
                        rx.icon("bar-chart-3", size=14, color="#94A3B8"),
                        rx.text(
                            "Details",
                            size="1",
                            weight="bold",
                            class_name="uppercase tracking-wide "
                            + TEXT_SECONDARY,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.text("Saison", size="1", class_name=TEXT_SECONDARY),
                        rx.spacer(),
                        rx.text(
                            draft["season"].to(str),
                            size="2",
                            weight="bold",
                            class_name=TEXT_PRIMARY,
                        ),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text("Runden", size="1", class_name=TEXT_SECONDARY),
                        rx.spacer(),
                        rx.text(
                            draft["rounds"].to(str),
                            size="2",
                            weight="bold",
                            class_name=TEXT_PRIMARY,
                        ),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text("Teams", size="1", class_name=TEXT_SECONDARY),
                        rx.spacer(),
                        rx.text(
                            draft["teams"].to(str),
                            size="2",
                            weight="bold",
                            class_name=TEXT_PRIMARY,
                        ),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text("Picks", size="1", class_name=TEXT_SECONDARY),
                        rx.spacer(),
                        rx.text(
                            f"{draft['total_picks']} / {draft['total_slots']}",
                            size="2",
                            weight="bold",
                            class_name=TEXT_PRIMARY,
                        ),
                        width="100%",
                    ),
                    spacing="1",
                    align="stretch",
                    padding="14px",
                    border_radius="10px",
                    height="100%",
                    width="100%",
                    class_name="border "
                    + t(
                        "bg-[#08090D] border-white/5",
                        "bg-gray-50 border-gray-200",
                    ),
                ),
                columns=rx.breakpoints(initial="1", md="3"),
                spacing="3",
                width="100%",
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _scheduled_draft_card(draft: rx.Var) -> rx.Component:
    is_scheduled = draft["start_time_ts"].to(int) > 0
    return rx.link(
        rx.card(
            rx.vstack(
                rx.hstack(
                    league_avatar_image(draft["league_avatar"], size="36px"),
                    rx.heading(
                        draft["league_name"].to(str),
                        size="4",
                        weight="bold",
                        class_name="line-clamp-1 flex-1 min-w-0 "
                        + TEXT_PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                _type_badges(draft),
                rx.hstack(
                    rx.icon(
                        rx.cond(is_scheduled, "calendar", "clock"),
                        size=16,
                        color="#DC2626",
                    ),
                    rx.text(
                        rx.cond(
                            is_scheduled,
                            draft["start_date_str"].to(str),
                            "Termin offen",
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
                        f"Saison {draft['season']}",
                        color_scheme="gray",
                        variant="soft",
                        size="1",
                    ),
                    rx.badge(
                        draft["status_label"].to(str),
                        color_scheme="yellow",
                        variant="soft",
                        size="1",
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            size="2",
            width="100%",
            class_name=rx.cond(
                is_scheduled,
                "border-l-4 border-l-amber-400 hover:border-l-[#DC2626] transition-all cursor-pointer",
                "border-l-4 border-l-gray-400 border-dashed hover:border-l-[#DC2626] transition-all cursor-pointer",
            ),
        ),
        href=draft["url"].to(str),
        is_external=True,
        underline="none",
        width="100%",
    )


def _completed_row(draft: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                league_avatar_image(draft["league_avatar"], size="28px"),
                rx.vstack(
                    rx.text(
                        draft["league_name"].to(str),
                        size="2",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    rx.text(
                        f"Saison {draft['season']}",
                        size="1",
                        class_name=TEXT_SECONDARY,
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.badge(
                draft["draft_type"].to(str),
                color_scheme="purple",
                variant="soft",
                size="1",
            ),
        ),
        rx.table.cell(
            rx.cond(
                draft["league_type"].to(str) != "",
                rx.badge(
                    draft["league_type"].to(str).title(),
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                rx.text("—", size="1", class_name=TEXT_SECONDARY),
            ),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(
                    draft["start_date_str"].to(str) != "",
                    draft["start_date_str"].to(str),
                    "—",
                ),
                size="2",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.link(
                rx.button(
                    "Board",
                    rx.icon("external-link", size=12),
                    size="1",
                    variant="soft",
                    color_scheme="red",
                ),
                href=draft["url"].to(str),
                is_external=True,
                underline="none",
            ),
        ),
    )


def _other_row(draft: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                league_avatar_image(draft["league_avatar"], size="24px"),
                rx.text(
                    draft["league_name"].to(str),
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.badge(
                draft["status_label"].to(str),
                color_scheme="gray",
                variant="soft",
                size="1",
            ),
        ),
        rx.table.cell(
            rx.text(
                draft["season"].to(str),
                size="2",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.link(
                rx.button(
                    "Board",
                    size="1",
                    variant="soft",
                    color_scheme="gray",
                ),
                href=draft["url"].to(str),
                is_external=True,
                underline="none",
            ),
        ),
    )


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("file-text", size=28, color="#DC2626"),
                rx.heading("Draft Center", size="7", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"{DraftState.total_count} Drafts",
                    color_scheme="red",
                    variant="solid",
                    size="2",
                ),
                spacing="3",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.text(
                "Live-Übersicht aller Stoned Lack Drafts — aktive Boards, "
                "kommende Termine und die komplette Historie seit 2021.",
                size="3",
                color_scheme="gray",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _stats_bar() -> rx.Component:
    return rx.grid(
        _stat_card(
            "Aktive Drafts",
            DraftState.active_count.to_string(),
            "radio",
            "#DC2626",
        ),
        _stat_card(
            "Geplante Drafts",
            DraftState.scheduled_count.to_string(),
            "calendar-check",
            "#F59E0B",
        ),
        _stat_card(
            "Abgeschlossen (alle Saisons)",
            DraftState.completed_count.to_string(),
            "circle-check",
            "#10B981",
        ),
        _stat_card(
            "Drafts gesamt",
            DraftState.total_count.to_string(),
            "list",
            "#3B82F6",
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="4"),
        spacing="4",
        width="100%",
    )


def _season_pill(item: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(
            item["season"].to(str),
            size="1",
            weight="bold",
            class_name=TEXT_PRIMARY,
        ),
        rx.badge(
            item["count"].to_string(),
            color_scheme="red",
            variant="soft",
            size="1",
        ),
        spacing="2",
        align="center",
        padding_x="10px",
        padding_y="4px",
        border_radius="9999px",
        class_name="border "
        + t(
            "bg-[#08090D] border-white/5",
            "bg-gray-50 border-gray-200",
        ),
    )


def _season_breakdown() -> rx.Component:
    return rx.cond(
        DraftState.season_breakdown.length() > 0,
        rx.card(
            rx.hstack(
                rx.icon("layers", size=18, color="#DC2626"),
                rx.text(
                    "Drafts pro Saison",
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.hstack(
                    rx.foreach(DraftState.season_breakdown, _season_pill),
                    spacing="2",
                    wrap="wrap",
                ),
                width="100%",
                align="center",
                wrap="wrap",
                spacing="3",
            ),
            size="2",
            width="100%",
        ),
    )


def _filter_bar() -> rx.Component:
    return rx.card(
        rx.hstack(
            _filter_tab("All"),
            _filter_tab("Active"),
            _filter_tab("Scheduled"),
            _filter_tab("Completed"),
            _filter_tab("Dynasty"),
            _filter_tab("Redraft"),
            _filter_tab("IDP"),
            _filter_tab("Bestball"),
            spacing="2",
            wrap="wrap",
        ),
        size="2",
        width="100%",
    )


def _active_section() -> rx.Component:
    return rx.cond(
        DraftState.filtered_active.length() > 0,
        rx.vstack(
            rx.hstack(
                rx.icon("radio", size=22, color="#DC2626"),
                rx.heading("Aktive Drafts", size="5", weight="bold"),
                rx.badge(
                    DraftState.filtered_active.length().to_string(),
                    color_scheme="red",
                    variant="solid",
                    size="1",
                ),
                spacing="2",
                align="center",
            ),
            rx.vstack(
                rx.foreach(DraftState.filtered_active, _active_draft_card),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
    )


def _scheduled_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("calendar-check", size=22, color="#F59E0B"),
            rx.heading("Geplante Drafts", size="5", weight="bold"),
            rx.badge(
                DraftState.filtered_scheduled.length().to_string(),
                color_scheme="orange",
                variant="soft",
                size="1",
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            DraftState.filtered_scheduled.length() > 0,
            rx.grid(
                rx.foreach(
                    DraftState.filtered_scheduled, _scheduled_draft_card
                ),
                columns=rx.breakpoints(initial="1", md="2", xl="3"),
                spacing="4",
                width="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.icon("calendar-x", size=32, color="gray"),
                    rx.text(
                        "Keine geplanten Drafts.",
                        size="2",
                        color_scheme="gray",
                        class_name="italic",
                    ),
                    spacing="2",
                    align="center",
                    padding="32px",
                    width="100%",
                ),
                class_name="border-dashed",
                width="100%",
            ),
        ),
        spacing="3",
        width="100%",
        align="stretch",
    )


def _completed_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("circle-check", size=22, color="#10B981"),
            rx.heading(
                "Abgeschlossene Drafts (alle Saisons)",
                size="5",
                weight="bold",
            ),
            rx.badge(
                DraftState.filtered_completed.length().to_string(),
                color_scheme="green",
                variant="soft",
                size="1",
            ),
            rx.spacer(),
            rx.cond(
                DraftState.filtered_completed.length() > 12,
                rx.button(
                    rx.cond(
                        DraftState.show_all_completed,
                        "Weniger anzeigen",
                        "Alle anzeigen",
                    ),
                    on_click=DraftState.toggle_completed,
                    variant="ghost",
                    color_scheme="gray",
                    size="2",
                ),
            ),
            width="100%",
            align="center",
        ),
        rx.cond(
            DraftState.filtered_completed.length() > 0,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Liga"),
                            rx.table.column_header_cell("Format"),
                            rx.table.column_header_cell("Typ"),
                            rx.table.column_header_cell("Datum"),
                            rx.table.column_header_cell("Board"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            rx.cond(
                                DraftState.show_all_completed,
                                DraftState.filtered_completed,
                                DraftState.filtered_completed[:12],
                            ),
                            _completed_row,
                        )
                    ),
                    variant="surface",
                    size="2",
                ),
                width="100%",
                overflow_x="auto",
                border_radius="12px",
                class_name="border " + t("border-gray-800", "border-gray-200"),
            ),
            rx.card(
                rx.text(
                    "Keine abgeschlossenen Drafts gefunden.",
                    size="2",
                    color_scheme="gray",
                    class_name="italic",
                ),
                padding="32px",
                class_name="border-dashed",
                width="100%",
            ),
        ),
        spacing="3",
        width="100%",
        align="stretch",
    )


def _other_section() -> rx.Component:
    return rx.cond(
        DraftState.filtered_other.length() > 0,
        rx.vstack(
            rx.hstack(
                rx.icon("gallery_horizontal", size=22, color="#94A3B8"),
                rx.heading("Weitere Drafts", size="5", weight="bold"),
                rx.badge(
                    DraftState.filtered_other.length().to_string(),
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                spacing="2",
                align="center",
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Liga"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("Saison"),
                            rx.table.column_header_cell("Board"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(DraftState.filtered_other, _other_row)
                    ),
                    variant="surface",
                    size="2",
                ),
                width="100%",
                overflow_x="auto",
                border_radius="12px",
                class_name="border " + t("border-gray-800", "border-gray-200"),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
    )


def _loading_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Lade Drafts…", size="2", color_scheme="gray"),
            spacing="3",
            align="center",
        ),
        padding_y="80px",
        width="100%",
    )


def drafts_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            _stats_bar(),
            _season_breakdown(),
            rx.cond(
                DraftState.is_loading,
                _loading_state(),
                rx.vstack(
                    _active_section(),
                    _filter_bar(),
                    _scheduled_section(),
                    _completed_section(),
                    _other_section(),
                    spacing="6",
                    width="100%",
                    align="stretch",
                ),
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
