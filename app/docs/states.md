# State-Referenz

Eine Datei = eine State-Klasse (`app/states/`). Für jede Klasse:
**Zweck**, **Variablen**, **Computed Vars**, **Events**, **private Helper**,
**Abhängigkeiten** und **Seiteneffekte / Fallstricke**.

Inhalt:
[AppState](#appstate) ·
[UserState](#userstate) ·
[ThemeState](#themestate) ·
[LeaguesState](#leaguesstate) ·
[LeaguePageState](#leaguepagestate) ·
[LeagueDetailState](#leaguedetailstate) ·
[ArchiveState](#archivestate) ·
[MatchupsState](#matchupsstate) ·
[DraftState](#draftstate) ·
[AdpState](#adpstate) ·
[CommunityState](#communitystate) ·
[WaitlistState](#waitliststate) ·
[RedraftRegistrationState](#redraftregistrationstate) ·
[AdminAuthState](#adminauthstate) ·
[AdminState](#adminstate)

---

## AppState

`app/states/app_state.py` — globaler App-Kontext: NFL-Status, Liga-Grunddaten,
Auswahl der aktiven Liga, Trending-Teaser.

### Modulfunktion

`league_sort_key(lg) -> tuple` — kanonische Sortierung
(`season DESC`, `league_sort ASC` mit NULLs hinten, `name ASC`). Funktioniert
sowohl mit normalisierten Dicts (`season`, `name`) als auch mit Supabase-Rohzeilen
(`league_season`, `league_name`).

### Variablen

| Var | Typ | Bedeutung |
| --- | --- | --- |
| `configured_league_ids` | `list[str]` | IDs aller geladenen Ligen |
| `nfl_state` | `dict[str, str|int|bool]` | Antwort von `/state/nfl`, `None`-Werte auf `""` normalisiert |
| `leagues_data` | `list[dict]` | Normalisierte Ligen (Schema siehe `_normalize_league`) |
| `selected_league_id` | `str` | Ausgewählte Liga für Matchups/Standings/Rosters; `""` = „alle“ |
| `trending_adds` | `list[dict]` | Top-5 Trending-Adds (angereichert) |
| `is_loading`, `is_full_loaded` | `bool` | Ladezustand / ob **alle** Saisons geladen sind |
| `search_query`, `filter_type` | `str` | **ungenutzt** (Altlast) |

`_normalize_league(lg, live_data=None)` erzeugt:
`league_id, name, season, status, types, total_rosters, avatar, league_sort`.
`status` = `primary` aus `normalize_league_types`, `types` = vollständige Liste.

### Computed Vars

| Var | Logik |
| --- | --- |
| `current_season` | Max. numerische `season` aus `leagues_data`, sonst `nfl_state["season"]`, sonst `""` |
| `current_dynasty_leagues` / `current_redraft_leagues` / `current_bestball_leagues` / `current_idp_leagues` | Ligen der aktuellen Saison, deren `types` (Fallback `status`) das Format enthalten. IDP prüft `idp` **oder** `idp_only` |
| `archived_leagues` | Alle Ligen, deren Saison ≠ `current_season` |
| `archive_seasons` | Saisons im Archiv, absteigend |
| `archived_dynasty_leagues` / `archived_redraft_leagues` / `archived_other_leagues` | Archiv nach Format |

Helper: `_lg_types_normalized(lg)` — Liste kleingeschriebener Formen,
Fallback auf `status`.

### Events

| Event | Wirkung |
| --- | --- |
| `init_app` | Kette: `fetch_nfl_state` → `fetch_trending` → `fetch_current_season_leagues` |
| `fetch_nfl_state` | Sleeper `/state/nfl` |
| `fetch_trending` | Sleeper Trending (limit 5) + `enrich_trending` |
| `fetch_current_season_leagues` | Max-Saison ermitteln, nur diese Ligen laden (schneller Erststart), `is_full_loaded=False` |
| `fetch_all_leagues_data` | Alle Ligen; bei ≤ 10 Ligen zusätzlich Live-`get_league` je Liga; `is_full_loaded=True` |
| `ensure_all_leagues_loaded` | Lädt Vollbestand, falls noch nicht geladen |
| `select_league(league_id)` | Setzt `selected_league_id` (entfernt Anführungszeichen) |

### Abhängigkeiten & Seiteneffekte

- Supabase `leagues`, Sleeper `/state/nfl`, `/league/{id}`, Trending.
- `fetch_all_leagues_data` mit Live-Enrichment kann bei kleinen Beständen
  10 HTTP-Requests auslösen — bewusst limitiert.
- `MatchupsState` schreibt `selected_league_id` direkt (`app_state.selected_league_id = ""`),
  wenn die Auswahl nicht zur aktuellen Saison gehört.

---

## UserState

`app/states/user_state.py` — Sleeper-Login („Login“ = Namensauflösung, kein Auth).

### Variablen

`sleeper_username` ist **`rx.LocalStorage`** (`name="sl_sleeper_username"`) und
überlebt daher Reloads. Weiter: `sleeper_user_id`, `sleeper_display_name`,
`sleeper_avatar`, `user_league_ids: list[str]`,
`my_leagues_data: list[dict]`, `is_resolving`, `is_loading_my_leagues`,
`username_input`.

### Computed Vars

`my_leagues_count`, `my_dynasty_leagues`, `my_redraft_leagues`,
`my_other_leagues` (jeweils über `status`), `is_logged_in`
(`username != "" and user_id != ""`), `has_username`.

### Events

| Event | Wirkung |
| --- | --- |
| `set_username_input(val)` | Eingabefeld |
| `save_username` | Trim + Toast bei leer, setzt `sleeper_username`, ruft `resolve_user` |
| `resolve_user` | `GET /v1/user/{name}` → `user_id`, `display_name`, `avatar`; dann `managers`-Query nach `user_id` → `user_league_ids`; danach `_load_my_leagues_data` |
| `init_user` | `on_load`-Hook: ruft `resolve_user`, wenn ein Name im LocalStorage steht |
| `clear_username` | Setzt alles zurück (Logout) |

Helper `_load_my_leagues_data(client)`: lädt `leagues` per `in_()` in Chunks von
100, mit `add_types_col`-Retry, normalisiert wie `AppState` und sortiert
`season DESC → league_sort → name`.

### Seiteneffekte

- Wird von `LeaguesState` **gelesen** (`await self.get_state(UserState)`) für den
  „Meine Ligen“-Scope-Filter.
- Ohne Supabase bleiben `user_league_ids`/`my_leagues_data` leer, `is_logged_in`
  ist trotzdem `True` (Sleeper hat geantwortet).

---

## ThemeState

`app/states/theme_state.py` — nur der Mobile-Drawer.
Vars: `mobile_sidebar_open: bool`.
Events: `toggle_mobile_sidebar`, `close_mobile_sidebar`.
Der Farbmodus selbst läuft über Reflex-Standard (`rx.toggle_color_mode`,
`rx.color_mode_cond` / `theme.t`).

---

## LeaguesState

`app/states/leagues_state.py` — Liga-Übersicht `/leagues` mit Filtern, Sortierung
und zweistufigem Laden.

### Modul-Helper

- `_lg_sort_key(lg)` — Sortierung wie oben.
- `PAGE_SIZE = 1000`.
- `_paginated_in_query(client, table, cols, filter_col, values, extra_eq, id_batch)`
  — kombiniert ID-Batching und Range-Paginierung.

### Variablen

Daten: `all_leagues`, `available_seasons`, `available_types`,
`available_managers`, `manager_to_leagues: dict[str, list[str]]`,
`current_season`, `is_loading`, `is_full_loaded`.

Filter: `selected_season`, `selected_type`, `selected_manager`,
`selected_week`, `selected_scope` (`all|mine|others`), `search_query`,
`sort_by` (`season_desc|season_asc|name_asc|name_desc|managers_desc|managers_asc|week_desc|week_asc`).

Jede Zeile in `all_leagues`:
`league_id, league_name, season, type, types, manager_count, manager_sample,
manager_names, available_weeks (list[str]), latest_week (int), league_sort, avatar`.

### Computed Vars

- `has_active_filters`, `active_filter_count`, `total_count`
- `filtered_leagues` — **async** Computed Var! Liest `UserState` über
  `_is_logged_in()` / `_get_user_league_ids()`, filtert Saison → Typ (Membership
  in `types`) → Manager → Woche → Scope → Freitext (inkl. Managernamen) und
  sortiert nach `sort_by`. Im Frontend ohne `await` verwendbar, im Backend
  **muss** `await self.filtered_leagues` verwendet werden.
- `result_count` — `len(await self.filtered_leagues)`

### Events

| Event | Besonderheit |
| --- | --- |
| `load_leagues` | `on_load`: ermittelt Max-Saison, lädt nur diese, `is_full_loaded=False`. Ruft `_populate_from_rows(..., include_week_metadata=True)` |
| `load_full_leagues` | Lädt alle Saisons (ohne Wochen-Metadaten!), idempotent |
| `ensure_full_loaded` | Synchroner Wrapper |
| `set_selected_season(val)` | Lädt Vollbestand nach, wenn eine andere als die aktuelle Saison gewählt wird |
| `set_selected_manager(val)` | Lädt Vollbestand nach, wenn ≠ `all` |
| `set_search_query(val)` | Lädt Vollbestand nach, wenn nicht leer |
| `set_selected_week(val)` | **Lazy Load** der Wochen-Verfügbarkeit für genau diese Woche |
| `set_selected_type`, `set_selected_scope`, `set_sort_by` | reine Setter |
| `reset_filters`, `clear_season/type/manager/week/scope/search` | Filter zurücksetzen |

### Private Helper

- `_populate_from_rows(client, rows, include_week_metadata=True)` — baut alle
  Listen/Maps. Managers werden paginiert geladen.
- `_collect_week_availability(client, table, ids, out)` — pro Woche `0..18` eine
  gezielte Abfrage (`.eq("week", w)`), nur `league_id,week` selektiert.
  **Nur** im Current-Season-Pfad aktiv, weil es über alle Historien zu langsam wäre.
- `_ensure_week_metadata_for_selected(week)` — Nachladen genau einer Woche für
  Ligen ohne Wochen-Metadaten; aktualisiert `available_weeks`/`latest_week`.
- `_load_full_leagues_sync()` — synchrone Variante, damit Setter-Events die Daten
  noch im selben Event-Tick haben.
- `_needs_full_data()` — Heuristik (aktuell nicht mehr aufgerufen, die Setter
  entscheiden selbst).

### Fallstricke

- Historische Ligen haben nach dem Vollbestand-Load zunächst
  `available_weeks == []`. Der Wochenfilter füllt sie **erst bei Auswahl** nach.
- `filtered_leagues` ist async — nicht in synchronen Helpern verwenden.

---

## LeaguePageState

`app/states/league_page_state.py` — Detailseite `/leagues/[lid]`.

### Variablen

Status: `loading`, `not_found`, `error_message`.
Meta: `league_id`, `league_name`, `league_type`, `league_types`,
`league_season`, `league_avatar`, `roster_positions`, `predecessor`
(`{league_id, name?, season?}`), `total_rosters`, `manager_count`, `latest_week`.
Daten: `available_weeks: list[int]`, `selected_matchup_week`, `champion`,
`top_standings`, `full_standings`, `matchup_pairs`, `manager_cards`,
`roster_cards`, `trades`, `trades_available`, `drafts`.

> `league_id` ist eine **eigene** State-Var — das ist erlaubt, weil der
> Routen-Parameter `lid` heißt.

### Events

| Event | Wirkung |
| --- | --- |
| `load_league` | `on_load`. Reset → `_extract_route_id()` → `not_found` bei leer → delegiert an `load_league_by_id` |
| `load_league_by_id(lid)` | Der eigentliche Ladevorgang (testbar ohne Router) |
| `change_matchup_week(week)` | Lädt nur `matchup_pairs` für die neue Woche neu (Manager-Map wird dafür erneut geholt) |

### Ladereihenfolge in `load_league_by_id`

1. `leagues` (1 Zeile) → Meta, `roster_positions`, `previous_league_id`
2. Vorgängerliga (Name/Saison) — bei Fehler bleibt nur die ID im `predecessor`
3. `managers` → `manager_count`, `mgr_map[roster_id]`
4. `rosters` max. `week` → `latest_week`
5. `rosters` (Top 5) → `top_standings` *(wird von der Seite nicht gerendert)*
6. `league_champion` → `champion`
7. `rosters` (alle) → `full_standings` inkl. `win_pct` und `win_pct_str`
8. `matchup_week_stats` Wochen-Set → `available_weeks`, Auswahl = max, dann
   `_fetch_matchup_pairs`
9. `manager_cards`
10. `roster_cards` (Starter/Bench/Reserve angereichert) *(nicht gerendert)*
11. `trades = []`, `trades_available = False` (es existiert keine Trade-Tabelle)
12. `drafts` inkl. Typ-Label, Datum, Sleeper-URL

Jeder Block hat sein eigenes `try/except` + `logging.exception` — ein Teilfehler
bricht die Seite nicht ab.

### Private Helper

- `_reset_state()`
- `_extract_route_id()` — liest `router.page.params` und (defensiv)
  `router.url.query_parameters`; akzeptiert `lid` und `league_id`, entpackt Listen.
- `_build_lineup(row)` — Starter/Bench/Reserve (inkl. `taxi`) + Punkte-Auflösung
  (`players_points` → `starters_points` → `custom_points` → 0.0).
- `_fetch_matchup_pairs(client, league_id, week, mgr_map)` — Paarbildung nach
  `matchup_id`; Einzel-Eintrag → `is_bye=True` mit leerem Team B.

---

## LeagueDetailState

`app/states/league_detail_state.py` — Vars und Events für den **Modal-Dialog**
`app/components/league_modal.py`.

> **Status: toter Code.** Weder `league_detail_modal()` noch
> `open_league_modal` werden von einer Seite aufgerufen; die Detailansicht läuft
> heute über die eigene Route `/leagues/[lid]`. Der Import in `app/app.py` hält
> die Klasse lediglich registriert. Beim Entfernen: Import **und** Komponente
> gemeinsam löschen.

Vars: `show_modal`, `modal_loading`, `modal_league_id/name/type/season`,
`modal_standings`, `modal_recent_matchups`, `modal_champion`,
`modal_roster_positions`.
Events: `open_league_modal(league_id)` (liest `AppState.leagues_data` für Meta und
danach `rosters`/`managers`/`matchup_week_stats`/`league_champion`/`leagues`),
`close_league_modal`, `set_modal_open(is_open)`.

---

## ArchiveState

`app/states/archive_state.py` — Seite `/archive`: alle Ligen **außer** der
aktuellen Saison.

Vars: `is_loading`, `all_leagues`, `manager_counts`, `manager_samples`,
`available_seasons`, `available_types`, `available_managers`,
`manager_to_leagues`, `current_season`;
Filter: `selected_season`, `selected_type`, `selected_manager`, `search_query`.

Event `load_archive` (`on_load`):
`leagues` (mit `add_types_col`-Retry, sortiert `season DESC, league_sort ASC`) →
Max-Saison bestimmen → `managers` in Chunks von 200 →
`manager_counts`/`manager_samples` (max. 3 Namen) / `manager_to_leagues` →
alle Ligen mit `season != current_season` in `all_leagues`.
`available_types` enthält nur Werte aus `SUPPORTED_TYPES`.

Setter/Clear-Events analog `LeaguesState` (ohne Woche/Scope).

Computed: `has_active_filters`, `active_filter_count`, `filtered_leagues`
(synchron!), `result_count`, `total_archive_count`.

---

## MatchupsState

`app/states/matchups_state.py` — Basis für `/matchups`, `/standings`, `/rosters`.

### Variablen

`selected_week`, `is_loading`, `matchups_by_league: dict[str, list[...]]`,
`league_names: dict[str, str]`, `current_season`, `current_nfl_week`,
`available_weeks: list[int]`, `current_league_ids`, `current_leagues_meta`,
`matchups_data`, `paired_matchups`, `league_users`, `league_rosters`,
`standings_data`, `selected_roster`.

Computed: `week_options` (**ungenutzt**), `current_league_options`
(= `current_leagues_meta`).

### Events

| Event | Wirkung |
| --- | --- |
| `init_matchups` | `on_load` `/matchups`. Liest `AppState`; wenn `leagues_data` leer ist, **Fallback** `_load_current_leagues_from_supabase()`. Ermittelt `current_nfl_week`, leert eine ungültige Ligaauswahl, lädt `available_weeks`, wählt Startwoche (aktuelle NFL-Woche, sonst kleinste Woche ≥ aktuell, sonst max) und lädt Matchups |
| `init_standings` / `init_rosters` | Laden nur bei gesetzter `selected_league_id` |
| `fetch_all_matchups` | Wrapper um `_load_all_matchups_for_current_season` |
| `fetch_matchups(week)` | Ohne Ligaauswahl → `fetch_all_matchups`; sonst `matchup_week_stats` für Liga+Woche, Paarbildung |
| `fetch_league_detail` | **Live** Sleeper: `get_league_users`, `get_rosters` |
| `fetch_standings` | **Live** Sleeper; berechnet W/L/T, `win_pct`, `fpts`, `fpts_against`, sortiert nach `(wins, fpts)` und setzt `rank` |
| `change_week(week)` / `change_week_str(val)` | Validierung gegen `available_weeks`, dann Neuladen |
| `view_roster(roster_id)` | Baut `selected_roster` aus `league_rosters` + `league_users`, reichert `starters`/`reserve` an und **redirectet auf `/rosters`** |
| `clear_selected_roster` | Zurück zur Kachelübersicht |

### Private Helper

`_determine_current_season(app_state)`,
`_load_current_leagues_from_supabase()`,
`_load_available_weeks(ids)`,
`_load_managers_map(client, ids)` → `{(league_id, roster_id): row}`,
`_build_pair_entry(matchup_id, a, b, mgr_map, league_id)` → `{matchup_id, team_a, team_b|None}`,
`_load_all_matchups_for_current_season()`.

### Fallstricke

- `/standings` und `/rosters` sind **live** von Sleeper abhängig. Ohne gesetzte
  `selected_league_id` zeigen sie die Leerzustände.
- `matchup_card` in `pages/matchups.py` erwartet `team_b` ggf. `None`
  (Vergleich `matchup["team_b"] != None`).

---

## DraftState

`app/states/draft_state.py` — Seite `/drafts`.

### Modul-Konstanten & Helper

`ACTIVE_STATUSES = {drafting, paused}`,
`SCHEDULED_STATUSES = {pre_draft}`,
`COMPLETED_STATUSES = {complete, completed}`;
`_dtype_label(raw)`, `_format_start_time(raw) -> (display, ts)`,
`_detect_flags(league_name, league_type, types_list)` →
`is_dynasty/is_redraft/is_bestball/is_idp` (Membership in `types_list`,
Fallback Legacy-Skalar, zusätzlich Namensheuristik für `BESTBALL`/`IDP`).

### Variablen

`is_loading`, `draft_filter` (`All|Active|Scheduled|Completed|Dynasty|Redraft|IDP|Bestball`),
`show_all_completed`, `all_drafts`, `active_drafts`, `scheduled_drafts`,
`completed_drafts`, `other_drafts`, `season_breakdown`.

### Events

- `init_drafts` (`on_load`): lädt `drafts` + `leagues` (mit Retry-Fallback),
  ermittelt Liga-IDs der **aktiven** Drafts, lädt dafür `managers`
  (Maps nach `roster_id` **und** `user_id`), baut je Draft ein Basis-Dict
  (`_build_base_draft`), reichert aktive Drafts live an (`_enrich_live_draft`),
  sortiert die vier Listen und berechnet `season_breakdown`.
- `set_draft_filter(new_filter)`, `toggle_completed`.

### Private Helper

- `_build_base_draft(d, lg)` — Basisfelder + Sleeper-Board-URL
  (`https://sleeper.com/draft/nfl/{draft_id}`) + Default-Live-Felder (0/"").
- `_status_label(status)` — `LIVE`, `PAUSED`, `SCHEDULED`, `COMPLETED`, sonst UPPER.
- `_enrich_live_draft(base, managers_by_league, managers_by_user)` —
  `get_draft`, `get_draft_picks`, `get_league`:
  - `rounds`, `teams`, `total_slots = rounds * teams`, `progress_pct`
  - letzter Pick (Name/Team/Pos) + `picked_by` → Manager/Team über `user_id`
  - „on the clock“: **bevorzugt** `league.metadata.on_the_clock_user_id`
    (`on_clock_source = "on_the_clock_user_id"`), sonst Slot-Berechnung
    (Snake: gerade Runde spiegelt Slot) über `slot_to_roster_id`
    (`on_clock_source = "slot_calculation"`)
- `_matches_filter(d)` — Filterlogik für die vier Computed Vars.

### Computed Vars

`filtered_active`, `filtered_scheduled`, `filtered_completed`, `filtered_other`,
`active_count`, `scheduled_count`, `completed_count`, `total_count`, `other_count`.

### Seiteneffekte

Pro aktivem Draft bis zu **drei** Sleeper-Requests bei jedem Seitenaufruf.
Bei vielen parallelen Live-Drafts kann `init_drafts` merklich dauern.

---

## AdpState

`app/states/adp_state.py` — Seite `/adp` (Average Draft Position + Draftboard).

### Modulebene

- `BOARD_SLOTS = 12`
- `_ADP_RESULTS_CACHE: dict[(season, format, draft_type), payload]` —
  **prozessweiter** Cache, damit Filterwechsel synchron und ohne DB-Roundtrip
  reagieren.

### Variablen

`is_loading`, `selected_season`, `selected_format`
(`dynasty|dynasty_idp|redraft` — `bestball` ist in `_get_matching_league_ids`
implementiert, aber nicht in der UI), `selected_draft_type`
(`"0"` alle Spieler, `"1"` Rookies, `"2"` Veterans), `available_seasons`,
`table_search`, `table_position`, `min_pick_count`, `min_pick_reset_counter`,
`adp_players`, `board_cells`, `total_drafts`, `total_picks`, `total_players`.

Ein `adp_players`-Eintrag:
`player_id, full_name, position, team, count, adp, adp_str, min_pick, max_pick,
avg_round, avg_slot, avg_display, overall_rank, overall_pick_rank,
positional_rank, positional_pick_rank`.

### Computed Vars

| Var | Logik |
| --- | --- |
| `max_pick_count` | Maximales `count` (Slider-Obergrenze) |
| `players_meeting_threshold` | Spieler mit `count >= min_pick_count` |
| `filtered_board_cells` | Board aus den Threshold-Spielern (`_build_board_cells`) |
| `filtered_total_rounds`, `filtered_round_range` | Runden für das gefilterte Board |
| `board_layout` | `redraft` → `snake`; Dynasty: Rookie-Draft (`"1"`) → `linear`, sonst `snake` |
| `total_rounds`, `round_range`, `slot_range` | Board-Geometrie (12 Slots) |
| `available_positions` | Positionen ≠ `?` |
| `filtered_players`, `filtered_count`, `has_table_filters` | Tabellenfilter (Threshold + Position + Freitext) |

### Events

`init_adp` (`load_seasons` → `load_adp`), `load_seasons`, `load_adp`,
`set_selected_season/format/draft_type` (jeweils Tabellenfilter zurücksetzen +
`_recompute_adp()`), `set_table_search`, `set_table_position`,
`clear_table_filters`, `set_min_pick_count(val)` (auf `1..max` geklemmt),
`reset_min_pick_count` (erhöht `min_pick_reset_counter`, damit der
`rx.el.input[type=range]` per `key` neu gemountet wird).

### Private Helper

- `_get_matching_league_ids(client)` — `leagues` (mit Retry-Fallback);
  IDP-Erkennung über `types` **oder** `"IDP"` im Namen; `dynasty` schließt IDP aus,
  `dynasty_idp` verlangt IDP.
- `_get_matching_draft_ids(client, league_ids)` — `drafts` mit
  `status=complete`, `season`, `draft_type`, ID-Batches à 100.
- `_fetch_picks(client, draft_ids)` — `draft_picks` mit Range-Paginierung
  (1000er-Seiten, Draft-Batches à 50).
- `_build_board_cells(players)` — ADP-Reihenfolge → Runde/Slot;
  im Snake-Layout wird in geraden Runden die Spalte gespiegelt.
  `pick_notation` = `R.Slot`.
- `_cache_key()`, `_apply_cached(payload)`, `_recompute_adp()`,
  `_load_adp_sync()`, `_clear_table_filters()`.

### Aggregation in `_load_adp_sync`

Picks → pro `player_id` alle `pick_no` sammeln → `count`, `adp` (Mittel),
`min`, `max`, `avg_round`/`avg_slot` (12er-Basis) → Sortierung nach `adp` →
`overall_rank` und positionaler Rang (`QB#3`) → Board-Zellen → Cache-Eintrag.

---

## CommunityState

`app/states/community_state.py` — News, Polls, YouTube, Trending.

### Variablen

`polls`, `news_items`, `polls_loaded`, `news_loaded`, `voted_polls: list[str]`,
`youtube_videos`, `youtube_filter` (`All|Videos|Shorts`),
`trending_adds`, `trending_drops`, `trending_timeframe` (`24h|48h`);
Altlast: `reg_team_name`, `reg_email`, `reg_sleeper_username`,
`reg_preferred_league`, `registration_submitted`, `registrations`.

Poll-Schema: `{id, question, options:[{text, votes, pct_str}], total_votes, is_active}`.
`pct_str` ist deutsch formatiert: `"52,3 % (47 Stimmen)"`.

### Events

| Event | Wirkung |
| --- | --- |
| `load_polls` | `polls` (desc `created_at`), Prozentwerte vorberechnen |
| `load_news` | `news` (desc), Datum `%d. %B %Y` |
| `vote_poll(poll_id, option_index)` | Doppelabstimmung wird über `voted_polls` (nur clientseitige State-Liste!) verhindert; aktualisiert lokal **und** per UPDATE `polls.stats` |
| `fetch_trending` | Sleeper Trending Add/Drop mit `lookback_hours` 24/48, limit 25 |
| `change_trending_timeframe(tf)` | Setzt Zeitraum + `fetch_trending` |
| `fetch_youtube_feed` | `app.youtube_feed.fetch_youtube_feed(limit=15)` |
| `set_youtube_filter(t)` | Filter für `filtered_youtube_videos` |
| `submit_registration` | **Legacy**: schreibt in `dynasty_waitinglist`; von keiner Seite aufgerufen |
| `init_community` | Polls + News + YouTube |
| `init_trending` | Nur Trending |

Computed: `filtered_youtube_videos` (All / nur Videos / nur Shorts).

### Fallstricke

- `voted_polls` lebt nur in der Session — ein Reload erlaubt erneutes Abstimmen.
  Für echte Vote-Sperren wäre eine Tabelle mit `user_id` nötig.
- `vote_poll` castet `poll_id` nach `int` für das DB-Update; die Poll-`id` muss
  numerisch bleiben.

---

## WaitlistState

`app/states/waitlist_state.py` — Seite `/waitinglist` (Dynasty-Warteliste).

### Variablen

Eingaben: `sleeper_name_input`, `discord_input`, `dynasty_checked`,
`dynasty_idp_checked`, `dynasty_bb_checked`.
Auflösung: `resolved_user_id`, `resolved_display_name`, `resolved_avatar`,
`username_valid`, `username_error`, `is_resolving`.
Prozess: `is_submitting`, `is_removing`, `submit_success`, `existing_entry`.
Statistik: `total_dynasty`, `total_idp`, `total_bb`, `total_registrations`,
`all_entries`.

### Computed Vars

`dynasty_entries`, `dynasty_idp_entries`, `dynasty_bb_entries` —
filtern `all_entries` nach Flag, sortieren nach dem **formatspezifischen**
Zeitstempel (`registration_dyn|idp|bb`, Fallback `created_at`) und ergänzen
`time_display` (`%d.%m.%Y %H:%M`).

### Events

| Event | Wirkung |
| --- | --- |
| `set_sleeper_name_input`, `set_discord_input` | Setter |
| `toggle_dynasty`, `toggle_dynasty_idp`, `toggle_dynasty_bb` | Format-Auswahl |
| `validate_sleeper_name` | Sleeper `/user/{name}`; bei Erfolg Lookup in `dynasty_waitinglist` per `user_id` → `existing_entry` und Vorbelegung von Checkboxen + Discord |
| `submit_waitlist` | Validierung (min. 1 Format, geprüfter Name, Discord Pflicht) → Upsert `on_conflict=user_id`. **Zeitstempel-Logik:** bestehender `registration_*` bleibt erhalten, wenn das Format vorher schon gewählt war; neu gewählt → `now`; abgewählt → `None` |
| `remove_from_waitlist` | DELETE nach `user_id`, danach vollständiger Formular-Reset |
| `reset_form` | Formular leeren |
| `load_waitlist_stats` | Alle Zeilen laden, Zähler berechnen, `all_entries` aufbauen |
| `init_waitlist` | `on_load` → `load_waitlist_stats` |

Helper: `_sort_key(entry, ts_field)` (stabiler Fallback), `_format_iso_to_display`.

---

## RedraftRegistrationState

`app/states/redraft_registration_state.py` — Seite `/redraft-registration`.
Vollständige fachliche Beschreibung: [`redraft_auslosung.md`](redraft_auslosung.md).

### Modulebene

`PRIMARY_TABLE = "redraft_registration_2026"`,
`FALLBACK_TABLE = "user_registration"` (nur **Lesen**),
`_OPTIONAL_COLUMNS = ("commish", "Doppelanmeldung")`,
`_gen_code(n=10)` (A-Z0-9 via `secrets`),
`_normalize_name(s)`, `_make_index(sleeper, user_id)` (Slug `[a-z0-9_.-]`,
Fallback `uid_…` / `anon_…`, max. 64 Zeichen).

### Variablen

Eingaben: `sleeper_input`, `discord_input`, `email_input`,
`teammate1..3_input`, `edit_code_input`, `commish_input`.
Auflösung: `resolved_user_id`, `resolved_display_name`, `resolved_avatar`,
`is_resolving`, `username_valid`, `username_error`.
Prozess: `is_submitting`, `submit_success`, `generated_code`,
`status_message`, `status_type`, `table_missing`, `using_fallback`,
`existing_entry`, `entries`, `is_loading`.

### Computed Vars

`total_entries`, `commish_count`, `full_leagues_count` (`// 12`),
`remaining_for_next_league` (`12 - n % 12`, `0` wenn voll).

### Events

| Event | Wirkung |
| --- | --- |
| `init_page` | `on_load` → `load_entries` |
| `load_entries` | Liest `PRIMARY_TABLE`; bei Fehler still auf `FALLBACK_TABLE` (setzt `table_missing`/`using_fallback`) → Warnbanner. Sortiert clientseitig nach `created_at` (fehlend → hinten), berechnet **gegenseitige Wünsche** (`✓`-Markierung, `mutual_count`). **E-Mail und `key` werden nie in `entries` übernommen.** |
| `validate_sleeper` | Sleeper `/user/{name}` → IDs; danach Lookup in `PRIMARY_TABLE` nach `user_id` → `existing_entry` (inkl. `key` für die interne Prüfung) und Vorbelegung von `commish_input` |
| `submit_registration` | Siehe unten |
| `reset_form` | Alles zurücksetzen |
| Setter | `set_sleeper_input`, `set_discord_input`, `set_email_input`, `set_teammate1..3_input`, `set_edit_code_input`, `set_commish_input(v)`, `set_commish_yes`, `set_commish_no`, `clear_status` |

### `submit_registration` — Ablauf

1. Vorbedingungen: geprüfter Sleeper-Name, Discord Pflicht, E-Mail optional
   (muss `@` enthalten, wenn gesetzt).
2. `_normalize_mates()` → `_resolve_teammates()`:
   - Erst **lokale** Prüfung (Selbstwunsch, Duplikate) → keine unnötigen
     Sleeper-Requests.
   - Dann pro Name `/user/{name}`; unbekannter Name ⇒ Abbruch mit Fehlermeldung.
   - Rückgabe: Anzeigenamen + `user_id`s.
3. Existenzprüfung über `existing_entry` (bzw. DB, wenn ein Code eingegeben wurde).
4. **Strikte Code-Pflicht:** existiert eine Anmeldung, wird **ohne** korrekten
   `key` **nichts** geschrieben (klare Fehlermeldung). Mit korrektem Code:
   UPDATE, `key` bleibt erhalten.
5. Payload: `index`, `user_id`, `sleeper`, `discord`, `email`, `mitspieler`,
   `mitspieler_user_ids`, `key` + optional `commish`, `Doppelanmeldung`.
   `created_at` **nur beim INSERT** (Updates dürfen es nicht überschreiben).
6. `_write()` versucht den Schreibvorgang und entfernt bei
   `PGRST204 / Could not find the 'X' column` genau diese optionale Spalte
   (max. `len(optional)+3` Versuche). Pflichtspalten werden nie entfernt.
7. Erfolg → `generated_code`, `submit_success`, `existing_entry` aktualisieren,
   `load_entries` nachziehen.

Helper: `_parse_mates(raw)` (Liste / JSON / CSV), `_fetch_from_table`,
`_set_status`, `_clear_status`.

---

## AdminAuthState

`app/states/admin_auth_state.py` — Passwortschutz für `/admin`.

Konstanten: `_SALT = b"stoned_lack_admin_v1_salt"`, `_ITERATIONS = 200_000`,
`_MAX_ATTEMPTS = 5`, `_LOCKOUT_SECONDS = 60`.
Helper: `_hash_password(pw)` (PBKDF2-SHA256 Hex), `_expected_hash()`
(`ADMIN_PASSWORD_HASH` → `ADMIN_PASSWORD` → Fallback `stonedlack2026`).

Vars: `is_authenticated`, `password_input`, `error_message`,
`failed_attempts`, `locked_until`, `is_checking`.
Computed: `is_locked`, `lockout_remaining`.
Events: `set_password_input(val)`, `submit_login` (Vergleich mit
`hmac.compare_digest`, Sperre nach 5 Fehlversuchen), `logout`.

> Der Auth-Status lebt in der Session (kein Cookie/LocalStorage) — ein Reload
> erfordert erneutes Login. **Jeder** schreibende `AdminState`-Handler prüft
> zusätzlich `await self._require_auth()`.

---

## AdminState

`app/states/admin_state.py` — größte State-Klasse: Liga-Verwaltung, Sync-Jobs,
Sync-Protokoll und Redraft-Auslosung.

### Variablen — Liga-Verwaltung

`leagues` (Zeilen mit `league_id, league_name, league_season, league_type,
league_types, avatar, league_sort`), `is_loading`, `is_syncing`, `sync_target`,
`add_league_input`, `add_league_type` (`dynasty|redraft|bestball`),
`search_query`, `filter_type`, `status_message`, `status_type`,
`log_entries` (max. 50, neueste zuerst), `last_sync_time`,
`show_confirm_sync_all`.

### Variablen — Bulk-Sync-Steuerung

`week_mode` (`single|range|all`), `week_single`, `week_start`, `week_end`
(jeweils auf 0..18 geklemmt), `target_league_id` (`""` = alle),
`sync_operation` (Anzeigename des laufenden Jobs).

### Variablen — Redraft

`redraft_registrations`, `redraft_assignments`, `redraft_nachruecker`,
`redraft_is_loading`, `redraft_error`, `redraft_warning`,
`redraft_last_loaded`, `redraft_last_generated`, `redraft_league_size` (12),
`redraft_is_saving`, `redraft_save_message`, `redraft_save_type`,
`redraft_last_saved`, `redraft_last_saved_run_id`.

### Computed Vars

Liga: `total_leagues`, `dynasty_count`, `redraft_count`, `bestball_count`,
`idp_count` (`idp` **oder** `idp_only`), `unique_seasons`,
`filtered_leagues` (Typ-Tab + Freitext über Name/ID/Saison),
`target_league_display` (`"__ALL__"` wenn leer).

Redraft: `redraft_total_count`, `redraft_commish_count`,
`redraft_possible_leagues` (`n // 12`), `redraft_remaining_count`,
`redraft_has_assignment`, `redraft_commish_shortfall`, `redraft_min_required`.

### Events — Liga-Verwaltung

| Event | Wirkung |
| --- | --- |
| `init_admin` | `on_load`; nur nach Auth → `load_leagues` |
| `load_leagues` | `leagues.select("*")`, normalisiert Typen, sortiert mit `_admin_sort_key` |
| `add_league` | Validiert numerische ID (≥ 6 Stellen) und Typ; erkennt Duplikate; `get_league` prüft Existenz bei Sleeper; Upsert (mit `avatar`-Retry); danach **vollständige Initialisierung**: Manager, Roster (aktuelle Woche), Matchups W1..aktuell, Drafts; Log + Statusmeldung; abschließend `load_leagues` |
| `sync_league(league_id)` | Metadaten + Manager + Roster + Matchups + Drafts für **eine** Liga |
| `sync_all` | Metadaten + Manager + Roster für **alle** Ligen (ohne Matchups/Drafts) |
| `open_confirm_sync_all`, `close_confirm_sync_all`, `set_confirm_sync_all_open(v)`, `confirm_and_sync_all` | Bestätigungsdialog |
| `set_add_league_input`, `set_add_league_type`, `set_search_query`, `set_filter_type`, `clear_status`, `clear_log` | Setter |

### Events — Bulk-Sync

| Event | Ziel-Tabelle | Besonderheit |
| --- | --- | --- |
| `sync_all_drafts` | `drafts` | `get_league_drafts` je Liga, Upsert `draft_id`, inkl. `json_data` |
| `sync_all_draft_picks` | `draft_picks` | Pro Draft **DELETE dann INSERT** (Batches à 500) — destruktiv, daher rot markiert |
| `sync_all_managers` | `managers` | Upsert `league_id,roster_id` |
| `sync_nfl_players` | `nfl_players` | Kompletter Sleeper-Katalog, 500er-Batches, `updated_at` UTC |
| `sync_matchups_bulk` | `matchup_week_stats` | Liga × Woche gemäß `week_mode` |
| `sync_rosters_bulk` | `rosters` | Liga × Woche, inkl. `ppts` und `settings` in `json_data` |

Setter: `set_week_mode`, `set_week_single`, `set_week_start`, `set_week_end`,
`set_target_league_id`.
Helper: `_resolve_weeks()`, `_resolve_league_ids()`.

### Events — Redraft

| Event | Wirkung |
| --- | --- |
| `load_redraft_registrations` | Lädt `redraft_registration_2026`, verwirft eine vorhandene Preview |
| `generate_redraft_assignment` | Lädt **immer neu** und berechnet die Auslosung (`_build_assignment`) |
| `save_redraft_assignment` | Persistiert die Preview (siehe `redraft_auslosung.md`) |
| `clear_redraft_error`, `clear_redraft_warning`, `clear_redraft_save_message` | Banner schließen |

### Private Helper

Sync: `_sync_league_metadata`, `_sync_managers`, `_sync_rosters`,
`_current_week`, `_sync_matchup_weeks`, `_sync_drafts`,
`_sync_draft_picks_for_draft`, `_sync_matchups_for_week`, `_sync_rosters_for_week`.
Sonstiges: `_lg_types(lg)`, `_admin_sort_key(x)`, `_log(msg, level)`,
`_set_status(msg, kind)`, `_require_auth()`.
Redraft: `_normalize_key`, `_parse_mitspieler`, `_format_created`,
`_fetch_redraft_registrations`, `_build_assignment`.

> `_OBSOLETE_ASSIGNMENT_SOURCE` ist ein **String-Literal** mit dem alten
> Algorithmus (Dokumentationszweck, kein ausführbarer Code). Nicht als Vorlage
> verwenden — die gültige Logik steht in `_build_assignment`.

### Seiteneffekte / Vorsicht

- Alle Sync-Jobs sind **synchron blockierend** und nicht abbrechbar. Große Läufe
  (alle Ligen × alle Wochen, NFL-Katalog) dauern Minuten; die UI warnt darauf hin.
- `sync_all_draft_picks` löscht Picks pro Draft vor dem Insert — bei Abbruch
  mitten im Lauf kann ein Draft temporär ohne Picks sein.
- `sync_all` ignoriert bewusst Matchups/Drafts, um die Laufzeit zu begrenzen.
- `_sync_league_metadata` **bewahrt** den bestehenden `league_type`
  (Fallback `dynasty`) — Sleeper liefert dieses Feld nicht.
