import reflex as rx
from app.states.app_state import AppState


def sidebar() -> rx.Component:
    nav_items = [
        {"icon": "home", "label": "Home", "href": "/"},
        {"icon": "trophy", "label": "Leagues", "href": "/leagues"},
        {"icon": "swords", "label": "Matchups", "href": "/matchups"},
        {"icon": "list-ordered", "label": "Standings", "href": "/standings"},
        {"icon": "users", "label": "Rosters", "href": "/rosters"},
        {"icon": "file-text", "label": "Drafts", "href": "/drafts"},
        {"icon": "trending-up", "label": "Trending", "href": "/trending"},
        {"icon": "mic", "label": "Community", "href": "/community"},
    ]
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.icon("podcast", class_name="h-8 w-8 text-emerald-500"),
                rx.el.span("FF Hub", class_name="text-xl font-bold text-white"),
                class_name="flex h-20 items-center gap-3 border-b border-gray-800 px-6",
            ),
            rx.el.nav(
                rx.foreach(
                    nav_items,
                    lambda item: rx.el.a(
                        rx.icon(item["icon"], class_name="h-5 w-5 mr-3"),
                        rx.el.span(item["label"]),
                        href=item["href"],
                        class_name="flex items-center px-4 py-3 text-gray-300 hover:bg-gray-800 hover:text-emerald-400 rounded-lg transition-colors font-medium mb-1",
                    ),
                ),
                class_name="flex flex-col p-4",
            ),
            class_name="flex-1 overflow-auto",
        ),
        class_name="flex flex-col border-r border-gray-800 bg-[#1a1a2e] w-64 h-screen shrink-0 hidden md:flex",
    )


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.h2(
                "Fantasy Football Hub",
                class_name="text-xl font-bold text-gray-900 hidden sm:block",
            ),
            rx.el.div(
                rx.cond(
                    AppState.nfl_state.contains("season"),
                    rx.el.div(
                        rx.el.span(
                            f"{AppState.nfl_state['season']} Season",
                            class_name="text-sm font-semibold text-gray-700",
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
                            class_name="ml-3 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-md text-xs font-bold shadow-sm",
                        ),
                        class_name="flex items-center",
                    ),
                    rx.el.div(
                        class_name="animate-pulse bg-gray-200 h-6 w-40 rounded-md"
                    ),
                ),
                class_name="flex items-center gap-4 ml-auto",
            ),
            class_name="flex items-center justify-between h-20 px-6 sm:px-10 bg-white border-b border-gray-200",
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
                class_name="p-6 md:p-10 max-w-7xl mx-auto h-[calc(100vh-5rem)] overflow-auto",
            ),
            class_name="flex-1 flex flex-col bg-gray-50 h-screen",
        ),
        class_name="flex h-screen w-screen font-['Inter'] text-gray-900 overflow-hidden",
    )