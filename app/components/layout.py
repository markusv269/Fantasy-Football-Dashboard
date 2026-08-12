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
    {"icon": "layout-grid", "label": "ADP Board", "href": "/adp"},
    {"icon": "trending-up", "label": "Trending", "href": "/trending"},
    {"icon": "mic", "label": "Community", "href": "/community"},
    {"icon": "archive", "label": "Archiv", "href": "/archive"},
    {"icon": "store", "label": "Fantasybörse", "href": "/fantasyboerse"},
    {"icon": "clipboard-list", "label": "Warteliste", "href": "/waitinglist"},
    {
        "icon": "user-plus",
        "label": "Redraft 2026",
        "href": "/redraft-registration",
    },
    # {
    #     "icon": "shuffle",
    #     "label": "Auslosung 2026",
    #     "href": "/redraft-auslosung",
    # },
    {"icon": "shield", "label": "Admin", "href": "/admin"},
]


def _nav_link(item: dict) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(item["icon"], size=18),
            rx.text(item["label"], size="2", weight="bold"),
            spacing="3",
            align="center",
            width="100%",
        ),
        href=item["href"],
        underline="none",
        width="100%",
        padding_x="12px",
        padding_y="10px",
        border_radius="10px",
        class_name=t(
            "text-slate-300 hover:bg-[#DC2626]/10 hover:text-[#DC2626] transition-all duration-200",
            "text-gray-800 hover:bg-gray-200 hover:text-[#DC2626] transition-all duration-200",
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
        rx.box(
            rx.vstack(
                *[_nav_link(item) for item in nav_items],
                spacing="1",
                width="100%",
                padding="10px",
                border_radius="16px",
                class_name=t(
                    "bg-[#0D1117] border border-white/10 shadow-[inset_0_2px_4px_rgba(0,0,0,0.3)]",
                    "bg-gray-50 border border-gray-200 shadow-[inset_0_2px_4px_rgba(0,0,0,0.03)]",
                ),
            ),
            width="100%",
            padding="16px",
            flex="1",
            overflow_y="auto",
            class_name="no-scrollbar",
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
            class_name="bg-black/80 backdrop-blur-xl md:hidden transition-opacity duration-300",
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
                    rx.icon("x", size=22),
                    on_click=ThemeState.close_mobile_sidebar,
                    variant="solid",
                    color_scheme="gray",
                    radius="full",
                    size="2",
                    class_name=t(
                        "bg-white/10 text-white", "bg-gray-200 text-gray-900"
                    ),
                ),
                width="100%",
                padding="24px",
                align="center",
                class_name=t(
                    "border-b border-white/20 bg-[#161B22] text-white",
                    "border-b border-gray-300 bg-gray-50 text-gray-900",
                ),
            ),
            rx.box(
                rx.vstack(
                    *[
                        rx.link(
                            rx.hstack(
                                rx.icon(item["icon"], size=20),
                                rx.text(item["label"], size="4", weight="bold"),
                                rx.spacer(),
                                rx.icon(
                                    "chevron-right",
                                    size=16,
                                    class_name="opacity-60",
                                ),
                                spacing="4",
                                align="center",
                                width="100%",
                            ),
                            href=item["href"],
                            on_click=ThemeState.close_mobile_sidebar,
                            underline="none",
                            width="100%",
                            padding_x="20px",
                            padding_y="18px",
                            class_name=t(
                                "text-white border-b border-white/10 last:border-0 hover:bg-white/5 active:bg-white/10 transition-colors",
                                "text-gray-900 border-b border-gray-200 last:border-0 hover:bg-gray-50 active:bg-gray-100 transition-colors",
                            ),
                        )
                        for item in nav_items
                    ],
                    spacing="0",
                    width="100%",
                    border_radius="24px",
                    overflow="hidden",
                    class_name=t(
                        "bg-[#161B22] border border-white/10 shadow-xl",
                        "bg-white border border-gray-200 shadow-md",
                    ),
                ),
                padding="20px",
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
                        "bg-white text-black hover:bg-gray-200",
                        "bg-gray-900 text-white",
                    ),
                ),
                padding="24px",
                width="100%",
                class_name=t(
                    "bg-[#161B22] border-t border-white/20",
                    "bg-gray-50 border-t border-gray-300",
                ),
            ),
            spacing="0",
            position="fixed",
            bottom="0",
            left="0",
            right="0",
            z_index="50",
            max_height="90vh",
            border_top_left_radius="32px",
            border_top_right_radius="32px",
            transform=rx.cond(
                ThemeState.mobile_sidebar_open,
                "translateY(0)",
                "translateY(100%)",
            ),
            transition="transform 500ms cubic-bezier(0.16, 1, 0.3, 1)",
            class_name=t(
                "bg-[#0D1117] shadow-[0_-20px_50px_-12px_rgba(0,0,0,0.8)] border-t border-white/30 md:hidden",
                "bg-white shadow-[0_-20px_50px_-12px_rgba(0,0,0,0.3)] border-t border-gray-400 md:hidden",
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


def layout(content: rx.Component, full_width: bool = False) -> rx.Component:
    return rx.flex(
        sidebar_std(),
        rx.flex(
            header_std(),
            rx.box(
                rx.box(
                    content,
                    width="100%",
                    max_width=rx.cond(full_width, "100%", "1280px"),
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
