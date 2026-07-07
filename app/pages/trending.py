import reflex as rx
from app.states.community_state import CommunityState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


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


def trending_player_row(player: dict, index: int, is_add: bool) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                (index + 1).to_string(),
                size="2",
                weight="bold",
                class_name=TEXT_SECONDARY,
                align="center",
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(
                    player["full_name"].to(str),
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.badge(
                    player["position"].to(str),
                    color_scheme=_pos_color(player["position"]),
                    variant="soft",
                    size="1",
                ),
                rx.text(
                    player["team"].to(str),
                    size="1",
                    weight="medium",
                    class_name=TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.hstack(
                rx.text(
                    player["count"].to_string(),
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.cond(
                    is_add,
                    rx.icon("trending-up", size=16, color="#10B981"),
                    rx.icon("trending-down", size=16, color="#EF4444"),
                ),
                spacing="2",
                align="center",
                justify="end",
            ),
        ),
    )


def _timeframe_btn(label: str, value: str) -> rx.Component:
    return rx.button(
        label,
        on_click=CommunityState.change_trending_timeframe(value),
        variant=rx.cond(
            CommunityState.trending_timeframe == value, "solid", "soft"
        ),
        color_scheme=rx.cond(
            CommunityState.trending_timeframe == value, "red", "gray"
        ),
        size="2",
    )


def _trending_section(
    title: str, icon: str, color: str, entries: rx.Var, is_add: bool
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=20, color=color),
                rx.heading(title, size="4", weight="bold"),
                spacing="2",
                align="center",
                padding="16px",
                width="100%",
                class_name="border-b "
                + t("border-gray-800", "border-gray-200"),
            ),
            rx.box(
                rx.table.root(
                    rx.table.body(
                        rx.foreach(
                            entries,
                            lambda p, i: trending_player_row(p, i, is_add),
                        )
                    ),
                    variant="ghost",
                    size="1",
                ),
                width="100%",
                overflow_x="auto",
                padding="8px",
            ),
            spacing="0",
            width="100%",
            align="stretch",
        ),
        size="1",
        width="100%",
    )


def trending_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.flex(
                rx.vstack(
                    rx.hstack(
                        rx.icon("flame", size=28, color="#F59E0B"),
                        rx.heading("Trending Players", size="7", weight="bold"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "The most added and dropped players across Sleeper leagues.",
                        size="3",
                        color_scheme="gray",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.hstack(
                    _timeframe_btn("24 Hours", "24h"),
                    _timeframe_btn("48 Hours", "48h"),
                    spacing="2",
                ),
                direction=rx.breakpoints(initial="column", md="row"),
                gap="4",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.grid(
                _trending_section(
                    "Hot Adds",
                    "arrow-up-right",
                    "#10B981",
                    CommunityState.trending_adds,
                    True,
                ),
                _trending_section(
                    "Trending Drops",
                    "arrow-down-right",
                    "#EF4444",
                    CommunityState.trending_drops,
                    False,
                ),
                columns=rx.breakpoints(initial="1", md="2"),
                spacing="6",
                width="100%",
            ),
            rx.text(
                "* Players sorted by Sleeper trending activity across all leagues.",
                size="1",
                color_scheme="gray",
                class_name="italic text-center",
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
