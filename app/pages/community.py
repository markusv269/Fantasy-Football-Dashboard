import reflex as rx
from app.states.community_state import CommunityState
from app.components.layout import layout
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY


def poll_option_active(poll: dict, option: dict, index: int) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.box(
                class_name=t(
                    "w-4 h-4 rounded-full border-2 border-gray-600",
                    "w-4 h-4 rounded-full border-2 border-gray-300",
                )
            ),
            rx.text(
                option["text"].to(str),
                size="2",
                weight="medium",
                class_name=TEXT_PRIMARY,
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        on_click=CommunityState.vote_poll(poll["id"].to(str), index),
        variant="ghost",
        color_scheme="gray",
        width="100%",
        justify="start",
        margin_bottom="8px",
    )


def poll_option_result(poll: dict, option: dict) -> rx.Component:
    votes = option["votes"].to(int)
    total = poll["total_votes"].to(int)
    pct = rx.cond(total > 0, votes * 100 / total, 0)
    return rx.box(
        rx.hstack(
            rx.text(
                option["text"].to(str),
                size="2",
                weight="bold",
                class_name="z-10 relative " + TEXT_PRIMARY,
            ),
            rx.spacer(),
            rx.text(
                option["pct_str"].to(str),
                size="2",
                weight="bold",
                class_name="z-10 relative " + TEXT_SECONDARY,
            ),
            width="100%",
            padding_x="8px",
            align="center",
        ),
        rx.box(
            rx.box(
                class_name=t(
                    "h-full bg-emerald-500/40 rounded-full transition-all duration-1000 shadow-inner shadow-emerald-900/50",
                    "h-full bg-emerald-100 rounded-full transition-all duration-1000",
                ),
                style={"width": f"{pct}%"},
            ),
            class_name=t(
                "h-8 w-full bg-black/30 border border-white/5 rounded-full overflow-hidden absolute top-0 left-0",
                "h-8 w-full bg-gray-100 rounded-full overflow-hidden absolute top-0 left-0",
            ),
        ),
        position="relative",
        padding_y="6px",
        margin_bottom="8px",
    )


def poll_card(poll: dict) -> rx.Component:
    has_voted = CommunityState.voted_polls.contains(poll["id"].to(str))
    is_closed = ~poll["is_active"].to(bool)
    show_results = has_voted | is_closed
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading(poll["question"].to(str), size="4", weight="bold"),
                rx.spacer(),
                rx.cond(
                    is_closed,
                    rx.badge("Closed", color_scheme="gray", variant="soft"),
                    rx.badge("Active", color_scheme="green", variant="soft"),
                ),
                width="100%",
                align="start",
                spacing="3",
            ),
            rx.cond(
                show_results,
                rx.box(
                    rx.foreach(
                        poll["options"].to(list[dict[str, str | int]]),
                        lambda opt, i: poll_option_result(poll, opt),
                    ),
                    width="100%",
                ),
                rx.box(
                    rx.foreach(
                        poll["options"].to(list[dict[str, str | int]]),
                        lambda opt, i: poll_option_active(poll, opt, i),
                    ),
                    width="100%",
                ),
            ),
            rx.divider(),
            rx.hstack(
                rx.text(
                    f"{poll['total_votes'].to(str)} votes",
                    size="2",
                    class_name=TEXT_SECONDARY,
                ),
                rx.spacer(),
                rx.cond(
                    has_voted,
                    rx.hstack(
                        rx.icon("circle-check", size=14),
                        rx.text("You voted!", size="2", weight="bold"),
                        spacing="1",
                        align="center",
                        class_name="text-emerald-500",
                    ),
                ),
                width="100%",
                align="center",
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
        margin_bottom="16px",
    )


def youtube_card(video: dict) -> rx.Component:
    return rx.link(
        rx.card(
            rx.vstack(
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
                            class_name="absolute top-2 right-2",
                        ),
                    ),
                    class_name=t(
                        "relative aspect-video w-full overflow-hidden rounded-xl bg-gray-800",
                        "relative aspect-video w-full overflow-hidden rounded-xl bg-gray-100",
                    ),
                ),
                rx.heading(
                    video["title"].to(str),
                    size="2",
                    weight="bold",
                    class_name="line-clamp-2",
                ),
                rx.hstack(
                    rx.text(
                        video["date_str"].to(str),
                        size="1",
                        class_name=TEXT_SECONDARY,
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.icon("eye", size=12),
                        rx.text(
                            f"{video['views'].to(str)} Views",
                            size="1",
                            class_name=TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="center",
                    ),
                    width="100%",
                    align="center",
                ),
                spacing="2",
                width="100%",
                align="stretch",
            ),
            size="2",
            width="100%",
            class_name="hover:shadow-md transition-shadow",
        ),
        href=video["link"].to(str),
        is_external=True,
        underline="none",
        width="100%",
        margin_bottom="16px",
    )


def news_card(news: dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading(news["title"].to(str), size="4", weight="bold"),
            rx.text(
                news["date"].to(str),
                size="1",
                class_name=TEXT_SECONDARY,
            ),
            rx.markdown(
                news["content"].to(str),
                size="2",
                class_name="leading-relaxed [&_a]:text-[#DC2626] [&_a]:hover:underline "
                + TEXT_PRIMARY,
            ),
            spacing="2",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
        margin_bottom="16px",
    )


def _youtube_filter_btn(label: str) -> rx.Component:
    return rx.button(
        label,
        on_click=CommunityState.set_youtube_filter(label),
        variant=rx.cond(
            CommunityState.youtube_filter == label, "solid", "soft"
        ),
        color_scheme=rx.cond(
            CommunityState.youtube_filter == label, "red", "gray"
        ),
        size="1",
    )


def community_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.vstack(
                rx.heading("Stoned Lack Community", size="7", weight="bold"),
                rx.text(
                    "Polls, News, Liga-Anmeldung und die neuesten Podcast-Folgen.",
                    size="3",
                    color_scheme="gray",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.grid(
                rx.vstack(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("newspaper", size=22, color="#DC2626"),
                            rx.heading("Neuigkeiten", size="5", weight="bold"),
                            spacing="2",
                            align="center",
                        ),
                        rx.cond(
                            CommunityState.news_items.length() > 0,
                            rx.box(
                                rx.foreach(
                                    CommunityState.news_items, news_card
                                ),
                                width="100%",
                            ),
                            rx.text(
                                "Keine Neuigkeiten vorhanden.",
                                size="2",
                                color_scheme="gray",
                                class_name="italic",
                            ),
                        ),
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("bar-chart-3", size=22, color="#DC2626"),
                            rx.heading(
                                "Community Polls", size="5", weight="bold"
                            ),
                            spacing="2",
                            align="center",
                        ),
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
                            ),
                            poll_card,
                        ),
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                    spacing="6",
                    width="100%",
                    align="stretch",
                ),
                rx.vstack(
                    rx.card(
                        rx.vstack(
                            rx.icon("clipboard-list", size=40, color="#10B981"),
                            rx.heading(
                                "Dynasty Warteliste", size="5", weight="bold"
                            ),
                            rx.text(
                                "Melde dich für die neuen Dynasty-Ligen an!",
                                size="2",
                                color_scheme="gray",
                                align="center",
                            ),
                            rx.link(
                                rx.button(
                                    "Zur Warteliste →",
                                    size="3",
                                    width="100%",
                                    style={"background_color": "#DC2626"},
                                ),
                                href="/waitinglist",
                                underline="none",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                            align="center",
                        ),
                        size="3",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.icon("circle_play", size=22, color="#DC2626"),
                            rx.heading(
                                "Stoned Lack YouTube",
                                size="5",
                                weight="bold",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            _youtube_filter_btn("All"),
                            _youtube_filter_btn("Videos"),
                            _youtube_filter_btn("Shorts"),
                            spacing="2",
                            align="center",
                        ),
                        rx.foreach(
                            CommunityState.filtered_youtube_videos[:6],
                            youtube_card,
                        ),
                        rx.link(
                            rx.button(
                                "Alle Videos ansehen",
                                variant="soft",
                                color_scheme="green",
                                size="2",
                                width="100%",
                            ),
                            href="https://www.youtube.com/channel/UCMD4pfyYl2hxHez34eqnfkQ",
                            is_external=True,
                            underline="none",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                        align="stretch",
                    ),
                    spacing="6",
                    width="100%",
                    align="stretch",
                ),
                columns=rx.breakpoints(initial="1", lg="3"),
                spacing="6",
                width="100%",
                template_columns=rx.breakpoints(initial="1fr", lg="2fr 1fr"),
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
