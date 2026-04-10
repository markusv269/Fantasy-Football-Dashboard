import reflex as rx
from app.states.waitlist_state import WaitlistState
from app.states.theme_state import ThemeState
from app.theme import (
    t,
    CARD,
    H1,
    H2,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    INPUT,
    BTN_PRIMARY,
    TABLE_CONTAINER,
    TABLE_HEADER_ROW,
    TABLE_HEADER_CELL,
    TABLE_ROW,
    EMPTY_STATE,
)
from app.components.layout import layout


def stats_card(
    title: str, value: rx.Var, icon_name: str, color_class: str
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    title,
                    class_name=t(
                        "text-sm font-bold text-gray-400 uppercase tracking-wide",
                        "text-sm font-bold text-gray-500 uppercase tracking-wide",
                    ),
                ),
                rx.el.span(
                    value,
                    class_name=t(
                        "text-3xl font-bold text-white mt-1 block",
                        "text-3xl font-bold text-gray-900 mt-1 block",
                    ),
                ),
            ),
            rx.el.div(
                rx.icon(icon_name, class_name=f"w-8 h-8 {color_class}"),
                class_name=f"p-3 rounded-xl {color_class.replace('text-', 'bg-').replace('500', '100').replace('600', '100')}",
            ),
            class_name="flex justify-between items-start",
        ),
        class_name=CARD + " p-6",
    )


def waitlist_row(entry: dict) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.span(
                entry["sleeper_name"].to(str), class_name="font-bold " + TEXT_PRIMARY
            ),
            class_name="p-4 whitespace-nowrap",
        ),
        rx.el.td(
            rx.cond(
                entry["dynasty"].to(bool),
                rx.icon("check", class_name="w-5 h-5 text-emerald-500"),
                rx.el.span("—", class_name=TEXT_SECONDARY),
            ),
            class_name="p-4 text-center",
        ),
        rx.el.td(
            rx.cond(
                entry["dynasty_idp"].to(bool),
                rx.icon("check", class_name="w-5 h-5 text-blue-500"),
                rx.el.span("—", class_name=TEXT_SECONDARY),
            ),
            class_name="p-4 text-center",
        ),
        rx.el.td(
            rx.cond(
                entry["dynasty_bb"].to(bool),
                rx.icon("check", class_name="w-5 h-5 text-orange-500"),
                rx.el.span("—", class_name=TEXT_SECONDARY),
            ),
            class_name="p-4 text-center",
        ),
        rx.el.td(
            rx.cond(
                entry["discord"].to(str) != "",
                rx.el.span(
                    entry["discord"].to(str), class_name="text-sm " + TEXT_SECONDARY
                ),
                rx.el.span("—", class_name=TEXT_SECONDARY),
            ),
            class_name="p-4",
        ),
        class_name=TABLE_ROW,
    )


def type_card(
    title: str,
    description: str,
    icon_name: str,
    color_class: str,
    is_checked: rx.Var,
    on_click: rx.event.EventType,
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(icon_name, class_name=f"w-6 h-6 mb-2 {color_class}"),
                rx.cond(
                    is_checked,
                    rx.icon(
                        "circle-check",
                        class_name="w-5 h-5 text-emerald-500 absolute top-4 right-4",
                    ),
                    rx.el.div(
                        class_name=t(
                            "w-5 h-5 border-2 border-gray-600 rounded-full absolute top-4 right-4",
                            "w-5 h-5 border-2 border-gray-300 rounded-full absolute top-4 right-4",
                        )
                    ),
                ),
            ),
            rx.el.h4(title, class_name="font-bold mb-1 " + TEXT_PRIMARY),
            rx.el.p(description, class_name="text-xs " + TEXT_SECONDARY),
        ),
        on_click=on_click,
        class_name=t(
            rx.cond(
                is_checked,
                f"bg-[#1C2033] p-4 rounded-xl border-2 border-{color_class.replace('text-', '')} cursor-pointer relative shadow-sm transition-all",
                "bg-[#161926] p-4 rounded-xl border-2 border-transparent hover:border-gray-700 cursor-pointer relative transition-all",
            ),
            rx.cond(
                is_checked,
                f"bg-white p-4 rounded-xl border-2 border-{color_class.replace('text-', '')} cursor-pointer relative shadow-sm transition-all",
                "bg-gray-50 p-4 rounded-xl border-2 border-transparent hover:border-gray-200 cursor-pointer relative transition-all",
            ),
        ),
    )


def registration_form() -> rx.Component:
    return rx.el.div(
        rx.cond(
            WaitlistState.submit_success,
            rx.el.div(
                rx.icon(
                    "message_circle_check",
                    class_name="w-16 h-16 text-emerald-500 mx-auto mb-4",
                ),
                rx.el.h3(
                    "Anmeldung gespeichert!",
                    class_name="text-xl font-bold text-center mb-2 " + TEXT_PRIMARY,
                ),
                rx.el.p(
                    "Deine Auswahl wurde erfolgreich gespeichert.",
                    class_name="text-center mb-1 " + TEXT_SECONDARY,
                ),
                rx.cond(
                    WaitlistState.existing_entry.contains("user_id"),
                    rx.el.p(
                        "Deine bestehende Anmeldung wurde aktualisiert.",
                        class_name="text-sm text-center text-emerald-600 font-medium mb-6",
                    ),
                    rx.el.div(class_name="mb-6"),
                ),
                rx.el.button(
                    "Weitere Anmeldung",
                    on_click=WaitlistState.reset_form,
                    class_name=BTN_PRIMARY + " w-full max-w-xs mx-auto block",
                ),
                class_name=t(
                    "bg-emerald-500/10 rounded-2xl p-8 border border-emerald-500/20 flex flex-col items-center",
                    "bg-emerald-50 rounded-2xl p-8 border border-emerald-100 flex flex-col items-center",
                ),
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Sleeper Name *",
                        class_name="block text-sm font-bold mb-2 " + TEXT_PRIMARY,
                    ),
                    rx.el.div(
                        rx.el.input(
                            placeholder="Sleeper Username",
                            on_change=WaitlistState.set_sleeper_name_input,
                            class_name=INPUT + " flex-1",
                            default_value=WaitlistState.sleeper_name_input,
                        ),
                        rx.el.button(
                            rx.cond(
                                WaitlistState.is_resolving,
                                rx.icon("loader", class_name="w-5 h-5 animate-spin"),
                                "Überprüfen",
                            ),
                            on_click=WaitlistState.validate_sleeper_name,
                            disabled=WaitlistState.is_resolving,
                            class_name="bg-gray-800 text-white hover:bg-gray-700 px-4 py-2 rounded-xl font-bold transition-colors shadow-sm ml-2",
                        ),
                        class_name="flex items-center",
                    ),
                    rx.cond(
                        WaitlistState.username_valid,
                        rx.el.div(
                            rx.icon(
                                "message_circle_check",
                                class_name="w-4 h-4 text-emerald-500 mr-2",
                            ),
                            rx.image(
                                src=rx.cond(
                                    WaitlistState.resolved_avatar != "",
                                    f"https://sleepercdn.com/avatars/{WaitlistState.resolved_avatar}",
                                    "/placeholder.svg",
                                ),
                                class_name="w-6 h-6 rounded-full mr-2",
                            ),
                            rx.el.span(
                                WaitlistState.resolved_display_name,
                                class_name="text-sm font-bold text-emerald-600",
                            ),
                            class_name="flex items-center mt-3 bg-emerald-50 text-emerald-800 px-3 py-2 rounded-lg border border-emerald-100",
                        ),
                        rx.cond(
                            WaitlistState.username_error != "",
                            rx.el.p(
                                WaitlistState.username_error,
                                class_name="text-sm text-red-500 mt-2 font-medium",
                            ),
                            rx.fragment(),
                        ),
                    ),
                    class_name="mb-6",
                ),
                rx.cond(
                    WaitlistState.username_valid,
                    rx.el.div(
                        rx.cond(
                            WaitlistState.existing_entry.contains("user_id"),
                            rx.el.div(
                                rx.icon(
                                    "info",
                                    class_name="w-4 h-4 text-blue-500 mr-2 shrink-0 mt-0.5",
                                ),
                                rx.el.p(
                                    "Du bist bereits angemeldet. Du kannst deine Auswahl hier aktualisieren.",
                                    class_name="text-sm text-blue-700 font-medium",
                                ),
                                class_name="flex items-start mb-6 bg-blue-50 p-3 rounded-lg border border-blue-100",
                            ),
                            rx.fragment(),
                        ),
                        rx.el.label(
                            "Welche Formate interessieren dich? *",
                            class_name="block text-sm font-bold mb-3 " + TEXT_PRIMARY,
                        ),
                        rx.el.div(
                            type_card(
                                "Dynasty",
                                "Standard Dynasty Format.",
                                "crown",
                                "text-purple-500",
                                WaitlistState.dynasty_checked,
                                WaitlistState.toggle_dynasty,
                            ),
                            type_card(
                                "Dynasty IDP",
                                "Mit Individual Defensive Players.",
                                "shield",
                                "text-blue-500",
                                WaitlistState.dynasty_idp_checked,
                                WaitlistState.toggle_dynasty_idp,
                            ),
                            type_card(
                                "Dynasty Bestball",
                                "Keine Startaufstellung nötig.",
                                "target",
                                "text-orange-500",
                                WaitlistState.dynasty_bb_checked,
                                WaitlistState.toggle_dynasty_bb,
                            ),
                            class_name="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6",
                        ),
                        rx.el.div(
                            rx.el.label(
                                "Discord Name (optional)",
                                class_name="block text-sm font-bold mb-1 "
                                + TEXT_PRIMARY,
                            ),
                            rx.el.p(
                                "Für die Kommunikation in der Liga.",
                                class_name="text-xs mb-2 " + TEXT_SECONDARY,
                            ),
                            rx.el.input(
                                placeholder="Dein Discord Name",
                                on_change=WaitlistState.set_discord_input,
                                class_name=INPUT,
                                default_value=WaitlistState.discord_input,
                            ),
                            class_name="mb-8",
                        ),
                        rx.el.button(
                            rx.cond(
                                WaitlistState.is_submitting,
                                rx.icon(
                                    "loader", class_name="w-5 h-5 animate-spin mx-auto"
                                ),
                                "Anmeldung absenden",
                            ),
                            on_click=WaitlistState.submit_waitlist,
                            disabled=WaitlistState.is_submitting
                            | ~(
                                WaitlistState.dynasty_checked
                                | WaitlistState.dynasty_idp_checked
                                | WaitlistState.dynasty_bb_checked
                            ),
                            class_name=BTN_PRIMARY + " w-full",
                        ),
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        class_name=CARD + " p-6 lg:p-8",
    )


def waitinglist_page() -> rx.Component:
    return layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    rx.icon(
                        "clipboard-list",
                        class_name="w-8 h-8 mr-3 text-emerald-500 inline",
                    ),
                    "Dynasty Warteliste",
                    class_name=H1 + " flex items-center",
                ),
                rx.el.p(
                    "Melde dich für die neuen Dynasty-Ligen an. Mehrfachanmeldungen sind möglich.",
                    class_name=TEXT_SECONDARY + " text-lg font-medium",
                ),
                class_name="mb-8",
            ),
            rx.el.div(
                stats_card(
                    "Total Anmeldungen",
                    WaitlistState.total_registrations.to_string(),
                    "users",
                    "text-emerald-500",
                ),
                stats_card(
                    "Dynasty",
                    WaitlistState.total_dynasty.to_string(),
                    "crown",
                    "text-purple-500",
                ),
                stats_card(
                    "Dynasty IDP",
                    WaitlistState.total_idp.to_string(),
                    "shield",
                    "text-blue-500",
                ),
                stats_card(
                    "Dynasty Bestball",
                    WaitlistState.total_bb.to_string(),
                    "target",
                    "text-orange-500",
                ),
                class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10",
            ),
            rx.el.div(
                rx.el.div(registration_form(), class_name="col-span-1"),
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            rx.icon(
                                "list",
                                class_name="w-6 h-6 mr-2 text-emerald-500 inline",
                            ),
                            "Aktuelle Anmeldungen",
                            class_name=H2 + " mb-6 flex items-center p-6 pb-0",
                        ),
                        rx.cond(
                            WaitlistState.all_entries.length() > 0,
                            rx.el.div(
                                rx.el.table(
                                    rx.el.thead(
                                        rx.el.tr(
                                            rx.el.th(
                                                "Sleeper Name",
                                                class_name=TABLE_HEADER_CELL
                                                + " p-4 text-left",
                                            ),
                                            rx.el.th(
                                                "Dynasty",
                                                class_name=TABLE_HEADER_CELL
                                                + " p-4 text-center",
                                            ),
                                            rx.el.th(
                                                "IDP",
                                                class_name=TABLE_HEADER_CELL
                                                + " p-4 text-center",
                                            ),
                                            rx.el.th(
                                                "Bestball",
                                                class_name=TABLE_HEADER_CELL
                                                + " p-4 text-center",
                                            ),
                                            rx.el.th(
                                                "Discord",
                                                class_name=TABLE_HEADER_CELL
                                                + " p-4 text-left",
                                            ),
                                            class_name=TABLE_HEADER_ROW,
                                        )
                                    ),
                                    rx.el.tbody(
                                        rx.foreach(
                                            WaitlistState.all_entries, waitlist_row
                                        )
                                    ),
                                    class_name="w-full table-auto",
                                ),
                                class_name="overflow-x-auto w-full pb-4",
                            ),
                            rx.el.div(
                                rx.icon(
                                    "clipboard-x",
                                    class_name="w-12 h-12 text-gray-300 mb-4",
                                ),
                                rx.el.h3(
                                    "Keine Anmeldungen",
                                    class_name="text-xl font-bold mb-2 " + TEXT_PRIMARY,
                                ),
                                rx.el.p(
                                    "Bisher hat sich noch niemand eingetragen.",
                                    class_name=TEXT_SECONDARY,
                                ),
                                class_name=EMPTY_STATE + " m-6",
                            ),
                        ),
                        class_name=CARD + " overflow-hidden",
                    ),
                    class_name="col-span-1",
                ),
                class_name="grid grid-cols-1 xl:grid-cols-2 gap-8",
            ),
        )
    )