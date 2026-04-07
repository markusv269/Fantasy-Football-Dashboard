import reflex as rx
from app.states.community_state import CommunityState
from app.components.layout import layout


def poll_option_active(poll: dict, option: dict, index: int) -> rx.Component:
    return rx.el.button(
        rx.el.div(class_name="w-4 h-4 rounded-full border-2 border-gray-300 mr-3"),
        rx.el.span(option["text"].to_string(), class_name="font-medium text-gray-700"),
        on_click=CommunityState.vote_poll(poll["id"].to_string(), index),
        class_name="w-full flex items-center p-3 rounded-xl hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all mb-2 text-left",
    )


def poll_option_result(poll: dict, option: dict) -> rx.Component:
    votes = option["votes"].to(int)
    total = poll["total_votes"].to(int)
    pct = rx.cond(total > 0, votes * 100 / total, 0)
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                option["text"].to_string(),
                class_name="text-sm font-semibold text-gray-800 z-10 relative",
            ),
            rx.el.span(
                f"{pct.to(int)}%",
                class_name="text-sm font-bold text-gray-600 z-10 relative",
            ),
            class_name="flex justify-between mb-1 px-2",
        ),
        rx.el.div(
            rx.el.div(
                class_name="h-full bg-emerald-100 rounded-full transition-all duration-1000",
                style={"width": f"{pct}%"},
            ),
            class_name="h-8 w-full bg-gray-100 rounded-full overflow-hidden absolute top-0 left-0",
        ),
        class_name="relative py-1.5 mb-2",
    )


def poll_card(poll: dict) -> rx.Component:
    has_voted = CommunityState.voted_polls.contains(poll["id"].to_string())
    is_closed = ~poll["is_active"].to(bool)
    show_results = has_voted | is_closed
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                poll["question"].to_string(),
                class_name="text-lg font-bold text-gray-900",
            ),
            rx.cond(
                is_closed,
                rx.el.span(
                    "Closed",
                    class_name="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-md font-bold uppercase tracking-wider",
                ),
                rx.el.span(
                    "Active",
                    class_name="bg-emerald-100 text-emerald-700 text-xs px-2 py-1 rounded-md font-bold uppercase tracking-wider",
                ),
            ),
            class_name="flex justify-between items-start mb-4 gap-4",
        ),
        rx.cond(
            show_results,
            rx.el.div(
                rx.foreach(
                    poll["options"].to(list[dict[str, str | int]]),
                    lambda opt, i: poll_option_result(poll, opt),
                )
            ),
            rx.el.div(
                rx.foreach(
                    poll["options"].to(list[dict[str, str | int]]),
                    lambda opt, i: poll_option_active(poll, opt, i),
                )
            ),
        ),
        rx.el.div(
            rx.el.span(
                f"{poll['total_votes'].to_string()} votes",
                class_name="text-sm text-gray-500 font-medium",
            ),
            rx.cond(
                has_voted,
                rx.el.span(
                    rx.icon("circle_check", class_name="w-4 h-4 mr-1 inline"),
                    "You voted!",
                    class_name="text-sm text-emerald-600 font-bold flex items-center",
                ),
                rx.el.span(""),
            ),
            class_name="flex justify-between items-center mt-4 pt-4 border-t border-gray-100",
        ),
        class_name="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm mb-4",
    )


def podcast_card(ep: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    f"Ep {ep['episode_number'].to_string()}",
                    class_name="text-xs font-bold text-white bg-emerald-600 px-2 py-1 rounded-md",
                ),
                rx.el.span(
                    ep["date"].to_string(),
                    class_name="text-xs text-gray-500 font-medium",
                ),
                class_name="flex justify-between items-center mb-2",
            ),
            rx.el.h4(
                ep["title"].to_string(), class_name="font-bold text-gray-900 mb-1"
            ),
            rx.el.p(
                ep["description"].to_string(),
                class_name="text-sm text-gray-600 line-clamp-2 mb-3",
            ),
            rx.el.div(
                rx.el.span(
                    rx.icon("clock", class_name="w-3 h-3 mr-1 inline"),
                    ep["duration"].to_string(),
                    class_name="text-xs text-gray-500 flex items-center",
                ),
                rx.el.a(
                    rx.icon("play", class_name="w-4 h-4 mr-1 inline"),
                    "Listen",
                    href=ep["link"].to_string(),
                    class_name="text-sm font-bold text-emerald-600 hover:text-emerald-700 flex items-center transition-colors",
                ),
                class_name="flex justify-between items-center",
            ),
        ),
        class_name="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm mb-4 hover:border-emerald-200 transition-colors",
    )


def registration_form() -> rx.Component:
    return rx.el.div(
        rx.cond(
            CommunityState.registration_submitted,
            rx.el.div(
                rx.icon(
                    "message_circle_check",
                    class_name="w-16 h-16 text-emerald-500 mx-auto mb-4",
                ),
                rx.el.h3(
                    "Registration Received!",
                    class_name="text-xl font-bold text-gray-900 text-center mb-2",
                ),
                rx.el.p(
                    "We've added your details to the waitlist. Keep an eye on your email!",
                    class_name="text-center text-gray-600",
                ),
                class_name="bg-emerald-50 rounded-2xl p-8 border border-emerald-100 flex flex-col items-center justify-center",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Team Name",
                        class_name="block text-sm font-bold text-gray-700 mb-1",
                    ),
                    rx.el.input(
                        placeholder="The Gridiron Goats",
                        on_change=CommunityState.set_reg_team_name,
                        class_name="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                        default_value=CommunityState.reg_team_name,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Email Address",
                        class_name="block text-sm font-bold text-gray-700 mb-1",
                    ),
                    rx.el.input(
                        placeholder="coach@example.com",
                        type="email",
                        on_change=CommunityState.set_reg_email,
                        class_name="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                        default_value=CommunityState.reg_email,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Sleeper Username (Optional)",
                        class_name="block text-sm font-bold text-gray-700 mb-1",
                    ),
                    rx.el.input(
                        placeholder="sleeper_user_123",
                        on_change=CommunityState.set_reg_sleeper_username,
                        class_name="w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                        default_value=CommunityState.reg_sleeper_username,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Preferred Format",
                        class_name="block text-sm font-bold text-gray-700 mb-1",
                    ),
                    rx.el.div(
                        rx.el.select(
                            rx.el.option("Redraft", value="Redraft"),
                            rx.el.option("Dynasty", value="Dynasty"),
                            rx.el.option("Keeper", value="Keeper"),
                            rx.el.option("Best Ball", value="Best Ball"),
                            value=CommunityState.reg_preferred_league,
                            on_change=CommunityState.set_reg_preferred_league,
                            class_name="appearance-none bg-white border border-gray-300 text-gray-900 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 block w-full px-4 py-2 outline-none font-medium",
                        ),
                        rx.icon(
                            "chevron-down",
                            class_name="absolute right-3 top-3 h-4 w-4 text-gray-500 pointer-events-none",
                        ),
                        class_name="relative",
                    ),
                    class_name="mb-6",
                ),
                rx.el.button(
                    "Submit Registration",
                    on_click=CommunityState.submit_registration,
                    class_name="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl transition-colors shadow-sm",
                ),
                class_name="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm",
            ),
        ),
        rx.el.div(
            rx.el.span(
                f"{CommunityState.registrations.length().to_string()} Current Registrations",
                class_name="text-sm font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full",
            ),
            class_name="mt-4 flex justify-center",
        ),
    )


def community_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Community Hub", class_name="text-3xl font-bold text-gray-900 mb-2"
                ),
                rx.el.p(
                    "Engage with polls, sign up for new leagues, and catch the latest podcast episodes.",
                    class_name="text-gray-500 font-medium",
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        rx.icon(
                            "bar-chart-3",
                            class_name="w-6 h-6 mr-2 text-emerald-600 inline",
                        ),
                        "Community Polls",
                        class_name="text-xl font-bold text-gray-800 mb-4 flex items-center",
                    ),
                    rx.foreach(
                        CommunityState.polls.to(
                            list[
                                dict[str, str | int | bool | list[dict[str, str | int]]]
                            ]
                        ),
                        poll_card,
                    ),
                    class_name="col-span-1",
                ),
                rx.el.div(
                    rx.el.h2(
                        rx.icon(
                            "user-plus",
                            class_name="w-6 h-6 mr-2 text-emerald-600 inline",
                        ),
                        "Join a League",
                        class_name="text-xl font-bold text-gray-800 mb-4 flex items-center",
                    ),
                    registration_form(),
                    class_name="col-span-1",
                ),
                rx.el.div(
                    rx.el.h2(
                        rx.icon(
                            "mic", class_name="w-6 h-6 mr-2 text-emerald-600 inline"
                        ),
                        "Latest Episodes",
                        class_name="text-xl font-bold text-gray-800 mb-4 flex items-center",
                    ),
                    rx.foreach(CommunityState.episodes, podcast_card),
                    rx.el.a(
                        "View All Episodes",
                        href="#",
                        class_name="block w-full text-center p-3 text-emerald-600 font-bold hover:text-emerald-700 bg-emerald-50 rounded-xl transition-colors",
                    ),
                    class_name="col-span-1",
                ),
                class_name="grid grid-cols-1 lg:grid-cols-3 gap-8",
            ),
        )
    )