import reflex as rx
from app.states.app_state import AppState
from app.states.theme_state import ThemeState
from app.states.user_state import UserState
from app.theme import t, PAGE_BG, INPUT, BTN_PRIMARY, H2

nav_items = [
    {"icon": "home", "label": "Home", "href": "/"},
    {"icon": "trophy", "label": "Leagues", "href": "/leagues"},
    {"icon": "swords", "label": "Matchups", "href": "/matchups"},
    {"icon": "list-ordered", "label": "Standings", "href": "/standings"},
    {"icon": "users", "label": "Rosters", "href": "/rosters"},
    {"icon": "file-text", "label": "Drafts", "href": "/drafts"},
    {"icon": "trending-up", "label": "Trending", "href": "/trending"},
    {"icon": "mic", "label": "Community", "href": "/community"},
    {"icon": "clipboard-list", "label": "Warteliste", "href": "/waitinglist"},
]
bottom_nav_items = [
    {"icon": "home", "label": "Home", "href": "/"},
    {"icon": "trophy", "label": "Leagues", "href": "/leagues"},
    {"icon": "swords", "label": "Matchups", "href": "/matchups"},
    {"icon": "file-text", "label": "Drafts", "href": "/drafts"},
    {"icon": "menu", "label": "More", "href": "#"},
]


def sidebar() -> rx.Component:
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.icon("podcast", class_name="h-8 w-8 text-[#DC2626]"),
                rx.el.span(
                    "Stoned Lack",
                    class_name=t(
                        "text-xl font-bold text-white",
                        "text-xl font-bold text-gray-900",
                    ),
                ),
                class_name=t(
                    "flex h-20 items-center gap-3 border-b border-gray-800 px-6",
                    "flex h-20 items-center gap-3 border-b border-gray-200 px-6",
                ),
            ),
            rx.el.nav(
                rx.foreach(
                    nav_items,
                    lambda item: rx.el.a(
                        rx.icon(item["icon"], class_name="h-5 w-5 mr-3"),
                        rx.el.span(item["label"]),
                        href=item["href"],
                        class_name=t(
                            "flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-[#DC2626] rounded-lg transition-colors font-medium mb-1",
                            "flex items-center px-4 py-3 text-gray-600 hover:bg-gray-100 hover:text-[#DC2626] rounded-lg transition-colors font-medium mb-1",
                        ),
                    ),
                ),
                class_name="flex flex-col p-4 flex-1",
            ),
            rx.el.div(
                rx.cond(
                    UserState.is_logged_in,
                    rx.el.div(
                        rx.cond(
                            UserState.sleeper_avatar != "",
                            rx.image(
                                src=f"https://sleepercdn.com/avatars/{UserState.sleeper_avatar}",
                                class_name="w-8 h-8 rounded-full",
                            ),
                            rx.icon("user", class_name="w-8 h-8 text-gray-400"),
                        ),
                        rx.el.div(
                            rx.el.span(
                                UserState.sleeper_display_name,
                                class_name=t(
                                    "font-bold text-sm text-gray-200",
                                    "font-bold text-sm text-gray-800",
                                ),
                            ),
                            rx.el.button(
                                "×",
                                on_click=UserState.clear_username,
                                class_name="text-gray-400 hover:text-red-500 ml-2",
                            ),
                        ),
                        class_name="flex items-center gap-3 px-4 py-3 mb-2",
                    ),
                    rx.el.div(
                        rx.el.input(
                            placeholder="Sleeper Username",
                            on_change=UserState.set_username_input,
                            class_name=INPUT,
                        ),
                        rx.el.button(
                            "Login",
                            on_click=UserState.save_username,
                            class_name=BTN_PRIMARY + " text-sm px-4 py-2 mt-2 w-full",
                        ),
                        class_name="px-4 py-3 mb-2",
                    ),
                ),
                rx.el.button(
                    rx.icon(
                        rx.cond(ThemeState.is_dark, "sun", "moon"),
                        class_name="w-5 h-5 mr-3",
                    ),
                    rx.el.span(rx.cond(ThemeState.is_dark, "Light Mode", "Dark Mode")),
                    on_click=ThemeState.toggle_color_mode,
                    class_name=t(
                        "flex items-center w-full px-4 py-3 text-gray-300 hover:bg-gray-800 rounded-lg transition-colors font-medium",
                        "flex items-center w-full px-4 py-3 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors font-medium",
                    ),
                ),
                class_name="p-4 mt-auto border-t "
                + t("border-gray-800", "border-gray-200"),
            ),
            class_name="flex-1 flex flex-col overflow-auto",
        ),
        class_name=t(
            "flex flex-col border-r border-gray-800 bg-[#161926] w-64 h-screen shrink-0 hidden md:flex",
            "flex flex-col border-r border-gray-200 bg-white w-64 h-screen shrink-0 hidden md:flex",
        ),
    )


def mobile_bottom_nav() -> rx.Component:
    return rx.el.nav(
        rx.el.div(
            rx.foreach(
                bottom_nav_items,
                lambda item: rx.cond(
                    item["label"] == "More",
                    rx.el.button(
                        rx.icon(item["icon"], class_name="h-6 w-6 mb-1"),
                        rx.el.span(item["label"], class_name="text-[10px] font-medium"),
                        on_click=ThemeState.toggle_mobile_sidebar,
                        class_name=t(
                            "flex flex-col items-center justify-center w-full py-2 text-gray-400 hover:text-[#DC2626]",
                            "flex flex-col items-center justify-center w-full py-2 text-gray-500 hover:text-[#DC2626]",
                        ),
                    ),
                    rx.el.a(
                        rx.icon(item["icon"], class_name="h-6 w-6 mb-1"),
                        rx.el.span(item["label"], class_name="text-[10px] font-medium"),
                        href=item["href"],
                        class_name=t(
                            "flex flex-col items-center justify-center w-full py-2 text-gray-400 hover:text-[#DC2626]",
                            "flex flex-col items-center justify-center w-full py-2 text-gray-500 hover:text-[#DC2626]",
                        ),
                    ),
                ),
            ),
            class_name="flex justify-around items-center h-full max-w-md mx-auto",
        ),
        class_name=t(
            "fixed bottom-0 left-0 right-0 z-40 bg-[#161926] border-t border-gray-800 pb-safe md:hidden h-16",
            "fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 pb-safe md:hidden h-16",
        ),
    )


def mobile_drawer() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            on_click=ThemeState.close_mobile_sidebar,
            class_name=rx.cond(
                ThemeState.mobile_sidebar_open,
                "fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity",
                "hidden",
            ),
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "More Options",
                        class_name=t(
                            "text-lg font-bold text-white",
                            "text-lg font-bold text-gray-900",
                        ),
                    ),
                    rx.el.button(
                        rx.icon("x", class_name=t("text-gray-400", "text-gray-600")),
                        on_click=ThemeState.close_mobile_sidebar,
                    ),
                    class_name="flex justify-between items-center p-4 border-b "
                    + t("border-gray-800", "border-gray-200"),
                ),
                rx.el.nav(
                    rx.foreach(
                        nav_items[3:],
                        lambda item: rx.el.a(
                            rx.icon(item["icon"], class_name="h-5 w-5 mr-4"),
                            rx.el.span(item["label"]),
                            href=item["href"],
                            on_click=ThemeState.close_mobile_sidebar,
                            class_name=t(
                                "flex items-center px-4 py-4 text-gray-300 border-b border-gray-800",
                                "flex items-center px-4 py-4 text-gray-700 border-b border-gray-100",
                            ),
                        ),
                    ),
                    class_name="flex flex-col",
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon(
                            rx.cond(ThemeState.is_dark, "sun", "moon"),
                            class_name="w-5 h-5 mr-4",
                        ),
                        rx.el.span(
                            rx.cond(
                                ThemeState.is_dark,
                                "Switch to Light Mode",
                                "Switch to Dark Mode",
                            )
                        ),
                        on_click=ThemeState.toggle_color_mode,
                        class_name=t(
                            "flex items-center w-full px-4 py-4 text-gray-300",
                            "flex items-center w-full px-4 py-4 text-gray-700",
                        ),
                    ),
                    class_name="mt-auto p-4",
                ),
            ),
            class_name=rx.cond(
                ThemeState.mobile_sidebar_open,
                t(
                    "fixed bottom-0 left-0 right-0 z-50 bg-[#161926] rounded-t-2xl transform transition-transform duration-300 translate-y-0 md:hidden flex flex-col max-h-[80vh]",
                    "fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-2xl transform transition-transform duration-300 translate-y-0 md:hidden flex flex-col max-h-[80vh]",
                ),
                t(
                    "fixed bottom-0 left-0 right-0 z-50 bg-[#161926] rounded-t-2xl transform transition-transform duration-300 translate-y-full md:hidden flex flex-col max-h-[80vh]",
                    "fixed bottom-0 left-0 right-0 z-50 bg-white rounded-t-2xl transform transition-transform duration-300 translate-y-full md:hidden flex flex-col max-h-[80vh]",
                ),
            ),
        ),
    )


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.icon("menu", class_name=t("text-white", "text-gray-900")),
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
                            "youtube",
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
                            "twitter",
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
                            "twitch",
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
                        class_name=t("w-5 h-5 text-gray-400", "w-5 h-5 text-gray-600"),
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
    return rx.el.div(
        sidebar(),
        rx.el.main(
            header(),
            rx.el.div(
                content,
                class_name="p-6 md:p-10 max-w-7xl mx-auto h-[calc(100vh-5rem)] overflow-auto pb-24 md:pb-10",
            ),
            mobile_bottom_nav(),
            mobile_drawer(),
            class_name=t(
                "flex-1 flex flex-col bg-[#0F1119] h-screen",
                "flex-1 flex flex-col bg-[#F8F9FC] h-screen",
            ),
        ),
        class_name=t(
            "flex h-screen w-screen font-['Inter'] text-[#F3F4F6] overflow-hidden",
            "flex h-screen w-screen font-['Inter'] text-gray-900 overflow-hidden",
        ),
    )