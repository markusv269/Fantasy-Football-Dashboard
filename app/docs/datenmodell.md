# Datenmodell: Supabase-Tabellen & Sleeper-Endpunkte

Diese Übersicht ist aus dem tatsächlichen Code abgeleitet (alle `client.table(...)`-
Aufrufe). Es gibt **keine** ORM-Modelle (`rx.Model` wird bewusst nicht verwendet) —
alle Zugriffe laufen über den Supabase-Python-Client mit dynamischen Dicts.

---

## 1. Tabellenübersicht

| Tabelle | Gelesen von | Geschrieben von | Konflikt-Key beim Upsert |
| --- | --- | --- | --- |
| `leagues` | `AppState`, `LeaguesState`, `ArchiveState`, `LeaguePageState`, `AdminState`, `AdpState`, `DraftState`, `UserState`, `MatchupsState`, `LeagueDetailState` | `AdminState`, `weekly_sync`, `sync_league_avatars` (nur UPDATE `avatar`) | `league_id` |
| `managers` | `LeaguesState`, `ArchiveState`, `LeaguePageState`, `MatchupsState`, `DraftState`, `UserState`, `LeagueDetailState` | `AdminState`, `weekly_sync` | `league_id,roster_id` |
| `rosters` | `LeaguesState` (Wochen), `LeaguePageState`, `ArchiveState` (indirekt), `LeagueDetailState` | `AdminState`, `weekly_sync` | `league_id,roster_id,week` |
| `matchup_week_stats` | `MatchupsState`, `LeaguePageState`, `LeaguesState` (Wochen), `LeagueDetailState` | `AdminState`, `weekly_sync` | `league_id,week,roster_id` |
| `drafts` | `DraftState`, `LeaguePageState`, `AdpState` | `AdminState`, `weekly_sync` | `draft_id` |
| `draft_picks` | `AdpState` | `AdminState` (DELETE + INSERT pro Draft) | — (kein Upsert) |
| `nfl_players` | — | `AdminState.sync_nfl_players` | `player_id` |
| `league_champion` | `LeaguePageState`, `LeagueDetailState` | — (extern gepflegt) | — |
| `polls` | `CommunityState.load_polls` | `CommunityState.vote_poll` (UPDATE `stats`) | — |
| `news` | `CommunityState.load_news` | — | — |
| `dynasty_waitinglist` | `WaitlistState` | `WaitlistState` (upsert/delete), `CommunityState.submit_registration` (Legacy-Insert) | `user_id` |
| `redraft_registration_2026` | `RedraftRegistrationState`, `AdminState` | `RedraftRegistrationState` (insert/update) | `user_id` (manuell geprüft, kein DB-Upsert) |
| `user_registration` | `RedraftRegistrationState` (nur Fallback-Lesen) | — | — |
| `redraft_assignment_runs_2026` | `AdminState.save_redraft_assignment` | dito (UPDATE `is_active=false` + INSERT) | — |
| `redraft_assignment_players_2026` | — | `AdminState.save_redraft_assignment` (INSERT, Batches à 500) | — |
| `redraft_assignment_waitlist_2026` | — | `AdminState.save_redraft_assignment` (INSERT, Batches à 500) | — |

---

## 2. Spalten je Tabelle (im Code verwendet)

### `leagues`

| Spalte | Typ/Format | Bemerkung |
| --- | --- | --- |
| `league_id` | text (PK) | Sleeper-League-ID als String |
| `league_name` | text NOT NULL | daher darf `sync_league_avatars` nie INSERT machen |
| `league_season` | int oder text | Code castet defensiv (`str(...).isdigit()`) |
| `league_type` | text | Legacy-Einzelwert (`dynasty|redraft|bestball`) |
| `league_types` | text **oder** text[] | Neu; kann fehlen → Retry-Fallback (`league_types.py`) |
| `league_sort` | int, nullable | Manuelle Sortierung; `NULL`/`<0` sortiert **hinten** |
| `avatar` | text, nullable | Sleeper-Avatar-ID oder volle URL |
| `previous_league_id` | text, nullable | Vorgängerliga (Dynasty-Kette) |
| `roster_positions` | jsonb/array | z. B. `["QB","RB",...]` |

**Kanonische Sortierung** (`league_sort_key` in `app_state.py`,
`_lg_sort_key` in `leagues_state.py`, `_admin_sort_key` in `admin_state.py`):
`season DESC`, `league_sort ASC` (NULLs zuletzt), `name ASC`.

### `managers`

`league_id`, `roster_id` (int), `user_id` (Sleeper-User-ID), `display_name`,
`team_name` (aus `user.metadata.team_name`, Fallback `display_name`).

### `rosters`

`league_id`, `roster_id`, `week`, `wins`, `losses`, `ties`, `fpts_for`,
`fpts_against`, optional `ppts`, `json_data` (jsonb).

`json_data`-Struktur (vom Sync geschrieben, vom Frontend gelesen):

```json
{
  "players":  ["1234", ...],
  "starters": ["1234", ...],
  "reserve":  ["5678", ...],
  "taxi":     ["9012", ...],
  "settings": { ... }            // nur im Bulk-Sync (sync_rosters_bulk)
}
```

Zusätzlich liest `LeaguePageState._build_lineup` optional
`players_points` (dict), `starters_points` (Liste, Reihenfolge = `starters`)
und `custom_points` (dict) aus `json_data`, um Punkte pro Spieler zu bestimmen.
Priorität: `players_points` → `starters_points` → `custom_points` → `0.0`.

### `matchup_week_stats`

`league_id`, `week`, `matchup_id`, `roster_id`, `points`, optional `json_data`
(vollständige Sleeper-Matchup-Row; nur `sync_matchups_bulk` schreibt sie).

### `drafts`

`draft_id` (PK), `league_id`, `season` (text), `draft_type`, `status`,
`start_time` (ISO-String), optional `json_data`.

`draft_type` wird beim Schreiben gemappt: `snake→"0"`, `linear→"1"`,
`auction→"2"`. Beim Lesen mappt `DraftState._dtype_label` bzw.
`LeaguePageState` zurück auf Labels („Snake“, „Linear“, „Auction“).

`status`-Werte, die der Code kennt:
`drafting`, `paused` (aktiv), `pre_draft` (geplant), `complete`/`completed`
(abgeschlossen), alles andere → „Weitere Drafts“.

### `draft_picks`

`draft_id`, `round`, `pick_no`, `roster_id` (nullable), `player_id`,
`metadata` (jsonb: `first_name`, `last_name`, `position`, `team`), `json_data`.

`AdpState` liest nur `draft_id, pick_no, round, player_id, metadata`
und paginiert mit `range(offset, offset+999)`.

### `nfl_players`

`player_id` (PK), `name`, `team`, `position`, `json_data`, `updated_at` (ISO-UTC).
Wird nur vom Admin-Sync geschrieben; die App liest Spielernamen aktuell über
`app/player_cache.py` direkt von Sleeper.

### `league_champion`

`league_id`, `team_name`, `display_name`. Wird von der App nur gelesen
(kein Schreibpfad im Code).

### `polls`

`id` (int), `poll` (Frage), `answers` (text[]), `stats` (int[]), `created_at`.
`options[i].votes = stats[i]`, `total_votes = sum(stats)`.
`vote_poll` erhöht `stats[index]` per UPDATE.

### `news`

`id`, `header`, `text` (Markdown), `created_at`. Anzeige-Datum:
`dt.strftime("%d. %B %Y")`.

### `dynasty_waitinglist`

`user_id` (Konflikt-Key), `sleeper_name`, `discord`, `dynasty` (bool),
`dynasty_idp` (bool), `dynasty_bb` (bool), `created_at`,
`registration_dyn` / `registration_idp` / `registration_bb`
(ISO-UTC pro Format; bleibt bei bestehender Anmeldung erhalten,
wird `NULL` wenn das Format abgewählt wird).

### `redraft_registration_2026`

`index` (Slug, NOT NULL), `user_id` (Sleeper), `sleeper`, `discord`, `email`,
`mitspieler` (text[]), `mitspieler_user_ids` (text[]), `key` (Änderungscode),
`created_at`, optional `commish` (bool), optional `Doppelanmeldung` (bool, **großes D**).

`RedraftRegistrationState` schreibt die optionalen Spalten „best effort“ und
entfernt sie aus dem Payload, wenn Postgrest `PGRST204 / Could not find the 'X' column`
meldet (siehe `_write()`).

### Redraft-Auslosungstabellen

Details und Semantik: [`redraft_auslosung.md`](redraft_auslosung.md).

`redraft_assignment_runs_2026`: `id` (uuid, generiert), `season`, `name`,
`generated_by`, `is_active`, `total_registrations`, `total_leagues`,
`total_assigned`, `total_nachruecker`, `total_commish`, `notes`.

`redraft_assignment_players_2026`: `assignment_run_id`, `season`,
`league_number`, `league_name`, `roster_position`, `draft_position`,
`sleeper_username`, `sleeper_user_id`, `discord`, `commish`,
`source_registration_id`, `source_registration_created_at`,
`league_id` (Platzhalter `""`), `league_invite_link` (Platzhalter `""`).

`redraft_assignment_waitlist_2026`: `assignment_run_id`, `waitlist_position`,
`sleeper_username`, `sleeper_user_id`, `discord`,
`source_registration_id`, `source_registration_created_at`.

---

## 3. Paginierung & Batching — die drei Muster

Supabase liefert standardmäßig max. 1000 Zeilen pro Request. Der Code nutzt
konsequent drei Muster:

1. **ID-Batching bei `in_()`** — Listen von `league_id`s werden in Chunks von
   100 (teils 200/50) aufgeteilt, damit die URL nicht zu lang wird.
2. **Range-Paginierung** — `.range(offset, offset + PAGE_SIZE - 1)` in einer
   `while True`-Schleife, Abbruch bei `len(rows) < PAGE_SIZE`
   (`LeaguesState._paginated_in_query`, `AdpState._fetch_picks`,
   `LeaguesState._collect_week_availability`).
3. **Insert-Batches** — `range(0, len(rows), 500)` beim Schreiben
   (`nfl_players`, `draft_picks`, Redraft-Assignments).

**Wichtig:** Beim Hinzufügen neuer Massen-Reads immer eines dieser Muster
verwenden, sonst fehlen ab Zeile 1001 stillschweigend Daten.

---

## 4. Datenflüsse (High Level)

```text
Sleeper API ──(Admin-UI / weekly_sync)──► Supabase ──(States)──► Reflex-Frontend
                                             ▲
YouTube RSS ─────────────────────────────────┘  (nur CommunityState, kein DB-Write)
Sleeper Trending ────────► CommunityState/AppState (live, kein DB-Write)
Sleeper /user/{name} ────► UserState / WaitlistState / RedraftRegistrationState
```

**Live-Ausnahmen** (Sleeper wird zur Anzeigezeit gelesen, nicht aus der DB):

- `DraftState._enrich_live_draft` → `get_draft`, `get_draft_picks`, `get_league`
  für **aktive** Drafts (Fortschritt, letzter Pick, „on the clock“).
- `MatchupsState.fetch_standings` / `fetch_league_detail` / `view_roster` →
  `get_rosters`, `get_league_users` (deshalb sind `/standings` und `/rosters`
  live und nicht historisierbar).
- `AppState.fetch_all_leagues_data` ruft `get_league` **nur** wenn ≤ 10 Ligen
  geladen werden (Schutz vor Rate-Limits).
- `AppState.fetch_trending` und `CommunityState.fetch_trending`.
