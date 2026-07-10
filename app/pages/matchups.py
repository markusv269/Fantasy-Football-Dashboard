import reflex as rx
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.theme import t, TEXT_SECONDARY, TEXT_PRIMARY
from app.components.layout import layout


def league_selector() -> rx.Component:
    return rx.box(
        rx.select.root(
            rx.select.trigger(placeholder="Alle aktuellen Ligen", width="100%"),
            rx.select.content(
                rx.select.item("Alle aktuellen Ligen", value=""),
                rx.foreach(
                    MatchupsState.current_league_options,
                    lambda lg: rx.select.item(
                        lg["name"].to(str),
                        value=lg["league_id"].to(str),
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
        class_name="w-full md:w-72",
    )


def _week_option(w: rx.Var) -> rx.Component:
    return rx.select.item(f"Woche {w.to(str)}", value=w.to(str))


def week_selector() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(
                "Saison",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
            ),
            rx.text(
                rx.cond(
                    MatchupsState.current_season != "",
                    MatchupsState.current_season,
                    "—",
                ),
                size="3",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
            spacing="0",
            align="start",
        ),
        rx.divider(orientation="vertical", size="4"),
        rx.vstack(
            rx.text(
                "Aktuelle NFL-Woche",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
            ),
            rx.text(
                rx.cond(
                    MatchupsState.current_nfl_week > 0,
                    MatchupsState.current_nfl_week.to_string(),
                    "—",
                ),
                size="3",
                weight="bold",
                class_name="text-[#DC2626]",
            ),
            spacing="0",
            align="start",
        ),
        rx.divider(orientation="vertical", size="4"),
        rx.vstack(
            rx.text(
                "Anzeigen",
                size="1",
                weight="bold",
                class_name="uppercase tracking-wide " + TEXT_SECONDARY,
            ),
            rx.hstack(
                rx.button(
                    rx.icon("chevron-left", size=16),
                    on_click=MatchupsState.change_week(
                        MatchupsState.selected_week - 1
                    ),
                    variant="soft",
                    color_scheme="gray",
                    size="2",
                    disabled=MatchupsState.available_weeks.length() == 0,
                ),
                rx.select.root(
                    rx.select.trigger(placeholder="Woche wählen"),
                    rx.select.content(
                        rx.foreach(MatchupsState.available_weeks, _week_option),
                    ),
                    value=MatchupsState.selected_week.to_string(),
                    on_change=MatchupsState.change_week_str,
                    size="2",
                ),
                rx.button(
                    rx.icon("chevron-right", size=16),
                    on_click=MatchupsState.change_week(
                        MatchupsState.selected_week + 1
                    ),
                    variant="soft",
                    color_scheme="gray",
                    size="2",
                    disabled=MatchupsState.available_weeks.length() == 0,
                ),
                spacing="2",
                align="center",
            ),
            spacing="1",
            align="start",
        ),
        spacing="4",
        align="center",
        padding="12px 16px",
        border_radius="12px",
        wrap="wrap",
        class_name="border "
        + t(
            "bg-[#12141C] border-white/10",
            "bg-white border-gray-200",
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


def league_matchup_group(league_id: str, matchups: list) -> rx.Component:
    league_name = MatchupsState.league_names[league_id]
    return rx.vstack(
        rx.hstack(
            rx.icon("trophy", size=20, color="#DC2626"),
            rx.heading(league_name, size="5", weight="bold"),
            spacing="2",
            align="center",
            padding_y="8px",
            border_bottom="1px solid",
            border_color=t("rgba(255,255,255,0.1)", "rgba(0,0,0,0.1)"),
            width="100%",
        ),
        rx.grid(
            rx.foreach(matchups, matchup_card),
            columns=rx.breakpoints(initial="1", md="2", xl="3"),
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
        align="stretch",
        padding_bottom="24px",
    )


def matchups_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.vstack(
                rx.hstack(
                    rx.heading("Matchups", size="7", weight="bold"),
                    rx.cond(
                        MatchupsState.current_season != "",
                        rx.badge(
                            f"Saison {MatchupsState.current_season}",
                            color_scheme="red",
                            variant="solid",
                            size="2",
                        ),
                    ),
                    rx.cond(
                        MatchupsState.current_nfl_week > 0,
                        rx.badge(
                            f"NFL Woche {MatchupsState.current_nfl_week}",
                            color_scheme="gray",
                            variant="soft",
                            size="2",
                        ),
                    ),
                    spacing="3",
                    align="center",
                    wrap="wrap",
                ),
                rx.text(
                    "Wöchentliche Matchups aller aktuellen Stoned Lack Ligen. Wähle eine Liga oder zeige alle Ligen der laufenden Saison gruppiert an.",
                    size="2",
                    color_scheme="gray",
                ),
                spacing="2",
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
                MatchupsState.is_loading,
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3", color="#DC2626"),
                        rx.text(
                            "Lade Matchups...", size="2", color_scheme="gray"
                        ),
                        spacing="3",
                        align="center",
                    ),
                    padding_y="80px",
                    width="100%",
                ),
                rx.cond(
                    AppState.selected_league_id == "",
                    rx.cond(
                        MatchupsState.matchups_by_league.keys().length() > 0,
                        rx.vstack(
                            rx.foreach(
                                MatchupsState.matchups_by_league.keys(),
                                lambda lid: league_matchup_group(
                                    lid, MatchupsState.matchups_by_league[lid]
                                ),
                            ),
                            spacing="8",
                            width="100%",
                        ),
                        rx.card(
                            rx.vstack(
                                rx.icon("search-x", size=40, color="gray"),
                                rx.heading(
                                    "Keine Matchups gefunden",
                                    size="4",
                                    weight="bold",
                                ),
                                rx.text(
                                    "Für die gewählte Woche konnten keine Daten geladen werden.",
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
                    rx.cond(
                        MatchupsState.paired_matchups.length() > 0,
                        rx.grid(
                            rx.foreach(
                                MatchupsState.paired_matchups, matchup_card
                            ),
                            columns=rx.breakpoints(initial="1", md="2", xl="3"),
                            spacing="4",
                            width="100%",
                        ),
                        rx.card(
                            rx.vstack(
                                rx.icon("calendar-x", size=40, color="gray"),
                                rx.heading(
                                    "No Matchups", size="4", weight="bold"
                                ),
                                rx.text(
                                    "No matchups available for this league in the selected week.",
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
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
