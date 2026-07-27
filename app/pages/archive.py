import reflex as rx
from app.states.archive_state import ArchiveState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout
from app.avatar_utils import league_avatar_image


def _type_color(t_val: rx.Var) -> rx.Var:
    return rx.match(
        t_val,
        ("dynasty", "purple"),
        ("redraft", "blue"),
        ("bestball", "orange"),
        ("idp", "red"),
        ("idp_only", "red"),
        "gray",
    )


def _type_badges(types: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.foreach(
            types,
            lambda t: rx.badge(
                t.upper(),
                color_scheme=_type_color(t),
                variant="soft",
                radius="full",
                size="1",
            ),
        ),
        spacing="1",
        wrap="wrap",
        align="center",
    )


def _archive_card(lg: dict) -> rx.Component:
    return rx.link(
        rx.card(
            rx.vstack(
                rx.hstack(
                    league_avatar_image(lg["avatar"], size="44px"),
                    rx.vstack(
                        rx.heading(
                            lg["league_name"].to(str),
                            size="4",
                            weight="bold",
                            class_name="line-clamp-2 " + TEXT_PRIMARY,
                        ),
                        rx.text(
                            f"Saison {lg['season'].to(str)}",
                            size="1",
                            class_name=TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="start",
                        flex="1",
                        min_width="0",
                    ),
                    _type_badges(lg["types"].to(list[str])),
                    spacing="3",
                    align="center",
                    width="100%",
                ),
                rx.hstack(
                    rx.icon("users", size=14, color="#DC2626"),
                    rx.text(
                        f"{lg['manager_count'].to(str)} Manager",
                        size="1",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    lg["manager_sample"].to(str) != "",
                    rx.text(
                        lg["manager_sample"].to(str),
                        size="1",
                        class_name="line-clamp-2 italic " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        "Keine Manager-Daten",
                        size="1",
                        class_name="italic " + TEXT_SECONDARY,
                    ),
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.hstack(
                        rx.text(
                            "Details",
                            size="1",
                            weight="bold",
                            class_name="text-[#DC2626]",
                        ),
                        rx.icon("arrow-right", size=14, color="#DC2626"),
                        spacing="1",
                        align="center",
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            size="2",
            width="100%",
            class_name="hover:border-[#DC2626] transition-all cursor-pointer border-l-4 border-l-transparent hover:border-l-[#DC2626]",
        ),
        href=f"/leagues/{lg['league_id'].to(str)}",
        underline="none",
        width="100%",
    )


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("archive", size=28, color="#DC2626"),
                rx.heading("Liga-Archiv", size="7", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"{ArchiveState.total_archive_count} Ligen im Archiv",
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
                "Ältere Ligen und vergangene Saisons der Stoned Lack Army — filterbar nach Saison, Typ, Manager und Suchtext.",
                size="3",
                color_scheme="gray",
            ),
            rx.link(
                rx.button(
                    rx.icon("arrow-left", size=16),
                    "Zur aktuellen Saison",
                    variant="soft",
                    color_scheme="red",
                    size="2",
                ),
                href="/",
                underline="none",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _season_option(season: rx.Var) -> rx.Component:
    return rx.select.item(season.to(str), value=season.to(str))


def _type_option(t_val: rx.Var) -> rx.Component:
    return rx.select.item(t_val.to(str).upper(), value=t_val.to(str))


def _manager_option(m: rx.Var) -> rx.Component:
    return rx.select.item(m.to(str), value=m.to(str))


def _filter_bar() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("filter", size=18, color="#DC2626"),
                rx.heading("Filter", size="4", weight="bold"),
                rx.cond(
                    ArchiveState.active_filter_count > 0,
                    rx.badge(
                        ArchiveState.active_filter_count.to_string(),
                        color_scheme="red",
                        variant="solid",
                        size="1",
                        radius="full",
                    ),
                ),
                rx.spacer(),
                rx.cond(
                    ArchiveState.has_active_filters,
                    rx.button(
                        rx.icon("x", size=14),
                        "Zurücksetzen",
                        on_click=ArchiveState.reset_filters,
                        variant="soft",
                        color_scheme="gray",
                        size="1",
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.grid(
                rx.vstack(
                    rx.text(
                        "Suche",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.input(
                        placeholder="Name, Manager, ID…",
                        on_change=ArchiveState.set_search_query.debounce(300),
                        default_value=ArchiveState.search_query,
                        size="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
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
                            rx.select.item("Alle Saisons", value="all"),
                            rx.foreach(
                                ArchiveState.available_seasons,
                                _season_option,
                            ),
                        ),
                        value=ArchiveState.selected_season,
                        on_change=ArchiveState.set_selected_season,
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                rx.vstack(
                    rx.text(
                        "Liga-Typ",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.select.root(
                        rx.select.trigger(width="100%"),
                        rx.select.content(
                            rx.select.item("Alle Typen", value="all"),
                            rx.foreach(
                                ArchiveState.available_types, _type_option
                            ),
                        ),
                        value=ArchiveState.selected_type,
                        on_change=ArchiveState.set_selected_type,
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                rx.vstack(
                    rx.text(
                        "Manager",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.select.root(
                        rx.select.trigger(width="100%"),
                        rx.select.content(
                            rx.select.item("Alle Manager", value="all"),
                            rx.foreach(
                                ArchiveState.available_managers,
                                _manager_option,
                            ),
                        ),
                        value=ArchiveState.selected_manager,
                        on_change=ArchiveState.set_selected_manager,
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="2",
        width="100%",
    )


def _filter_badge(label: rx.Var, on_clear: rx.event.EventType) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="1", weight="bold", class_name=TEXT_PRIMARY),
        rx.button(
            rx.icon("x", size=12),
            on_click=on_clear,
            variant="ghost",
            color_scheme="gray",
            size="1",
        ),
        spacing="1",
        align="center",
        padding_x="10px",
        padding_y="4px",
        border_radius="9999px",
        class_name="border "
        + t(
            "bg-[#DC2626]/10 border-[#DC2626]/30",
            "bg-red-50 border-red-200",
        ),
    )


def _active_filters() -> rx.Component:
    return rx.cond(
        ArchiveState.has_active_filters,
        rx.hstack(
            rx.text(
                "Aktive Filter:",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
            ),
            rx.cond(
                ArchiveState.selected_season != "all",
                _filter_badge(
                    f"Saison: {ArchiveState.selected_season}",
                    ArchiveState.clear_season,
                ),
            ),
            rx.cond(
                ArchiveState.selected_type != "all",
                _filter_badge(
                    f"Typ: {ArchiveState.selected_type.upper()}",
                    ArchiveState.clear_type,
                ),
            ),
            rx.cond(
                ArchiveState.selected_manager != "all",
                _filter_badge(
                    f"Manager: {ArchiveState.selected_manager}",
                    ArchiveState.clear_manager,
                ),
            ),
            rx.cond(
                ArchiveState.search_query != "",
                _filter_badge(
                    f"Suche: {ArchiveState.search_query}",
                    ArchiveState.clear_search,
                ),
            ),
            spacing="2",
            align="center",
            wrap="wrap",
            width="100%",
        ),
    )


def _result_bar() -> rx.Component:
    return rx.hstack(
        rx.icon("list-checks", size=16, color="#DC2626"),
        rx.text(
            f"{ArchiveState.result_count} von {ArchiveState.total_archive_count} Ligen",
            size="2",
            weight="bold",
            class_name=TEXT_PRIMARY,
        ),
        rx.spacer(),
        width="100%",
        align="center",
        padding_x="12px",
        padding_y="8px",
        border_radius="8px",
        class_name="border "
        + t(
            "bg-[#08090D] border-white/5",
            "bg-gray-50 border-gray-200",
        ),
    )


def _empty_archive() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon("inbox", size=40, color="gray"),
            rx.heading("Kein Archiv vorhanden", size="4", weight="bold"),
            rx.text(
                "Es gibt derzeit keine älteren Ligen im Archiv.",
                size="2",
                color_scheme="gray",
                align="center",
            ),
            rx.link(
                rx.button(
                    "Zurück zur Startseite",
                    style={"background_color": "#DC2626"},
                ),
                href="/",
                underline="none",
            ),
            spacing="3",
            align="center",
            padding="48px",
            width="100%",
        ),
        width="100%",
        class_name="border-dashed",
    )


def _empty_results() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon("search-x", size=40, color="gray"),
            rx.heading("Keine Treffer", size="4", weight="bold"),
            rx.text(
                "Keine Ligen entsprechen den aktuellen Filtern.",
                size="2",
                color_scheme="gray",
                align="center",
            ),
            rx.button(
                rx.icon("rotate-ccw", size=14),
                "Filter zurücksetzen",
                on_click=ArchiveState.reset_filters,
                variant="soft",
                color_scheme="red",
                size="2",
            ),
            spacing="3",
            align="center",
            padding="48px",
            width="100%",
        ),
        width="100%",
        class_name="border-dashed",
    )


def _loading_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Lade Archiv…", size="2", color_scheme="gray"),
            spacing="3",
            align="center",
        ),
        padding_y="80px",
        width="100%",
    )


def archive_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            rx.cond(
                ArchiveState.is_loading,
                _loading_state(),
                rx.cond(
                    ArchiveState.total_archive_count > 0,
                    rx.vstack(
                        _filter_bar(),
                        _active_filters(),
                        _result_bar(),
                        rx.cond(
                            ArchiveState.result_count > 0,
                            rx.grid(
                                rx.foreach(
                                    ArchiveState.filtered_leagues,
                                    _archive_card,
                                ),
                                columns=rx.breakpoints(
                                    initial="1", sm="1", md="2", lg="3"
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            _empty_results(),
                        ),
                        spacing="4",
                        width="100%",
                        align="stretch",
                    ),
                    _empty_archive(),
                ),
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
