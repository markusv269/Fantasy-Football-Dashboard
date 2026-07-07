import reflex as rx
from app.states.waitlist_state import WaitlistState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


def stats_card(
    title: str, value: rx.Var, icon_name: str, color: str
) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(
                    title,
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                rx.heading(value, size="7", weight="bold"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.icon(icon_name, size=32, color=color),
            width="100%",
            align="center",
        ),
        size="3",
        width="100%",
    )


def waitlist_row(entry: dict, index: int) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                (index + 1).to_string(),
                size="2",
                weight="bold",
                class_name=TEXT_SECONDARY,
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(
                entry["sleeper_name"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.cond(
                entry["discord"].to(str) != "",
                rx.text(
                    entry["discord"].to(str),
                    size="2",
                    class_name=TEXT_SECONDARY,
                ),
                rx.text("—", size="2", class_name=TEXT_SECONDARY),
            ),
        ),
        rx.table.cell(
            rx.text(
                entry["created_at_display"].to(str),
                size="1",
                class_name=TEXT_SECONDARY,
            ),
        ),
    )


def waitlist_section(
    title: str,
    icon_name: str,
    icon_color: str,
    badge_color: str,
    count: rx.Var,
    entries: rx.Var,
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon_name, size=22, color=icon_color),
                rx.heading(title, size="4", weight="bold"),
                rx.spacer(),
                rx.badge(
                    count.to_string(),
                    color_scheme=badge_color,
                    variant="soft",
                    size="2",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                entries.length() > 0,
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("#"),
                                rx.table.column_header_cell("Sleeper Name"),
                                rx.table.column_header_cell("Discord"),
                                rx.table.column_header_cell("Angemeldet am"),
                            ),
                        ),
                        rx.table.body(rx.foreach(entries, waitlist_row)),
                        variant="surface",
                        size="1",
                    ),
                    width="100%",
                    overflow_x="auto",
                ),
                rx.text(
                    "Noch keine Anmeldungen für dieses Format.",
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
    )


def type_card(
    title: str,
    description: str,
    icon_name: str,
    color: str,
    is_checked: rx.Var,
    on_click: rx.event.EventType,
) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon_name, size=24, color=color),
                rx.spacer(),
                rx.cond(
                    is_checked,
                    rx.icon("circle-check", size=20, color="#10B981"),
                    rx.box(
                        class_name=t(
                            "w-5 h-5 border-2 border-gray-600 rounded-full",
                            "w-5 h-5 border-2 border-gray-300 rounded-full",
                        )
                    ),
                ),
                width="100%",
                align="center",
            ),
            rx.heading(title, size="3", weight="bold"),
            rx.text(description, size="1", class_name=TEXT_SECONDARY),
            spacing="2",
            width="100%",
            align="start",
        ),
        on_click=on_click,
        size="2",
        width="100%",
        class_name=rx.cond(
            is_checked,
            "cursor-pointer border-2 border-emerald-500 transition-all",
            "cursor-pointer border-2 border-transparent hover:border-gray-300 transition-all",
        ),
    )


def _success_state() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon("circle-check", size=56, color="#10B981"),
            rx.heading(
                "Anmeldung gespeichert!",
                size="5",
                weight="bold",
            ),
            rx.text(
                "Deine Auswahl wurde erfolgreich gespeichert.",
                size="2",
                color_scheme="gray",
                align="center",
            ),
            rx.cond(
                WaitlistState.existing_entry.contains("user_id"),
                rx.text(
                    "Deine bestehende Anmeldung wurde aktualisiert.",
                    size="2",
                    weight="medium",
                    class_name="text-emerald-600",
                    align="center",
                ),
            ),
            rx.button(
                "Weitere Anmeldung",
                on_click=WaitlistState.reset_form,
                size="3",
                style={"background_color": "#DC2626"},
            ),
            spacing="3",
            align="center",
            width="100%",
            padding="24px",
        ),
        size="3",
        width="100%",
    )


def _form_state() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.text(
                "Sleeper Name *",
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
            rx.hstack(
                rx.input(
                    placeholder="Sleeper Username",
                    on_change=WaitlistState.set_sleeper_name_input,
                    default_value=WaitlistState.sleeper_name_input,
                    size="3",
                    flex="1",
                ),
                rx.button(
                    rx.cond(
                        WaitlistState.is_resolving,
                        rx.spinner(size="2"),
                        rx.text("Überprüfen"),
                    ),
                    on_click=WaitlistState.validate_sleeper_name,
                    disabled=WaitlistState.is_resolving,
                    size="3",
                    color_scheme="gray",
                ),
                spacing="2",
                width="100%",
                align="center",
            ),
            rx.cond(
                WaitlistState.username_valid,
                rx.hstack(
                    rx.icon("circle-check", size=16, color="#10B981"),
                    rx.image(
                        src=rx.cond(
                            WaitlistState.resolved_avatar != "",
                            f"https://sleepercdn.com/avatars/{WaitlistState.resolved_avatar}",
                            "/placeholder.svg",
                        ),
                        width="24px",
                        height="24px",
                        border_radius="9999px",
                    ),
                    rx.text(
                        WaitlistState.resolved_display_name,
                        size="2",
                        weight="bold",
                        class_name="text-emerald-700",
                    ),
                    spacing="2",
                    align="center",
                    padding="8px 12px",
                    border_radius="8px",
                    class_name=t(
                        "bg-emerald-500/10 border border-emerald-500/30",
                        "bg-emerald-50 border border-emerald-200",
                    ),
                ),
                rx.cond(
                    WaitlistState.username_error != "",
                    rx.text(
                        WaitlistState.username_error,
                        size="2",
                        weight="medium",
                        class_name="text-red-500",
                    ),
                ),
            ),
            spacing="2",
            width="100%",
            align="stretch",
        ),
        rx.cond(
            WaitlistState.username_valid,
            rx.vstack(
                rx.cond(
                    WaitlistState.existing_entry.contains("user_id"),
                    rx.hstack(
                        rx.icon("info", size=16, color="#3B82F6"),
                        rx.text(
                            "Du bist bereits angemeldet. Du kannst deine Auswahl hier aktualisieren.",
                            size="2",
                            weight="medium",
                            class_name="text-blue-700",
                        ),
                        spacing="2",
                        align="start",
                        padding="12px",
                        border_radius="8px",
                        class_name=t(
                            "bg-blue-500/10 border border-blue-500/30",
                            "bg-blue-50 border border-blue-200",
                        ),
                        width="100%",
                    ),
                ),
                rx.text(
                    "Welche Formate interessieren dich? *",
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.grid(
                    type_card(
                        "Dynasty",
                        "Standard Dynasty Format.",
                        "crown",
                        "#A855F7",
                        WaitlistState.dynasty_checked,
                        WaitlistState.toggle_dynasty,
                    ),
                    type_card(
                        "Dynasty IDP",
                        "Mit Individual Defensive Players.",
                        "shield",
                        "#3B82F6",
                        WaitlistState.dynasty_idp_checked,
                        WaitlistState.toggle_dynasty_idp,
                    ),
                    type_card(
                        "Dynasty Bestball",
                        "Keine Startaufstellung nötig.",
                        "target",
                        "#F97316",
                        WaitlistState.dynasty_bb_checked,
                        WaitlistState.toggle_dynasty_bb,
                    ),
                    columns=rx.breakpoints(initial="1", sm="3"),
                    spacing="3",
                    width="100%",
                ),
                rx.vstack(
                    rx.text(
                        "Discord Name *",
                        size="2",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Pflichtfeld für weitere Kommunikation.",
                        size="1",
                        class_name=TEXT_SECONDARY,
                    ),
                    rx.input(
                        placeholder="Dein Discord Name",
                        on_change=WaitlistState.set_discord_input,
                        default_value=WaitlistState.discord_input,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                    align="stretch",
                ),
                rx.button(
                    rx.cond(
                        WaitlistState.is_submitting,
                        rx.spinner(size="2"),
                        rx.text("Anmeldung absenden"),
                    ),
                    on_click=WaitlistState.submit_waitlist,
                    disabled=WaitlistState.is_submitting
                    | ~(
                        WaitlistState.dynasty_checked
                        | WaitlistState.dynasty_idp_checked
                        | WaitlistState.dynasty_bb_checked
                    )
                    | (WaitlistState.discord_input == ""),
                    size="3",
                    width="100%",
                    style={"background_color": "#DC2626"},
                ),
                spacing="4",
                width="100%",
                align="stretch",
            ),
        ),
        spacing="4",
        width="100%",
        align="stretch",
    )


def registration_form() -> rx.Component:
    return rx.card(
        rx.cond(WaitlistState.submit_success, _success_state(), _form_state()),
        size="4",
        width="100%",
    )


def waitinglist_page() -> rx.Component:
    return layout(
        rx.vstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("clipboard-list", size=28, color="#10B981"),
                    rx.heading("Dynasty Warteliste", size="7", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Melde dich für die neuen Dynasty-Ligen an. Mehrfachanmeldungen sind möglich.",
                    size="3",
                    color_scheme="gray",
                ),
                spacing="1",
                align="start",
                width="100%",
            ),
            rx.grid(
                stats_card(
                    "Total Anmeldungen",
                    WaitlistState.total_registrations.to_string(),
                    "users",
                    "#10B981",
                ),
                stats_card(
                    "Dynasty",
                    WaitlistState.total_dynasty.to_string(),
                    "crown",
                    "#A855F7",
                ),
                stats_card(
                    "Dynasty IDP",
                    WaitlistState.total_idp.to_string(),
                    "shield",
                    "#3B82F6",
                ),
                stats_card(
                    "Dynasty Bestball",
                    WaitlistState.total_bb.to_string(),
                    "target",
                    "#F97316",
                ),
                columns=rx.breakpoints(initial="1", sm="2", lg="4"),
                spacing="4",
                width="100%",
            ),
            rx.grid(
                registration_form(),
                rx.vstack(
                    waitlist_section(
                        "Dynasty Warteliste",
                        "crown",
                        "#A855F7",
                        "purple",
                        WaitlistState.total_dynasty,
                        WaitlistState.dynasty_entries,
                    ),
                    waitlist_section(
                        "Dynasty IDP Warteliste",
                        "shield",
                        "#3B82F6",
                        "blue",
                        WaitlistState.total_idp,
                        WaitlistState.dynasty_idp_entries,
                    ),
                    waitlist_section(
                        "Dynasty Bestball Warteliste",
                        "target",
                        "#F97316",
                        "orange",
                        WaitlistState.total_bb,
                        WaitlistState.dynasty_bb_entries,
                    ),
                    spacing="4",
                    width="100%",
                    align="stretch",
                ),
                columns=rx.breakpoints(initial="1", xl="2"),
                spacing="6",
                width="100%",
            ),
            spacing="6",
            width="100%",
            align="stretch",
        )
    )
