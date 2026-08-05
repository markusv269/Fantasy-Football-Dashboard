import reflex as rx
from app.states.redraft_auslosung_state import RedraftAuslosungState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout
from app.avatar_utils import league_avatar_image


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("shuffle", size=28, color="#DC2626"),
                rx.heading("Aktive Redraft-Auslosung", size="7", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.cond(
                        RedraftAuslosungState.is_loading,
                        rx.spinner(size="1"),
                        rx.icon("refresh-cw", size=14),
                    ),
                    "Aktualisieren",
                    on_click=RedraftAuslosungState.load_assignment,
                    disabled=RedraftAuslosungState.is_loading,
                    variant="soft",
                    color_scheme="gray",
                    size="2",
                ),
                spacing="3",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.text(
                "Die aktuell gültige Ligaeinteilung für die Redraft-Saison "
                "2026. Ein Häkchen bedeutet, dass der Manager der echten "
                "Sleeper-Liga bereits beigetreten ist. Offene Plätze warten "
                "noch auf den Beitritt.",
                size="3",
                color_scheme="gray",
            ),
            rx.cond(
                RedraftAuslosungState.has_active_run,
                rx.hstack(
                    rx.badge(
                        RedraftAuslosungState.run["name"].to(str),
                        color_scheme="red",
                        variant="solid",
                        size="2",
                    ),
                    rx.cond(
                        RedraftAuslosungState.run["generated_display"].to(str)
                        != "",
                        rx.badge(
                            "Erstellt: "
                            + RedraftAuslosungState.run["generated_display"].to(
                                str
                            ),
                            color_scheme="gray",
                            variant="soft",
                            size="2",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _stat_tile(
    label: str, value: rx.Var, icon: str, color: str
) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=22, color=color),
                padding="10px",
                border_radius="10px",
                class_name="w-fit " + t("bg-white/5", "bg-gray-50"),
            ),
            rx.vstack(
                rx.text(
                    label,
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                rx.heading(value, size="6", weight="bold"),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="14px",
        border_radius="12px",
        width="100%",
        class_name="border "
        + t("bg-[#08090D] border-white/5", "bg-white border-gray-200"),
    )


def _manager_search() -> rx.Component:
    return rx.card(
        rx.el.div(
            rx.el.div(
                rx.icon("search", size=20, color="#DC2626"),
                rx.el.div(
                    rx.el.h2(
                        "Manager suchen",
                        class_name="text-base font-bold " + TEXT_PRIMARY,
                    ),
                    rx.el.p(
                        "Finde deine Liga über Sleeper-Name, Discord, Team oder Liga.",
                        class_name="text-sm " + TEXT_SECONDARY,
                    ),
                    class_name="flex min-w-0 flex-col gap-1",
                ),
                class_name="flex min-w-0 items-start gap-3",
            ),
            rx.el.div(
                rx.el.input(
                    placeholder="Manager, Discord, Team oder Liga…",
                    default_value=RedraftAuslosungState.manager_search_query,
                    on_change=RedraftAuslosungState.set_manager_search.debounce(
                        250
                    ),
                    class_name="min-w-0 flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-hidden transition focus:border-[#DC2626] focus:ring-2 focus:ring-[#DC2626]/20 dark:border-white/10 dark:bg-[#08090D] dark:text-white",
                ),
                rx.cond(
                    RedraftAuslosungState.manager_search_query != "",
                    rx.el.button(
                        rx.icon("x", size=14),
                        "Zurücksetzen",
                        on_click=RedraftAuslosungState.clear_manager_search,
                        type="button",
                        class_name="inline-flex shrink-0 items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-semibold text-gray-700 transition hover:border-[#DC2626] hover:text-[#DC2626] dark:border-white/10 dark:text-gray-300",
                    ),
                    rx.fragment(),
                ),
                class_name="flex w-full min-w-0 flex-col gap-2 sm:flex-row",
            ),
            rx.cond(
                RedraftAuslosungState.manager_search_query != "",
                rx.el.div(
                    rx.icon("list-checks", size=14, color="#DC2626"),
                    rx.el.span(
                        RedraftAuslosungState.filtered_league_count.to_string()
                        + " Treffer"
                    ),
                    class_name="flex items-center gap-2 text-sm font-semibold text-[#DC2626]",
                ),
                rx.fragment(),
            ),
            class_name="flex flex-col gap-3",
        ),
        size="3",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _filtered_empty_state() -> rx.Component:
    return rx.card(
        rx.el.div(
            rx.icon("search-x", size=40, color="#DC2626"),
            rx.el.h2(
                "Keine passende Liga gefunden",
                class_name="text-lg font-bold " + TEXT_PRIMARY,
            ),
            rx.el.p(
                "Für deine Suche gibt es keine zugeordneten Manager oder Ligen. Prüfe die Schreibweise oder setze die Suche zurück.",
                class_name="max-w-xl text-center text-sm " + TEXT_SECONDARY,
            ),
            rx.el.button(
                rx.icon("rotate-ccw", size=14),
                "Suche zurücksetzen",
                on_click=RedraftAuslosungState.clear_manager_search,
                type="button",
                class_name="inline-flex items-center gap-2 rounded-lg bg-[#DC2626] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#B91C1C]",
            ),
            class_name="flex flex-col items-center gap-3 py-10 text-center",
        ),
        size="3",
        width="100%",
        class_name="border-dashed",
    )


def _stats() -> rx.Component:
    return rx.grid(
        _stat_tile(
            "Ligen",
            RedraftAuslosungState.total_leagues.to_string(),
            "trophy",
            "#DC2626",
        ),
        _stat_tile(
            "Zugeteilt",
            RedraftAuslosungState.total_assigned.to_string(),
            "users",
            "#3B82F6",
        ),
        _stat_tile(
            "Beigetreten",
            RedraftAuslosungState.joined_count.to_string(),
            "circle-check",
            "#10B981",
        ),
        _stat_tile(
            "Offen",
            RedraftAuslosungState.open_count.to_string(),
            "clock",
            "#F59E0B",
        ),
        _stat_tile(
            "Nachrücker",
            RedraftAuslosungState.waitlist_count.to_string(),
            "user-plus",
            "#A855F7",
        ),
        columns=rx.breakpoints(initial="2", sm="3", lg="5"),
        spacing="3",
        width="100%",
    )


def _player_row(p: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                p["slot"].to_string(),
                size="1",
                weight="bold",
                class_name="font-mono " + TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(
                    p["sleeper_username"].to(str),
                    size="2",
                    weight="bold",
                    class_name="truncate " + TEXT_PRIMARY,
                ),
                rx.cond(
                    p["commish"].to(bool),
                    rx.badge(
                        rx.icon("crown", size=12),
                        "Commish",
                        color_scheme="red",
                        variant="soft",
                        size="1",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
                wrap="wrap",
            ),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(p["discord"].to(str) != "", p["discord"].to(str), "—"),
                size="1",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.cond(
                p["joined"].to(bool),
                rx.badge(
                    rx.icon("check", size=12),
                    "Beigetreten",
                    color_scheme="green",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    rx.icon("clock", size=12),
                    "Offen",
                    color_scheme="orange",
                    variant="soft",
                    size="1",
                ),
            ),
        ),
        rx.table.cell(
            rx.cond(
                p["joined"].to(bool),
                rx.vstack(
                    rx.text(
                        rx.cond(
                            p["team_name"].to(str) != "",
                            p["team_name"].to(str),
                            "—",
                        ),
                        size="1",
                        weight="bold",
                        class_name="truncate " + TEXT_PRIMARY,
                    ),
                    rx.cond(
                        p["display_name"].to(str) != "",
                        rx.text(
                            p["display_name"].to(str),
                            size="1",
                            class_name="truncate " + TEXT_SECONDARY,
                        ),
                        rx.fragment(),
                    ),
                    spacing="0",
                    align="start",
                ),
                rx.text("—", size="1", class_name=TEXT_SECONDARY),
            ),
        ),
    )


def _league_card(lg: rx.Var) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.cond(
                    lg["avatar"].to(str) != "",
                    league_avatar_image(lg["avatar"], size="36px"),
                    rx.box(
                        rx.icon("trophy", size=18, color="#DC2626"),
                        class_name="w-9 h-9 rounded-full flex items-center justify-center "
                        + t("bg-white/5", "bg-gray-50"),
                    ),
                ),
                rx.vstack(
                    rx.heading(
                        lg["league_name"].to(str),
                        size="4",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    rx.cond(
                        lg["is_mapped"].to(bool),
                        rx.text(
                            "Sleeper-Liga: " + lg["league_id"].to(str),
                            size="1",
                            class_name="font-mono " + TEXT_SECONDARY,
                        ),
                        rx.text(
                            "Noch keine Sleeper-Liga verknüpft",
                            size="1",
                            class_name="italic " + TEXT_SECONDARY,
                        ),
                    ),
                    spacing="0",
                    align="start",
                    flex="1",
                    min_width="0",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.badge(
                        lg["joined_count"].to_string()
                        + " / "
                        + lg["size"].to_string(),
                        color_scheme=rx.cond(
                            lg["is_complete"].to(bool), "green", "gray"
                        ),
                        variant="soft",
                        size="1",
                    ),
                    rx.cond(
                        lg["open_count"].to(int) > 0,
                        rx.badge(
                            lg["open_count"].to_string() + " offen",
                            color_scheme="orange",
                            variant="soft",
                            size="1",
                        ),
                        rx.badge(
                            "Vollständig",
                            color_scheme="green",
                            variant="solid",
                            size="1",
                        ),
                    ),
                    spacing="2",
                    align="center",
                    wrap="wrap",
                ),
                spacing="3",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.cond(
                lg["has_invite"].to(bool),
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=14),
                        "Deine Liga? Hier beitreten!",
                        size="2",
                        style={"background_color": "#DC2626"},
                    ),
                    href=lg["invite_link"].to(str),
                    is_external=True,
                    underline="none",
                ),
                rx.cond(
                    lg["is_mapped"].to(bool),
                    rx.link(
                        rx.button(
                            rx.icon("eye", size=14),
                            "Liga-Details",
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                        ),
                        href="/leagues/" + lg["league_id"].to(str),
                        underline="none",
                    ),
                    rx.hstack(
                        rx.icon("info", size=14, color="#F59E0B"),
                        rx.text(
                            "Einladungslink folgt, sobald die Liga angelegt ist.",
                            size="1",
                            weight="medium",
                            class_name="text-amber-500",
                        ),
                        spacing="2",
                        align="center",
                        padding="8px 12px",
                        border_radius="8px",
                        class_name="border border-amber-500/30 bg-amber-500/5",
                    ),
                ),
            ),
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("#"),
                            rx.table.column_header_cell("Sleeper"),
                            rx.table.column_header_cell("Discord"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("Team"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            lg["players"].to(list[dict[str, str | int | bool]]),
                            _player_row,
                        ),
                    ),
                    variant="surface",
                    size="1",
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
        size="3",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _waitlist_row(w: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                w["position"].to_string(),
                size="1",
                weight="bold",
                class_name="font-mono " + TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                w["sleeper_username"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(w["discord"].to(str) != "", w["discord"].to(str), "—"),
                size="1",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                w["created_display"].to(str),
                size="1",
                class_name="font-mono " + TEXT_SECONDARY,
            ),
        ),
    )


def _waitlist_card() -> rx.Component:
    return rx.cond(
        RedraftAuslosungState.waitlist_count > 0,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("user-plus", size=20, color="#F59E0B"),
                    rx.heading("Nachrücker", size="5", weight="bold"),
                    rx.badge(
                        RedraftAuslosungState.waitlist_count.to_string(),
                        color_scheme="orange",
                        variant="soft",
                        size="1",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("#"),
                                rx.table.column_header_cell("Sleeper"),
                                rx.table.column_header_cell("Discord"),
                                rx.table.column_header_cell("Angemeldet"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                RedraftAuslosungState.waitlist, _waitlist_row
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
                spacing="3",
                width="100%",
                align="stretch",
            ),
            size="3",
            width="100%",
        ),
        rx.fragment(),
    )


def _mapping_hint() -> rx.Component:
    return rx.cond(
        RedraftAuslosungState.has_league_mapping,
        rx.fragment(),
        rx.card(
            rx.hstack(
                rx.icon("triangle-alert", size=20, color="#F59E0B"),
                rx.text(
                    "Für diese Auslosung sind noch keine echten Sleeper-Ligen "
                    "verknüpft. Beitrittsstatus und Einladungslinks erscheinen, "
                    "sobald die Ligen angelegt und zugeordnet sind.",
                    size="2",
                    weight="medium",
                    class_name=TEXT_PRIMARY,
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            size="2",
            width="100%",
            class_name="border-l-4 border-l-amber-500 bg-amber-500/5",
        ),
    )


def _loading() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Lade Auslosung…", size="2", color_scheme="gray"),
            spacing="3",
            align="center",
        ),
        padding_y="80px",
        width="100%",
    )


def _empty_box(icon: str, title: str, text: str) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon(icon, size=40, color="gray"),
            rx.heading(title, size="4", weight="bold"),
            rx.text(text, size="2", color_scheme="gray", align="center"),
            spacing="2",
            align="center",
            padding="48px",
            width="100%",
        ),
        class_name="border-dashed",
        width="100%",
    )


def _error_state() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon("circle-alert", size=40, color="#DC2626"),
            rx.heading("Fehler", size="4", weight="bold"),
            rx.text(
                RedraftAuslosungState.error_message,
                size="2",
                color_scheme="gray",
                align="center",
            ),
            rx.button(
                rx.icon("refresh-cw", size=14),
                "Erneut versuchen",
                on_click=RedraftAuslosungState.load_assignment,
                size="2",
                style={"background_color": "#DC2626"},
            ),
            spacing="3",
            align="center",
            padding="48px",
            width="100%",
        ),
        class_name="border-dashed",
        width="100%",
    )


def _content() -> rx.Component:
    return rx.vstack(
        _stats(),
        _mapping_hint(),
        rx.cond(
            RedraftAuslosungState.has_players,
            rx.vstack(
                rx.hstack(
                    rx.icon("list-checks", size=20, color="#DC2626"),
                    rx.heading("Ligen", size="5", weight="bold"),
                    rx.badge(
                        RedraftAuslosungState.filtered_league_count.to_string(),
                        color_scheme="red",
                        variant="soft",
                        size="1",
                    ),
                    rx.spacer(),
                    rx.text(
                        "Beitrittsquote: "
                        + RedraftAuslosungState.joined_pct_str,
                        size="1",
                        weight="bold",
                        class_name=TEXT_SECONDARY,
                    ),
                    width="100%",
                    align="center",
                    wrap="wrap",
                ),
                rx.cond(
                    RedraftAuslosungState.filtered_leagues.length() > 0,
                    rx.grid(
                        rx.foreach(
                            RedraftAuslosungState.filtered_leagues,
                            _league_card,
                        ),
                        columns=rx.breakpoints(initial="1", xl="2"),
                        spacing="4",
                        width="100%",
                    ),
                    _filtered_empty_state(),
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            _empty_box(
                "inbox",
                "Keine Spieler zugeteilt",
                "Die aktive Auslosung enthält derzeit keine Spielerzuordnungen.",
            ),
        ),
        _waitlist_card(),
        spacing="5",
        width="100%",
        align="stretch",
    )


def redraft_auslosung_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            _manager_search(),
            rx.cond(
                RedraftAuslosungState.is_loading,
                _loading(),
                rx.cond(
                    RedraftAuslosungState.error_message != "",
                    _error_state(),
                    rx.cond(
                        RedraftAuslosungState.has_active_run,
                        _content(),
                        _empty_box(
                            "shuffle",
                            "Keine aktive Auslosung",
                            "Es ist derzeit keine Redraft-Auslosung veröffentlicht. "
                            "Sobald die Einteilung feststeht, erscheint sie hier.",
                        ),
                    ),
                ),
            ),
            spacing="5",
            width="100%",
            align="stretch",
        ),
        full_width=True,
    )
