import reflex as rx
from app.states.admin_state import AdminState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


def _filter_tab(label: str, value: str) -> rx.Component:
    return rx.button(
        label,
        on_click=AdminState.set_filter_type(value),
        variant=rx.cond(AdminState.filter_type == value, "solid", "soft"),
        color_scheme=rx.cond(AdminState.filter_type == value, "red", "gray"),
        size="2",
        radius="full",
    )


def _type_badge(t_val: rx.Var) -> rx.Component:
    return rx.badge(
        t_val.to(str).upper(),
        color_scheme=rx.match(
            t_val.to(str),
            ("dynasty", "purple"),
            ("redraft", "blue"),
            ("bestball", "orange"),
            "gray",
        ),
        variant="soft",
        size="1",
    )


def _confirm_sync_all_dialog() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                on_click=AdminState.close_confirm_sync_all,
                class_name="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 cursor-pointer",
            ),
            rx.radix.primitives.dialog.content(
                rx.vstack(
                    rx.hstack(
                        rx.icon("triangle-alert", size=24, color="#F59E0B"),
                        rx.radix.primitives.dialog.title(
                            "Alle Ligen synchronisieren?",
                            class_name="text-xl font-bold " + TEXT_PRIMARY,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Dies aktualisiert Metadaten, Manager und Roster für ALLE Ligen. Der Vorgang kann einige Minuten dauern und kann nicht abgebrochen werden.",
                        size="2",
                        class_name=TEXT_SECONDARY,
                    ),
                    rx.hstack(
                        rx.spacer(),
                        rx.button(
                            "Abbrechen",
                            on_click=AdminState.close_confirm_sync_all,
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                        ),
                        rx.button(
                            rx.icon("refresh-cw", size=14),
                            "Ja, alle synchronisieren",
                            on_click=AdminState.confirm_and_sync_all,
                            size="2",
                            style={"background_color": "#DC2626"},
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-2xl shadow-2xl p-6 w-[95%] max-w-md z-50 border "
                + t(
                    "bg-[#12141C] border-white/10 text-slate-50",
                    "bg-white border-gray-200 text-gray-900",
                ),
            ),
        ),
        open=AdminState.show_confirm_sync_all,
        on_open_change=AdminState.set_confirm_sync_all_open,
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
                rx.heading(value, size="7", weight="bold"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.icon(icon, size=28, color=color),
            width="100%",
            align="center",
        ),
        size="3",
        width="100%",
    )


def _status_banner() -> rx.Component:
    return rx.cond(
        AdminState.status_message != "",
        rx.card(
            rx.hstack(
                rx.icon(
                    rx.match(
                        AdminState.status_type,
                        ("success", "circle-check"),
                        ("error", "circle-alert"),
                        "info",
                    ),
                    size=20,
                    color=rx.match(
                        AdminState.status_type,
                        ("success", "#10B981"),
                        ("error", "#EF4444"),
                        "#3B82F6",
                    ),
                ),
                rx.text(
                    AdminState.status_message,
                    size="2",
                    weight="medium",
                    class_name=TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    on_click=AdminState.clear_status,
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            size="2",
            width="100%",
            class_name=rx.match(
                AdminState.status_type,
                ("success", "border-l-4 border-l-emerald-500"),
                ("error", "border-l-4 border-l-red-500"),
                "border-l-4 border-l-blue-500",
            ),
        ),
    )


def _add_league_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("circle_plus", size=20, color="#DC2626"),
                rx.heading("Neue Liga hinzufügen", size="4", weight="bold"),
                spacing="2",
                align="center",
            ),
            rx.text(
                "Gib eine Sleeper League-ID ein. Metadaten, Manager und Roster werden direkt initialisiert.",
                size="2",
                color_scheme="gray",
            ),
            rx.flex(
                rx.input(
                    placeholder="Sleeper League-ID (z. B. 987654321)",
                    on_change=AdminState.set_add_league_input,
                    default_value=AdminState.add_league_input,
                    size="3",
                    flex="1",
                ),
                rx.select.root(
                    rx.select.trigger(placeholder="Liga-Typ"),
                    rx.select.content(
                        rx.select.item("Dynasty", value="dynasty"),
                        rx.select.item("Redraft", value="redraft"),
                        rx.select.item("Bestball", value="bestball"),
                    ),
                    value=AdminState.add_league_type,
                    on_change=AdminState.set_add_league_type,
                    size="3",
                ),
                rx.button(
                    rx.cond(
                        AdminState.is_syncing,
                        rx.spinner(size="2"),
                        rx.icon("download", size=16),
                    ),
                    "Hinzufügen",
                    on_click=AdminState.add_league,
                    disabled=AdminState.is_syncing,
                    size="3",
                    style={"background_color": "#DC2626"},
                ),
                direction=rx.breakpoints(initial="column", md="row"),
                gap="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _league_row(lg: dict) -> rx.Component:
    is_target = AdminState.sync_target == lg["league_id"]
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.cond(
                    is_target & AdminState.is_syncing,
                    rx.box(
                        class_name="w-2 h-2 rounded-full bg-amber-500 animate-pulse"
                    ),
                    rx.box(class_name="w-2 h-2 rounded-full bg-emerald-500"),
                ),
                rx.text(
                    lg["league_id"].to(str),
                    size="1",
                    class_name="font-mono " + TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(
                lg["league_name"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(_type_badge(lg["league_type"])),
        rx.table.cell(
            rx.text(lg["league_season"].to(str), size="2", weight="medium"),
        ),
        rx.table.cell(
            rx.hstack(
                rx.link(
                    rx.button(
                        rx.icon("eye", size=14),
                        variant="soft",
                        color_scheme="gray",
                        size="1",
                    ),
                    href=f"/leagues/{lg['league_id'].to(str)}",
                    underline="none",
                ),
                rx.button(
                    rx.cond(
                        is_target & AdminState.is_syncing,
                        rx.spinner(size="1"),
                        rx.icon("refresh-cw", size=14),
                    ),
                    rx.cond(
                        is_target & AdminState.is_syncing, "Syncing…", "Sync"
                    ),
                    on_click=AdminState.sync_league(lg["league_id"].to(str)),
                    disabled=AdminState.is_syncing,
                    size="1",
                    style={"background_color": "#DC2626"},
                ),
                spacing="2",
                align="center",
                justify="end",
            ),
        ),
        class_name=rx.cond(
            is_target & AdminState.is_syncing,
            "bg-amber-500/5",
            "",
        ),
    )


def _empty_leagues_state() -> rx.Component:
    return rx.cond(
        AdminState.leagues.length() == 0,
        rx.vstack(
            rx.icon("database", size=40, color="gray"),
            rx.heading(
                "Noch keine Ligen vorhanden",
                size="4",
                weight="bold",
            ),
            rx.text(
                "Füge oben eine Sleeper League-ID hinzu, um zu starten.",
                size="2",
                color_scheme="gray",
                align="center",
            ),
            spacing="2",
            align="center",
            padding="48px",
            width="100%",
            class_name="border border-dashed rounded-xl "
            + t("border-gray-800", "border-gray-200"),
        ),
        rx.vstack(
            rx.icon("search-x", size=40, color="gray"),
            rx.heading(
                "Keine Treffer",
                size="4",
                weight="bold",
            ),
            rx.text(
                "Keine Ligen entsprechen den aktuellen Filtern.",
                size="2",
                color_scheme="gray",
                align="center",
            ),
            rx.button(
                "Filter zurücksetzen",
                on_click=[
                    AdminState.set_search_query(""),
                    AdminState.set_filter_type("all"),
                ],
                variant="soft",
                color_scheme="gray",
                size="2",
            ),
            spacing="2",
            align="center",
            padding="48px",
            width="100%",
            class_name="border border-dashed rounded-xl "
            + t("border-gray-800", "border-gray-200"),
        ),
    )


def _leagues_table() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("database", size=20, color="#DC2626"),
                rx.heading("Ligen verwalten", size="4", weight="bold"),
                rx.badge(
                    AdminState.filtered_leagues.length().to_string(),
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                rx.spacer(),
                rx.input(
                    placeholder="Suche nach Name, ID, Saison…",
                    on_change=AdminState.set_search_query.debounce(300),
                    size="2",
                    width="260px",
                ),
                rx.button(
                    rx.cond(
                        (AdminState.sync_target == "ALL")
                        & AdminState.is_syncing,
                        rx.spinner(size="1"),
                        rx.icon("refresh-cw", size=14),
                    ),
                    rx.cond(
                        (AdminState.sync_target == "ALL")
                        & AdminState.is_syncing,
                        "Synchronisiere…",
                        "Alle synchronisieren",
                    ),
                    on_click=AdminState.open_confirm_sync_all,
                    disabled=AdminState.is_syncing
                    | (AdminState.leagues.length() == 0),
                    size="2",
                    style={"background_color": "#DC2626"},
                ),
                width="100%",
                align="center",
                wrap="wrap",
                spacing="3",
            ),
            rx.hstack(
                _filter_tab("Alle", "all"),
                _filter_tab("Dynasty", "dynasty"),
                _filter_tab("Redraft", "redraft"),
                _filter_tab("Bestball", "bestball"),
                spacing="2",
                wrap="wrap",
            ),
            rx.cond(
                AdminState.is_loading,
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text(
                            "Lade Ligen…",
                            size="2",
                            class_name=TEXT_SECONDARY,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    padding_y="60px",
                    width="100%",
                ),
                rx.cond(
                    AdminState.filtered_leagues.length() > 0,
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("League-ID"),
                                    rx.table.column_header_cell("Name"),
                                    rx.table.column_header_cell("Typ"),
                                    rx.table.column_header_cell("Saison"),
                                    rx.table.column_header_cell(
                                        rx.text("Aktionen", align="right"),
                                    ),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    AdminState.filtered_leagues, _league_row
                                )
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
                    _empty_leagues_state(),
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _log_entry(entry: dict) -> rx.Component:
    return rx.hstack(
        rx.text(
            entry["time"].to(str),
            size="1",
            class_name="font-mono " + TEXT_SECONDARY,
        ),
        rx.icon(
            rx.cond(entry["level"] == "error", "circle-alert", "circle-check"),
            size=12,
            color=rx.cond(entry["level"] == "error", "#EF4444", "#10B981"),
        ),
        rx.text(
            entry["message"].to(str),
            size="1",
            class_name=TEXT_PRIMARY,
        ),
        spacing="2",
        align="center",
        width="100%",
        padding_y="4px",
        class_name="border-b last:border-0 "
        + t("border-gray-800", "border-gray-100"),
    )


def _log_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("scroll-text", size=20, color="#DC2626"),
                rx.heading("Sync-Protokoll", size="4", weight="bold"),
                rx.badge(
                    AdminState.log_entries.length().to_string(),
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                rx.spacer(),
                rx.cond(
                    AdminState.last_sync_time != "",
                    rx.text(
                        f"Letzter Sync: {AdminState.last_sync_time}",
                        size="1",
                        class_name=TEXT_SECONDARY,
                    ),
                ),
                rx.cond(
                    AdminState.log_entries.length() > 0,
                    rx.button(
                        rx.icon("trash-2", size=12),
                        "Löschen",
                        on_click=AdminState.clear_log,
                        variant="ghost",
                        color_scheme="gray",
                        size="1",
                    ),
                ),
                width="100%",
                align="center",
                wrap="wrap",
                spacing="2",
            ),
            rx.cond(
                AdminState.log_entries.length() > 0,
                rx.box(
                    rx.foreach(AdminState.log_entries, _log_entry),
                    width="100%",
                    max_height="360px",
                    overflow_y="auto",
                    padding_x="4px",
                ),
                rx.vstack(
                    rx.icon("inbox", size=28, color="gray"),
                    rx.text(
                        "Noch keine Sync-Aktivität.",
                        size="2",
                        color_scheme="gray",
                        class_name="italic",
                    ),
                    spacing="2",
                    align="center",
                    padding_y="24px",
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


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("shield", size=28, color="#DC2626"),
                rx.heading("Admin-Dashboard", size="7", weight="bold"),
                spacing="3",
                align="center",
            ),
            rx.text(
                "Synchronisiere Liga-Metadaten, Manager und Roster mit der Sleeper-API und der Datenbank.",
                size="3",
                color_scheme="gray",
            ),
            spacing="2",
            width="100%",
            align="start",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def admin_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            _status_banner(),
            rx.grid(
                _stat_card(
                    "Ligen gesamt",
                    AdminState.total_leagues.to_string(),
                    "database",
                    "#DC2626",
                ),
                _stat_card(
                    "Dynasty",
                    AdminState.dynasty_count.to_string(),
                    "crown",
                    "#A855F7",
                ),
                _stat_card(
                    "Redraft",
                    AdminState.redraft_count.to_string(),
                    "trophy",
                    "#3B82F6",
                ),
                _stat_card(
                    "Bestball",
                    AdminState.bestball_count.to_string(),
                    "target",
                    "#F97316",
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                spacing="4",
                width="100%",
            ),
            _add_league_card(),
            _leagues_table(),
            _log_card(),
            _confirm_sync_all_dialog(),
            spacing="5",
            width="100%",
            align="stretch",
        )
    )
