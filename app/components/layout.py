import reflex as rx
from app.states.app_state import AppState
from app.states.theme_state import ThemeState
from app.states.user_state import UserState
from app.theme import t, PAGE_BG, INPUT, BTN_PRIMARY, H2

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
bottom_nav_items = [
    {"icon": "house", "label": "Home", "href": "/"},
    {"icon": "trophy", "label": "Leagues", "href": "/leagues"},
    {"icon": "swords", "label": "Matchups", "href": "/matchups"},
    {"icon": "file-text", "label": "Drafts", "href": "/drafts"},
    {"icon": "menu", "label": "More", "href": "#"},
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
            "text-gray-300 hover:bg-gray-800 hover:text-[#DC2626] transition-colors",
            "text-gray-700 hover:bg-gray-100 hover:text-[#DC2626] transition-colors",
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
                "border-b border-gray-800", "border-b border-gray-200"
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
                    rx.icon(
                        rx.cond(ThemeState.is_dark, "sun", "moon"), size=16
                    ),
                    rx.text(
                        rx.cond(ThemeState.is_dark, "Light Mode", "Dark Mode"),
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                on_click=ThemeState.toggle_color_mode,
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
            "bg-[#161926] border-r border-gray-800 hidden md:flex",
            "bg-white border-r border-gray-200 hidden md:flex",
        ),
    )


def _bottom_nav_item(item: dict) -> rx.Component:
    inner = rx.vstack(
        rx.icon(item["icon"], size=22),
        rx.text(item["label"], size="1", weight="medium"),
        spacing="1",
        align="center",
        justify="center",
    )
    return rx.cond(
        item["label"] == "More",
        rx.button(
            inner,
            on_click=ThemeState.toggle_mobile_sidebar,
            variant="ghost",
            color_scheme="gray",
            width="100%",
            height="100%",
        ),
        rx.link(
            inner,
            href=item["href"],
            underline="none",
            width="100%",
            height="100%",
            display="flex",
            align_items="center",
            justify_content="center",
            class_name=t(
                "text-gray-400 hover:text-[#DC2626]",
                "text-gray-500 hover:text-[#DC2626]",
            ),
        ),
    )


def mobile_bottom_nav() -> rx.Component:
    return rx.hstack(
        *[
            rx.box(_bottom_nav_item(item), flex="1", height="100%")
            for item in bottom_nav_items
        ],
        spacing="0",
        width="100%",
        height="64px",
        position="fixed",
        bottom="0",
        left="0",
        right="0",
        z_index="40",
        class_name=t(
            "bg-[#161926] border-t border-gray-800 md:hidden",
            "bg-white border-t border-gray-200 md:hidden",
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
            class_name="bg-black/50 md:hidden",
        ),
        rx.vstack(
            rx.hstack(
                rx.heading("More Options", size="4", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=18),
                    on_click=ThemeState.close_mobile_sidebar,
                    variant="ghost",
                    color_scheme="gray",
                ),
                width="100%",
                padding="16px",
                align="center",
                class_name=t(
                    "border-b border-gray-800",
                    "border-b border-gray-200",
                ),
            ),
            rx.vstack(
                *[
                    rx.link(
                        rx.hstack(
                            rx.icon(item["icon"], size=18),
                            rx.text(item["label"], size="3"),
                            spacing="3",
                            align="center",
                        ),
                        href=item["href"],
                        on_click=ThemeState.close_mobile_sidebar,
                        underline="none",
                        width="100%",
                        padding="14px",
                        class_name=t(
                            "text-gray-300 border-b border-gray-800",
                            "text-gray-700 border-b border-gray-100",
                        ),
                    )
                    for item in nav_items
                ],
                spacing="0",
                width="100%",
                overflow_y="auto",
                flex="1",
            ),
            rx.button(
                rx.hstack(
                    rx.icon(
                        rx.cond(ThemeState.is_dark, "sun", "moon"), size=16
                    ),
                    rx.text(
                        rx.cond(ThemeState.is_dark, "Light Mode", "Dark Mode"),
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                on_click=ThemeState.toggle_color_mode,
                variant="soft",
                color_scheme="gray",
                margin="16px",
            ),
            spacing="0",
            position="fixed",
            bottom="0",
            left="0",
            right="0",
            z_index="50",
            max_height="80vh",
            border_top_left_radius="16px",
            border_top_right_radius="16px",
            transform=rx.cond(
                ThemeState.mobile_sidebar_open,
                "translateY(0)",
                "translateY(100%)",
            ),
            transition="transform 300ms",
            class_name=t(
                "bg-[#161926] md:hidden",
                "bg-white md:hidden",
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
            rx.icon("menu", size=20),
            on_click=ThemeState.toggle_mobile_sidebar,
            variant="ghost",
            color_scheme="gray",
            class_name="md:hidden",
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
            rx.icon(rx.cond(ThemeState.is_dark, "sun", "moon"), size=18),
            on_click=ThemeState.toggle_color_mode,
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
            "bg-[#161926] border-b border-gray-800",
            "bg-white border-b border-gray-200",
        ),
    )


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.icon(
                        "menu", class_name=t("text-white", "text-gray-900")
                    ),
                    on_click=ThemeState.toggle_mobile_sidebar,
                    class_name="md:hidden mr-4",
                ),
                rx.el.h2(
                    "Stoned Lack Fantasy",
                    class_name=t(
                        "text-xl font-bold text-white",
                        "text-xl font-bold text-gray-900",
                    ),
                ),
                class_name="flex items-center",
            ),
            rx.el.div(
                rx.cond(
                    AppState.nfl_state.contains("season"),
                    rx.el.div(
                        rx.el.span(
                            f"{AppState.nfl_state['season']} Season",
                            class_name=t(
                                "text-sm font-semibold text-gray-300",
                                "text-sm font-semibold text-gray-700",
                            ),
                        ),
                        rx.el.span(
                            rx.cond(
                                AppState.nfl_state["season_type"] == "off",
                                "Offseason",
                                rx.cond(
                                    AppState.nfl_state["week"].to(int) == 0,
                                    "Pre-Season",
                                    f"Week {AppState.nfl_state['week']}",
                                ),
                            ),
                            class_name="ml-3 px-3 py-1 bg-[#5B7BA5]/20 text-[#5B7BA5] rounded-md text-xs font-bold shadow-sm",
                        ),
                        class_name="hidden sm:flex items-center",
                    ),
                    rx.el.div(
                        class_name="animate-pulse bg-gray-200 h-6 w-40 rounded-md hidden sm:block"
                    ),
                ),
                rx.el.div(
                    rx.el.a(
                        rx.icon(
                            "video",
                            class_name=t(
                                "w-5 h-5 text-gray-400 hover:text-[#DC2626]",
                                "w-5 h-5 text-gray-500 hover:text-[#DC2626]",
                            ),
                        ),
                        href="https://www.youtube.com/channel/UCMD4pfyYl2hxHez34eqnfkQ",
                        target="_blank",
                        class_name="p-1.5 rounded-lg transition-colors "
                        + t("hover:bg-gray-800", "hover:bg-gray-100"),
                    ),
                    rx.el.a(
                        rx.icon(
                            "message-circle",
                            class_name=t(
                                "w-5 h-5 text-gray-400 hover:text-[#5865F2]",
                                "w-5 h-5 text-gray-500 hover:text-[#5865F2]",
                            ),
                        ),
                        href="https://discord.gg/g367Tt9j",
                        target="_blank",
                        class_name="p-1.5 rounded-lg transition-colors "
                        + t("hover:bg-gray-800", "hover:bg-gray-100"),
                    ),
                    rx.el.a(
                        rx.icon(
                            "wifi",
                            class_name=t(
                                "w-5 h-5 text-gray-400 hover:text-white",
                                "w-5 h-5 text-gray-500 hover:text-black",
                            ),
                        ),
                        href="https://x.com/StonedLack",
                        target="_blank",
                        class_name="p-1.5 rounded-lg transition-colors "
                        + t("hover:bg-gray-800", "hover:bg-gray-100"),
                    ),
                    rx.el.a(
                        rx.icon(
                            "webcam",
                            class_name=t(
                                "w-5 h-5 text-gray-400 hover:text-[#9146FF]",
                                "w-5 h-5 text-gray-500 hover:text-[#9146FF]",
                            ),
                        ),
                        href="https://www.twitch.tv/stoned_lack/videos?filter=archives",
                        target="_blank",
                        class_name="p-1.5 rounded-lg transition-colors "
                        + t("hover:bg-gray-800", "hover:bg-gray-100"),
                    ),
                    class_name="hidden sm:flex items-center gap-1 ml-4",
                ),
                rx.el.button(
                    rx.icon(
                        rx.cond(ThemeState.is_dark, "sun", "moon"),
                        class_name=t(
                            "w-5 h-5 text-gray-400", "w-5 h-5 text-gray-600"
                        ),
                    ),
                    on_click=ThemeState.toggle_color_mode,
                    class_name="p-2 rounded-full hover:bg-gray-200/50 transition-colors md:hidden ml-2",
                ),
                class_name="flex items-center gap-4 ml-auto",
            ),
            class_name=t(
                "flex items-center justify-between h-20 px-6 sm:px-10 bg-[#161926] border-b border-gray-800",
                "flex items-center justify-between h-20 px-6 sm:px-10 bg-white border-b border-gray-200",
            ),
        ),
        class_name="shrink-0",
    )


def layout(content: rx.Component) -> rx.Component:
    return rx.theme(
        rx.flex(
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
                        padding_bottom=["96px", "96px", "40px"],
                    ),
                    flex="1",
                    width="100%",
                    overflow_y="auto",
                ),
                mobile_bottom_nav(),
                mobile_drawer_std(),
                direction="column",
                flex="1",
                min_width="0",
                height="100vh",
                overflow="hidden",
                class_name=t("bg-[#0F1119]", "bg-[#F8F9FC]"),
            ),
            width="100vw",
            height="100vh",
            overflow="hidden",
            class_name=t(
                "font-['Inter'] text-[#F3F4F6]",
                "font-['Inter'] text-gray-900",
            ),
        ),
        appearance=rx.cond(ThemeState.is_dark, "dark", "light"),
        accent_color="red",
        radius="large",
        has_background=True,
    )
