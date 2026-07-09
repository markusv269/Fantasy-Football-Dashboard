import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.states.theme_state import ThemeState
from app.theme import (
    t,
    H1,
    TEXT_SECONDARY,
    TEXT_PRIMARY,
    CARD,
    EMPTY_STATE,
)
from app.components.layout import layout


def league_selector() -> rx.Component:
    return rx.box(
        rx.select.root(
            rx.select.trigger(placeholder="Select a League", width="100%"),
            rx.select.content(
                rx.foreach(
                    AppState.leagues_data,
                    lambda lg: rx.select.item(
                        lg["name"].to(str),
                        value=lg["league_id"].to_string(),
                    ),
                ),
            ),
            value=AppState.selected_league_id,
            on_change=lambda val: [
                AppState.select_league(val),
                MatchupsState.init_matchups(),
            ],
            size="3",
        ),
        class_name="w-full md:w-64",
    )


def week_selector() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon("chevron-left", size=16),
            on_click=MatchupsState.change_week(MatchupsState.selected_week - 1),
            variant="ghost",
            color_scheme="gray",
            size="2",
        ),
        rx.hstack(
            rx.foreach(
                rx.Var.range(1, 19),
                lambda w: rx.button(
                    w.to_string(),
                    on_click=MatchupsState.change_week(w),
                    variant=rx.cond(
                        w == MatchupsState.selected_week, "solid", "ghost"
                    ),
                    color_scheme=rx.cond(
                        w == MatchupsState.selected_week, "red", "gray"
                    ),
                    size="1",
                    class_name="min-w-[32px]",
                ),
            ),
            spacing="1",
            overflow_x="auto",
            class_name="no-scrollbar",
        ),
        rx.button(
            rx.icon("chevron-right", size=16),
            on_click=MatchupsState.change_week(MatchupsState.selected_week + 1),
            variant="ghost",
            color_scheme="gray",
            size="2",
        ),
        spacing="2",
        align="center",
        padding="8px 12px",
        border_radius="9999px",
        class_name=t(
            "bg-[#12141C] border border-white/10",
            "bg-white border border-gray-200",
        ),
    )


def matchup_card(matchup: rx.Var) -> rx.Component:
    team_a = matchup["team_a"].to(dict)
    team_b = matchup["team_b"].to(dict)
    has_team_b = matchup["team_b"] != None  # noqa: E711
    return rx.card(
        rx.vstack(
            rx.badge(
                f"Matchup {matchup['matchup_id']}",
                color_scheme="gray",
                variant="soft",
                size="1",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text(
                        team_a["team_name"].to(str),
                        size="2",
                        weight="bold",
                        class_name="truncate max-w-[120px] " + TEXT_PRIMARY,
                    ),
                    rx.text(
                        team_a["points"].to_string(),
                        size="5",
                        weight="bold",
                        class_name=rx.cond(
                            team_a["points"].to(float)
                            > team_b["points"].to(float),
                            "text-[#DC2626]",
                            TEXT_SECONDARY,
                        ),
                    ),
                    spacing="1",
                    align="center",
                    flex="1",
                ),
                rx.badge(
                    rx.cond(has_team_b, "VS", "BYE"),
                    color_scheme="gray",
                    variant="soft",
                    size="2",
                ),
                rx.cond(
                    has_team_b,
                    rx.vstack(
                        rx.text(
                            team_b["team_name"].to(str),
                            size="2",
                            weight="bold",
                            class_name="truncate max-w-[120px] " + TEXT_PRIMARY,
                        ),
                        rx.text(
                            team_b["points"].to_string(),
                            size="5",
                            weight="bold",
                            class_name=rx.cond(
                                team_b["points"].to(float)
                                > team_a["points"].to(float),
                                "text-[#DC2626]",
                                TEXT_SECONDARY,
                            ),
                        ),
                        spacing="1",
                        align="center",
                        flex="1",
                    ),
                    rx.vstack(
                        rx.text(
                            "BYE",
                            size="2",
                            weight="bold",
                            class_name=TEXT_SECONDARY,
                        ),
                        rx.text(
                            "—",
                            size="5",
                            weight="bold",
                            class_name=TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="center",
                        flex="1",
                    ),
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
        class_name="hover:shadow-md transition-shadow",
    )


def matchups_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.vstack(
                rx.heading("Matchups", size="7", weight="bold"),
                rx.text(
                    "View weekly scores and head-to-head results.",
                    size="2",
                    color_scheme="gray",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.flex(
                league_selector(),
                week_selector(),
                direction=rx.breakpoints(
                    initial="column", sm="column", md="row"
                ),
                justify="between",
                align="center",
                gap="4",
                width="100%",
            ),
            rx.cond(
                AppState.selected_league_id == "",
                rx.card(
                    rx.vstack(
                        rx.icon("trophy", size=40, color="gray"),
                        rx.heading(
                            "No League Selected", size="4", weight="bold"
                        ),
                        rx.text(
                            "Select a league to view matchups.",
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
                rx.cond(
                    MatchupsState.paired_matchups.length() > 0,
                    rx.grid(
                        rx.foreach(MatchupsState.paired_matchups, matchup_card),
                        columns=rx.breakpoints(initial="1", md="2", xl="3"),
                        spacing="4",
                        width="100%",
                    ),
                    rx.card(
                        rx.vstack(
                            rx.icon("calendar-x", size=40, color="gray"),
                            rx.heading("No Matchups", size="4", weight="bold"),
                            rx.text(
                                "No matchups available for this week.",
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
                ),
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
