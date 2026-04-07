import reflex as rx
from app.states.community_state import CommunityState
from app.states.theme_state import ThemeState
from app.components.layout import layout


def poll_option_active(poll: dict, option: dict, index: int) -> rx.Component:
    return rx.el.button(
        rx.el.div(
            class_name=rx.cond(
                ThemeState.is_dark,
                "w-4 h-4 rounded-full border-2 border-gray-600 mr-3",
                "w-4 h-4 rounded-full border-2 border-gray-300 mr-3",
            )
        ),
        rx.el.span(
            option["text"].to(str),
            class_name=rx.cond(
                ThemeState.is_dark,
                "font-medium text-gray-300",
                "font-medium text-gray-700",
            ),
        ),
        on_click=CommunityState.vote_poll(poll["id"].to(str), index),
        class_name=rx.cond(
            ThemeState.is_dark,
            "w-full flex items-center p-3 rounded-xl hover:bg-gray-800 border border-transparent hover:border-gray-700 transition-all mb-2 text-left",
            "w-full flex items-center p-3 rounded-xl hover:bg-gray-50 border border-transparent hover:border-gray-200 transition-all mb-2 text-left",
        ),
    )


def poll_option_result(poll: dict, option: dict) -> rx.Component:
    votes = option["votes"].to(int)
    total = poll["total_votes"].to(int)
    pct = rx.cond(total > 0, votes * 100 / total, 0)
    return rx.el.div(
        rx.el.div(
            rx.el.span(
                option["text"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "text-sm font-semibold text-gray-200 z-10 relative",
                    "text-sm font-semibold text-gray-800 z-10 relative",
                ),
            ),
            rx.el.span(
                f"{pct.to(int)}%",
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "text-sm font-bold text-gray-400 z-10 relative",
                    "text-sm font-bold text-gray-600 z-10 relative",
                ),
            ),
            class_name="flex justify-between mb-1 px-2",
        ),
        rx.el.div(
            rx.el.div(
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "h-full bg-emerald-500/30 rounded-full transition-all duration-1000",
                    "h-full bg-emerald-100 rounded-full transition-all duration-1000",
                ),
                style={"width": f"{pct}%"},
            ),
            class_name=rx.cond(
                ThemeState.is_dark,
                "h-8 w-full bg-gray-800 rounded-full overflow-hidden absolute top-0 left-0",
                "h-8 w-full bg-gray-100 rounded-full overflow-hidden absolute top-0 left-0",
            ),
        ),
        class_name="relative py-1.5 mb-2",
    )


def poll_card(poll: dict) -> rx.Component:
    has_voted = CommunityState.voted_polls.contains(poll["id"].to(str))
    is_closed = ~poll["is_active"].to(bool)
    show_results = has_voted | is_closed
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                poll["question"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "text-lg font-bold text-white",
                    "text-lg font-bold text-gray-900",
                ),
            ),
            rx.cond(
                is_closed,
                rx.el.span(
                    "Closed",
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "bg-gray-800 text-gray-400 text-xs px-2 py-1 rounded-md font-bold uppercase tracking-wider",
                        "bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-md font-bold uppercase tracking-wider",
                    ),
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
                f"{poll['total_votes'].to(str)} votes",
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "text-sm text-gray-400 font-medium",
                    "text-sm text-gray-500 font-medium",
                ),
            ),
            rx.cond(
                has_voted,
                rx.el.span(
                    rx.icon("circle_check", class_name="w-4 h-4 mr-1 inline"),
                    "You voted!",
                    class_name="text-sm text-emerald-500 font-bold flex items-center",
                ),
                rx.el.span(""),
            ),
            class_name=rx.cond(
                ThemeState.is_dark,
                "flex justify-between items-center mt-4 pt-4 border-t border-gray-800",
                "flex justify-between items-center mt-4 pt-4 border-t border-gray-100",
            ),
        ),
        class_name=rx.cond(
            ThemeState.is_dark,
            "bg-[#1C2033] p-6 rounded-2xl border border-gray-800 shadow-sm mb-4",
            "bg-white p-6 rounded-2xl border border-gray-200 shadow-sm mb-4",
        ),
    )


def youtube_card(video: dict) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.image(
                src=video["thumbnail"].to(str), class_name="w-full h-full object-cover"
            ),
            rx.cond(
                video["is_short"].to(bool),
                rx.el.span(
                    "Short",
                    class_name="absolute top-2 right-2 bg-[#DC2626] text-white text-[10px] font-bold px-2 py-0.5 rounded-md",
                ),
            ),
            class_name=rx.cond(
                ThemeState.is_dark,
                "relative aspect-video w-full overflow-hidden rounded-xl bg-gray-800",
                "relative aspect-video w-full overflow-hidden rounded-xl bg-gray-100",
            ),
        ),
        rx.el.div(
            rx.el.h4(
                video["title"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "font-bold text-sm text-white line-clamp-2 mb-1",
                    "font-bold text-sm text-gray-900 line-clamp-2 mb-1",
                ),
            ),
            rx.el.div(
                rx.el.span(
                    video["date_str"].to(str),
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-xs text-gray-400 font-medium",
                        "text-xs text-gray-500 font-medium",
                    ),
                ),
                rx.el.span(
                    rx.icon("eye", class_name="w-3 h-3 mr-1 inline"),
                    f"{video['views'].to(str)} Views",
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-xs text-gray-400 font-medium flex items-center",
                        "text-xs text-gray-500 font-medium flex items-center",
                    ),
                ),
                class_name="flex justify-between items-center",
            ),
            class_name="mt-2",
        ),
        href=video["link"].to(str),
        target="_blank",
        class_name=rx.cond(
            ThemeState.is_dark,
            "block bg-[#1C2033] rounded-2xl border border-gray-800 shadow-sm hover:shadow-md transition-shadow overflow-hidden p-3 mb-4",
            "block bg-white rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden p-3 mb-4",
        ),
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
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-xl font-bold text-white text-center mb-2",
                        "text-xl font-bold text-gray-900 text-center mb-2",
                    ),
                ),
                rx.el.p(
                    "We've added your details to the waitlist. Keep an eye on your email!",
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-center text-gray-400",
                        "text-center text-gray-600",
                    ),
                ),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "bg-emerald-500/10 rounded-2xl p-8 border border-emerald-500/20 flex flex-col items-center justify-center",
                    "bg-emerald-50 rounded-2xl p-8 border border-emerald-100 flex flex-col items-center justify-center",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Team Name",
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "block text-sm font-bold text-gray-300 mb-1",
                            "block text-sm font-bold text-gray-700 mb-1",
                        ),
                    ),
                    rx.el.input(
                        placeholder="The Gridiron Goats",
                        on_change=CommunityState.set_reg_team_name,
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "w-full px-4 py-2 bg-[#0F1119] text-white border border-gray-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                            "w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                        ),
                        default_value=CommunityState.reg_team_name,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Email Address",
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "block text-sm font-bold text-gray-300 mb-1",
                            "block text-sm font-bold text-gray-700 mb-1",
                        ),
                    ),
                    rx.el.input(
                        placeholder="coach@example.com",
                        type="email",
                        on_change=CommunityState.set_reg_email,
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "w-full px-4 py-2 bg-[#0F1119] text-white border border-gray-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                            "w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                        ),
                        default_value=CommunityState.reg_email,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Sleeper Username (Optional)",
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "block text-sm font-bold text-gray-300 mb-1",
                            "block text-sm font-bold text-gray-700 mb-1",
                        ),
                    ),
                    rx.el.input(
                        placeholder="sleeper_user_123",
                        on_change=CommunityState.set_reg_sleeper_username,
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "w-full px-4 py-2 bg-[#0F1119] text-white border border-gray-700 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                            "w-full px-4 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none",
                        ),
                        default_value=CommunityState.reg_sleeper_username,
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Preferred Format",
                        class_name=rx.cond(
                            ThemeState.is_dark,
                            "block text-sm font-bold text-gray-300 mb-1",
                            "block text-sm font-bold text-gray-700 mb-1",
                        ),
                    ),
                    rx.el.div(
                        rx.el.select(
                            rx.el.option("Redraft", value="Redraft"),
                            rx.el.option("Dynasty", value="Dynasty"),
                            rx.el.option("Keeper", value="Keeper"),
                            rx.el.option("Best Ball", value="Best Ball"),
                            value=CommunityState.reg_preferred_league,
                            on_change=CommunityState.set_reg_preferred_league,
                            class_name=rx.cond(
                                ThemeState.is_dark,
                                "appearance-none bg-[#0F1119] border border-gray-700 text-white rounded-xl focus:ring-emerald-500 focus:border-emerald-500 block w-full px-4 py-2 outline-none font-medium",
                                "appearance-none bg-white border border-gray-300 text-gray-900 rounded-xl focus:ring-emerald-500 focus:border-emerald-500 block w-full px-4 py-2 outline-none font-medium",
                            ),
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
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "bg-[#1C2033] p-6 rounded-2xl border border-gray-800 shadow-sm",
                    "bg-white p-6 rounded-2xl border border-gray-200 shadow-sm",
                ),
            ),
        ),
        rx.el.div(
            rx.el.span(
                f"{CommunityState.registrations.length().to(str)} Current Registrations",
                class_name="text-sm font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full",
            ),
            class_name="mt-4 flex justify-center",
        ),
    )


def news_card(news: dict) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                news["title"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "text-lg font-bold text-white mb-2",
                    "text-lg font-bold text-gray-900 mb-2",
                ),
            ),
            rx.el.span(
                news["date"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "text-xs text-gray-400 font-medium block mb-3",
                    "text-xs text-gray-500 font-medium block mb-3",
                ),
            ),
            rx.el.p(
                news["content"].to(str),
                class_name=rx.cond(
                    ThemeState.is_dark,
                    "text-sm text-gray-300 line-clamp-3 leading-relaxed",
                    "text-sm text-gray-600 line-clamp-3 leading-relaxed",
                ),
            ),
        ),
        class_name=rx.cond(
            ThemeState.is_dark,
            "bg-[#1C2033] p-6 rounded-2xl border border-gray-800 shadow-sm mb-4 hover:border-emerald-500 transition-colors",
            "bg-white p-6 rounded-2xl border border-gray-200 shadow-sm mb-4 hover:border-emerald-200 transition-colors",
        ),
    )


def community_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Stoned Lack Community",
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-3xl font-bold text-white mb-2",
                        "text-3xl font-bold text-gray-900 mb-2",
                    ),
                ),
                rx.el.p(
                    "Polls, News, Liga-Anmeldung und die neuesten Podcast-Folgen.",
                    class_name=rx.cond(
                        ThemeState.is_dark,
                        "text-gray-400 font-medium",
                        "text-gray-500 font-medium",
                    ),
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            rx.icon(
                                "newspaper",
                                class_name="w-6 h-6 mr-2 text-[#DC2626] inline",
                            ),
                            "📰 Neuigkeiten",
                            class_name=rx.cond(
                                ThemeState.is_dark,
                                "text-xl font-bold text-white mb-4 flex items-center",
                                "text-xl font-bold text-gray-800 mb-4 flex items-center",
                            ),
                        ),
                        rx.cond(
                            CommunityState.news_items.length() > 0,
                            rx.el.div(rx.foreach(CommunityState.news_items, news_card)),
                            rx.el.p(
                                "Keine Neuigkeiten vorhanden.",
                                class_name="text-gray-500 italic",
                            ),
                        ),
                        class_name="mb-8",
                    ),
                    rx.el.div(
                        rx.el.h2(
                            rx.icon(
                                "bar-chart-3",
                                class_name="w-6 h-6 mr-2 text-[#DC2626] inline",
                            ),
                            "📊 Community Polls",
                            class_name=rx.cond(
                                ThemeState.is_dark,
                                "text-xl font-bold text-white mb-4 flex items-center",
                                "text-xl font-bold text-gray-800 mb-4 flex items-center",
                            ),
                        ),
                        rx.foreach(
                            CommunityState.polls.to(
                                list[
                                    dict[
                                        str,
                                        str | int | bool | list[dict[str, str | int]],
                                    ]
                                ]
                            ),
                            poll_card,
                        ),
                    ),
                    class_name="col-span-1 lg:col-span-2",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            rx.icon(
                                "user-plus",
                                class_name="w-6 h-6 mr-2 text-[#DC2626] inline",
                            ),
                            "Join a League",
                            class_name=rx.cond(
                                ThemeState.is_dark,
                                "text-xl font-bold text-white mb-4 flex items-center",
                                "text-xl font-bold text-gray-800 mb-4 flex items-center",
                            ),
                        ),
                        registration_form(),
                        class_name="mb-8",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.h2(
                                rx.icon(
                                    "circle_play",
                                    class_name="w-6 h-6 mr-2 text-[#DC2626] inline",
                                ),
                                "🎬 Stoned Lack YouTube",
                                class_name=rx.cond(
                                    ThemeState.is_dark,
                                    "text-xl font-bold text-white flex items-center",
                                    "text-xl font-bold text-gray-800 flex items-center",
                                ),
                            ),
                            rx.el.div(
                                rx.el.button(
                                    "All",
                                    on_click=CommunityState.set_youtube_filter("All"),
                                    class_name=rx.cond(
                                        CommunityState.youtube_filter == "All",
                                        "px-3 py-1 text-xs font-bold bg-[#DC2626]/20 text-[#DC2626] rounded-md",
                                        rx.cond(
                                            ThemeState.is_dark,
                                            "px-3 py-1 text-xs font-bold bg-gray-800 text-gray-400 hover:bg-gray-700 rounded-md transition-colors",
                                            "px-3 py-1 text-xs font-bold bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-md transition-colors",
                                        ),
                                    ),
                                ),
                                rx.el.button(
                                    "Videos",
                                    on_click=CommunityState.set_youtube_filter(
                                        "Videos"
                                    ),
                                    class_name=rx.cond(
                                        CommunityState.youtube_filter == "Videos",
                                        "px-3 py-1 text-xs font-bold bg-[#DC2626]/20 text-[#DC2626] rounded-md",
                                        rx.cond(
                                            ThemeState.is_dark,
                                            "px-3 py-1 text-xs font-bold bg-gray-800 text-gray-400 hover:bg-gray-700 rounded-md transition-colors",
                                            "px-3 py-1 text-xs font-bold bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-md transition-colors",
                                        ),
                                    ),
                                ),
                                rx.el.button(
                                    "Shorts",
                                    on_click=CommunityState.set_youtube_filter(
                                        "Shorts"
                                    ),
                                    class_name=rx.cond(
                                        CommunityState.youtube_filter == "Shorts",
                                        "px-3 py-1 text-xs font-bold bg-[#DC2626]/20 text-[#DC2626] rounded-md",
                                        rx.cond(
                                            ThemeState.is_dark,
                                            "px-3 py-1 text-xs font-bold bg-gray-800 text-gray-400 hover:bg-gray-700 rounded-md transition-colors",
                                            "px-3 py-1 text-xs font-bold bg-gray-100 text-gray-600 hover:bg-gray-200 rounded-md transition-colors",
                                        ),
                                    ),
                                ),
                                class_name="flex items-center gap-2 mt-3",
                            ),
                            class_name="mb-4",
                        ),
                        rx.foreach(
                            CommunityState.filtered_youtube_videos[:6], youtube_card
                        ),
                        rx.el.a(
                            "Alle Videos ansehen",
                            href="https://www.youtube.com/channel/UCMD4pfyYl2hxHez34eqnfkQ",
                            target="_blank",
                            class_name="block w-full text-center p-3 text-emerald-600 font-bold hover:text-emerald-700 bg-emerald-50 rounded-xl transition-colors",
                        ),
                    ),
                    class_name="col-span-1",
                ),
                class_name="grid grid-cols-1 lg:grid-cols-3 gap-8",
            ),
        )
    )