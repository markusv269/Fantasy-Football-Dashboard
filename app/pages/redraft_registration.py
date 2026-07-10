import reflex as rx
from app.states.redraft_registration_state import RedraftRegistrationState
from app.theme import t, TEXT_PRIMARY, TEXT_SECONDARY
from app.components.layout import layout


def _hero() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("trophy", size=28, color="#DC2626"),
                rx.heading(
                    "Redraft Registrierung 2026", size="7", weight="bold"
                ),
                spacing="3",
                align="center",
                wrap="wrap",
            ),
            rx.text(
                "Melde dich hier für die Redraft-Saison 2026 an. Sleeper-Name "
                "und Discord sind Pflichtfelder. E-Mail ist optional und wird "
                "in der öffentlichen Übersicht NICHT angezeigt. Du kannst bis "
                "zu drei Mitspieler-Wünsche angeben — beidseitige Wünsche "
                "werden in der Übersicht mit einem ✓ markiert.",
                size="3",
                color_scheme="gray",
            ),
            rx.text(
                "Nach der Anmeldung erhältst du einen Änderungscode. Bewahre "
                "ihn gut auf — du brauchst ihn, um deine Anmeldung später zu "
                "aktualisieren.",
                size="2",
                class_name="italic " + TEXT_SECONDARY,
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
        class_name="border-l-4 border-l-[#DC2626]",
    )


def _status_banner() -> rx.Component:
    return rx.cond(
        RedraftRegistrationState.status_message != "",
        rx.card(
            rx.hstack(
                rx.icon(
                    rx.match(
                        RedraftRegistrationState.status_type,
                        ("success", "circle-check"),
                        ("error", "circle-alert"),
                        "info",
                    ),
                    size=20,
                    color=rx.match(
                        RedraftRegistrationState.status_type,
                        ("success", "#10B981"),
                        ("error", "#EF4444"),
                        "#3B82F6",
                    ),
                ),
                rx.text(
                    RedraftRegistrationState.status_message,
                    size="2",
                    weight="medium",
                    class_name=TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=14),
                    on_click=RedraftRegistrationState.clear_status,
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            size="2",
            width="100%",
            class_name=rx.match(
                RedraftRegistrationState.status_type,
                ("success", "border-l-4 border-l-emerald-500 bg-emerald-500/5"),
                ("error", "border-l-4 border-l-red-500 bg-red-500/5"),
                "border-l-4 border-l-blue-500 bg-blue-500/5",
            ),
        ),
    )


def _table_warning() -> rx.Component:
    return rx.cond(
        RedraftRegistrationState.using_fallback,
        rx.card(
            rx.hstack(
                rx.icon("triangle-alert", size=20, color="#F59E0B"),
                rx.text(
                    "Hinweis: Die Ziel-Tabelle „redraft_registration_2026“ "
                    "existiert noch nicht. Die Übersicht unten zeigt "
                    "Referenzdaten aus „user_registration“. Neue Anmeldungen "
                    "können erst gespeichert werden, wenn die Tabelle angelegt "
                    "ist.",
                    size="2",
                    weight="medium",
                    class_name=TEXT_PRIMARY,
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            size="2",
            width="100%",
            class_name="border-l-4 border-l-amber-500 bg-amber-500/5",
        ),
    )


def _success_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.icon("circle-check", size=56, color="#10B981"),
            rx.heading("Anmeldung gespeichert!", size="5", weight="bold"),
            rx.text(
                "Dein Änderungscode:",
                size="2",
                class_name=TEXT_SECONDARY,
            ),
            rx.box(
                rx.text(
                    RedraftRegistrationState.generated_code,
                    size="6",
                    weight="bold",
                    class_name="font-mono tracking-widest " + TEXT_PRIMARY,
                ),
                padding="16px 24px",
                border_radius="12px",
                class_name="border-2 border-dashed "
                + t(
                    "border-[#DC2626]/50 bg-[#DC2626]/5",
                    "border-red-300 bg-red-50",
                ),
            ),
            rx.text(
                "Bewahre diesen Code gut auf! Ohne ihn kannst du deine "
                "Anmeldung später nicht ändern.",
                size="1",
                class_name="italic text-center " + TEXT_SECONDARY,
            ),
            rx.button(
                "Neue Anmeldung",
                on_click=RedraftRegistrationState.reset_form,
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


def _validation_state() -> rx.Component:
    return rx.cond(
        RedraftRegistrationState.username_valid,
        rx.hstack(
            rx.icon("circle-check", size=16, color="#10B981"),
            rx.cond(
                RedraftRegistrationState.resolved_avatar != "",
                rx.image(
                    src=f"https://sleepercdn.com/avatars/{RedraftRegistrationState.resolved_avatar}",
                    width="24px",
                    height="24px",
                    border_radius="9999px",
                ),
                rx.fragment(),
            ),
            rx.text(
                RedraftRegistrationState.resolved_display_name,
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
            RedraftRegistrationState.username_error != "",
            rx.text(
                RedraftRegistrationState.username_error,
                size="2",
                weight="medium",
                class_name="text-red-500",
            ),
        ),
    )


def _commish_option(
    label: str, value: bool, icon: str, description: str
) -> rx.Component:
    is_selected = RedraftRegistrationState.commish_input == value
    return rx.box(
        rx.hstack(
            rx.box(
                rx.cond(
                    is_selected,
                    rx.box(
                        class_name="w-3 h-3 rounded-full bg-[#DC2626]",
                    ),
                    rx.fragment(),
                ),
                class_name=rx.cond(
                    is_selected,
                    "w-5 h-5 rounded-full border-2 border-[#DC2626] flex items-center justify-center flex-shrink-0",
                    "w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 "
                    + t("border-gray-600", "border-gray-300"),
                ),
            ),
            rx.icon(icon, size=18, color="#DC2626"),
            rx.vstack(
                rx.text(
                    label,
                    size="2",
                    weight="bold",
                    class_name=TEXT_PRIMARY,
                ),
                rx.text(description, size="1", class_name=TEXT_SECONDARY),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        on_click=rx.cond(
            value,
            RedraftRegistrationState.set_commish_yes,
            RedraftRegistrationState.set_commish_no,
        ),
        padding="12px 14px",
        border_radius="10px",
        width="100%",
        class_name=rx.cond(
            is_selected,
            "cursor-pointer border-2 border-[#DC2626] "
            + t("bg-[#DC2626]/10", "bg-red-50")
            + " transition-all",
            "cursor-pointer border-2 "
            + t(
                "border-white/10 bg-[#08090D] hover:border-white/20",
                "border-gray-200 bg-white hover:border-gray-300",
            )
            + " transition-all",
        ),
    )


def _commish_selector() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon("crown", size=18, color="#DC2626"),
            rx.text(
                "Interesse als Commissioner?",
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
            rx.text("*", size="2", weight="bold", class_name="text-red-500"),
            spacing="2",
            align="center",
        ),
        rx.text(
            "Ein Commish übernimmt die organisatorische Verantwortung für eine Liga (Setup, Regeln, Kommunikation).",
            size="1",
            class_name=TEXT_SECONDARY,
        ),
        rx.grid(
            _commish_option(
                "Ja, ich möchte Commish sein",
                True,
                "check",
                "Ich übernehme Verantwortung für eine Liga.",
            ),
            _commish_option(
                "Nein, danke",
                False,
                "x",
                "Ich möchte nur als Manager teilnehmen.",
            ),
            columns=rx.breakpoints(initial="1", sm="2"),
            spacing="2",
            width="100%",
        ),
        spacing="2",
        width="100%",
        align="stretch",
    )


def _form_group(
    label: str, required: bool, child: rx.Component
) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                label,
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
            rx.cond(
                required,
                rx.text(
                    "*", size="2", weight="bold", class_name="text-red-500"
                ),
                rx.fragment(),
            ),
            spacing="1",
            align="center",
        ),
        child,
        spacing="1",
        width="100%",
        align="stretch",
    )


def _form() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Anmeldung", size="5", weight="bold"),
            rx.divider(),
            _form_group(
                "Sleeper Name",
                True,
                rx.hstack(
                    rx.input(
                        placeholder="Dein Sleeper Username",
                        on_change=RedraftRegistrationState.set_sleeper_input,
                        default_value=RedraftRegistrationState.sleeper_input,
                        size="3",
                        flex="1",
                    ),
                    rx.button(
                        rx.cond(
                            RedraftRegistrationState.is_resolving,
                            rx.spinner(size="2"),
                            rx.text("Überprüfen"),
                        ),
                        on_click=RedraftRegistrationState.validate_sleeper,
                        disabled=RedraftRegistrationState.is_resolving,
                        size="3",
                        color_scheme="gray",
                    ),
                    spacing="2",
                    width="100%",
                ),
            ),
            _validation_state(),
            _form_group(
                "Discord Name",
                True,
                rx.input(
                    placeholder="Dein Discord Name",
                    on_change=RedraftRegistrationState.set_discord_input,
                    default_value=RedraftRegistrationState.discord_input,
                    size="3",
                    width="100%",
                ),
            ),
            _form_group(
                "E-Mail (optional, nicht öffentlich)",
                False,
                rx.input(
                    placeholder="deine@email.de",
                    type="email",
                    on_change=RedraftRegistrationState.set_email_input,
                    default_value=RedraftRegistrationState.email_input,
                    size="3",
                    width="100%",
                ),
            ),
            rx.divider(),
            _commish_selector(),
            rx.divider(),
            rx.vstack(
                rx.hstack(
                    rx.icon("users", size=18, color="#DC2626"),
                    rx.text(
                        "Mitspieler-Wünsche (optional, max. 3)",
                        size="2",
                        weight="bold",
                        class_name=TEXT_PRIMARY,
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    "Sleeper-Namen deiner gewünschten Mitspieler. "
                    "Beidseitige Wünsche werden in der Übersicht markiert.",
                    size="1",
                    class_name=TEXT_SECONDARY,
                ),
                rx.input(
                    placeholder="Mitspieler 1",
                    on_change=RedraftRegistrationState.set_teammate1_input,
                    default_value=RedraftRegistrationState.teammate1_input,
                    size="3",
                    width="100%",
                ),
                rx.input(
                    placeholder="Mitspieler 2",
                    on_change=RedraftRegistrationState.set_teammate2_input,
                    default_value=RedraftRegistrationState.teammate2_input,
                    size="3",
                    width="100%",
                ),
                rx.input(
                    placeholder="Mitspieler 3",
                    on_change=RedraftRegistrationState.set_teammate3_input,
                    default_value=RedraftRegistrationState.teammate3_input,
                    size="3",
                    width="100%",
                ),
                spacing="2",
                width="100%",
                align="stretch",
            ),
            rx.cond(
                RedraftRegistrationState.existing_entry.contains("user_id"),
                rx.vstack(
                    rx.divider(),
                    _form_group(
                        "Änderungscode (für bestehende Anmeldung)",
                        True,
                        rx.input(
                            placeholder="Dein bestehender Änderungscode",
                            on_change=RedraftRegistrationState.set_edit_code_input,
                            default_value=RedraftRegistrationState.edit_code_input,
                            size="3",
                            width="100%",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                    align="stretch",
                ),
                rx.fragment(),
            ),
            rx.button(
                rx.cond(
                    RedraftRegistrationState.is_submitting,
                    rx.spinner(size="2"),
                    rx.text("Anmeldung absenden"),
                ),
                on_click=RedraftRegistrationState.submit_registration,
                disabled=RedraftRegistrationState.is_submitting
                | ~RedraftRegistrationState.username_valid,
                size="3",
                width="100%",
                style={"background_color": "#DC2626"},
            ),
            spacing="4",
            width="100%",
            align="stretch",
        ),
        size="4",
        width="100%",
    )


def _entry_row(e: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(
                e["sleeper"].to(str),
                size="2",
                weight="bold",
                class_name=TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.text(
                e["discord"].to(str),
                size="2",
                class_name=TEXT_SECONDARY,
            ),
        ),
        rx.table.cell(
            rx.cond(
                e["commish"].to(bool),
                rx.badge(
                    rx.icon("crown", size=12),
                    "Ja",
                    color_scheme="red",
                    variant="solid",
                    size="1",
                ),
                rx.badge(
                    "Nein",
                    color_scheme="gray",
                    variant="soft",
                    size="1",
                ),
            ),
        ),
        rx.table.cell(
            rx.text(
                e["mates_display"].to(str),
                size="2",
                class_name=TEXT_PRIMARY,
            ),
        ),
        rx.table.cell(
            rx.badge(
                e["mutual_count"].to(str),
                color_scheme="green",
                variant="soft",
                size="1",
            ),
        ),
        rx.table.cell(
            rx.text(
                e["created_display"].to(str),
                size="1",
                class_name=TEXT_SECONDARY,
            ),
        ),
    )


def _stat_tile(
    label: str, value: rx.Var, icon: str, color: str, subtitle: str = ""
) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon, size=22, color=color),
                padding="10px",
                border_radius="10px",
                class_name="w-fit " + t("bg-white/5", "bg-gray-50"),
            ),
            rx.vstack(
                rx.text(
                    label,
                    size="1",
                    weight="bold",
                    class_name="uppercase tracking-wide " + TEXT_SECONDARY,
                ),
                rx.heading(value, size="6", weight="bold"),
                rx.cond(
                    subtitle != "",
                    rx.text(subtitle, size="1", class_name=TEXT_SECONDARY),
                    rx.fragment(),
                ),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="14px",
        border_radius="12px",
        width="100%",
        class_name="border "
        + t(
            "bg-[#08090D] border-white/5",
            "bg-white border-gray-200",
        ),
    )


def _stats_bar() -> rx.Component:
    return rx.grid(
        _stat_tile(
            "Anmeldungen",
            RedraftRegistrationState.total_entries.to_string(),
            "users",
            "#DC2626",
        ),
        _stat_tile(
            "Commish-Interesse",
            RedraftRegistrationState.commish_count.to_string(),
            "crown",
            "#DC2626",
        ),
        _stat_tile(
            "Volle Ligen",
            RedraftRegistrationState.full_leagues_count.to_string(),
            "trophy",
            "#10B981",
            "12 Manager je Liga",
        ),
        _stat_tile(
            "Fehlend f. nächste Liga",
            RedraftRegistrationState.remaining_for_next_league.to_string(),
            "user-plus",
            "#F59E0B",
        ),
        columns=rx.breakpoints(initial="1", sm="2", lg="4"),
        spacing="3",
        width="100%",
    )


def _entries_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("list-checks", size=20, color="#DC2626"),
                rx.heading("Aktuelle Anmeldungen", size="5", weight="bold"),
                rx.badge(
                    RedraftRegistrationState.total_entries.to_string(),
                    color_scheme="red",
                    variant="soft",
                    size="2",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("refresh-cw", size=14),
                    "Neu laden",
                    on_click=RedraftRegistrationState.load_entries,
                    variant="soft",
                    color_scheme="gray",
                    size="1",
                ),
                width="100%",
                align="center",
                wrap="wrap",
            ),
            _stats_bar(),
            rx.text(
                "E-Mail-Adressen werden aus Datenschutzgründen NICHT angezeigt.",
                size="1",
                class_name="italic " + TEXT_SECONDARY,
            ),
            rx.cond(
                RedraftRegistrationState.is_loading,
                rx.center(
                    rx.spinner(size="3"),
                    padding_y="40px",
                    width="100%",
                ),
                rx.cond(
                    RedraftRegistrationState.entries.length() > 0,
                    rx.box(
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Sleeper"),
                                    rx.table.column_header_cell("Discord"),
                                    rx.table.column_header_cell("Commish"),
                                    rx.table.column_header_cell(
                                        "Mitspieler-Wünsche"
                                    ),
                                    rx.table.column_header_cell("Beidseitig"),
                                    rx.table.column_header_cell("Angemeldet"),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    RedraftRegistrationState.entries,
                                    _entry_row,
                                ),
                            ),
                            variant="surface",
                            size="1",
                        ),
                        width="100%",
                        overflow_x="auto",
                        border_radius="12px",
                        class_name="border "
                        + t("border-gray-800", "border-gray-200"),
                    ),
                    rx.text(
                        "Noch keine Anmeldungen vorhanden.",
                        size="2",
                        color_scheme="gray",
                        class_name="italic",
                    ),
                ),
            ),
            spacing="3",
            width="100%",
            align="stretch",
        ),
        size="3",
        width="100%",
    )


def redraft_registration_page() -> rx.Component:
    return layout(
        rx.vstack(
            _hero(),
            _status_banner(),
            _table_warning(),
            rx.cond(
                RedraftRegistrationState.submit_success,
                _success_card(),
                _form(),
            ),
            _entries_card(),
            spacing="5",
            width="100%",
            align="stretch",
        )
    )
