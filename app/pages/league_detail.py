import reflex as rx
from app.states.league_page_state import LeaguePageState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


def _back_button() -> rx.Component:
    return rx.link(
        rx.button(
            rx.icon("arrow-left", size=16),
            "Zurück zu den Ligen",
            variant="soft",
            color_scheme="gray",
            size="2",
        ),
        href="/leagues",
        underline="none",
    )


def _loading_state() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.spinner(size="3"),
            rx.text("Lade Ligadaten…", size="2", color_scheme="gray"),
            spacing="3",
            align="center",
        ),
        padding_y="120px",
        width="100%",
    )


def _not_found_state() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon("triangle-alert", size=40, color="#DC2626"),
            rx.heading("Liga nicht gefunden", size="5", weight="bold"),
            rx.text(
                "Diese Liga konnte nicht geladen werden.",
                size="2",
                color_scheme="gray",
            ),
            _back_button(),
            spacing="3",
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
            rx.heading("Fehler", size="5", weight="bold"),
            rx.text(
                LeaguePageState.error_message,
                size="2",
                color_scheme="gray",
            ),
            _back_button(),
            spacing="3",
            align="center",
            padding="48px",
            width="100%",
        ),
        class_name="border-dashed",
        width="100%",
    )


def _type_color(t_val: rx.Var) -> rx.Var:
    return rx.match(
        t_val,
        ("dynasty", "purple"),
        ("redraft", "blue"),
        "gray",
    )


def _header() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                _back_button(),
                rx.spacer(),
                rx.badge(
                    f"ID: {LeaguePageState.league_id}",
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        LeaguePageState.league_name,
                        size="7",
                        weight="bold",
                    ),
                    rx.hstack(
                        rx.badge(
                            LeaguePageState.league_type.upper(),
                            color_scheme=_type_color(
                                LeaguePageState.league_type
                            ),
                            variant="soft",
                            radius="full",
                        ),
                        rx.badge(
                            f"Season {LeaguePageState.league_season}",
                            color_scheme="gray",
                            variant="soft",
                            radius="full",
                        ),
                        spacing="2",
                        align="center",
                        wrap="wrap",
                    ),
                    spacing="2",
                    align="start",
                ),
                spacing="4",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
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
        size="3",
        width="100%",
    )


def _quick_stats() -> rx.Component:
    return rx.grid(
        _stat_card(
            "Teams",
            LeaguePageState.total_rosters.to_string(),
            "users",
            "#DC2626",
        ),
        _stat_card(
            "Manager",
            LeaguePageState.manager_count.to_string(),
            "user",
            "#3B82F6",
        ),
        _stat_card(
            "Letzte Woche",
            LeaguePageState.latest_week.to_string(),
            "calendar",
            "#10B981",
        ),
        _stat_card(
            "Roster-Plätze",
            LeaguePageState.roster_positions.length().to_string(),
            "list",
            "#F59E0B",
        ),
        columns=rx.breakpoints(initial="2", md="4"),
        spacing="4",
        width="100%",
    )


def _champion_card() -> rx.Component:
    return rx.cond(
        LeaguePageState.champion.contains("team_name")
        & (LeaguePageState.champion["team_name"] != ""),
        rx.card(
            rx.hstack(
                rx.icon("trophy", size=28, color="#F59E0B"),
                rx.vstack(
                    rx.text(
                        "Liga-Champion",
                        size="1",
                        weight="bold",
                        class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                    ),
                    rx.heading(
                        LeaguePageState.champion["team_name"].to(str),
                        size="5",
                        weight="bold",
                    ),
                    rx.text(
                        LeaguePageState.champion["display_name"].to(str),
                        size="2",
                        color_scheme="gray",
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="4",
                align="center",
                width="100%",
            ),
            size="3",
            width="100%",
            class_name=t(
                "border-l-4 border-l-yellow-500 bg-yellow-500/5",
                "border-l-4 border-l-yellow-500 bg-yellow-50",
            ),
        ),
    )


def _roster_positions_card() -> rx.Component:
    return rx.cond(
        LeaguePageState.roster_positions.length() > 0,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("layout-grid", size=18, color="#DC2626"),
                    rx.heading("Roster-Konfiguration", size="4", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.flex(
                    rx.foreach(
                        LeaguePageState.roster_positions,
                        lambda pos: rx.badge(
                            pos,
                            color_scheme="gray",
                            variant="soft",
                            size="2",
                        ),
                    ),
                    wrap="wrap",
                    gap="2",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            size="3",
            width="100%",
        ),
    )


def _standings_row(team: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                team["rank"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(
                    team["team_name"].to(str),
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.text(
                    team["display_name"].to(str),
                    size="1",
                    class_name=TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
            ),
        ),
        rx.table.cell(
            rx.text(
                f"{team['wins']}-{team['losses']}-{team['ties']}",
                size="2",
                weight="medium",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["fpts_for"].to(str),
                size="2",
                weight="bold",
                class_name="text-[#DC2626]",
                align="right",
            ),
        ),
    )


def _top_standings_card() -> rx.Component:
    return rx.cond(
        LeaguePageState.top_standings.length() > 0,
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("list-ordered", size=18, color="#DC2626"),
                    rx.heading("Top-Teams", size="4", weight="bold"),
                    rx.spacer(),
                    rx.badge(
                        f"Woche {LeaguePageState.latest_week}",
                        color_scheme="gray",
                        variant="soft",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("#"),
                                rx.table.column_header_cell("Team"),
                                rx.table.column_header_cell("W-L-T"),
                                rx.table.column_header_cell("PF"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                LeaguePageState.top_standings,
                                _standings_row,
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
    )


def _full_standings_row(team: rx.Var) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                team["rank"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.vstack(
                rx.text(
                    team["team_name"].to(str),
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.text(
                    team["display_name"].to(str),
                    size="1",
                    class_name=TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
            ),
        ),
        rx.table.cell(
            rx.text(
                f"{team['wins']}-{team['losses']}-{team['ties']}",
                size="2",
                weight="medium",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["win_pct_str"].to(str),
                size="2",
                weight="medium",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["fpts_for"].to(str),
                size="2",
                weight="bold",
                class_name="text-[#DC2626]",
                align="right",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["fpts_against"].to(str),
                size="2",
                weight="medium",
                class_name=TEXT_SECONDARY,
                align="right",
            ),
        ),
    )


def _full_standings_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("table-2", size=20, color="#DC2626"),
                rx.heading("Tabelle", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"Woche {LeaguePageState.latest_week}",
                    color_scheme="gray",
                    variant="soft",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                LeaguePageState.full_standings.length() > 0,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("#"),
                                rx.table.column_header_cell("Team / Manager"),
                                rx.table.column_header_cell("W-L-T"),
                                rx.table.column_header_cell("Pct"),
                                rx.table.column_header_cell("PF"),
                                rx.table.column_header_cell("PA"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                LeaguePageState.full_standings,
                                _full_standings_row,
                            ),
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
                rx.text(
                    "Keine Tabellendaten verfügbar.",
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


def _matchup_card(m: rx.Var) -> rx.Component:
    a = m["team_a_points"].to(float)
    b = m["team_b_points"].to(float)
    return rx.card(
        rx.vstack(
            rx.badge(
                f"Matchup {m['matchup_id']}",
                color_scheme="gray",
                variant="soft",
                size="1",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text(
                        m["team_a_name"].to(str),
                        size="2",
                        weight="bold",
                        class_name="truncate max-w-[140px] " + TEXT_PRIMARY,
                    ),
                    rx.text(
                        m["team_a_manager"].to(str),
                        size="1",
                        class_name="truncate max-w-[140px] " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        m["team_a_points"].to(str),
                        size="5",
                        weight="bold",
                        class_name=rx.cond(
                            a > b, "text-[#DC2626]", TEXT_SECONDARY
                        ),
                    ),
                    spacing="1",
                    align="center",
                    flex="1",
                ),
                rx.badge("VS", color_scheme="gray", variant="soft"),
                rx.vstack(
                    rx.text(
                        m["team_b_name"].to(str),
                        size="2",
                        weight="bold",
                        class_name="truncate max-w-[140px] " + TEXT_PRIMARY,
                    ),
                    rx.text(
                        m["team_b_manager"].to(str),
                        size="1",
                        class_name="truncate max-w-[140px] " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        m["team_b_points"].to(str),
                        size="5",
                        weight="bold",
                        class_name=rx.cond(
                            b > a, "text-[#DC2626]", TEXT_SECONDARY
                        ),
                    ),
                    spacing="1",
                    align="center",
                    flex="1",
                ),
                spacing="3",
                align="center",
                width="100%",
                justify="between",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="2",
        width="100%",
    )


def _matchups_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("swords", size=20, color="#DC2626"),
                rx.heading("Matchups", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"Woche {LeaguePageState.latest_week}",
                    color_scheme="gray",
                    variant="soft",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                LeaguePageState.matchup_pairs.length() > 0,
                rx.grid(
                    rx.foreach(LeaguePageState.matchup_pairs, _matchup_card),
                    columns=rx.breakpoints(initial="1", md="2", xl="3"),
                    spacing="4",
                    width="100%",
                ),
                rx.text(
                    "Keine Matchups für diese Woche verfügbar.",
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


def _manager_card(m: rx.Var) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text(
                        m["roster_id"].to(str),
                        size="2",
                        weight="bold",
                    ),
                    class_name="w-10 h-10 rounded-full flex items-center justify-center bg-[#DC2626] text-white",
                ),
                rx.vstack(
                    rx.text(
                        m["team_name"].to(str),
                        size="2",
                        weight="bold",
                        class_name="truncate " + TEXT_PRIMARY,
                    ),
                    rx.text(
                        m["display_name"].to(str),
                        size="1",
                        class_name="truncate " + TEXT_SECONDARY,
                    ),
                    spacing="0",
                    align="start",
                    flex="1",
                    min_width="0",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            spacing="2",
            width="100%",
            align="stretch",
        ),
        size="2",
        width="100%",
    )


def _managers_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("users", size=20, color="#DC2626"),
                rx.heading("Manager", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    LeaguePageState.manager_count.to_string(),
                    color_scheme="gray",
                    variant="soft",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                LeaguePageState.manager_cards.length() > 0,
                rx.grid(
                    rx.foreach(LeaguePageState.manager_cards, _manager_card),
                    columns=rx.breakpoints(initial="1", sm="2", md="3", lg="4"),
                    spacing="3",
                    width="100%",
                ),
                rx.text(
                    "Keine Manager gefunden.",
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


def _roster_card(r: rx.Var) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.text(
                    r["team_name"].to(str),
                    size="2",
                    weight="bold",
                    class_name="truncate " + TEXT_PRIMARY,
                ),
                rx.text(
                    r["display_name"].to(str),
                    size="1",
                    class_name="truncate " + TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
                width="100%",
            ),
            rx.divider(),
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Starter",
                        size="1",
                        weight="bold",
                        class_name="uppercase " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        r["starters_count"].to(str),
                        size="4",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    spacing="0",
                    align="center",
                ),
                rx.divider(orientation="vertical", size="4"),
                rx.vstack(
                    rx.text(
                        "Bank",
                        size="1",
                        weight="bold",
                        class_name="uppercase " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        r["bench_count"].to(str),
                        size="4",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    spacing="0",
                    align="center",
                ),
                rx.divider(orientation="vertical", size="4"),
                rx.vstack(
                    rx.text(
                        "Total",
                        size="1",
                        weight="bold",
                        class_name="uppercase " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        r["players_count"].to(str),
                        size="4",
                        weight="bold",
                        class_name="text-[#DC2626]",
                    ),
                    spacing="0",
                    align="center",
                ),
                spacing="3",
                align="center",
                justify="between",
                width="100%",
            ),
            rx.hstack(
                rx.text(
                    f"{r['wins']}-{r['losses']}-{r['ties']}",
                    size="1",
                    weight="medium",
                    class_name=TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.text(
                    f"PF {r['fpts_for']}",
                    size="1",
                    weight="bold",
                    class_name="text-[#DC2626]",
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
    )


def _rosters_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("layout-list", size=20, color="#DC2626"),
                rx.heading("Roster", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    LeaguePageState.roster_cards.length().to_string(),
                    color_scheme="gray",
                    variant="soft",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                LeaguePageState.roster_cards.length() > 0,
                rx.grid(
                    rx.foreach(LeaguePageState.roster_cards, _roster_card),
                    columns=rx.breakpoints(initial="1", md="2", lg="3"),
                    spacing="4",
                    width="100%",
                ),
                rx.text(
                    "Keine Roster-Daten verfügbar.",
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


def _trades_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("repeat", size=20, color="#DC2626"),
                rx.heading("Trades", size="5", weight="bold"),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.cond(
                LeaguePageState.trades_available,
                rx.text(
                    "Keine aktuellen Trades.",
                    size="2",
                    color_scheme="gray",
                ),
                rx.vstack(
                    rx.icon("info", size=32, color="gray"),
                    rx.text(
                        "Keine Trade-Daten verfügbar",
                        size="3",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Es ist derzeit keine Trade-/Transaktionstabelle in der Datenbank konfiguriert.",
                        size="2",
                        color_scheme="gray",
                        align="center",
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


def _content() -> rx.Component:
    return rx.vstack(
        _header(),
        _quick_stats(),
        _champion_card(),
        _top_standings_card(),
        _full_standings_section(),
        _matchups_section(),
        _managers_section(),
        _rosters_section(),
        _trades_section(),
        _roster_positions_card(),
        spacing="4",
        width="100%",
        align="stretch",
    )


def league_detail_page() -> rx.Component:
    return layout(
        rx.cond(
            LeaguePageState.loading,
            _loading_state(),
            rx.cond(
                LeaguePageState.not_found,
                _not_found_state(),
                rx.cond(
                    LeaguePageState.error_message != "",
                    _error_state(),
                    _content(),
                ),
            ),
        )
    )
