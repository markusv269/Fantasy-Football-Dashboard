import reflex as rx
from app.states.app_state import AppState
from app.states.user_state import UserState
from app.states.community_state import CommunityState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout
from app.avatar_utils import league_avatar_src


def _type_color(t_val: rx.Var) -> rx.Var:
    return rx.match(
        t_val,
        ("dynasty", "purple"),
        ("redraft", "blue"),
        ("bestball", "orange"),
        ("idp", "red"),
        ("idp_only", "red"),
        "gray",
    )


def _type_badges(types: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.foreach(
            types,
            lambda t: rx.badge(
                t.upper(),
                color_scheme=_type_color(t),
                variant="soft",
                radius="full",
            ),
        ),
        spacing="1",
        wrap="wrap",
        align="center",
    )


def league_card(league: dict) -> rx.Component:
    avatar_url = league_avatar_src(league["avatar"])
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.image(
                    src=avatar_url,
                    width="56px",
                    height="56px",
                    border_radius="9999px",
                    class_name="object-cover",
                ),
                rx.vstack(
                    rx.heading(
                        league["name"],
                        size="4",
                        weight="bold",
                        line_height="1.2",
                    ),
                    rx.text(
                        f"Season {league['season']}",
                        size="1",
                        color_scheme="gray",
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                    min_width="0",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.hstack(
                _type_badges(league["types"].to(list[str])),
                rx.spacer(),
                rx.cond(
                    (league["total_rosters"].to(str) != "")
                    & (league["total_rosters"].to(str) != "0"),
                    rx.text(
                        f"{league['total_rosters']} Teams",
                        size="1",
                        weight="medium",
                        color_scheme="gray",
                    ),
                ),
                width="100%",
                align="center",
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        on_click=rx.redirect(f"/leagues/{league['league_id'].to(str)}"),
        size="2",
        class_name="cursor-pointer hover:border-[#DC2626] transition-all "
        + t(
            "bg-[#12141C] border-white/10 shadow-lg",
            "bg-white border-gray-200 shadow-sm",
        ),
    )


def _section(
    title: str, icon: str, count: rx.Var, leagues: rx.Var
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=22, color="#DC2626"),
                rx.heading(title, size="5", weight="bold"),
                rx.badge(
                    count.to_string(),
                    color_scheme="red",
                    variant="soft",
                    size="2",
                ),
                rx.spacer(),
                rx.link(
                    rx.button(
                        "Alle Ligen",
                        rx.icon("arrow-right", size=14),
                        variant="soft",
                        color_scheme="gray",
                        size="1",
                    ),
                    href="/leagues",
                    underline="none",
                ),
                spacing="3",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.cond(
                leagues.length() > 0,
                rx.scroll_area(
                    rx.grid(
                        rx.foreach(leagues, league_card),
                        columns=rx.breakpoints(
                            initial="1", sm="2", md="3", lg="3", xl="4"
                        ),
                        spacing="4",
                        width="100%",
                        padding_right="8px",
                    ),
                    type="hover",
                    scrollbars="vertical",
                    class_name="h-[420px] w-full",
                ),
                rx.box(
                    rx.vstack(
                        rx.icon("inbox", size=32, color="gray"),
                        rx.text(
                            "Keine Ligen in dieser Kategorie.",
                            size="2",
                            color_scheme="gray",
                        ),
                        spacing="2",
                        align="center",
                        padding="32px",
                        width="100%",
                    ),
                    class_name="border border-dashed rounded-xl "
                    + t("border-gray-800", "border-gray-200"),
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _login_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("user-plus", size=22, color="#DC2626"),
                rx.heading(
                    "Melde dich mit Sleeper an", size="4", weight="bold"
                ),
                spacing="2",
                align="center",
            ),
            rx.text(
                "Gib deinen Sleeper-Namen ein, um deine Ligen zu sehen.",
                size="2",
                color_scheme="gray",
            ),
            rx.hstack(
                rx.input(
                    placeholder="Sleeper Username",
                    on_change=UserState.set_username_input,
                    size="3",
                    flex="1",
                ),
                rx.button(
                    "Los geht's",
                    on_click=UserState.save_username,
                    size="3",
                    style={"background_color": "#DC2626"},
                ),
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _user_profile_card() -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.cond(
                UserState.sleeper_avatar != "",
                rx.image(
                    src=f"https://sleepercdn.com/avatars/{UserState.sleeper_avatar}",
                    width="56px",
                    height="56px",
                    border_radius="9999px",
                    class_name="object-cover",
                ),
                rx.box(
                    rx.icon("user", size=28, color="#DC2626"),
                    class_name="w-14 h-14 rounded-full flex items-center justify-center "
                    + t("bg-white/5", "bg-gray-100"),
                ),
            ),
            rx.vstack(
                rx.text(
                    "Angemeldet als",
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                rx.heading(
                    UserState.sleeper_display_name,
                    size="5",
                    weight="bold",
                ),
                rx.hstack(
                    rx.icon("trophy", size=14, color="#DC2626"),
                    rx.text(
                        f"{UserState.my_leagues_count} Ligen gefunden",
                        size="2",
                        weight="medium",
                        class_name=TEXT_SECONDARY,
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="1",
                align="start",
                flex="1",
                min_width="0",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("log-out", size=14),
                "Abmelden",
                on_click=UserState.clear_username,
                variant="soft",
                color_scheme="red",
                size="2",
            ),
            spacing="3",
            align="center",
            width="100%",
            wrap="wrap",
        ),
        size="3",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _my_leagues_section() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("star", size=22, color="#DC2626"),
                rx.heading("Meine Ligen", size="5", weight="bold"),
                rx.badge(
                    UserState.my_leagues_count.to_string(),
                    color_scheme="red",
                    variant="soft",
                    size="2",
                ),
                rx.spacer(),
                rx.cond(
                    UserState.is_loading_my_leagues,
                    rx.spinner(size="2"),
                    rx.fragment(),
                ),
                rx.link(
                    rx.button(
                        "Alle Ligen",
                        rx.icon("arrow-right", size=14),
                        variant="soft",
                        color_scheme="gray",
                        size="1",
                    ),
                    href="/leagues",
                    underline="none",
                ),
                spacing="3",
                align="center",
                width="100%",
                wrap="wrap",
            ),
            rx.cond(
                UserState.my_leagues_count > 0,
                rx.scroll_area(
                    rx.grid(
                        rx.foreach(UserState.my_leagues_data, league_card),
                        columns=rx.breakpoints(
                            initial="1", sm="2", md="3", lg="3", xl="4"
                        ),
                        spacing="4",
                        width="100%",
                        padding_right="8px",
                    ),
                    type="hover",
                    scrollbars="vertical",
                    class_name="h-[420px] w-full",
                ),
                rx.box(
                    rx.vstack(
                        rx.icon("search-x", size=32, color="gray"),
                        rx.text(
                            "Für deinen Sleeper-Account wurden keine Ligen in unserer Datenbank gefunden.",
                            size="2",
                            color_scheme="gray",
                            align="center",
                        ),
                        spacing="2",
                        align="center",
                        padding="32px",
                        width="100%",
                    ),
                    class_name="border border-dashed rounded-xl "
                    + t("border-gray-800", "border-gray-200"),
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(
                    "Willkommen bei Stoned Lack Sleeper Ligen",
                    size="7",
                    weight="bold",
                ),
                rx.spacer(),
                rx.cond(
                    AppState.current_season != "",
                    rx.badge(
                        f"Saison {AppState.current_season}",
                        color_scheme="red",
                        variant="solid",
                        size="2",
                    ),
                ),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            rx.text(
                "Dein Zugang zu allen aktuellen Ligen der Stoned Lack Army. Verfolge Matchups, entdecke Trends und werde Teil der Community.",
                size="3",
                color_scheme="gray",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _news_link(text, **props) -> rx.Component:
    return rx.link(
        text,
        **props,
        class_name="text-[#DC2626] underline underline-offset-2 hover:text-[#B91C1C] transition-colors",
    )


def _news_item(item: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("newspaper", size=14, color="#DC2626"),
                rx.text(
                    item["date"].to(str),
                    size="1",
                    weight="medium",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
            rx.heading(
                item["title"].to(str),
                size="3",
                weight="bold",
                class_name="line-clamp-1 " + TEXT_PRIMARY,
            ),
            rx.markdown(
                item["content"].to(str),
                component_map={"a": _news_link},
                class_name=t(
                    "line-clamp-2 leading-relaxed text-slate-400",
                    "line-clamp-2 leading-relaxed text-gray-500",
                ),
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        padding="12px",
        border_radius="8px",
        width="100%",
        class_name="border "
        + t(
            "bg-[#08090D] border-white/5 hover:border-[#DC2626]/40",
            "bg-gray-50 border-gray-200 hover:border-[#DC2626]/40",
        )
        + " transition-all",
    )


def _news_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("newspaper", size=22, color="#DC2626"),
                rx.heading("Neuigkeiten", size="5", weight="bold"),
                rx.spacer(),
                rx.link(
                    rx.button(
                        "Alle News",
                        rx.icon("arrow-right", size=14),
                        variant="soft",
                        color_scheme="gray",
                        size="1",
                    ),
                    href="/community",
                    underline="none",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                CommunityState.news_items.length() > 0,
                rx.vstack(
                    rx.foreach(CommunityState.news_items[:3], _news_item),
                    spacing="2",
                    width="100%",
                    align="stretch",
                ),
                rx.text(
                    "Keine Neuigkeiten verfügbar.",
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
        height="100%",
    )


def _poll_preview(poll: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("bar-chart-3", size=14, color="#DC2626"),
                rx.text(
                    f"{poll['total_votes']} Stimmen",
                    size="1",
                    weight="medium",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
            rx.heading(
                poll["question"].to(str),
                size="3",
                weight="bold",
                class_name="line-clamp-2 " + TEXT_PRIMARY,
            ),
            rx.vstack(
                rx.foreach(
                    poll["options"].to(list[dict[str, str | int]])[:3],
                    lambda opt: rx.hstack(
                        rx.text(
                            opt["text"].to(str),
                            size="1",
                            weight="medium",
                            class_name="truncate " + TEXT_PRIMARY,
                        ),
                        rx.spacer(),
                        rx.text(
                            opt["pct_str"].to(str),
                            size="1",
                            class_name=TEXT_SECONDARY,
                        ),
                        width="100%",
                        align="center",
                    ),
                ),
                spacing="1",
                width="100%",
                align="stretch",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        padding="12px",
        border_radius="8px",
        width="100%",
        class_name="border "
        + t(
            "bg-[#08090D] border-white/5 hover:border-[#DC2626]/40",
            "bg-gray-50 border-gray-200 hover:border-[#DC2626]/40",
        )
        + " transition-all",
    )


def _polls_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("bar-chart-3", size=22, color="#DC2626"),
                rx.heading("Community Polls", size="5", weight="bold"),
                rx.spacer(),
                rx.link(
                    rx.button(
                        "Alle Polls",
                        rx.icon("arrow-right", size=14),
                        variant="soft",
                        color_scheme="gray",
                        size="1",
                    ),
                    href="/community",
                    underline="none",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                CommunityState.polls.length() > 0,
                rx.vstack(
                    rx.foreach(
                        CommunityState.polls.to(
                            list[
                                dict[
                                    str,
                                    str
                                    | int
                                    | bool
                                    | list[dict[str, str | int]],
                                ]
                            ]
                        )[:2],
                        _poll_preview,
                    ),
                    spacing="2",
                    width="100%",
                    align="stretch",
                ),
                rx.text(
                    "Keine aktiven Polls.",
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
        height="100%",
    )


def _latest_video_card() -> rx.Component:
    video = CommunityState.filtered_youtube_videos[0]
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("circle-play", size=22, color="#DC2626"),
                rx.heading("Letztes Video", size="5", weight="bold"),
                rx.spacer(),
                rx.link(
                    rx.button(
                        "YouTube Kanal",
                        rx.icon("external-link", size=14),
                        variant="soft",
                        color_scheme="gray",
                        size="1",
                    ),
                    href="https://www.youtube.com/channel/UCMD4pfyYl2hxHez34eqnfkQ",
                    is_external=True,
                    underline="none",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                CommunityState.youtube_videos.length() > 0,
                rx.link(
                    rx.grid(
                        rx.box(
                            rx.image(
                                src=video["thumbnail"].to(str),
                                class_name="w-full h-full object-cover",
                            ),
                            rx.cond(
                                video["is_short"].to(bool),
                                rx.badge(
                                    "Short",
                                    color_scheme="red",
                                    variant="solid",
                                    class_name="absolute top-3 right-3",
                                ),
                            ),
                            class_name=t(
                                "relative aspect-video w-full overflow-hidden rounded-xl bg-gray-800",
                                "relative aspect-video w-full overflow-hidden rounded-xl bg-gray-100",
                            ),
                        ),
                        rx.vstack(
                            rx.heading(
                                video["title"].to(str),
                                size="4",
                                weight="bold",
                                class_name="line-clamp-3 " + TEXT_PRIMARY,
                            ),
                            rx.hstack(
                                rx.icon("calendar", size=14, color="#DC2626"),
                                rx.text(
                                    video["date_str"].to(str),
                                    size="2",
                                    weight="medium",
                                    class_name=TEXT_SECONDARY,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.hstack(
                                rx.icon("eye", size=14, color="#DC2626"),
                                rx.text(
                                    f"{video['views']} Views",
                                    size="2",
                                    weight="medium",
                                    class_name=TEXT_SECONDARY,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.spacer(),
                            rx.button(
                                rx.icon("play", size=16),
                                "Jetzt ansehen",
                                size="2",
                                style={"background_color": "#DC2626"},
                                width="100%",
                            ),
                            spacing="3",
                            align="start",
                            width="100%",
                            height="100%",
                        ),
                        columns=rx.breakpoints(initial="1", md="2"),
                        spacing="4",
                        width="100%",
                    ),
                    href=video["link"].to(str),
                    is_external=True,
                    underline="none",
                    width="100%",
                ),
                rx.text(
                    "Keine Videos verfügbar.",
                    size="2",
                    color_scheme="gray",
                    class_name="italic",
                ),
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def _highlight_tile(
    title: str,
    description: str,
    icon: str,
    color: str,
    cta_text: str,
    href: str,
) -> rx.Component:
    return rx.link(
        rx.card(
            rx.vstack(
                rx.box(
                    rx.icon(icon, size=28, color=color),
                    padding="12px",
                    border_radius="12px",
                    class_name="w-fit " + t("bg-white/5", "bg-gray-50"),
                ),
                rx.heading(
                    title,
                    size="4",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.text(
                    description,
                    size="2",
                    class_name=TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(
                        cta_text,
                        size="2",
                        weight="bold",
                        class_name="text-[#DC2626]",
                    ),
                    rx.icon("arrow-right", size=14, color="#DC2626"),
                    spacing="1",
                    align="center",
                ),
                spacing="3",
                width="100%",
                align="start",
                height="100%",
            ),
            size="3",
            width="100%",
            height="100%",
            class_name="hover:border-[#DC2626] transition-all cursor-pointer border-l-4 border-l-transparent hover:border-l-[#DC2626]",
        ),
        href=href,
        underline="none",
        width="100%",
    )


def _highlights_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("sparkles", size=22, color="#DC2626"),
            rx.heading("Highlights", size="5", weight="bold"),
            spacing="2",
            align="center",
        ),
        rx.grid(
            _highlight_tile(
                "Dynasty Warteliste",
                "Sichere dir jetzt deinen Platz in einer der neuen Dynasty-Ligen 2026.",
                "clipboard-list",
                "#10B981",
                "Jetzt anmelden",
                "/waitinglist",
            ),
            _highlight_tile(
                "Community & Podcast",
                "Diskussionen, Live-Shows und Community-Aktionen rund um Stoned Lack.",
                "mic",
                "#A855F7",
                "Zur Community",
                "/community",
            ),
            _highlight_tile(
                "Trending Player",
                "Die heißesten Adds und Drops aus allen Sleeper-Ligen — täglich aktuell.",
                "flame",
                "#F97316",
                "Trends ansehen",
                "/trending",
            ),
            _highlight_tile(
                "Liga-Archiv",
                "Vergangene Saisons und historische Ligen der Stoned Lack Army.",
                "archive",
                "#3B82F6",
                "Archiv öffnen",
                "/archive",
            ),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="4",
            width="100%",
        ),
        spacing="4",
        width="100%",
        align="stretch",
    )


def home_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            rx.cond(
                UserState.is_logged_in,
                rx.vstack(
                    _user_profile_card(),
                    _my_leagues_section(),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                _login_card(),
            ),
            _section(
                f"Dynasty Ligen {AppState.current_season}",
                "crown",
                AppState.current_dynasty_leagues.length(),
                AppState.current_dynasty_leagues,
            ),
            _section(
                f"Redraft Ligen {AppState.current_season}",
                "trophy",
                AppState.current_redraft_leagues.length(),
                AppState.current_redraft_leagues,
            ),
            rx.grid(
                _news_card(),
                _polls_card(),
                columns=rx.breakpoints(initial="1", lg="2"),
                spacing="6",
                width="100%",
            ),
            _latest_video_card(),
            _highlights_section(),
            spacing="6",
            width="100%",
            align="stretch",
        ),
        full_width=True,
    )
