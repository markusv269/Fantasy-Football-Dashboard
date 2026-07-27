import reflex as rx
from app.states.adp_state import AdpState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


def _pos_color(pos: rx.Var) -> rx.Var:
    return rx.match(
        pos.to(str),
        ("QB", "red"),
        ("RB", "blue"),
        ("WR", "green"),
        ("TE", "orange"),
        ("K", "gray"),
        ("DEF", "purple"),
        ("DL", "purple"),
        ("LB", "purple"),
        ("DB", "purple"),
        ("IDP", "purple"),
        "gray",
    )


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("layout-grid", size=28, color="#DC2626"),
                rx.heading("ADP Draftboard", size="7", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"{AdpState.total_drafts} Drafts",
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
                "Durchschnittliche Draftposition aller abgeschlossenen Drafts "
                "gefiltert nach Saison und Liga-Format. Dynasty & Dynasty IDP "
                "nutzen Linear-Layout, Redraft nutzt Snake-Layout.",
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


def _format_btn(label: str, value: str, icon: str) -> rx.Component:
    is_active = AdpState.selected_format == value
    return rx.button(
        rx.hstack(
            rx.icon(icon, size=14),
            rx.text(label, size="2", weight="bold"),
            spacing="2",
            align="center",
        ),
        on_click=AdpState.set_selected_format(value),
        variant=rx.cond(is_active, "solid", "soft"),
        color_scheme=rx.cond(is_active, "red", "gray"),
        size="2",
    )


def _draft_type_btn(label: str, value: str, icon: str) -> rx.Component:
    is_active = AdpState.selected_draft_type == value
    return rx.button(
        rx.hstack(
            rx.icon(icon, size=14),
            rx.text(label, size="2", weight="bold"),
            spacing="2",
            align="center",
        ),
        on_click=AdpState.set_selected_draft_type(value),
        variant=rx.cond(is_active, "solid", "soft"),
        color_scheme=rx.cond(is_active, "red", "gray"),
        size="2",
    )


def _season_option(s: rx.Var) -> rx.Component:
    return rx.select.item(s.to(str), value=s.to(str))


def _position_option(p: rx.Var) -> rx.Component:
    return rx.select.item(p.to(str), value=p.to(str))


def _min_pick_slider() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                f"Mindestens {AdpState.min_pick_count} Picks",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
            ),
            rx.spacer(),
            rx.cond(
                AdpState.min_pick_count > 1,
                rx.button(
                    rx.icon("rotate-ccw", size=12),
                    "Reset",
                    on_click=AdpState.reset_min_pick_count,
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                ),
            ),
            width="100%",
            align="center",
        ),
        rx.el.input(
            type="range",
            min="1",
            max=AdpState.max_pick_count.to_string(),
            step="1",
            default_value=AdpState.min_pick_count.to_string(),
            key=AdpState.min_pick_reset_counter.to_string(),
            on_change=AdpState.set_min_pick_count.throttle(100),
            class_name="w-full accent-[#DC2626] cursor-pointer",
        ),
        rx.hstack(
            rx.text("1", size="1", class_name=TEXT_SECONDARY),
            rx.spacer(),
            rx.text(
                f"{AdpState.players_meeting_threshold.length()} von {AdpState.total_players} Spielern",
                size="1",
                weight="medium",
                class_name="text-[#DC2626]",
            ),
            rx.spacer(),
            rx.text(
                AdpState.max_pick_count.to_string(),
                size="1",
                class_name=TEXT_SECONDARY,
            ),
            width="100%",
            align="center",
        ),
        spacing="2",
        width="100%",
        align="stretch",
    )


def _filters() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("filter", size=18, color="#DC2626"),
                rx.heading("Filter", size="4", weight="bold"),
                rx.spacer(),
                rx.badge(
                    rx.cond(
                        AdpState.board_layout == "snake",
                        "Snake Layout",
                        "Linear Layout",
                    ),
                    color_scheme="red",
                    variant="soft",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.grid(
                rx.vstack(
                    rx.text(
                        "Saison",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.select.root(
                        rx.select.trigger(width="100%"),
                        rx.select.content(
                            rx.foreach(
                                AdpState.available_seasons, _season_option
                            ),
                        ),
                        value=AdpState.selected_season,
                        on_change=AdpState.set_selected_season,
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                rx.vstack(
                    rx.text(
                        "Liga-Format",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.hstack(
                        _format_btn("Dynasty", "dynasty", "crown"),
                        _format_btn("Dynasty IDP", "dynasty_idp", "shield"),
                        _format_btn("Redraft", "redraft", "trophy"),
                        spacing="2",
                        wrap="wrap",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                rx.vstack(
                    rx.text(
                        "Draft-Typ",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.hstack(
                        _draft_type_btn("Alle Spieler", "0", "users"),
                        _draft_type_btn("Rookies", "1", "sparkles"),
                        _draft_type_btn("Veterans", "2", "shield-check"),
                        spacing="2",
                        wrap="wrap",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                columns=rx.breakpoints(initial="1", md="2", lg="3"),
                spacing="4",
                width="100%",
            ),
            rx.divider(),
            _min_pick_slider(),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="2",
        width="100%",
    )


def _stat_card(
    label: str, value: rx.Var, icon: str, color: str
) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(
                    label,
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                rx.heading(value, size="6", weight="bold"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.icon(icon, size=28, color=color),
            width="100%",
            align="center",
        ),
        size="2",
        width="100%",
    )


def _stats() -> rx.Component:
    return rx.grid(
        _stat_card(
            "Drafts", AdpState.total_drafts.to_string(), "list", "#DC2626"
        ),
        _stat_card(
            "Picks", AdpState.total_picks.to_string(), "target", "#3B82F6"
        ),
        _stat_card(
            "Spieler", AdpState.total_players.to_string(), "users", "#10B981"
        ),
        _stat_card(
            "Runden", AdpState.total_rounds.to_string(), "layers", "#F59E0B"
        ),
        columns=rx.breakpoints(initial="2", sm="4"),
        spacing="3",
        width="100%",
    )


def _board_cell(cell: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    cell["overall_pick_rank"].to(str),
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                rx.spacer(),
                rx.text(
                    cell["pick_notation"].to(str),
                    size="1",
                    weight="bold",
                    class_name="font-mono " + TEXT_SECONDARY,
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                cell["full_name"].to(str),
                size="2",
                weight="bold",
                class_name="line-clamp-2 " + TEXT_PRIMARY,
            ),
            rx.hstack(
                rx.badge(
                    cell["positional_pick_rank"].to(str),
                    color_scheme=_pos_color(cell["position"]),
                    variant="soft",
                    size="1",
                ),
                rx.text(
                    cell["team"].to(str),
                    size="1",
                    weight="medium",
                    class_name=TEXT_SECONDARY,
                ),
                spacing="1",
                align="center",
            ),
            rx.hstack(
                rx.hstack(
                    rx.icon("trending-up", size=10, color="#DC2626"),
                    rx.text(
                        f"ADP {cell['adp_str']}",
                        size="1",
                        weight="bold",
                        class_name="text-[#DC2626]",
                    ),
                    spacing="1",
                    align="center",
                ),
                rx.spacer(),
                rx.text(
                    f"n={cell['count']}",
                    size="1",
                    class_name=TEXT_SECONDARY,
                ),
                width="100%",
                align="center",
            ),
            spacing="1",
            align="stretch",
            width="100%",
        ),
        padding="8px",
        border_radius="8px",
        width="100%",
        height="100%",
        class_name="border transition-all hover:border-[#DC2626] "
        + t(
            "bg-[#08090D] border-white/5",
            "bg-white border-gray-200",
        ),
    )


def _board_slot(rnd: rx.Var, slot: rx.Var) -> rx.Component:
    """Render the fixed visual slot for a round, including its snake-order pick."""
    return rx.el.div(
        rx.foreach(
            AdpState.filtered_board_cells,
            lambda cell: rx.cond(
                (cell["round"] == rnd) & (cell["display_column"] == slot),
                _board_cell(cell),
                rx.fragment(),
            ),
        ),
        min_width="140px",
        width="140px",
        flex_shrink="0",
    )


def _board_row(rnd: rx.Var) -> rx.Component:
    """Render a round with twelve fixed visual slots in board order."""
    return rx.hstack(
        rx.box(
            rx.vstack(
                rx.text(
                    f"R{rnd}",
                    size="2",
                    weight="bold",
                    class_name="text-[#DC2626]",
                ),
                rx.text(
                    "Round",
                    size="1",
                    class_name="uppercase " + TEXT_SECONDARY,
                ),
                spacing="0",
                align="center",
            ),
            padding="8px",
            border_radius="8px",
            min_width="60px",
            width="60px",
            class_name="border flex items-center justify-center "
            + t(
                "bg-[#DC2626]/10 border-[#DC2626]/30",
                "bg-red-50 border-red-200",
            ),
        ),
        rx.foreach(AdpState.slot_range, lambda slot: _board_slot(rnd, slot)),
        spacing="2",
        align="stretch",
        width="fit-content",
    )


def _board_header() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(
                "Round",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                align="center",
            ),
            padding="8px",
            min_width="60px",
            width="60px",
        ),
        rx.foreach(
            AdpState.slot_range,
            lambda slot: rx.box(
                rx.text(
                    f"Slot {slot}",
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide text-center "
                    + TEXT_SECONDARY,
                ),
                padding="8px",
                min_width="140px",
                width="140px",
                flex_shrink="0",
                class_name="text-center",
            ),
        ),
        spacing="2",
        align="center",
        width="fit-content",
    )


def _board() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("layout-grid", size=20, color="#DC2626"),
                rx.heading("Draftboard", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"{AdpState.filtered_total_rounds} Runden × 12 Slots",
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                AdpState.filtered_total_rounds > 0,
                rx.box(
                    rx.vstack(
                        _board_header(),
                        rx.foreach(AdpState.filtered_round_range, _board_row),
                        spacing="2",
                        align="stretch",
                    ),
                    width="100%",
                    overflow_x="auto",
                    padding_bottom="8px",
                ),
                rx.box(
                    rx.vstack(
                        rx.icon("inbox", size=40, color="gray"),
                        rx.text(
                            "Keine Board-Daten für diese Filter.",
                            size="2",
                            color_scheme="gray",
                            class_name="italic",
                        ),
                        spacing="2",
                        align="center",
                        padding="48px",
                        width="100%",
                    ),
                    class_name="border border-dashed rounded-xl "
                    + t("border-gray-800", "border-gray-200"),
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _table_row(p: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                p["overall_pick_rank"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                p["full_name"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.badge(
                p["position"].to(str),
                color_scheme=_pos_color(p["position"]),
                variant="soft",
                size="1",
            ),
        ),
        rx.table.cell(
            rx.badge(
                p["positional_pick_rank"].to(str),
                color_scheme=_pos_color(p["position"]),
                variant="soft",
                size="1",
            ),
        ),
        rx.table.cell(
            rx.text(
                p["team"].to(str),
                size="2",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                p["adp_str"].to(str),
                size="2",
                weight="bold",
                class_name="text-[#DC2626] tabular-nums",
            ),
        ),
        rx.table.cell(
            rx.text(
                p["avg_display"].to(str),
                size="2",
                class_name="font-mono " + TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                p["min_pick"].to(str),
                size="2",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                p["max_pick"].to(str),
                size="2",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.badge(
                p["count"].to_string(),
                color_scheme="gray",
                variant="soft",
                size="1",
            ),
        ),
    )


def _table_filter_bar() -> rx.Component:
    return rx.hstack(
        rx.input(
            placeholder="Spieler, Team oder Position suchen…",
            on_change=AdpState.set_table_search.debounce(300),
            default_value=AdpState.table_search,
            size="2",
            class_name="flex-1 min-w-[220px]",
        ),
        rx.select.root(
            rx.select.trigger(placeholder="Position"),
            rx.select.content(
                rx.select.item("Alle Positionen", value="all"),
                rx.foreach(AdpState.available_positions, _position_option),
            ),
            value=AdpState.table_position,
            on_change=AdpState.set_table_position,
            size="2",
        ),
        rx.cond(
            AdpState.has_table_filters,
            rx.button(
                rx.icon("x", size=14),
                "Zurücksetzen",
                on_click=AdpState.clear_table_filters,
                variant="soft",
                color_scheme="gray",
                size="2",
            ),
        ),
        spacing="3",
        align="center",
        wrap="wrap",
        width="100%",
    )


def _empty_filtered_state() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.icon("search-x", size=40, color="gray"),
            rx.heading(
                "Keine Treffer",
                size="4",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
            rx.text(
                "Keine Spieler entsprechen deinen Filtern. Passe die Suche "
                "oder Position an oder setze die Filter zurück.",
                size="2",
                color_scheme="gray",
                align="center",
                class_name="max-w-md",
            ),
            rx.button(
                rx.icon("rotate-ccw", size=14),
                "Filter zurücksetzen",
                on_click=AdpState.clear_table_filters,
                variant="soft",
                color_scheme="red",
                size="2",
            ),
            spacing="3",
            align="center",
            padding="48px",
            width="100%",
        ),
        class_name="border border-dashed rounded-xl "
        + t("border-gray-800", "border-gray-200"),
        width="100%",
    )


def _adp_table() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("list-ordered", size=20, color="#DC2626"),
                rx.heading("ADP Rankings", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"{AdpState.filtered_count} / {AdpState.total_players}",
                    color_scheme="red",
                    variant="soft",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            _table_filter_bar(),
            rx.cond(
                AdpState.total_players > 0,
                rx.cond(
                    AdpState.filtered_count > 0,
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Overall"),
                                    rx.table.column_header_cell("Spieler"),
                                    rx.table.column_header_cell("Pos"),
                                    rx.table.column_header_cell("Pos-Rang"),
                                    rx.table.column_header_cell("Team"),
                                    rx.table.column_header_cell("ADP"),
                                    rx.table.column_header_cell("Ø Round.Pick"),
                                    rx.table.column_header_cell("Min"),
                                    rx.table.column_header_cell("Max"),
                                    rx.table.column_header_cell("n"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    AdpState.filtered_players, _table_row
                                ),
                            ),
                            variant="surface",
                            size="1",
                        ),
                        width="100%",
                        overflow_x="auto",
                        border_radius="12px",
                        class_name="border "
                        + t("border-gray-800", "border-gray-200"),
                    ),
                    _empty_filtered_state(),
                ),
                rx.text(
                    "Keine Spielerdaten vorhanden.",
                    size="2",
                    color_scheme="gray",
                    class_name="italic",
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _loading() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Lade ADP-Daten…", size="2", color_scheme="gray"),
            spacing="3",
            align="center",
        ),
        padding_y="80px",
        width="100%",
    )


def adp_draftboard_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            _filters(),
            _stats(),
            rx.cond(
                AdpState.is_loading,
                _loading(),
                rx.vstack(
                    _board(),
                    _adp_table(),
                    spacing="6",
                    width="100%",
                    align="stretch",
                ),
            ),
            spacing="5",
            width="100%",
            align="stretch",
        ),
        full_width=True,
    )
