import reflex as rx
from app.states.league_detail_state import LeagueDetailState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY


def _rank_badge(rank: rx.Var) -> rx.Component:
    return rx.box(
        rx.text(rank.to(str), size="1", weight="bold"),
        class_name=rx.match(
            rank.to(int),
            (
                1,
                "w-6 h-6 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center",
            ),
            (
                2,
                "w-6 h-6 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center",
            ),
            (
                3,
                "w-6 h-6 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center",
            ),
            "w-6 h-6 rounded-full flex items-center justify-center "
            + t("bg-gray-800 text-gray-400", "bg-gray-50 text-gray-600"),
        ),
    )


def standing_row(team: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(_rank_badge(team["rank"])),
        rx.table.cell(
            rx.vstack(
                rx.text(
                    team["team_name"].to(str),
                    weight="bold",
                    size="2",
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
                team["wins"].to(str), size="2", align="center", weight="medium"
            ),
        ),
        rx.table.cell(
            rx.text(
                team["losses"].to(str),
                size="2",
                align="center",
                weight="medium",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["ties"].to(str), size="2", align="center", weight="medium"
            ),
        ),
        rx.table.cell(
            rx.text(
                team["fpts_for"].to(str),
                size="2",
                align="right",
                weight="bold",
                class_name="text-emerald-500",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["fpts_against"].to(str),
                size="2",
                align="right",
                weight="medium",
                class_name="text-red-500",
            ),
        ),
    )


def matchup_card(matchup: dict) -> rx.Component:
    a_pts = matchup["team_a_points"].to(float)
    b_pts = matchup["team_b_points"].to(float)
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    matchup["team_a_name"].to(str),
                    size="2",
                    weight="medium",
                    class_name="truncate max-w-[100px] " + TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.text(
                    matchup["team_a_points"].to(str),
                    size="2",
                    class_name=rx.cond(
                        a_pts > b_pts,
                        "font-bold text-emerald-500",
                        "font-medium " + TEXT_SECONDARY,
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text(
                    matchup["team_b_name"].to(str),
                    size="2",
                    weight="medium",
                    class_name="truncate max-w-[100px] " + TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.text(
                    matchup["team_b_points"].to(str),
                    size="2",
                    class_name=rx.cond(
                        b_pts > a_pts,
                        "font-bold text-emerald-500",
                        "font-medium " + TEXT_SECONDARY,
                    ),
                ),
                width="100%",
                align="center",
            ),
            spacing="1",
            width="100%",
        ),
        padding="12px",
        border_radius="12px",
        class_name="border "
        + t("bg-[#08090D] border-white/5", "bg-gray-50 border-gray-200"),
    )


def _header() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.radix.primitives.dialog.title(
                LeagueDetailState.modal_league_name,
                class_name="text-2xl font-bold " + TEXT_PRIMARY,
            ),
            rx.hstack(
                rx.badge(
                    LeagueDetailState.modal_league_type.upper(),
                    color_scheme="blue",
                    variant="soft",
                    radius="full",
                ),
                rx.badge(
                    LeagueDetailState.modal_league_season,
                    color_scheme="gray",
                    variant="soft",
                    radius="full",
                ),
                spacing="2",
                align="center",
            ),
            spacing="2",
            align="start",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("x", size=18),
            on_click=LeagueDetailState.close_league_modal,
            variant="ghost",
            color_scheme="gray",
            size="2",
        ),
        width="100%",
        align="start",
        margin_bottom="24px",
    )


def _champion() -> rx.Component:
    return rx.cond(
        LeagueDetailState.modal_champion.contains("team_name"),
        rx.hstack(
            rx.icon("trophy", size=20, color="#F59E0B"),
            rx.text(
                "League Champion: ",
                weight="medium",
                class_name=t("text-yellow-200", "text-yellow-800"),
            ),
            rx.text(
                f"{LeagueDetailState.modal_champion['team_name'].to(str)} ({LeagueDetailState.modal_champion['display_name'].to(str)})",
                weight="bold",
                class_name=t("text-yellow-100", "text-yellow-900"),
            ),
            spacing="2",
            align="center",
            padding="16px",
            border_radius="12px",
            margin_bottom="24px",
            class_name=t(
                "bg-yellow-500/10 border border-yellow-500/30",
                "bg-yellow-50 border border-yellow-200",
            ),
        ),
    )


def _standings_section() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Standings",
            size="4",
            weight="bold",
            class_name=t("text-gray-100", "text-gray-900"),
        ),
        rx.cond(
            LeagueDetailState.modal_standings.length() > 0,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Rank"),
                            rx.table.column_header_cell("Team"),
                            rx.table.column_header_cell("W"),
                            rx.table.column_header_cell("L"),
                            rx.table.column_header_cell("T"),
                            rx.table.column_header_cell("PF"),
                            rx.table.column_header_cell("PA"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            LeagueDetailState.modal_standings,
                            standing_row,
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
            rx.text(
                "No standings available.",
                size="2",
                class_name="italic p-4 border border-dashed rounded-xl "
                + t(
                    "text-gray-400 border-gray-800 bg-gray-900/20",
                    "text-gray-500 border-gray-200 bg-gray-50",
                ),
            ),
        ),
        spacing="3",
        width="100%",
        align="stretch",
        margin_bottom="24px",
    )


def _matchups_section() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Recent Matchups",
            size="4",
            weight="bold",
            class_name=t("text-gray-100", "text-gray-900"),
        ),
        rx.cond(
            LeagueDetailState.modal_recent_matchups.length() > 0,
            rx.grid(
                rx.foreach(
                    LeagueDetailState.modal_recent_matchups,
                    matchup_card,
                ),
                columns=rx.breakpoints(initial="1", md="2"),
                spacing="3",
                width="100%",
            ),
            rx.text(
                "No matchup data available.",
                size="2",
                class_name="italic " + TEXT_SECONDARY,
            ),
        ),
        spacing="3",
        width="100%",
        align="stretch",
        margin_bottom="24px",
    )


def _roster_section() -> rx.Component:
    return rx.vstack(
        rx.heading(
            "Roster Settings",
            size="4",
            weight="bold",
            class_name=t("text-gray-100", "text-gray-900"),
        ),
        rx.cond(
            LeagueDetailState.modal_roster_positions.length() > 0,
            rx.flex(
                rx.foreach(
                    LeagueDetailState.modal_roster_positions,
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
            rx.text(
                "No roster info.",
                size="2",
                class_name=TEXT_SECONDARY,
            ),
        ),
        spacing="3",
        width="100%",
        align="stretch",
    )


def league_detail_modal() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                on_click=LeagueDetailState.close_league_modal,
                class_name="fixed inset-0 bg-black/75 z-40 cursor-pointer transition-opacity",
            ),
            rx.radix.primitives.dialog.content(
                rx.cond(
                    LeagueDetailState.modal_loading,
                    rx.flex(
                        rx.icon(
                            "loader",
                            class_name="w-8 h-8 animate-spin text-emerald-500",
                        ),
                        justify="center",
                        align="center",
                        padding_y="80px",
                        width="100%",
                    ),
                    rx.vstack(
                        _header(),
                        _champion(),
                        _standings_section(),
                        _matchups_section(),
                        _roster_section(),
                        spacing="0",
                        width="100%",
                        align="stretch",
                    ),
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-2xl shadow-2xl p-6 w-[95%] sm:w-full max-w-4xl max-h-[85vh] overflow-y-auto z-50 border border-white/10 "
                + t("bg-[#12141C] text-slate-50", "bg-white text-gray-900"),
            ),
        ),
        open=LeagueDetailState.show_modal,
        on_open_change=LeagueDetailState.set_modal_open,
    )
