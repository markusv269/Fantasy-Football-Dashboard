# Seiten- und Komponenten-Referenz

Für jede Seite: **Route & `on_load`**, **gelesene States**, **ausgelöste Events**,
**Aufbau**, **Editier-Hinweise**.

Alle Seiten wickeln ihren Inhalt in `layout(...)` aus
`app/components/layout.py` — dadurch erscheinen Sidebar, Header und
Mobile-Drawer automatisch.

Inhalt:
[layout()](#komponente-appcomponentslayoutpy) ·
[league_modal](#komponente-appcomponentsleague_modalpy) ·
[/ Home](#-home) ·
[/leagues](#leagues) ·
[/leagues/[lid]](#leagueslid) ·
[/matchups](#matchups) ·
[/standings](#standings) ·
[/rosters](#rosters) ·
[/drafts](#drafts) ·
[/adp](#adp) ·
[/trending](#trending) ·
[/community](#community) ·
[/archive](#archive) ·
[/waitinglist](#waitinglist) ·
[/redraft-registration](#redraft-registration) ·
[/admin](#admin)

---

## Komponente: `app/components/layout.py`

**Exportiert:** `layout(content, full_width=False)`, `sidebar_std()`,
`mobile_drawer_std()`, `header_std()`, `nav_items`.

**Genutzte States:** `AppState` (Saison/Woche im Header), `ThemeState`
(Mobile-Drawer), `UserState` (Login-Block in der Sidebar).

**Struktur von `layout()`**

```text
rx.flex(  width=100vw, height=100vh, overflow=hidden
├─ sidebar_std()                  # w-260px, hidden md:flex
└─ rx.flex(column, flex=1, min_width=0, height=100vh, overflow=hidden)
   ├─ header_std()                # sticky, h-72px
   ├─ rx.box(content, flex=1, overflow_y=auto)
   │     max_width = rx.cond(full_width, "100%", "1280px"), margin="0 auto"
   └─ mobile_drawer_std()         # fixed bottom sheet, md:hidden
```

**`nav_items`** — eine Liste von `{icon, label, href}`, die **sowohl** die
Desktop-Sidebar **als auch** den Mobile-Drawer versorgt:
Home `/`, Leagues `/leagues`, Matchups `/matchups`, Standings `/standings`,
Rosters `/rosters`, Drafts `/drafts`, ADP Board `/adp`, Trending `/trending`,
Community `/community`, Archiv `/archive`, Warteliste `/waitinglist`,
Redraft 2026 `/redraft-registration`, Admin `/admin`.

**Ausgelöste Events**
`UserState.set_username_input`, `UserState.save_username`,
`UserState.clear_username`, `ThemeState.toggle_mobile_sidebar`,
`ThemeState.close_mobile_sidebar`, `rx.toggle_color_mode`.

**Header-Details** — zeigt `AppState.nfl_state["season"]` und ein Badge:
`season_type == "off"` → „Offseason“, `week == 0` → „Pre-Season“,
sonst „Week N“. Rechts vier externe Social-Links (YouTube, Discord, X, Twitch).

**Editier-Hinweise**

- Neue Navigationspunkte **nur** in `nav_items` ergänzen — beide Menüs erben es.
- Die Listen werden mit `*[... for item in nav_items]` entpackt. Das ist erlaubt,
  weil `nav_items` eine statische Python-Liste ist (kein State-Var). Würde die
  Liste in den State wandern, müsste auf `rx.foreach` umgestellt werden.
- Seiten mit breiten Tabellen/Boards (`/`, `/adp`) rufen `layout(..., full_width=True)`.
- `sidebar_std` ist absichtlich **nicht** einklappbar (`hidden md:flex`).

---

## Komponente: `app/components/league_modal.py`

**Exportiert:** `league_detail_modal()`, `standing_row(team)`,
`matchup_card(matchup)`, plus private Abschnitte
(`_header`, `_champion`, `_standings_section`, `_matchups_section`,
`_roster_section`, `_rank_badge`).

**Genutzter State:** `LeagueDetailState`.

**Status:** wird von **keiner** Seite gerendert. Die Liga-Detailansicht läuft über
die Route `/leagues/[lid]`. Basiert auf `rx.radix.primitives.dialog`
(Overlay + Content, `on_open_change=LeagueDetailState.set_modal_open`).

**Editier-Hinweis:** Entweder reaktivieren (z. B. `league_detail_modal()` in
`leagues_page()` einhängen und Karten auf `LeagueDetailState.open_league_modal`
klicken lassen) oder zusammen mit `app/states/league_detail_state.py` und dem
Import in `app/app.py` entfernen.

---

## `/` Home

`app/pages/home.py` → `home_page()` · `layout(..., full_width=True)`

**on_load:** `AppState.init_app`, `UserState.init_user`,
`CommunityState.load_news`, `CommunityState.load_polls`,
`CommunityState.fetch_youtube_feed`

**Gelesene States:** `AppState` (`current_season`,
`current_dynasty_leagues`, `current_redraft_leagues`), `UserState`
(`is_logged_in`, Profil, `my_leagues_data`, `my_leagues_count`,
`is_loading_my_leagues`), `CommunityState` (`news_items`, `polls`,
`youtube_videos`, `filtered_youtube_videos`)

**Ausgelöste Events:** `UserState.set_username_input`,
`UserState.save_username`, `UserState.clear_username`,
`rx.redirect(f"/leagues/{id}")` (Klick auf Liga-Karte)

**Aufbau**

1. `_hero()` — Begrüßung + Saison-Badge
2. `rx.cond(UserState.is_logged_in, …)` → `_user_profile_card()` +
   `_my_leagues_section()` **oder** `_login_card()`
3. `_section("Dynasty Ligen …")` und `_section("Redraft Ligen …")` —
   Grid in `rx.scroll_area` (`h-[420px]`)
4. Grid: `_news_card()` (3 News) + `_polls_card()` (2 Polls mit je 3 Optionen)
5. `_latest_video_card()` — `CommunityState.filtered_youtube_videos[0]`
6. `_highlights_section()` — 4 `_highlight_tile()` (Warteliste, Community,
   Trending, Archiv)

**Editier-Hinweise**

- `league_card()` nutzt `league_avatar_src()` direkt in `rx.image`.
- Das „Letztes Video“ greift auf Index `0` zu und ist mit
  `rx.cond(CommunityState.youtube_videos.length() > 0, …)` geschützt —
  diese Absicherung nicht entfernen.
- Neue Kacheln über `_highlight_tile(title, description, icon, color, cta, href)`.

---

## `/leagues`

`app/pages/leagues.py` → `leagues_page()`

**on_load:** `AppState.init_app`, `UserState.init_user`, `LeaguesState.load_leagues`

**Gelesene States:** `LeaguesState` (alle Filter, `filtered_leagues`,
`result_count`, `total_count`, `is_loading`, `is_full_loaded`,
`available_*`), `UserState` (`is_logged_in`, `has_username`)

**Ausgelöste Events:** `LeaguesState.load_full_leagues`,
`set_search_query` (debounce 300 ms), `set_selected_season`,
`set_selected_type`, `set_selected_manager`, `set_selected_week`,
`set_selected_scope`, `set_sort_by`, `reset_filters`,
`clear_season/type/manager/week/scope/search`

**Aufbau:** `_hero()` (mit Button „Alle Ligen laden“, solange
`~is_full_loaded`) → `_filter_bar()` (6–7 Felder im responsiven Grid) →
`_active_filters()` (Chips mit ✕) → `_result_bar()` → Karten-Grid
(`_league_card`) oder `_empty_state()`.

**Editier-Hinweise**

- `_week_range()` liefert eine statische Liste `"1".."18"` und wird per
  `*[...]` entpackt — kein State, daher zulässig.
- `_scope_selector()` erscheint nur bei `UserState.is_logged_in`.
- Die Setter laden bei Bedarf **synchron** den Vollbestand nach
  (siehe `LeaguesState._load_full_leagues_sync`) — deshalb reagiert die UI
  im selben Tick.

---

## `/leagues/[lid]`

`app/pages/league_detail.py` → `league_detail_page()`

**on_load:** `LeaguePageState.load_league`

**Gelesener State:** `LeaguePageState`

**Ausgelöstes Event:** `LeaguePageState.change_matchup_week(week)` (Wochen-Pills)

**Aufbau (Reihenfolge `_content()`):** `_header()` (Avatar, Typ-Badge, Saison,
Vorgänger-Link) → `_quick_stats()` (Teams / Manager / letzte Woche) →
`_champion_card()` → `_full_standings_section()` → `_matchups_section()`
(Wochen-Pills + Karten mit Starter/Bank/Reserve je Team) →
`_managers_section()` → `_drafts_section()` → `_trades_section()`.

Oben umschließt eine dreistufige `rx.cond`-Kette den Inhalt:
`loading` → Spinner, `not_found` → Hinweis, `error_message != ""` → Fehler,
sonst `_content()`.

**Editier-Hinweise**

- Der Routenparameter heißt `lid`. Beim Umbenennen auch
  `LeaguePageState._extract_route_id()` anpassen.
- `_matchup_player_section` castet explizit
  `players.to(list[dict[str, str | float]])` — nötig für `rx.foreach`.
- `_trades_section()` zeigt bewusst einen Info-Zustand: es existiert keine
  Trade-/Transaktionstabelle in Supabase (`trades_available = False`).
- `LeaguePageState.top_standings` und `roster_cards` werden aktuell **nicht**
  gerendert; sie stehen für zukünftige Abschnitte bereit.

---

## `/matchups`

`app/pages/matchups.py` → `matchups_page()`
**Exportiert außerdem `league_selector()`**, das von `/standings` und `/rosters`
importiert wird.

**on_load:** `AppState.init_app`, `MatchupsState.init_matchups`

**Gelesene States:** `AppState` (`selected_league_id`), `MatchupsState`
(`current_league_options`, `current_season`, `current_nfl_week`,
`available_weeks`, `selected_week`, `matchups_by_league`, `league_names`,
`paired_matchups`, `is_loading`)

**Ausgelöste Events:** `AppState.select_league(val)` **kombiniert mit**
`MatchupsState.init_matchups()` (Liste von Events im `on_change`),
`MatchupsState.change_week(...)`, `MatchupsState.change_week_str(...)`

**Aufbau:** Titel + Saison/Woche-Badges → `league_selector()` +
`week_selector()` → Inhalt:
- `is_loading` → Spinner
- keine Liga gewählt → Gruppierung über `matchups_by_league.keys()` mit
  `league_matchup_group(lid, ...)`
- Liga gewählt → Grid aus `paired_matchups`
- jeweils Leerzustands-Karten

**Editier-Hinweise**

- `matchup_card` behandelt BYE-Wochen (`matchup["team_b"] != None`).
- `league_selector()` ist bewusst hier definiert, damit `/standings` und
  `/rosters` denselben Selektor benutzen — beim Verschieben alle drei Importe
  anpassen.
- Die Wochen-Pfeile rufen `change_week(selected_week ± 1)`; ungültige Wochen
  werden im State abgefangen.

---

## `/standings`

`app/pages/standings.py` → `standings_page()`

**on_load:** `AppState.init_app`, `MatchupsState.init_standings`

**Gelesene States:** `AppState.selected_league_id`, `MatchupsState.standings_data`

**Ausgelöstes Event:** `MatchupsState.view_roster(roster_id)` (Zeilenklick →
Redirect auf `/rosters`)

**Aufbau:** Titel → `league_selector()` → `rx.cond(selected_league_id == "", Leerzustand, Tabelle)`.
Tabelle: Rank-Badge (Gold/Silber/Bronze via `rx.match`), Team/Manager, W, L, T,
Pct, PF, PA.

**Editier-Hinweis:** Die Daten kommen **live von Sleeper**
(`MatchupsState.fetch_standings`), nicht aus `rosters`. Historische Standings
müssten über `LeaguePageState.full_standings` gelesen werden.

---

## `/rosters`

`app/pages/rosters.py` → `rosters_page()`

**on_load:** `AppState.init_app`, `MatchupsState.init_standings`
*(bewusst `init_standings`, weil die Roster-Kacheln `standings_data` nutzen)*

**Gelesene States:** `AppState.selected_league_id`, `MatchupsState`
(`standings_data`, `selected_roster`)

**Ausgelöste Events:** `MatchupsState.view_roster(id)`,
`MatchupsState.clear_selected_roster`

**Aufbau:** `rx.cond(selected_roster.contains("roster_id"), roster_detail(), Kachelübersicht)`.
`roster_detail()` zeigt Record/Waiver sowie zwei Spalten
(Starters, Reserve/IR) über `_player_row`.

**Editier-Hinweis:** `roster_detail()` liest `roster["starters"]` /
`roster["reserve"]` als `list[dict[str, str]]` — diese Struktur erzeugt
`MatchupsState.view_roster` über `enrich_roster_players`. Bench-Spieler werden
hier (anders als in `/leagues/[lid]`) nicht dargestellt.

---

## `/drafts`

`app/pages/drafts.py` → `drafts_page()`

**on_load:** `DraftState.init_drafts`

**Gelesener State:** `DraftState` (alle Listen, Counter, `season_breakdown`,
`draft_filter`, `show_all_completed`, `is_loading`)

**Ausgelöste Events:** `DraftState.set_draft_filter(label)`,
`DraftState.toggle_completed`

**Aufbau:** `_hero()` → `_stats_bar()` (4 Kacheln) → `_season_breakdown()`
(Pills) → bei `is_loading` Spinner, sonst
`_active_section()` (große Karten mit Fortschrittsbalken, „Letzter Pick“,
„Als Nächstes“, „Details“) → `_filter_bar()` (8 Tabs) →
`_scheduled_section()` (Karten-Grid) → `_completed_section()` (Tabelle,
Standard 12 Zeilen) → `_other_section()`.

**Editier-Hinweise**

- Fortschrittsbalken nutzt `style={"width": f"{draft['progress_pct']}%"}` —
  das ist ein erlaubter f-String für ein **Style-Attribut**, nicht für `class_name`.
- Alle Live-Felder (`last_*`, `next_*`, `progress_*`) sind für nicht-aktive
  Drafts mit `0`/`""` vorbelegt; `rx.cond`-Guards vor dem Rendern beibehalten.
- Neue Filter: `_matches_filter` in `DraftState` **und** `_filter_tab(...)` in
  `_filter_bar()` ergänzen.

---

## `/adp`

`app/pages/adp_draftboard.py` → `adp_draftboard_page()` · `full_width=True`

**on_load:** `AdpState.init_adp`

**Gelesener State:** `AdpState` (Filter, `filtered_board_cells`,
`filtered_round_range`, `slot_range`, `filtered_players`, Statistiken,
`board_layout`, `is_loading`)

**Ausgelöste Events:** `set_selected_season`, `set_selected_format`,
`set_selected_draft_type`, `set_min_pick_count` (throttle 100 ms),
`reset_min_pick_count`, `set_table_search` (debounce 300 ms),
`set_table_position`, `clear_table_filters`

**Aufbau:** `_hero()` → `_filters()` (Saison-Select, Format-Buttons,
Draft-Typ-Buttons, Mindest-Pick-Slider) → `_stats()` (4 Kacheln) →
`_board()` (horizontal scrollbares 12-Slot-Board) → `_adp_table()`
(Suche/Position + Ranking-Tabelle).

**Board-Rendering:** `_board_row(rnd)` rendert 12 feste `_board_slot(rnd, slot)`.
Jeder Slot iteriert über **alle** `filtered_board_cells` und rendert die Zelle
nur bei `(cell["round"] == rnd) & (cell["display_column"] == slot)`.
Das ist bewusst so gelöst, weil im Frontend keine Python-Filterung möglich ist.

**Editier-Hinweise**

- Der Slider ist `rx.el.input(type="range")` mit
  `key=AdpState.min_pick_reset_counter.to_string()` — der wechselnde `key`
  erzwingt beim Reset ein Remount. `key` und `default_value` gemeinsam belassen.
- Bei sehr vielen Spielern wächst der Board-Aufwand quadratisch
  (Runden × Slots × Zellen). Für > ~1000 Spieler sollte serverseitig eine
  `(round, slot)`-Map vorberechnet werden.
- `bestball` ist im State vorbereitet, in der UI aber nicht als Button vorhanden.

---

## `/trending`

`app/pages/trending.py` → `trending_page()`

**on_load:** `CommunityState.init_trending`

**Gelesener State:** `CommunityState` (`trending_adds`, `trending_drops`,
`trending_timeframe`)

**Ausgelöstes Event:** `CommunityState.change_trending_timeframe("24h"|"48h")`

**Aufbau:** Kopf mit Zeitraum-Buttons → zwei Sektionen („Hot Adds“,
„Trending Drops“) mit `trending_player_row(player, index, is_add)`.

**Editier-Hinweis:** Die Daten kommen direkt von Sleeper (kein DB-Write).
Spielernamen werden über `player_cache` aufgelöst — der erste Aufruf kann
dauern, weil der Katalog geladen wird.

---

## `/community`

`app/pages/community.py` → `community_page()`

**on_load:** `CommunityState.init_community`

**Gelesener State:** `CommunityState` (`news_items`, `polls`, `voted_polls`,
`filtered_youtube_videos`, `youtube_filter`)

**Ausgelöste Events:** `CommunityState.vote_poll(poll_id, index)`,
`CommunityState.set_youtube_filter(label)`

**Aufbau:** Zwei-Spalten-Grid (`template_columns lg="2fr 1fr"`):
links News (`news_card`, Markdown) + Polls (`poll_card`),
rechts Warteliste-CTA + YouTube (`_youtube_filter_btn`, `youtube_card`,
`filtered_youtube_videos[:6]`).

`poll_card` entscheidet über `has_voted | is_closed`, ob
`poll_option_result` (Balken) oder `poll_option_active` (Button) gerendert wird.
Der Balken nutzt `style={"width": f"{pct}%"}`.

**Editier-Hinweis:** `poll["options"]` muss explizit gecastet werden
(`.to(list[dict[str, str | int]])`), damit `rx.foreach` typisiert ist.

---

## `/archive`

`app/pages/archive.py` → `archive_page()`

**on_load:** `AppState.init_app`, `UserState.init_user`, `ArchiveState.load_archive`

**Gelesener State:** `ArchiveState`

**Ausgelöste Events:** `set_search_query` (debounce 300 ms),
`set_selected_season`, `set_selected_type`, `set_selected_manager`,
`reset_filters`, `clear_season/type/manager/search`

**Aufbau:** `_hero()` (mit Link zurück auf `/`) → bei `is_loading` Spinner →
`rx.cond(total_archive_count > 0, Filter+Chips+Result+Grid, _empty_archive())`.
Karten verlinken auf `/leagues/{league_id}`.

**Editier-Hinweis:** Was „Archiv“ ist, ergibt sich ausschließlich aus
`season != current_season` (Max-Saison in `leagues`). Es gibt kein
Archiv-Flag in der Datenbank.

---

## `/waitinglist`

`app/pages/waitinglist.py` → `waitinglist_page()`

**on_load:** `WaitlistState.init_waitlist`

**Gelesener State:** `WaitlistState`

**Ausgelöste Events:** `set_sleeper_name_input`, `set_discord_input`,
`validate_sleeper_name`, `toggle_dynasty`, `toggle_dynasty_idp`,
`toggle_dynasty_bb`, `submit_waitlist`, `remove_from_waitlist`, `reset_form`

**Aufbau:** Kopf → 4 Statistik-Karten → Grid: links `registration_form()`
(`_success_state()` **oder** `_form_state()`), rechts drei
`waitlist_section(...)` (Dynasty / IDP / Bestball).

**Formular-Fluss:** Name eingeben → „Überprüfen“ → bei Erfolg erscheinen
Formatauswahl, Discord-Feld und Submit. Bestehende Anmeldung wird als
Info-Banner angezeigt und vorbelegt; im „Gefahrenbereich“ kann komplett
ausgetragen werden.

**Editier-Hinweise**

- `submit_waitlist` ist deaktiviert, solange kein Format gewählt oder Discord
  leer ist (`disabled=...` mit `|`/`~`-Operatoren — Klammern beachten).
- Die Reihenfolge der Listen richtet sich nach den **formatspezifischen**
  Zeitstempeln. Wer das Datum ändert, muss die Sortierlogik in den
  Computed Vars mitziehen.

---

## `/redraft-registration`

`app/pages/redraft_registration.py` → `redraft_registration_page()`

**on_load:** `RedraftRegistrationState.init_page`

**Gelesener State:** `RedraftRegistrationState`

**Ausgelöste Events:** `set_sleeper_input`, `validate_sleeper`,
`set_discord_input`, `set_email_input`, `set_commish_yes`, `set_commish_no`,
`set_teammate1..3_input`, `set_edit_code_input`, `submit_registration`,
`reset_form`, `load_entries`, `clear_status`

**Aufbau:** `_hero()` (Datenschutz-/Ablauf-Hinweise) → `_status_banner()` →
`_table_warning()` (nur wenn `using_fallback`) →
`rx.cond(submit_success, _success_card(), _form())` → `_entries_card()`
(Statistik-Kacheln + Tabelle).

`_form()`: Sleeper-Name + Prüfen, `_validation_state()` (grüner Treffer mit
Avatar oder Fehlertext), Discord (Pflicht), E-Mail (optional, nicht öffentlich),
`_commish_selector()` (zwei Radio-Karten), drei Mitspieler-Felder, und —
**nur wenn `existing_entry.contains("user_id")`** — das Feld „Änderungscode“.

**Editier-Hinweise**

- Der Änderungscode ist **Pflicht** für jede Änderung. Diese Prüfung liegt im
  State (`submit_registration`) und darf nicht in die UI verlagert werden.
- E-Mail und `key` werden in der öffentlichen Tabelle **niemals** angezeigt —
  `load_entries` übernimmt sie gar nicht in `entries`.
- Gegenseitige Wünsche werden mit `✓` markiert (`mates_display`),
  `mutual_count` zeigt die Anzahl.

---

## `/admin`

`app/pages/admin.py` → `admin_page()`

**on_load:** `AdminState.init_admin` (lädt nur nach erfolgreicher Auth)

**Gelesene States:** `AdminAuthState`, `AdminState`

**Einstieg:** `admin_page()` = `rx.cond(AdminAuthState.is_authenticated,
_admin_dashboard(), _login_form())`.

### `_login_form()`

`rx.el.form(on_submit=AdminAuthState.submit_login, reset_on_submit=False)`
mit Passwortfeld, Fehlermeldung, Lockout-Hinweis
(`is_locked`, `lockout_remaining`) und Spinner (`is_checking`).

### `_admin_dashboard()` — Reihenfolge

1. `_hero()` — Titel + Logout (`AdminAuthState.logout`)
2. `_status_banner()` — `status_message`/`status_type`, schließbar
3. Vier `_stat_card()` — Ligen gesamt, Dynasty, Redraft, Bestball
4. `_add_league_card()` — ID-Eingabe + Typ-Select + `AdminState.add_league`
5. `_data_updates_card()` — Ziel-Liga-Select (`__ALL__`), Wochenmodus
   (`single|range|all`), Zahlenfelder (debounce 200 ms) und sechs
   `_sync_button(...)`:
   Drafts scannen, Draftpicks importieren *(destruktiv, `warn=True`)*,
   Manager aktualisieren, NFL-Spieler synchronisieren *(warn)*,
   Matchups synchronisieren, Roster synchronisieren
6. `_leagues_table()` — Suche (debounce 300 ms), Typ-Tabs, Tabelle mit
   Live-Punkt (grün/amber), Detail-Link, Einzel-Sync, „Alle synchronisieren“
   (öffnet `_confirm_sync_all_dialog()`)
7. `_redraft_card()` — Redraft-Preview & Persistenz
   (siehe [`redraft_auslosung.md`](redraft_auslosung.md))
8. `_log_card()` — `AdminState.log_entries` (max. 50, scrollbar, löschbar)
9. `_confirm_sync_all_dialog()` — Radix-Dialog mit Warnhinweis

**Editier-Hinweise**

- **Jeder** neue schreibende Handler muss mit
  `if not await self._require_auth(): return` beginnen.
- Sync-Buttons deaktivieren sich über `disabled=AdminState.is_syncing`;
  `sync_operation` liefert den Anzeigenamen des laufenden Jobs.
- `_type_badges` erwartet `lg["league_types"].to(list[str])` — Ligen ohne
  strukturierte Typen erhalten über `normalize_league_types` einen Fallback.
- Der Bestätigungsdialog schützt nur „Alle synchronisieren“.
  `sync_all_draft_picks` ist ebenfalls destruktiv (DELETE + INSERT) und wäre
  ein guter Kandidat für einen zweiten Dialog.
