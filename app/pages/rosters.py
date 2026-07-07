import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout
from app.pages.matchups import league_selector


def _position_badge(pos: rx.Var) -> rx.Component:
    return rx.badge(
        pos.to(str),
        color_scheme=rx.match(
            pos.to(str),
            ("QB", "red"),
            ("RB", "blue"),
            ("WR", "green"),
            ("TE", "orange"),
            ("K", "gray"),
            ("DEF", "purple"),
            "gray",
        ),
        variant="soft",
        size="1",
    )


def _player_row(p: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.text(
            p["full_name"].to(str),
            size="2",
            weight="bold",
            class_name=TEXT_PRIMARY,
        ),
        rx.spacer(),
        rx.hstack(
            _position_badge(p["position"]),
            rx.text(
                p["team"].to(str),
                size="1",
                weight="medium",
                class_name=TEXT_SECONDARY,
            ),
            spacing="2",
            align="center",
        ),
        width="100%",
        align="center",
        padding="12px",
        class_name="border-b last:border-0 "
        + t(
            "border-gray-800 hover:bg-[#161926]",
            "border-gray-100 hover:bg-gray-50",
        ),
    )


def roster_card(roster: rx.Var) -> rx.Component:
    settings = roster["settings"].to(dict)
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.heading(
                    roster["team_name"].to(str),
                    size="4",
                    weight="bold",
                    class_name="truncate " + TEXT_PRIMARY,
                ),
                rx.text(
                    roster["owner_name"].to(str),
                    size="1",
                    class_name="truncate " + TEXT_SECONDARY,
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "W-L-T",
                        size="1",
                        weight="bold",
                        class_name="uppercase " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        f"{settings['wins']}-{settings['losses']}-{settings['ties']}",
                        size="2",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    spacing="0",
                    align="start",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text(
                        "PF",
                        size="1",
                        weight="bold",
                        class_name="uppercase " + TEXT_SECONDARY,
                    ),
                    rx.text(
                        settings["fpts"].to_string(),
                        size="2",
                        weight="bold",
                        class_name="text-[#DC2626]",
                    ),
                    spacing="0",
                    align="end",
                ),
                width="100%",
                padding="12px",
                border_radius="8px",
                class_name=t("bg-[#161926]", "bg-gray-50"),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        on_click=MatchupsState.view_roster(roster["roster_id"].to(int)),
        size="2",
        class_name="cursor-pointer hover:border-[#DC2626] transition-all "
        + t("bg-[#1C2033] border-gray-800", "bg-white border-gray-200"),
    )


def roster_detail() -> rx.Component:
    roster = MatchupsState.selected_roster
    settings = roster["settings"].to(dict)
    return rx.vstack(
        rx.button(
            rx.icon("arrow-left", size=16),
            "Back to Rosters",
            on_click=MatchupsState.clear_selected_roster,
            variant="ghost",
            color_scheme="gray",
            size="2",
        ),
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.heading(
                        roster["team_name"].to(str),
                        size="6",
                        weight="bold",
                    ),
                    rx.text(
                        roster["owner_name"].to(str),
                        size="2",
                        color_scheme="gray",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Record",
                            size="1",
                            weight="bold",
                            class_name="uppercase " + TEXT_SECONDARY,
                        ),
                        rx.text(
                            f"{settings['wins']}-{settings['losses']}-{settings['ties']}",
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
                            "Waiver",
                            size="1",
                            weight="bold",
                            class_name="uppercase " + TEXT_SECONDARY,
                        ),
                        rx.text(
                            f"${settings['waiver_budget_used']}",
                            size="4",
                            weight="bold",
                            class_name=TEXT_PRIMARY,
                        ),
                        spacing="0",
                        align="center",
                    ),
                    spacing="4",
                    align="center",
                    padding="12px 16px",
                    border_radius="12px",
                    class_name=t("bg-[#161926]", "bg-gray-50"),
                ),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            size="3",
            width="100%",
        ),
        rx.grid(
            rx.vstack(
                rx.heading("Starters", size="4", weight="bold"),
                rx.box(
                    rx.foreach(
                        roster["starters"].to(list[dict[str, str]]),
                        _player_row,
                    ),
                    width="100%",
                    border_radius="12px",
                    class_name="border overflow-hidden "
                    + t(
                        "bg-[#1C2033] border-gray-800",
                        "bg-white border-gray-200",
                    ),
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            rx.vstack(
                rx.heading("Reserve / IR", size="4", weight="bold"),
                rx.cond(
                    roster["reserve"].to(list[dict[str, str]]).length() > 0,
                    rx.box(
                        rx.foreach(
                            roster["reserve"].to(list[dict[str, str]]),
                            _player_row,
                        ),
                        width="100%",
                        border_radius="12px",
                        class_name="border overflow-hidden "
                        + t(
                            "bg-[#1C2033] border-gray-800",
                            "bg-white border-gray-200",
                        ),
                    ),
                    rx.card(
                        rx.text(
                            "No players on reserve/IR.",
                            size="2",
                            color_scheme="gray",
                            class_name="italic",
                        ),
                        class_name="border-dashed",
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            columns=rx.breakpoints(initial="1", md="2"),
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
        align="stretch",
    )


def rosters_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.vstack(
                rx.heading("Rosters", size="7", weight="bold"),
                rx.text(
                    "Explore team rosters and player details.",
                    size="2",
                    color_scheme="gray",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.cond(
                MatchupsState.selected_roster.contains("roster_id"),
                roster_detail(),
                rx.vstack(
                    league_selector(),
                    rx.cond(
                        AppState.selected_league_id == "",
                        rx.card(
                            rx.vstack(
                                rx.icon("users", size=40, color="gray"),
                                rx.heading(
                                    "No League Selected",
                                    size="4",
                                    weight="bold",
                                ),
                                rx.text(
                                    "Select a league to view rosters.",
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
                        rx.grid(
                            rx.foreach(
                                MatchupsState.standings_data, roster_card
                            ),
                            columns=rx.breakpoints(
                                initial="1", md="2", lg="3", xl="4"
                            ),
                            spacing="4",
                            width="100%",
                        ),
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
