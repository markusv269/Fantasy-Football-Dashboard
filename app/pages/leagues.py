import reflex as rx
from app.states.leagues_state import LeaguesState
from app.states.user_state import UserState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


def _type_color(t_val: rx.Var) -> rx.Var:
    return rx.match(
        t_val,
        ("dynasty", "purple"),
        ("redraft", "blue"),
        ("bestball", "orange"),
        "gray",
    )


def _league_card(lg: dict) -> rx.Component:
    return rx.link(
        rx.card(
            rx.vstack(
                rx.hstack(
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
                    rx.badge(
                        lg["type"].to(str).upper(),
                        color_scheme=_type_color(lg["type"]),
                        variant="soft",
                        radius="full",
                        size="1",
                    ),
                    spacing="2",
                    align="start",
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
                    rx.spacer(),
                    rx.cond(
                        lg["latest_week"].to(int) > 0,
                        rx.hstack(
                            rx.icon("calendar", size=14, color="#DC2626"),
                            rx.text(
                                f"Woche {lg['latest_week'].to(str)}",
                                size="1",
                                weight="bold",
                                class_name=TEXT_PRIMARY,
                            ),
                            spacing="1",
                            align="center",
                        ),
                        rx.text(
                            "keine Wochen",
                            size="1",
                            class_name="italic " + TEXT_SECONDARY,
                        ),
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
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
                rx.icon("trophy", size=28, color="#DC2626"),
                rx.heading("Ligen", size="7", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"{LeaguesState.total_count} Ligen gesamt",
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
                "Filtere und sortiere alle Stoned Lack Ligen nach Saison, Typ, Manager, Woche und Suchtext.",
                size="3",
                color_scheme="gray",
            ),
            rx.cond(
                ~UserState.has_username,
                rx.text(
                    "Tipp: Melde dich mit deinem Sleeper-Namen an, um zwischen deinen Ligen und allen Ligen zu filtern.",
                    size="2",
                    class_name="italic " + TEXT_SECONDARY,
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _season_option(s: rx.Var) -> rx.Component:
    return rx.select.item(s.to(str), value=s.to(str))


def _type_option(t_val: rx.Var) -> rx.Component:
    return rx.select.item(t_val.to(str).upper(), value=t_val.to(str))


def _manager_option(m: rx.Var) -> rx.Component:
    return rx.select.item(m.to(str), value=m.to(str))


def _week_option(w: rx.Var) -> rx.Component:
    return rx.select.item(f"Woche {w.to(str)}", value=w.to(str))


def _week_range() -> list[str]:
    return [str(i) for i in range(1, 19)]


def _scope_selector() -> rx.Component:
    return rx.cond(
        UserState.is_logged_in,
        rx.vstack(
            rx.text(
                "Meine Ligen",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
            ),
            rx.select.root(
                rx.select.trigger(width="100%"),
                rx.select.content(
                    rx.select.item("Alle Ligen", value="all"),
                    rx.select.item("Nur meine Ligen", value="mine"),
                    rx.select.item("Alle außer meinen", value="others"),
                ),
                value=LeaguesState.selected_scope,
                on_change=LeaguesState.set_selected_scope,
                size="2",
            ),
            spacing="1",
            width="100%",
            align="stretch",
        ),
        rx.fragment(),
    )


def _filter_bar() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("filter", size=18, color="#DC2626"),
                rx.heading("Filter & Sortierung", size="4", weight="bold"),
                rx.cond(
                    LeaguesState.active_filter_count > 0,
                    rx.badge(
                        LeaguesState.active_filter_count.to_string(),
                        color_scheme="red",
                        variant="solid",
                        size="1",
                        radius="full",
                    ),
                ),
                rx.spacer(),
                rx.cond(
                    LeaguesState.has_active_filters,
                    rx.button(
                        rx.icon("x", size=14),
                        "Zurücksetzen",
                        on_click=LeaguesState.reset_filters,
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
                        on_change=LeaguesState.set_search_query.debounce(300),
                        default_value=LeaguesState.search_query,
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
                                LeaguesState.available_seasons, _season_option
                            ),
                        ),
                        value=LeaguesState.selected_season,
                        on_change=LeaguesState.set_selected_season,
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
                                LeaguesState.available_types, _type_option
                            ),
                        ),
                        value=LeaguesState.selected_type,
                        on_change=LeaguesState.set_selected_type,
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
                                LeaguesState.available_managers,
                                _manager_option,
                            ),
                        ),
                        value=LeaguesState.selected_manager,
                        on_change=LeaguesState.set_selected_manager,
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                rx.vstack(
                    rx.text(
                        "Woche",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.select.root(
                        rx.select.trigger(width="100%"),
                        rx.select.content(
                            rx.select.item("Alle Wochen", value="all"),
                            *[
                                rx.select.item(f"Woche {w}", value=w)
                                for w in _week_range()
                            ],
                        ),
                        value=LeaguesState.selected_week,
                        on_change=LeaguesState.set_selected_week,
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                rx.vstack(
                    rx.text(
                        "Sortierung",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.select.root(
                        rx.select.trigger(width="100%"),
                        rx.select.content(
                            rx.select.item("Saison ↓", value="season_desc"),
                            rx.select.item("Saison ↑", value="season_asc"),
                            rx.select.item("Name A–Z", value="name_asc"),
                            rx.select.item("Name Z–A", value="name_desc"),
                            rx.select.item(
                                "Manager (viele zuerst)",
                                value="managers_desc",
                            ),
                            rx.select.item(
                                "Manager (wenige zuerst)",
                                value="managers_asc",
                            ),
                            rx.select.item("Letzte Woche ↓", value="week_desc"),
                            rx.select.item("Letzte Woche ↑", value="week_asc"),
                        ),
                        value=LeaguesState.sort_by,
                        on_change=LeaguesState.set_sort_by,
                        size="2",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                _scope_selector(),
                columns=rx.breakpoints(initial="1", sm="2", md="3", lg="4"),
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
        LeaguesState.has_active_filters,
        rx.hstack(
            rx.text(
                "Aktive Filter:",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
            ),
            rx.cond(
                LeaguesState.selected_season != "all",
                _filter_badge(
                    f"Saison: {LeaguesState.selected_season}",
                    LeaguesState.clear_season,
                ),
            ),
            rx.cond(
                LeaguesState.selected_type != "all",
                _filter_badge(
                    f"Typ: {LeaguesState.selected_type.upper()}",
                    LeaguesState.clear_type,
                ),
            ),
            rx.cond(
                LeaguesState.selected_manager != "all",
                _filter_badge(
                    f"Manager: {LeaguesState.selected_manager}",
                    LeaguesState.clear_manager,
                ),
            ),
            rx.cond(
                LeaguesState.selected_week != "all",
                _filter_badge(
                    f"Woche: {LeaguesState.selected_week}",
                    LeaguesState.clear_week,
                ),
            ),
            rx.cond(
                LeaguesState.selected_scope != "all",
                _filter_badge(
                    rx.cond(
                        LeaguesState.selected_scope == "mine",
                        "Nur meine Ligen",
                        "Alle außer meinen",
                    ),
                    LeaguesState.clear_scope,
                ),
            ),
            rx.cond(
                LeaguesState.search_query != "",
                _filter_badge(
                    f"Suche: {LeaguesState.search_query}",
                    LeaguesState.clear_search,
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
            f"{LeaguesState.result_count} von {LeaguesState.total_count} Ligen",
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


def _empty_state() -> rx.Component:
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
                on_click=LeaguesState.reset_filters,
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
            rx.text("Lade Ligen…", size="2", color_scheme="gray"),
            spacing="3",
            align="center",
        ),
        padding_y="80px",
        width="100%",
    )


def leagues_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            rx.cond(
                LeaguesState.is_loading,
                _loading_state(),
                rx.vstack(
                    _filter_bar(),
                    _active_filters(),
                    _result_bar(),
                    rx.cond(
                        LeaguesState.result_count > 0,
                        rx.grid(
                            rx.foreach(
                                LeaguesState.filtered_leagues,
                                _league_card,
                            ),
                            columns=rx.breakpoints(
                                initial="1", sm="1", md="2", lg="3"
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        _empty_state(),
                    ),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
