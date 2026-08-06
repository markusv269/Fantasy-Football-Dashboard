import reflex as rx

from app.states.fantasyboerse_state import FantasyBoerseState
from app.theme import TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, t


def _status_badge(entry: rx.Var) -> rx.Component:
    return rx.match(
        entry["status"].to(str),
        (
            "open",
            rx.el.span(
                "Frei",
                class_name="w-fit rounded-full bg-green-100 px-2.5 py-1 text-xs font-bold text-green-700",
            ),
        ),
        (
            "reserved",
            rx.el.span(
                "Reserviert",
                class_name="w-fit rounded-full bg-yellow-100 px-2.5 py-1 text-xs font-bold text-yellow-700",
            ),
        ),
        (
            "filled",
            rx.el.span(
                "Vergeben",
                class_name="w-fit rounded-full bg-blue-100 px-2.5 py-1 text-xs font-bold text-blue-700",
            ),
        ),
        (
            "archived",
            rx.el.span(
                "Archiviert",
                class_name="w-fit rounded-full bg-gray-100 px-2.5 py-1 text-xs font-bold text-gray-600",
            ),
        ),
        rx.el.span(
            "Unbekannt",
            class_name="w-fit rounded-full bg-gray-100 px-2.5 py-1 text-xs font-bold text-gray-600",
        ),
    )


def _entry_type_badge(entry: rx.Var) -> rx.Component:
    return rx.match(
        entry["entry_type"].to(str),
        (
            "manager_spot",
            rx.el.span(
                rx.icon("user-round", class_name="h-3.5 w-3.5"),
                "Managerposten",
                class_name="flex w-fit items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-bold text-red-700",
            ),
        ),
        (
            "whole_league",
            rx.el.span(
                rx.icon("trophy", class_name="h-3.5 w-3.5"),
                "Ganze Liga",
                class_name="flex w-fit items-center gap-1 rounded-full bg-purple-100 px-2.5 py-1 text-xs font-bold text-purple-700",
            ),
        ),
        rx.el.span(
            "Fantasybörse",
            class_name="w-fit rounded-full bg-gray-100 px-2.5 py-1 text-xs font-bold text-gray-600",
        ),
    )


def _stat_card(label: str, value: rx.Var, icon: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-5 w-5 text-[#DC2626]"),
            class_name=t(
                "flex h-10 w-10 items-center justify-center rounded-xl bg-[#DC2626]/10",
                "flex h-10 w-10 items-center justify-center rounded-xl bg-red-50",
            ),
        ),
        rx.el.p(
            label, class_name="mt-4 text-sm font-semibold " + TEXT_SECONDARY
        ),
        rx.el.p(
            value.to_string(),
            class_name="mt-1 text-2xl font-bold " + TEXT_PRIMARY,
        ),
        class_name="rounded-2xl border border-gray-200 bg-white p-5 "
        + t("border-white/10 bg-[#12141C]", "border-gray-200 bg-white")
        + "",
    )


def _filter_select(
    label: str,
    value: rx.Var,
    options: rx.Component,
    on_change: rx.event.EventType,
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            label,
            class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
            + TEXT_MUTED,
        ),
        rx.el.div(
            rx.el.select(
                options,
                value=value,
                on_change=on_change,
                class_name="w-full appearance-none rounded-xl border px-3 py-2.5 pr-9 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                + t(
                    "border-white/10 bg-[#12141C] text-slate-100",
                    "border-gray-200 bg-white text-gray-800",
                ),
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 "
                + TEXT_MUTED,
            ),
            class_name="relative",
        ),
        class_name="min-w-0",
    )


def _filter_bar() -> rx.Component:
    return rx.el.div(
        _filter_select(
            "Form",
            FantasyBoerseState.form_filter,
            rx.fragment(
                rx.el.option("Alle Formen", value="all"),
                rx.el.option("Managerposten", value="manager_spot"),
                rx.el.option("Ganze Liga", value="whole_league"),
            ),
            FantasyBoerseState.set_form_filter,
        ),
        _filter_select(
            "Liga-Größe",
            FantasyBoerseState.size_filter,
            rx.fragment(
                rx.el.option("Alle Größen", value="all"),
                rx.foreach(
                    FantasyBoerseState.league_size_options,
                    lambda size: rx.el.option(
                        f"{size} Teams",
                        value=size,
                    ),
                ),
            ),
            FantasyBoerseState.set_size_filter,
        ),
        _filter_select(
            "Buy-in",
            FantasyBoerseState.buyin_filter,
            rx.fragment(
                rx.el.option("Alle Buy-ins", value="all"),
                rx.el.option("Kostenlos", value="free"),
                rx.el.option("Bis 25 €", value="up_to_25"),
                rx.el.option("25–50 €", value="25_to_50"),
                rx.el.option("Über 50 €", value="over_50"),
            ),
            FantasyBoerseState.set_buyin_filter,
        ),
        _filter_select(
            "Status",
            FantasyBoerseState.status_filter,
            rx.fragment(
                rx.el.option("Alle Status", value="all"),
                rx.el.option("Frei", value="open"),
                rx.el.option("Reserviert", value="reserved"),
                rx.el.option("Vergeben", value="filled"),
                rx.el.option("Archiviert", value="archived"),
            ),
            FantasyBoerseState.set_status_filter,
        ),
        rx.cond(
            FantasyBoerseState.has_active_filters,
            rx.el.button(
                rx.icon("x", class_name="h-4 w-4"),
                "Filter löschen",
                on_click=FantasyBoerseState.clear_filters,
                class_name="mt-5 flex items-center justify-center gap-2 rounded-xl border border-red-200 px-3 py-2.5 text-sm font-bold text-[#DC2626] transition hover:bg-red-50 md:mt-0",
            ),
            rx.el.div(class_name="hidden md:block"),
        ),
        class_name="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5",
    )


def _active_filters() -> rx.Component:
    return rx.cond(
        FantasyBoerseState.has_active_filters,
        rx.el.div(
            rx.el.div(
                rx.icon("list-filter", class_name="h-4 w-4 text-[#DC2626]"),
                rx.el.span(
                    f"{FantasyBoerseState.active_filter_count} aktive Filter",
                    class_name="text-sm font-bold " + TEXT_PRIMARY,
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.cond(
                    FantasyBoerseState.form_filter != "all",
                    rx.el.button(
                        rx.match(
                            FantasyBoerseState.form_filter,
                            ("manager_spot", "Managerposten"),
                            ("whole_league", "Ganze Liga"),
                            "Form",
                        ),
                        rx.icon("x", class_name="h-3 w-3"),
                        on_click=lambda: FantasyBoerseState.set_form_filter(
                            "all"
                        ),
                        class_name="flex w-fit items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-bold text-red-700",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    FantasyBoerseState.size_filter != "all",
                    rx.el.button(
                        f"{FantasyBoerseState.size_filter} Teams",
                        rx.icon("x", class_name="h-3 w-3"),
                        on_click=lambda: FantasyBoerseState.set_size_filter(
                            "all"
                        ),
                        class_name="flex w-fit items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-bold text-red-700",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    FantasyBoerseState.buyin_filter != "all",
                    rx.el.button(
                        rx.match(
                            FantasyBoerseState.buyin_filter,
                            ("free", "Kostenlos"),
                            ("up_to_25", "Bis 25 €"),
                            ("25_to_50", "25–50 €"),
                            ("over_50", "Über 50 €"),
                            "Buy-in",
                        ),
                        rx.icon("x", class_name="h-3 w-3"),
                        on_click=lambda: FantasyBoerseState.set_buyin_filter(
                            "all"
                        ),
                        class_name="flex w-fit items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-bold text-red-700",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    FantasyBoerseState.status_filter != "all",
                    rx.el.button(
                        rx.match(
                            FantasyBoerseState.status_filter,
                            ("open", "Frei"),
                            ("reserved", "Reserviert"),
                            ("filled", "Vergeben"),
                            ("archived", "Archiviert"),
                            "Status",
                        ),
                        rx.icon("x", class_name="h-3 w-3"),
                        on_click=lambda: FantasyBoerseState.set_status_filter(
                            "all"
                        ),
                        class_name="flex w-fit items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-bold text-red-700",
                    ),
                    rx.fragment(),
                ),
                class_name="flex flex-wrap items-center gap-2",
            ),
            class_name="flex flex-col gap-3 rounded-xl border border-red-100 bg-red-50/60 px-4 py-3 sm:flex-row sm:items-center sm:justify-between",
        ),
        rx.fragment(),
    )


def _entry_card(entry: rx.Var) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                _entry_type_badge(entry),
                _status_badge(entry),
                class_name="flex flex-wrap items-center gap-2",
            ),
            rx.el.h3(
                entry["league_name"].to(str),
                class_name="mt-4 line-clamp-1 text-lg font-bold "
                + TEXT_PRIMARY,
            ),
            rx.el.p(
                f"Liga {entry['league_id']}"
                + rx.cond(
                    entry["team_name"].to(str) != "",
                    f" · {entry['team_name']}",
                    "",
                ),
                class_name="mt-1 text-xs font-medium " + TEXT_MUTED,
            ),
            class_name="border-b border-gray-100 pb-4 "
            + t("border-white/10", "border-gray-100"),
        ),
        rx.el.p(
            entry["description"].to(str),
            class_name="mt-4 min-h-12 text-sm leading-6 " + TEXT_SECONDARY,
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("users", class_name="h-4 w-4 text-[#DC2626]"),
                rx.el.span(
                    rx.cond(
                        entry["league_size"] > 0,
                        f"{entry['league_size']} Teams",
                        "Größe nicht angegeben",
                    ),
                    class_name="text-sm font-semibold " + TEXT_PRIMARY,
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.div(
                rx.icon("coins", class_name="h-4 w-4 text-[#DC2626]"),
                rx.el.span(
                    rx.cond(
                        entry["buyin"] > 0,
                        f"{entry['buyin']:.2f} € Buy-in",
                        "Kostenlos",
                    ),
                    class_name="text-sm font-semibold " + TEXT_PRIMARY,
                ),
                class_name="flex items-center gap-3",
            ),
            class_name="mt-5 grid grid-cols-2 gap-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("layout-list", class_name="h-4 w-4 text-[#DC2626]"),
                rx.el.div(
                    rx.el.p(
                        "Roster",
                        class_name="text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.p(
                        entry["roster_structure"].to(str),
                        class_name="mt-1 text-xs leading-5 " + TEXT_SECONDARY,
                    ),
                ),
                class_name="flex items-start gap-2",
            ),
            rx.el.div(
                rx.icon(
                    "chart-no-axes-combined",
                    class_name="h-4 w-4 text-[#DC2626]",
                ),
                rx.el.div(
                    rx.el.p(
                        "Scoring",
                        class_name="text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.p(
                        entry["scoring_summary"].to(str),
                        class_name="mt-1 text-xs leading-5 " + TEXT_SECONDARY,
                    ),
                ),
                class_name="flex items-start gap-2",
            ),
            class_name="mt-5 grid grid-cols-1 gap-3 border-t border-gray-100 pt-4 "
            + t("border-white/10", "border-gray-100"),
        ),
        rx.cond(
            (entry["entry_type"].to(str) == "manager_spot")
            & (entry["team_name"].to(str) != ""),
            rx.el.div(
                rx.icon(
                    "user-round-check", class_name="h-4 w-4 text-amber-600"
                ),
                rx.el.p(
                    f"Aktuelles Team: {entry['team_name']}",
                    class_name="text-xs font-semibold text-amber-700",
                ),
                class_name="mt-4 flex items-center gap-2 rounded-xl bg-amber-50 px-3 py-2",
            ),
            rx.fragment(),
        ),
        rx.cond(
            entry["live_error"].to(str) != "",
            rx.el.p(
                entry["live_error"].to(str),
                class_name="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs font-semibold text-red-700",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.p(
                f"Kontakt: {entry['contact_sleeper']}",
                class_name="truncate text-xs font-medium " + TEXT_SECONDARY,
            ),
            rx.el.p(
                f"Discord: {entry['contact_discord']}",
                class_name="truncate text-xs font-medium " + TEXT_SECONDARY,
            ),
            class_name="mt-5 space-y-1 border-t border-gray-100 pt-4 "
            + t("border-white/10", "border-gray-100"),
        ),
        rx.cond(
            entry["invite_link"].to(str) != "",
            rx.el.a(
                rx.icon("external-link", class_name="h-4 w-4"),
                "Invite-Link öffnen",
                href=entry["invite_link"].to(str),
                target="_blank",
                rel="noreferrer",
                class_name="mt-4 flex w-fit items-center gap-2 text-sm font-bold text-[#DC2626] hover:text-[#B91C1C]",
            ),
            rx.el.p(
                "Invite-Link auf Anfrage",
                class_name="mt-4 text-xs font-semibold " + TEXT_MUTED,
            ),
        ),
        class_name="flex h-full flex-col rounded-2xl border p-5 transition-colors hover:border-[#DC2626] "
        + t("border-white/10 bg-[#12141C]", "border-gray-200 bg-white"),
    )


def _table_row(entry: rx.Var) -> rx.Component:
    return rx.el.tr(
        rx.el.td(
            rx.el.div(
                rx.el.p(
                    entry["league_name"].to(str),
                    class_name="font-bold " + TEXT_PRIMARY,
                ),
                rx.el.p(
                    f"{entry['league_id']}", class_name="text-xs " + TEXT_MUTED
                ),
            ),
            class_name="px-4 py-3 align-top",
        ),
        rx.el.td(
            rx.el.div(
                _entry_type_badge(entry),
                rx.el.div(_status_badge(entry), class_name="mt-2"),
            ),
            class_name="px-4 py-3 align-top",
        ),
        rx.el.td(
            rx.cond(entry["league_size"] > 0, f"{entry['league_size']}", "–"),
            class_name="whitespace-nowrap px-4 py-3 text-sm font-semibold "
            + TEXT_SECONDARY,
        ),
        rx.el.td(
            rx.cond(entry["buyin"] > 0, f"{entry['buyin']:.2f} €", "Kostenlos"),
            class_name="whitespace-nowrap px-4 py-3 text-sm font-semibold "
            + TEXT_PRIMARY,
        ),
        rx.el.td(
            rx.el.div(
                rx.el.p(
                    entry["league_form"].to(str).upper(),
                    class_name="text-xs font-bold " + TEXT_PRIMARY,
                ),
                rx.el.p(
                    entry["scoring_summary"].to(str),
                    class_name="mt-1 max-w-56 text-xs leading-5 " + TEXT_MUTED,
                ),
            ),
            class_name="min-w-48 px-4 py-3 align-top",
        ),
        rx.el.td(
            rx.el.div(
                rx.el.p(
                    entry["roster_structure"].to(str),
                    class_name="max-w-64 text-xs leading-5 " + TEXT_SECONDARY,
                ),
                rx.cond(
                    (entry["entry_type"].to(str) == "manager_spot")
                    & (entry["team_name"].to(str) != ""),
                    rx.el.p(
                        f"Aktuelles Team: {entry['team_name']}",
                        class_name="mt-1 text-xs font-semibold text-amber-700",
                    ),
                    rx.fragment(),
                ),
            ),
            class_name="min-w-64 px-4 py-3 align-top",
        ),
        rx.el.td(
            f"{entry['contact_sleeper']}",
            class_name="whitespace-nowrap px-4 py-3 text-sm " + TEXT_SECONDARY,
        ),
        class_name="border-b transition-colors hover:bg-red-50/40 "
        + t("border-white/10", "border-gray-100"),
    )


def _empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("search-x", class_name="h-7 w-7 text-[#DC2626]"),
            class_name="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50",
        ),
        rx.el.h3(
            rx.cond(
                FantasyBoerseState.has_active_filters,
                "Keine passenden Einträge",
                "Noch keine Einträge vorhanden",
            ),
            class_name="mt-4 text-lg font-bold " + TEXT_PRIMARY,
        ),
        rx.el.p(
            rx.cond(
                FantasyBoerseState.has_active_filters,
                "Passe deine Filter an oder setze sie zurück, um weitere Angebote zu sehen.",
                "Sobald die ersten Angebote veröffentlicht sind, erscheinen sie hier.",
            ),
            class_name="mt-2 max-w-lg text-center text-sm leading-6 "
            + TEXT_SECONDARY,
        ),
        rx.cond(
            FantasyBoerseState.has_active_filters,
            rx.el.button(
                "Filter zurücksetzen",
                on_click=FantasyBoerseState.clear_filters,
                class_name="mt-5 rounded-xl bg-[#DC2626] px-4 py-2.5 text-sm font-bold text-white transition hover:bg-[#B91C1C]",
            ),
            rx.fragment(),
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-dashed px-6 py-16 text-center "
        + t("border-white/10 bg-[#0D1117]", "border-gray-200 bg-gray-50"),
    )


def _loading_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(class_name="h-64 animate-pulse rounded-2xl bg-gray-200/70"),
        rx.el.div(class_name="h-64 animate-pulse rounded-2xl bg-gray-200/70"),
        rx.el.div(class_name="h-64 animate-pulse rounded-2xl bg-gray-200/70"),
        class_name="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3",
    )


def _error_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("circle-alert", class_name="h-7 w-7 text-red-600"),
            class_name="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-100",
        ),
        rx.el.h3(
            "Fantasybörse konnte nicht geladen werden",
            class_name="mt-4 text-lg font-bold " + TEXT_PRIMARY,
        ),
        rx.el.p(
            FantasyBoerseState.error_message,
            class_name="mt-2 max-w-lg text-center text-sm leading-6 "
            + TEXT_SECONDARY,
        ),
        rx.el.button(
            rx.icon("refresh-cw", class_name="h-4 w-4"),
            "Erneut versuchen",
            on_click=FantasyBoerseState.load_entries,
            class_name="mt-5 flex items-center gap-2 rounded-xl bg-[#DC2626] px-4 py-2.5 text-sm font-bold text-white transition hover:bg-[#B91C1C]",
        ),
        class_name="flex flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-6 py-16 text-center",
    )


def _entry_form_message() -> rx.Component:
    return rx.cond(
        FantasyBoerseState.form_message != "",
        rx.el.div(
            rx.icon(
                rx.match(
                    FantasyBoerseState.form_message_type,
                    ("success", "circle-check"),
                    ("error", "circle-alert"),
                    "info",
                ),
                class_name=rx.cond(
                    FantasyBoerseState.form_message_type == "success",
                    "h-5 w-5 text-green-600",
                    "h-5 w-5 text-red-600",
                ),
            ),
            rx.el.p(
                FantasyBoerseState.form_message,
                class_name="text-sm font-semibold " + TEXT_PRIMARY,
            ),
            class_name=rx.cond(
                FantasyBoerseState.form_message_type == "success",
                "flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 px-4 py-3",
                "flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3",
            ),
        ),
        rx.fragment(),
    )


def _entry_form() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.div(
                rx.icon("megaphone", class_name="h-6 w-6 text-white"),
                class_name="flex h-11 w-11 items-center justify-center rounded-xl bg-[#DC2626]",
            ),
            rx.el.div(
                rx.el.h2(
                    "Eigenes Angebot einstellen",
                    class_name="text-lg font-bold " + TEXT_PRIMARY,
                ),
                rx.el.p(
                    "Veröffentliche einen freien Managerposten oder eine komplette Liga.",
                    class_name="mt-1 text-sm " + TEXT_SECONDARY,
                ),
            ),
            class_name="flex items-start gap-3",
        ),
        _entry_form_message(),
        rx.el.form(
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Angebotsart *",
                        class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.select(
                        rx.el.option(
                            "Freier Managerposten", value="manager_spot"
                        ),
                        rx.el.option("Ganze Liga", value="whole_league"),
                        name="entry_type",
                        value=FantasyBoerseState.entry_type,
                        on_change=FantasyBoerseState.set_entry_type,
                        class_name="w-full appearance-none rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                        + t(
                            "border-white/10 bg-[#12141C] text-slate-100",
                            "border-gray-200 bg-white text-gray-800",
                        ),
                    ),
                    class_name="min-w-0",
                ),
                rx.el.div(
                    rx.el.label(
                        "Sleeper League-ID *",
                        class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.input(
                        name="league_id",
                        type="text",
                        input_mode="numeric",
                        placeholder="z. B. 123456789",
                        required=True,
                        class_name="w-full rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                        + t(
                            "border-white/10 bg-[#12141C] text-slate-100 placeholder:text-slate-500",
                            "border-gray-200 bg-white text-gray-800 placeholder:text-gray-400",
                        ),
                    ),
                    class_name="min-w-0",
                ),
                rx.el.div(
                    rx.cond(
                        FantasyBoerseState.entry_type == "manager_spot",
                        rx.el.div(
                            rx.el.label(
                                "Roster-Spot *",
                                class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.input(
                                name="roster_id",
                                type="number",
                                min="1",
                                step="1",
                                placeholder="z. B. 7",
                                required=True,
                                class_name="w-full rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                                + t(
                                    "border-white/10 bg-[#12141C] text-slate-100 placeholder:text-slate-500",
                                    "border-gray-200 bg-white text-gray-800 placeholder:text-gray-400",
                                ),
                            ),
                        ),
                        rx.el.div(
                            rx.el.label(
                                "Roster-Spot",
                                class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.p(
                                "Bei einer ganzen Liga nicht erforderlich.",
                                class_name="rounded-xl border border-dashed px-3 py-2.5 text-sm "
                                + t(
                                    "border-white/10 text-slate-500",
                                    "border-gray-200 text-gray-500",
                                ),
                            ),
                        ),
                    ),
                    class_name="min-w-0",
                ),
                rx.el.div(
                    rx.el.label(
                        "Buy-in in €",
                        class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.input(
                        name="buyin",
                        type="number",
                        min="0",
                        step="0.01",
                        placeholder="0,00",
                        class_name="w-full rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                        + t(
                            "border-white/10 bg-[#12141C] text-slate-100 placeholder:text-slate-500",
                            "border-gray-200 bg-white text-gray-800 placeholder:text-gray-400",
                        ),
                    ),
                    class_name="min-w-0",
                ),
                class_name="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Invite-Link",
                        class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.input(
                        name="invite_link",
                        type="url",
                        placeholder="https://sleeper.com/i/...",
                        class_name="w-full rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                        + t(
                            "border-white/10 bg-[#12141C] text-slate-100 placeholder:text-slate-500",
                            "border-gray-200 bg-white text-gray-800 placeholder:text-gray-400",
                        ),
                    ),
                    class_name="min-w-0",
                ),
                rx.el.div(
                    rx.el.label(
                        "Kontakt Sleeper *",
                        class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.input(
                        name="contact_sleeper",
                        type="text",
                        placeholder="Dein Sleeper-Name",
                        required=True,
                        class_name="w-full rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                        + t(
                            "border-white/10 bg-[#12141C] text-slate-100 placeholder:text-slate-500",
                            "border-gray-200 bg-white text-gray-800 placeholder:text-gray-400",
                        ),
                    ),
                    class_name="min-w-0",
                ),
                rx.el.div(
                    rx.el.label(
                        "Kontakt Discord *",
                        class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                        + TEXT_MUTED,
                    ),
                    rx.el.input(
                        name="contact_discord",
                        type="text",
                        placeholder="Dein Discord-Name",
                        required=True,
                        class_name="w-full rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                        + t(
                            "border-white/10 bg-[#12141C] text-slate-100 placeholder:text-slate-500",
                            "border-gray-200 bg-white text-gray-800 placeholder:text-gray-400",
                        ),
                    ),
                ),
                class_name="grid grid-cols-1 gap-4 md:grid-cols-3",
            ),
            rx.el.div(
                rx.el.label(
                    "Beschreibung *",
                    class_name="mb-2 block text-xs font-bold uppercase tracking-wide "
                    + TEXT_MUTED,
                ),
                rx.el.textarea(
                    name="description",
                    placeholder="Beschreibe kurz die Liga, den freien Platz oder wichtige Rahmenbedingungen …",
                    required=True,
                    rows=4,
                    max_length=500,
                    class_name="w-full resize-y rounded-xl border px-3 py-2.5 text-sm font-medium outline-hidden transition focus:border-[#DC2626] "
                    + t(
                        "border-white/10 bg-[#12141C] text-slate-100 placeholder:text-slate-500",
                        "border-gray-200 bg-white text-gray-800 placeholder:text-gray-400",
                    ),
                ),
                rx.el.p(
                    "Mindestens 20 Zeichen, maximal 500 Zeichen.",
                    class_name="mt-1 text-xs " + TEXT_MUTED,
                ),
            ),
            rx.el.div(
                rx.el.button(
                    rx.cond(
                        FantasyBoerseState.is_submitting,
                        rx.el.span(
                            rx.icon(
                                "loader-circle",
                                class_name="h-4 w-4 animate-spin",
                            ),
                            "Wird gespeichert …",
                            class_name="flex items-center gap-2",
                        ),
                        rx.el.span(
                            rx.icon("send", class_name="h-4 w-4"),
                            "Angebot veröffentlichen",
                            class_name="flex items-center gap-2",
                        ),
                    ),
                    type="submit",
                    disabled=FantasyBoerseState.is_submitting,
                    class_name="flex w-fit items-center justify-center gap-2 rounded-xl bg-[#DC2626] px-4 py-2.5 text-sm font-bold text-white transition hover:bg-[#B91C1C] disabled:cursor-not-allowed disabled:opacity-60",
                ),
                class_name="flex justify-end",
            ),
            key=FantasyBoerseState.form_reset_counter.to_string(),
            on_submit=FantasyBoerseState.submit_entry,
            reset_on_submit=False,
            class_name="flex flex-col gap-5",
        ),
        class_name="flex flex-col gap-5 rounded-2xl border-l-4 border-l-[#DC2626] p-5 "
        + t("border-white/10 bg-[#12141C]", "border-gray-200 bg-white"),
    )


def _listings() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Angebote", class_name="text-xl font-bold " + TEXT_PRIMARY
                ),
                rx.el.p(
                    f"{FantasyBoerseState.filtered_entries.length()} Treffer",
                    class_name="text-sm font-medium " + TEXT_MUTED,
                ),
                class_name="flex items-baseline gap-3",
            ),
            class_name="flex items-center justify-between",
        ),
        rx.el.div(
            rx.foreach(FantasyBoerseState.filtered_entries, _entry_card),
            class_name="mt-4 grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Kompakte Liste",
                    class_name="text-xl font-bold " + TEXT_PRIMARY,
                ),
                rx.el.p(
                    "Alle Treffer auf einen Blick",
                    class_name="text-sm font-medium " + TEXT_MUTED,
                ),
                class_name="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-3",
            ),
            rx.el.div(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th(
                                "Liga",
                                class_name="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.th(
                                "Form / Status",
                                class_name="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.th(
                                "Größe",
                                class_name="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.th(
                                "Buy-in",
                                class_name="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.th(
                                "Form / Scoring",
                                class_name="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.th(
                                "Roster-Struktur",
                                class_name="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            rx.el.th(
                                "Kontakt",
                                class_name="px-4 py-3 text-left text-xs font-bold uppercase tracking-wide "
                                + TEXT_MUTED,
                            ),
                            class_name=t("bg-[#0D1117]", "bg-gray-50"),
                        ),
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            FantasyBoerseState.filtered_entries, _table_row
                        )
                    ),
                    class_name="table-auto min-w-full",
                ),
                class_name="mt-4 overflow-x-auto rounded-2xl border "
                + t("border-white/10 bg-[#12141C]", "border-gray-200 bg-white"),
            ),
            class_name="mt-10",
        ),
        class_name="w-full",
    )


def fantasyboerse_content() -> rx.Component:
    return rx.el.div(
        rx.match(
            FantasyBoerseState.display_state,
            ("loading", _loading_state()),
            ("error", _error_state()),
            ("empty", _empty_state()),
            _listings(),
        ),
        class_name="w-full",
    )


def fantasyboerse_page_content() -> rx.Component:
    return rx.el.div(
        rx.el.section(
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("store", class_name="h-7 w-7 text-white"),
                        class_name="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#DC2626]",
                    ),
                    rx.el.div(
                        rx.el.p(
                            "STONED LACK COMMUNITY",
                            class_name="text-xs font-bold uppercase tracking-[0.18em] text-[#DC2626]",
                        ),
                        rx.el.h1(
                            "Fantasybörse",
                            class_name="mt-1 text-3xl font-bold tracking-tight "
                            + TEXT_PRIMARY,
                        ),
                    ),
                    class_name="flex items-center gap-4",
                ),
                rx.el.p(
                    "Freie Managerposten und ganze Ligen der Stoned Lack Army auf einen Blick.",
                    class_name="mt-5 max-w-3xl text-base leading-7 "
                    + TEXT_SECONDARY,
                ),
                class_name="rounded-2xl border-l-4 border-l-[#DC2626] p-6 "
                + t("border-white/10 bg-[#12141C]", "border-gray-200 bg-white"),
            ),
            class_name="w-full",
        ),
        rx.el.div(
            _stat_card(
                "Angebote gesamt", FantasyBoerseState.total_count, "layers-3"
            ),
            _stat_card(
                "Davon frei", FantasyBoerseState.open_count, "circle-check"
            ),
            _stat_card(
                "Managerposten",
                FantasyBoerseState.manager_spot_count,
                "user-round",
            ),
            _stat_card(
                "Ganze Ligen", FantasyBoerseState.whole_league_count, "trophy"
            ),
            class_name="grid grid-cols-2 gap-4 lg:grid-cols-4",
        ),
        rx.el.section(
            rx.el.div(
                rx.el.div(
                    rx.icon(
                        "sliders-horizontal",
                        class_name="h-5 w-5 text-[#DC2626]",
                    ),
                    rx.el.h2(
                        "Angebote filtern",
                        class_name="text-lg font-bold " + TEXT_PRIMARY,
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.p(
                    "Finde das passende Format, die richtige Liga-Größe und dein Budget.",
                    class_name="mt-1 text-sm " + TEXT_SECONDARY,
                ),
                class_name="mb-5",
            ),
            _filter_bar(),
            _active_filters(),
            class_name="rounded-2xl border p-5 "
            + t("border-white/10 bg-[#12141C]", "border-gray-200 bg-white"),
        ),
        _entry_form(),
        fantasyboerse_content(),
        class_name="flex w-full flex-col gap-6",
    )
