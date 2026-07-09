import reflex as rx
from app.states.app_state import AppState
from app.states.theme_state import ThemeState
from app.states.user_state import UserState
from app.theme import t


def _theme_icon() -> rx.Component:
    return rx.color_mode_cond(
        light=rx.icon("moon", size=16), dark=rx.icon("sun", size=16)
    )


def _theme_icon_lg() -> rx.Component:
    return rx.color_mode_cond(
        light=rx.icon("moon", size=18), dark=rx.icon("sun", size=18)
    )


def _theme_label() -> rx.Component:
    return rx.color_mode_cond(
        light=rx.text("Dark Mode", size="2"),
        dark=rx.text("Light Mode", size="2"),
    )


def _theme_label_bold() -> rx.Component:
    return rx.color_mode_cond(
        light=rx.text("Dark Mode", size="2", weight="bold"),
        dark=rx.text("Light Mode", size="2", weight="bold"),
    )


nav_items = [
    {"icon": "house", "label": "Home", "href": "/"},
    {"icon": "trophy", "label": "Leagues", "href": "/leagues"},
    {"icon": "swords", "label": "Matchups", "href": "/matchups"},
    {"icon": "list-ordered", "label": "Standings", "href": "/standings"},
    {"icon": "users", "label": "Rosters", "href": "/rosters"},
    {"icon": "file-text", "label": "Drafts", "href": "/drafts"},
    {"icon": "trending-up", "label": "Trending", "href": "/trending"},
    {"icon": "mic", "label": "Community", "href": "/community"},
    {"icon": "archive", "label": "Archiv", "href": "/archive"},
    {"icon": "clipboard-list", "label": "Warteliste", "href": "/waitinglist"},
]


def _nav_link(item: dict) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(item["icon"], size=18),
            rx.text(item["label"], size="2", weight="medium"),
            spacing="3",
            align="center",
            width="100%",
        ),
        href=item["href"],
        underline="none",
        width="100%",
        padding_x="12px",
        padding_y="10px",
        border_radius="8px",
        class_name=t(
            "text-slate-400 hover:bg-white/5 hover:text-[#DC2626] transition-all",
            "text-gray-700 hover:bg-gray-100 hover:text-[#DC2626] transition-all",
        ),
    )


def sidebar_std() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("podcast", size=28, color="#DC2626"),
            rx.heading("Stoned Lack", size="5", weight="bold"),
            spacing="3",
            align="center",
            padding="20px",
            width="100%",
            class_name=t(
                "border-b border-white/5 shadow-sm", "border-b border-gray-200"
            ),
        ),
        rx.vstack(
            *[_nav_link(item) for item in nav_items],
            spacing="1",
            width="100%",
            padding="12px",
            flex="1",
            overflow_y="auto",
        ),
        rx.box(
            rx.cond(
                UserState.is_logged_in,
                rx.hstack(
                    rx.cond(
                        UserState.sleeper_avatar != "",
                        rx.image(
                            src=f"https://sleepercdn.com/avatars/{UserState.sleeper_avatar}",
                            width="32px",
                            height="32px",
                            border_radius="9999px",
                        ),
                        rx.icon("user", size=20),
                    ),
                    rx.text(
                        UserState.sleeper_display_name,
                        size="2",
                        weight="bold",
                        flex="1",
                    ),
                    rx.button(
                        rx.icon("x", size=14),
                        on_click=UserState.clear_username,
                        variant="ghost",
                        size="1",
                        color_scheme="gray",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                    padding="8px",
                ),
                rx.vstack(
                    rx.input(
                        placeholder="Sleeper Username",
                        on_change=UserState.set_username_input,
                        size="2",
                        width="100%",
                    ),
                    rx.button(
                        "Login",
                        on_click=UserState.save_username,
                        size="2",
                        width="100%",
                        style={"background_color": "#DC2626"},
                    ),
                    spacing="2",
                    width="100%",
                    padding="8px",
                ),
            ),
            rx.button(
                rx.hstack(
                    _theme_icon(),
                    _theme_label(),
                    spacing="2",
                    align="center",
                ),
                on_click=rx.toggle_color_mode,
                variant="soft",
                color_scheme="gray",
                width="100%",
                margin_top="8px",
            ),
            padding="12px",
            width="100%",
            class_name=t(
                "border-t border-gray-800", "border-t border-gray-200"
            ),
        ),
        spacing="0",
        width="260px",
        height="100vh",
        class_name=t(
            "bg-[#040507] border-r border-white/5 hidden md:flex",
            "bg-white border-r border-gray-200 hidden md:flex",
        ),
    )


def mobile_drawer_std() -> rx.Component:
    return rx.box(
        rx.box(
            on_click=ThemeState.close_mobile_sidebar,
            position="fixed",
            top="0",
            left="0",
            right="0",
            bottom="0",
            z_index="40",
            display=rx.cond(ThemeState.mobile_sidebar_open, "block", "none"),
            class_name="bg-black/60 backdrop-blur-sm md:hidden",
        ),
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("podcast", size=22, color="#DC2626"),
                    rx.heading("Navigation", size="4", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=20),
                    on_click=ThemeState.close_mobile_sidebar,
                    variant="soft",
                    color_scheme="gray",
                    radius="full",
                    size="1",
                ),
                width="100%",
                padding="20px",
                align="center",
                class_name=t(
                    "border-b border-white/10 bg-[#12141C]",
                    "border-b border-gray-200 bg-gray-50",
                ),
            ),
            rx.vstack(
                *[
                    rx.link(
                        rx.hstack(
                            rx.icon(item["icon"], size=18),
                            rx.text(item["label"], size="3", weight="medium"),
                            rx.spacer(),
                            rx.icon(
                                "chevron-right",
                                size=14,
                                class_name="opacity-50",
                            ),
                            spacing="3",
                            align="center",
                            width="100%",
                        ),
                        href=item["href"],
                        on_click=ThemeState.close_mobile_sidebar,
                        underline="none",
                        width="100%",
                        padding_x="20px",
                        padding_y="16px",
                        class_name=t(
                            "text-slate-400 border-b border-white/5 hover:bg-white/5 hover:text-white active:bg-white/10",
                            "text-gray-700 border-b border-gray-100 hover:bg-gray-50 hover:text-[#DC2626] active:bg-gray-100",
                        ),
                    )
                    for item in nav_items
                ],
                spacing="0",
                width="100%",
                overflow_y="auto",
                flex="1",
                class_name="no-scrollbar",
            ),
            rx.box(
                rx.button(
                    rx.hstack(
                        _theme_icon_lg(),
                        _theme_label_bold(),
                        spacing="2",
                        align="center",
                    ),
                    on_click=rx.toggle_color_mode,
                    variant="solid",
                    color_scheme="gray",
                    width="100%",
                    size="3",
                    class_name=t(
                        "bg-slate-800 text-white hover:bg-slate-700",
                        "bg-gray-900 text-white",
                    ),
                ),
                padding="20px",
                width="100%",
                class_name=t(
                    "bg-[#12141C] border-t border-white/10",
                    "bg-gray-50 border-t border-gray-200",
                ),
            ),
            spacing="0",
            position="fixed",
            bottom="0",
            left="0",
            right="0",
            z_index="50",
            max_height="85vh",
            border_top_left_radius="24px",
            border_top_right_radius="24px",
            transform=rx.cond(
                ThemeState.mobile_sidebar_open,
                "translateY(0)",
                "translateY(100%)",
            ),
            transition="transform 400ms cubic-bezier(0.4, 0, 0.2, 1)",
            class_name=t(
                "bg-[#08090D] shadow-2xl border-t border-white/10 md:hidden",
                "bg-white shadow-2xl border-t border-gray-200 md:hidden",
            ),
        ),
    )


def header_std() -> rx.Component:
    social_link_class = t(
        "text-gray-400 hover:text-[#DC2626]",
        "text-gray-500 hover:text-[#DC2626]",
    )
    return rx.hstack(
        rx.button(
            rx.hstack(
                rx.icon("menu", size=20),
                rx.text(
                    "Menu",
                    size="2",
                    weight="bold",
                    class_name="hidden xs:block",
                ),
                spacing="2",
                align="center",
            ),
            on_click=ThemeState.toggle_mobile_sidebar,
            variant="solid",
            class_name=t(
                "md:hidden bg-[#DC2626] hover:bg-[#B91C1C] text-white px-4 shadow-lg active:scale-95 transition-all",
                "md:hidden bg-[#DC2626] hover:bg-[#B91C1C] text-white px-4 shadow-md active:scale-95 transition-all",
            ),
            radius="full",
        ),
        rx.heading("Stoned Lack Fantasy", size="5", weight="bold"),
        rx.spacer(),
        rx.cond(
            AppState.nfl_state.contains("season"),
            rx.hstack(
                rx.text(
                    f"{AppState.nfl_state['season']} Season",
                    size="2",
                    weight="medium",
                    class_name="hidden sm:block",
                ),
                rx.badge(
                    rx.cond(
                        AppState.nfl_state["season_type"] == "off",
                        "Offseason",
                        rx.cond(
                            AppState.nfl_state["week"].to(int) == 0,
                            "Pre-Season",
                            f"Week {AppState.nfl_state['week']}",
                        ),
                    ),
                    color_scheme="blue",
                    variant="soft",
                ),
                spacing="2",
                align="center",
            ),
        ),
        rx.hstack(
            rx.link(
                rx.icon("video", size=18),
                href="https://www.youtube.com/channel/UCMD4pfyYl2hxHez34eqnfkQ",
                is_external=True,
                class_name=social_link_class,
            ),
            rx.link(
                rx.icon("message-circle", size=18),
                href="https://discord.gg/g367Tt9j",
                is_external=True,
                class_name=social_link_class,
            ),
            rx.link(
                rx.icon("wifi", size=18),
                href="https://x.com/StonedLack",
                is_external=True,
                class_name=social_link_class,
            ),
            rx.link(
                rx.icon("webcam", size=18),
                href="https://www.twitch.tv/stoned_lack/videos?filter=archives",
                is_external=True,
                class_name=social_link_class,
            ),
            spacing="3",
            align="center",
            class_name="hidden sm:flex",
        ),
        rx.button(
            _theme_icon_lg(),
            on_click=rx.toggle_color_mode,
            variant="ghost",
            color_scheme="gray",
        ),
        spacing="4",
        align="center",
        width="100%",
        height="72px",
        padding_x="24px",
        position="sticky",
        top="0",
        z_index="30",
        class_name=t(
            "bg-[#040507] border-b border-white/5 shadow-sm",
            "bg-white border-b border-gray-200",
        ),
    )


def layout(content: rx.Component) -> rx.Component:
    return rx.flex(
        sidebar_std(),
        rx.flex(
            header_std(),
            rx.box(
                rx.box(
                    content,
                    width="100%",
                    max_width="1280px",
                    margin="0 auto",
                    padding_x=["16px", "24px", "32px"],
                    padding_y=["20px", "24px", "32px"],
                    padding_bottom=["40px", "40px", "40px"],
                ),
                flex="1",
                width="100%",
                overflow_y="auto",
                class_name=t("bg-[#020617]", "bg-[#F8F9FC]"),
            ),
            mobile_drawer_std(),
            direction="column",
            flex="1",
            min_width="0",
            height="100vh",
            overflow="hidden",
        ),
        width="100vw",
        height="100vh",
        overflow="hidden",
        class_name=t(
            "font-['Inter'] text-[#F3F4F6] bg-[#020617]",
            "font-['Inter'] text-gray-900 bg-[#F8F9FC]",
        ),
    )
