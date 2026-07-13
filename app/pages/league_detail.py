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
        columns=rx.breakpoints(initial="1", sm="3"),
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


def _pos_badge_color(pos: rx.Var) -> rx.Var:
    return rx.match(
        pos.to(str),
        ("QB", "red"),
        ("RB", "blue"),
        ("WR", "green"),
        ("TE", "orange"),
        ("K", "gray"),
        ("DEF", "purple"),
        "gray",
    )


def _matchup_player_row(p: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.badge(
            p["position"].to(str),
            color_scheme=_pos_badge_color(p["position"]),
            variant="soft",
            size="1",
        ),
        rx.vstack(
            rx.text(
                p["full_name"].to(str),
                size="1",
                weight="bold",
                class_name="truncate " + TEXT_PRIMARY,
            ),
            rx.text(
                p["team"].to(str),
                size="1",
                class_name=TEXT_SECONDARY,
            ),
            spacing="0",
            align="start",
            flex="1",
            min_width="0",
        ),
        rx.text(
            p["points"].to(str),
            size="1",
            weight="bold",
            class_name="text-[#DC2626] tabular-nums",
        ),
        spacing="2",
        align="center",
        width="100%",
        padding_y="4px",
        padding_x="8px",
        class_name="border-b last:border-0 "
        + t("border-white/5", "border-gray-100"),
    )


def _matchup_player_section(
    label: str, players: rx.Var, accent_class: str
) -> rx.Component:
    # Explicitly cast to list of dicts to satisfy strong typing requirements in foreach/indexing
    players_list = players.to(list[dict[str, str | float]])
    return rx.vstack(
        rx.hstack(
            rx.text(
                label,
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + accent_class,
            ),
            rx.badge(
                players_list.length().to_string(),
                color_scheme="gray",
                variant="soft",
                size="1",
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            players_list.length() > 0,
            rx.box(
                rx.foreach(players_list, _matchup_player_row),
                width="100%",
                border_radius="8px",
                class_name="border overflow-hidden "
                + t(
                    "bg-[#08090D] border-white/5",
                    "bg-white border-gray-200",
                ),
            ),
            rx.text(
                "—",
                size="1",
                class_name="italic " + TEXT_SECONDARY,
            ),
        ),
        spacing="1",
        width="100%",
        align="stretch",
    )


def _matchup_team_column(
    name: rx.Var,
    manager: rx.Var,
    points: rx.Var,
    starters: rx.Var,
    bench: rx.Var,
    reserve: rx.Var,
    is_winner: rx.Var,
) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text(
                    name.to(str),
                    size="2",
                    weight="bold",
                    class_name="truncate " + TEXT_PRIMARY,
                ),
                rx.text(
                    manager.to(str),
                    size="1",
                    class_name="truncate " + TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
                flex="1",
                min_width="0",
            ),
            rx.text(
                points.to(str),
                size="6",
                weight="bold",
                class_name=rx.cond(is_winner, "text-[#DC2626]", TEXT_SECONDARY)
                + " tabular-nums",
            ),
            spacing="2",
            align="center",
            width="100%",
            padding="10px 12px",
            border_radius="10px",
            class_name="border "
            + t(
                "bg-[#08090D] border-white/5",
                "bg-gray-50 border-gray-200",
            ),
        ),
        _matchup_player_section("Starter", starters, "text-[#DC2626]"),
        _matchup_player_section("Bank", bench, TEXT_SECONDARY),
        _matchup_player_section("Reserve / IR", reserve, "text-amber-500"),
        spacing="3",
        width="100%",
        align="stretch",
    )


def _matchup_card(m: rx.Var) -> rx.Component:
    a = m["team_a_points"].to(float)
    b = m["team_b_points"].to(float)
    is_bye = m["is_bye"].to(bool)
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    f"Matchup {m['matchup_id']}",
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                rx.spacer(),
                rx.badge(
                    rx.cond(is_bye, "BYE", "VS"),
                    color_scheme=rx.cond(is_bye, "gray", "red"),
                    variant="soft",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.grid(
                _matchup_team_column(
                    m["team_a_name"],
                    m["team_a_manager"],
                    m["team_a_points"],
                    m["team_a_starters"],
                    m["team_a_bench"],
                    m["team_a_reserve"],
                    a > b,
                ),
                rx.cond(
                    is_bye,
                    rx.center(
                        rx.vstack(
                            rx.icon("moon", size=28, color="gray"),
                            rx.text(
                                "BYE-Woche",
                                size="2",
                                weight="bold",
                                class_name=TEXT_SECONDARY,
                            ),
                            rx.text(
                                "Kein Gegner in dieser Woche",
                                size="1",
                                class_name="italic " + TEXT_SECONDARY,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        padding="24px",
                        width="100%",
                        class_name="border border-dashed rounded-xl "
                        + t("border-white/10", "border-gray-200"),
                    ),
                    _matchup_team_column(
                        m["team_b_name"],
                        m["team_b_manager"],
                        m["team_b_points"],
                        m["team_b_starters"],
                        m["team_b_bench"],
                        m["team_b_reserve"],
                        b > a,
                    ),
                ),
                columns=rx.breakpoints(initial="1", md="2"),
                spacing="4",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="2",
        width="100%",
    )


def _week_pill(week: rx.Var) -> rx.Component:
    is_active = week == LeaguePageState.selected_matchup_week
    return rx.button(
        week.to_string(),
        on_click=LeaguePageState.change_matchup_week(week),
        variant=rx.cond(is_active, "solid", "soft"),
        color_scheme=rx.cond(is_active, "red", "gray"),
        size="1",
        class_name="min-w-[36px]",
    )


def _week_pill_bar() -> rx.Component:
    return rx.cond(
        LeaguePageState.available_weeks.length() > 0,
        rx.hstack(
            rx.icon("calendar", size=16, color="#DC2626"),
            rx.text(
                "Woche:",
                size="1",
                weight="bold",
                class_name="uppercase " + TEXT_SECONDARY,
            ),
            rx.hstack(
                rx.foreach(LeaguePageState.available_weeks, _week_pill),
                spacing="1",
                overflow_x="auto",
                class_name="no-scrollbar",
            ),
            spacing="3",
            align="center",
            padding="8px 12px",
            border_radius="9999px",
            class_name="border "
            + t(
                "bg-[#08090D] border-white/5",
                "bg-gray-50 border-gray-200",
            ),
            width="100%",
        ),
    )


def _matchups_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("swords", size=20, color="#DC2626"),
                rx.heading("Matchups", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    f"Woche {LeaguePageState.selected_matchup_week}",
                    color_scheme="red",
                    variant="soft",
                ),
                width="100%",
                align="center",
            ),
            _week_pill_bar(),
            rx.cond(
                LeaguePageState.matchup_pairs.length() > 0,
                rx.grid(
                    rx.foreach(LeaguePageState.matchup_pairs, _matchup_card),
                    columns=rx.breakpoints(initial="1", xl="2"),
                    spacing="4",
                    width="100%",
                ),
                rx.box(
                    rx.vstack(
                        rx.icon("calendar-x", size=32, color="gray"),
                        rx.text(
                            "Keine Matchups für diese Woche verfügbar.",
                            size="2",
                            color_scheme="gray",
                            class_name="italic",
                        ),
                        spacing="2",
                        align="center",
                        padding="32px",
                        width="100%",
                    ),
                    class_name="border border-dashed rounded-xl "
                    + t("border-white/10", "border-gray-200"),
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


def _pos_color(pos: rx.Var) -> rx.Var:
    return rx.match(
        pos.to(str),
        ("QB", "red"),
        ("RB", "blue"),
        ("WR", "green"),
        ("TE", "orange"),
        ("K", "gray"),
        ("DEF", "purple"),
        "gray",
    )


def _player_row(p: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.badge(
            p["position"].to(str),
            color_scheme=_pos_color(p["position"]),
            variant="soft",
            size="1",
        ),
        rx.text(
            p["full_name"].to(str),
            size="1",
            weight="medium",
            class_name="truncate " + TEXT_PRIMARY,
        ),
        rx.spacer(),
        rx.text(
            p["team"].to(str),
            size="1",
            weight="medium",
            class_name=TEXT_SECONDARY,
        ),
        spacing="2",
        align="center",
        width="100%",
        padding_y="4px",
        padding_x="8px",
        class_name="border-b last:border-0 "
        + t("border-white/5", "border-gray-100"),
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


def _status_color(status: rx.Var) -> rx.Var:
    return rx.match(
        status.to(str),
        ("complete", "gray"),
        ("drafting", "green"),
        ("pre_draft", "yellow"),
        ("paused", "orange"),
        "blue",
    )


def _draft_card(d: rx.Var) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    d["draft_type"].to(str),
                    color_scheme="purple",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    d["status"].to(str).upper(),
                    color_scheme=_status_color(d["status"]),
                    variant="soft",
                    size="1",
                ),
                rx.spacer(),
                rx.badge(
                    f"Saison {d['season'].to(str)}",
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
                spacing="2",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.hstack(
                rx.icon("calendar", size=16, color="#DC2626"),
                rx.cond(
                    d["start_time_display"].to(str) != "",
                    rx.text(
                        d["start_time_display"].to(str),
                        size="2",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Startzeit noch nicht festgelegt",
                        size="2",
                        class_name="italic " + TEXT_SECONDARY,
                    ),
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            rx.hstack(
                rx.text(
                    f"Draft-ID: {d['draft_id'].to(str)}",
                    size="1",
                    class_name="font-mono " + TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.link(
                    rx.button(
                        rx.icon("external-link", size=14),
                        "Sleeper",
                        size="1",
                        style={"background_color": "#DC2626"},
                    ),
                    href=d["url"].to(str),
                    is_external=True,
                    underline="none",
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
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _drafts_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("file-text", size=20, color="#DC2626"),
                rx.heading("Drafts", size="5", weight="bold"),
                rx.spacer(),
                rx.badge(
                    LeaguePageState.drafts.length().to_string(),
                    color_scheme="gray",
                    variant="soft",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                LeaguePageState.drafts.length() > 0,
                rx.grid(
                    rx.foreach(LeaguePageState.drafts, _draft_card),
                    columns=rx.breakpoints(initial="1", md="2", xl="3"),
                    spacing="4",
                    width="100%",
                ),
                rx.vstack(
                    rx.icon("calendar-x", size=40, color="gray"),
                    rx.heading(
                        "Keine Drafts vorhanden",
                        size="4",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Für diese Liga sind aktuell keine Drafts in der Datenbank hinterlegt.",
                        size="2",
                        color_scheme="gray",
                        align="center",
                    ),
                    spacing="2",
                    align="center",
                    padding="32px",
                    width="100%",
                    class_name="border border-dashed rounded-xl "
                    + t("border-gray-800", "border-gray-200"),
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
        _full_standings_section(),
        _matchups_section(),
        _managers_section(),
        _drafts_section(),
        _trades_section(),
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
