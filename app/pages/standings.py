import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout
from app.pages.matchups import league_selector


def _rank_badge(rank: rx.Var) -> rx.Component:
    return rx.box(
        rx.text(rank.to(str), size="2", weight="bold"),
        class_name=rx.match(
            rank.to(int),
            (
                1,
                "w-8 h-8 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center",
            ),
            (
                2,
                "w-8 h-8 rounded-full bg-gray-200 text-gray-700 flex items-center justify-center",
            ),
            (
                3,
                "w-8 h-8 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center",
            ),
            "w-8 h-8 rounded-full flex items-center justify-center "
            + t("bg-gray-800 text-gray-400", "bg-gray-50 text-gray-600"),
        ),
    )


def standings_row(team: dict) -> rx.Component:
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
                    team["owner_name"].to(str),
                    size="1",
                    class_name=TEXT_SECONDARY,
                ),
                spacing="0",
                align="start",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["wins"].to(str), size="2", weight="medium", align="center"
            ),
        ),
        rx.table.cell(
            rx.text(
                team["losses"].to(str),
                size="2",
                weight="medium",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(
                team["ties"].to(str), size="2", weight="medium", align="center"
            ),
        ),
        rx.table.cell(
            rx.text(team["win_pct"].to(str), size="2", align="center"),
        ),
        rx.table.cell(
            rx.text(
                team["fpts"].to(str),
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
                class_name="text-[#5B7BA5]",
                align="right",
            ),
        ),
        on_click=MatchupsState.view_roster(team["roster_id"].to(int)),
        class_name="cursor-pointer "
        + t("hover:bg-white/5", "hover:bg-gray-50")
        + " transition-colors",
    )


def standings_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.vstack(
                rx.heading("Standings", size="7", weight="bold"),
                rx.text(
                    "League rankings, records, and points.",
                    size="2",
                    color_scheme="gray",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            league_selector(),
            rx.cond(
                AppState.selected_league_id == "",
                rx.card(
                    rx.vstack(
                        rx.icon("list-ordered", size=40, color="gray"),
                        rx.heading(
                            "No League Selected", size="4", weight="bold"
                        ),
                        rx.text(
                            "Select a league to view standings.",
                            size="2",
                            color_scheme="gray",
                        ),
                        spacing="2",
                        align="center",
                        padding="48px",
                        width="100%",
                    ),
                    class_name="border-dashed",
                    width="100%",
                ),
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Rank"),
                                rx.table.column_header_cell("Team"),
                                rx.table.column_header_cell("W"),
                                rx.table.column_header_cell("L"),
                                rx.table.column_header_cell("T"),
                                rx.table.column_header_cell("Pct"),
                                rx.table.column_header_cell("PF"),
                                rx.table.column_header_cell("PA"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                MatchupsState.standings_data, standings_row
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
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
