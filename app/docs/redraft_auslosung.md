# Redraft 2026: Anmeldung, Auslosung und Persistenz

Dieses Dokument beschreibt den kompletten Redraft-2026-Prozess: von der
öffentlichen Anmeldung über die Berechnung der Ligaeinteilung bis zur
Speicherung in Supabase.

Beteiligte Dateien:

| Datei | Rolle |
| --- | --- |
| `app/pages/redraft_registration.py` | Öffentliches Anmeldeformular + Übersicht (`/redraft-registration`) |
| `app/states/redraft_registration_state.py` | Anmelde-Logik, Validierung, Änderungscode |
| `app/pages/admin.py` → `_redraft_card()` | Admin-UI für Preview & Speichern |
| `app/states/admin_state.py` | Laden, Auslosung (`_build_assignment`), Persistenz (`save_redraft_assignment`) |
| `assets/SLR2025.ipynb` | Historisches Notebook, fachliche Vorlage des Algorithmus |
| `app/pages/redraft_auslosung.py` | **Öffentliche Seite** `/redraft-auslosung` (aktive Auslosung) |
| `app/states/redraft_auslosung_state.py` | `RedraftAuslosungState`: liest den aktiven Run + Beitrittsstatus |

## 0. Öffentliche Seite `/redraft-auslosung`

Route: `app.add_page(redraft_auslosung_page, route="/redraft-auslosung",
on_load=RedraftAuslosungState.init_page)`. Navigationseintrag „Auslosung 2026“
(`shuffle`) in `nav_items`.

`RedraftAuslosungState` liest **ausschließlich** aus Supabase:

- `redraft_assignment_runs_2026` mit `is_active = true` (neuester Run)
- `redraft_assignment_players_2026` für `assignment_run_id` (paginiert)
- `redraft_assignment_waitlist_2026` für `assignment_run_id`
- `leagues` (Mapping über `league_id`, sonst über `league_name`)
- `managers` (Beitrittsstatus je `sleeper_user_id`, liefert `roster_id`/`team_name`)
- `rosters` (Anzahl vorhandener Roster der verknüpften Liga)

Spieler werden nach `league_number`/`league_name` gruppiert; pro Liga eine Karte
mit Standard-`rx.table`. Beigetretene Manager erhalten ein Häkchen-Badge, offene
Plätze ein „Offen“-Badge. `league_invite_link` rendert einen externen
Beitritts-Button, sonst (falls verknüpft) einen Link auf `/leagues/{id}`.
Zustände: Laden, Fehler, kein aktiver Run, keine Spieler, kein Liga-Mapping.

---

## 1. Datenquelle: `redraft_registration_2026`

Alle Anmeldungen liegen in der Supabase-Tabelle **`redraft_registration_2026`**.

| Spalte | Bedeutung |
| --- | --- |
| `index` | Slug-Schlüssel (kleingeschrieben, `[a-z0-9_.-]`), primärer Join-Key der Auslosung |
| `user_id` | Sleeper-User-ID (kanonische Identität) |
| `sleeper` | Sleeper-Anzeigename |
| `discord` | Discord-Name (Pflichtfeld im Formular) |
| `email` | optional, **nie öffentlich sichtbar** |
| `mitspieler` | `text[]` mit Anzeigenamen der Wunsch-Mitspieler (max. 3) |
| `mitspieler_user_ids` | `text[]` mit den zugehörigen Sleeper-IDs |
| `commish` | optional `bool` — „Interesse als Commissioner“ |
| `Doppelanmeldung` | optional `bool` (Schreibweise mit großem **D** wie im Schema) |
| `key` | Änderungscode (10 Zeichen A–Z0–9) |
| `created_at` | ISO-UTC, nur beim INSERT gesetzt |

**Optionale Spalten:** `commish` und `Doppelanmeldung` werden „best effort“
geschrieben. Meldet Postgrest `PGRST204` / „Could not find the 'X' column“,
entfernt `_write()` genau diese Spalte aus dem Payload und wiederholt den
Schreibvorgang. Pflichtspalten (`index`, `user_id`, `sleeper`, `discord`,
`email`, `mitspieler`, `mitspieler_user_ids`, `key`) werden **nie** entfernt.

**Lese-Fallback:** Existiert `redraft_registration_2026` (noch) nicht, liest
`RedraftRegistrationState.load_entries` ersatzweise die alte Tabelle
`user_registration` und setzt `table_missing = True` / `using_fallback = True`.
Die Seite zeigt dann einen Amber-Warnhinweis; **Schreiben** ist in diesem
Zustand nicht möglich.

---

## 2. Anmeldung (öffentlich)

1. **Sleeper-Name prüfen** (`validate_sleeper`) → `GET /v1/user/{name}`.
   Erfolg liefert `user_id`, `display_name`, `avatar`. Danach Lookup in
   `redraft_registration_2026` nach `user_id`; ein Treffer füllt
   `existing_entry` (inkl. `key`) und übernimmt `commish`.
2. **Mitspieler-Wünsche** (`_normalize_mates` → `_resolve_teammates`):
   - Lokale Vorprüfung **vor** jedem Netzwerkaufruf: Selbstwunsch
     (Vergleich gegen eigenen Anzeigenamen **und** Eingabe) und Duplikate
     werden mit klarer Meldung abgelehnt.
   - Danach je Name `GET /v1/user/{name}`. Unbekannter Name ⇒ Abbruch.
   - Zusätzliche Prüfung gegen die eigene `user_id` und gegen bereits
     gesehene IDs.
3. **Änderungscode-Pflicht:** Existiert bereits eine Anmeldung für diese
   `user_id`, wird **ohne** korrekten `key` **nichts** geschrieben. Mit
   korrektem Code erfolgt ein UPDATE, der `key` bleibt unverändert.
   `created_at` wird bei Updates nie überschrieben.
4. **Erfolg:** Bei Neuanmeldung wird ein neuer 10-stelliger Code erzeugt und
   in `_success_card()` groß angezeigt („bitte aufbewahren“).

### Gegenseitige Wünsche in der Übersicht

`load_entries` baut einen Reverse-Index (`mentioned_by`). Ist ein Wunsch
beidseitig, wird der Name mit `✓` markiert und `mutual_count` erhöht.
`entries` enthält bewusst **nur**: `sleeper`, `discord`, `mates_display`,
`mutual_count`, `created_display`, `commish` — **keine** E-Mail, **kein** `key`.

---

## 3. Auslosung im Admin (`AdminState._build_assignment`)

Aufruf über den Button „Ligaeinteilung generieren“
(`generate_redraft_assignment`). Dieser lädt die Anmeldungen **immer neu**
aus `redraft_registration_2026` und verwirft eine bestehende Preview.

### Algorithmus (Reihenfolge ist verbindlich)

1. **Sortierung nach `created_at` aufsteigend.** Die ersten
   `N * 12` Anmeldungen sind aktive Plätze
   (`N = len(rows) // redraft_league_size`), alle weiteren sind **Nachrücker**.
   Sind weniger als 12 Anmeldungen vorhanden, gibt es keine Liga und die
   Methode liefert eine erklärende Fehlermeldung.
2. **Wunschgruppen bilden:** Nur **beidseitige** Wünsche zählen
   (`A→B` und `B→A`). Überlappende Paare werden zu Gruppen verschmolzen, sodass
   Ketten (`A→B`, `B→C`) zu `{A,B,C}` werden.
3. **Genau ein Commissioner pro Liga.** Aus dem Pool der Commish-Kandidaten
   wird per `random.SystemRandom()` **je Liga einer** ausgewählt.
4. **Commish-Fallback:** Gibt es weniger `commish=True`-Anmeldungen als Ligen,
   werden **zufällig** weitere aktive Teilnehmer (Nicht-Commish) zu Commish
   befördert, bis jede Liga genau einen Commish hat. Diese Fallback-Commishes
   sind in jeder anderen Hinsicht normale Teilnehmer.
5. **Commish setzen:** Der ausgewählte Commish wird zusammen mit seiner
   kompletten Wunschgruppe platziert, sofern die Gruppe in eine Liga passt;
   sonst alleine.
6. **Restplätze mit Gruppen füllen:** Übrige Wunschgruppen werden in die erste
   Liga mit ausreichend freien Plätzen gelegt. Die Gruppenreihenfolge wird
   gemischt (`rnd.sample`), damit Gruppenmitglieder nicht deterministisch
   benachbarte Draft-Slots erhalten. Passt eine Gruppe nirgends, wird sie
   zurückgestellt (`deferred`) und blockiert den Lauf nicht.
7. **Einzelplatz-Fallback:** Restliche Teilnehmer werden einzeln aufgefüllt,
   bis alle Ligen voll sind.
8. **Draftreihenfolge mischen:** Jede Liga wird abschließend geshuffelt, damit
   der Commish nicht automatisch Slot 1 belegt.

**Ausgabe:** `redraft_assignments` — Liste von
`{name: "SLR 2026 - Liga n", size, commish_count, players: [...]}`.
Ein Spieler: `{slot, sleeper, discord, commish, index}`.

**Wichtig:** In der Ausgabe hat **nur** der ausgewählte Liga-Commish
`commish=True`. Nicht ausgewählte Kandidaten erscheinen mit `commish=False`.
Nachrücker (`redraft_nachruecker`) haben immer `commish=False`, weil sie keiner
Liga zugeordnet sind.

**Soft-Warnung:** Liegt die Zahl echter `commish=True`-Anmeldungen unter der
Anzahl der Ligen, setzt `generate_redraft_assignment` zusätzlich
`redraft_warning` (Amber-Banner). Die Preview wird trotzdem erzeugt.

**Reproduzierbarkeit:** Es wird bewusst `random.SystemRandom()` **ohne Seed**
verwendet — jeder Klick ergibt eine neue Auslosung. Wer deterministische Läufe
braucht, müsste einen Seed einführen und ihn im Run-Datensatz mitspeichern.

---

## 4. Persistenz: `AdminState.save_redraft_assignment`

Button „Auslosung speichern (überschreibt aktive)“. Vorbedingungen:
Admin-Auth (`_require_auth`) und eine vorhandene Preview
(`redraft_assignments` nicht leer).

### Überschreib-Semantik

1. **Alle bisherigen Runs deaktivieren**
   `UPDATE redraft_assignment_runs_2026 SET is_active = false`
   (Filter: `id != '00000000-0000-0000-0000-000000000000'`, d. h. praktisch alle
   Zeilen). Historische Runs bleiben inhaltlich erhalten — sie sind nur nicht
   mehr aktiv. Es wird **nichts gelöscht**.
2. **Neuen aktiven Run einfügen** in `redraft_assignment_runs_2026`:

   | Spalte | Wert |
   | --- | --- |
   | `season` | `2026` |
   | `name` | `"Redraft 2026 Auslosung {dd.mm.yyyy HH:MM:SS}"` |
   | `generated_by` | `"admin_ui"` |
   | `is_active` | `true` |
   | `total_registrations` | `len(redraft_registrations)` |
   | `total_leagues` | Anzahl Ligen |
   | `total_assigned` | Summe aller Spieler |
   | `total_nachruecker` | Anzahl Nachrücker |
   | `total_commish` | Anzahl Spieler mit `commish=True` |
   | `notes` | Freitext inkl. Zeitstempel und Überschreib-Hinweis |

   Die von Supabase generierte `id` (uuid) wird als `run_id` weiterverwendet.
   Liefert der Insert keine Zeile/keine `id`, bricht der Vorgang mit Fehler ab.
3. **Spieler einfügen** in `redraft_assignment_players_2026`
   (Batches à 500):

   | Spalte | Wert |
   | --- | --- |
   | `assignment_run_id` | `run_id` |
   | `season` | `2026` |
   | `league_number` | 1-basierter Index der Liga |
   | `league_name` | `"SLR 2026 - Liga n"` |
   | `roster_position` | `slot` aus der Preview |
   | `draft_position` | identisch mit `slot` |
   | `sleeper_username` | Anzeigename |
   | `sleeper_user_id` | aus der Quell-Anmeldung |
   | `discord` | Preview-Wert, Fallback Quell-Anmeldung |
   | `commish` | `true` nur für den Liga-Commish |
   | `source_registration_id` | `user_id`, Fallback `index` |
   | `source_registration_created_at` | `created_at` der Anmeldung (oder `NULL`) |
   | **`league_id`** | **`""` — Platzhalter** |
   | **`league_invite_link`** | **`""` — Platzhalter** |

4. **Nachrücker einfügen** in `redraft_assignment_waitlist_2026`
   (Batches à 500): `assignment_run_id`, `waitlist_position` (1-basiert,
   Reihenfolge = `created_at`), `sleeper_username`, `sleeper_user_id`,
   `discord`, `source_registration_id`, `source_registration_created_at`.

**Ergebnis:** Nach erfolgreichem Speichern existiert genau **ein** Run mit
`is_active = true`. `redraft_last_saved` und `redraft_last_saved_run_id` werden
gesetzt, `redraft_save_message`/`redraft_save_type` steuern das Banner, und ein
Eintrag landet im Sync-Protokoll (`_log`).

### Auflösung der Quell-Daten

Vor dem Schreiben baut die Methode zwei Lookups aus
`redraft_registrations`:

- `by_index` — Schlüssel `_normalize_key(row["index"])`
- `by_norm_sleeper` — Schlüssel `_normalize_key(row["sleeper"])` (erster Treffer gewinnt)

Für jede Preview-Zeile wird zuerst über `index`, dann über den Sleeper-Namen
gesucht. Fehlt beides, werden `sleeper_user_id`, `discord` und
`source_registration_*` als `""`/`NULL` geschrieben — der Datensatz bleibt
schreibbar.

### Die Platzhalter `league_id` und `league_invite_link`

Beide Spalten werden absichtlich als **leerer String** gespeichert:
Zum Zeitpunkt der Auslosung existieren die Sleeper-Ligen noch nicht.
Der geplante Ablauf ist:

1. Auslosung speichern (Platzhalter `""`).
2. Ligen manuell in Sleeper anlegen.
3. `redraft_assignment_players_2026.league_id` und `league_invite_link`
   nachtragen — z. B. per SQL oder einem künftigen Admin-Schritt:

   ```sql
   update redraft_assignment_players_2026
      set league_id = '1234567890',
          league_invite_link = 'https://sleeper.com/i/xxxxxxx'
    where assignment_run_id = '<run_id>'
      and league_number = 1;
   ```

4. Anschließend kann die Liga über den normalen Admin-Flow
   („Neue Liga hinzufügen“) in `leagues` aufgenommen und synchronisiert werden.

**Nicht verwechseln:** `league_id` in dieser Tabelle ist die **Sleeper**-Liga-ID
(nach Anlage), `league_number`/`league_name` sind die internen Bezeichner der
Auslosung.

---

## 5. Fehlerbehandlung

Jeder Schritt in `save_redraft_assignment` ist einzeln abgesichert. Bei einem
Fehler wird:

- `logging.exception(...)` geschrieben,
- `redraft_save_message` mit deutschem Fehlertext gesetzt,
- `redraft_save_type = "error"`,
- ein Log-Eintrag erzeugt,
- und die Methode **abgebrochen** (`return`).

`redraft_is_saving` wird immer im `finally` zurückgesetzt.

> **Achtung:** Es gibt **keine** Transaktion über die vier Schritte. Bricht der
> Vorgang nach Schritt 2 ab, existiert ein aktiver Run ohne (bzw. mit
> unvollständigen) Spielerzeilen. In diesem Fall einfach erneut speichern —
> Schritt 1 deaktiviert den unvollständigen Run wieder. Verwaiste Zeilen können
> über `assignment_run_id` identifiziert und entfernt werden.

---

## 6. Admin-UI: `_redraft_card()` in `app/pages/admin.py`

**Gelesene Vars:** `redraft_total_count`, `redraft_commish_count`,
`redraft_possible_leagues`, `redraft_remaining_count`,
`redraft_assignments`, `redraft_nachruecker`, `redraft_has_assignment`,
`redraft_is_loading`, `redraft_is_saving`, `redraft_error`,
`redraft_warning`, `redraft_save_message`, `redraft_save_type`,
`redraft_last_loaded`, `redraft_last_generated`, `redraft_last_saved`

**Buttons / Events**

| Button | Event |
| --- | --- |
| „Anmeldungen laden“ | `AdminState.load_redraft_registrations` |
| „Ligaeinteilung generieren“ / „Neu auslosen (Daten refreshen)“ | `AdminState.generate_redraft_assignment` |
| „Auslosung speichern (überschreibt aktive)“ | `AdminState.save_redraft_assignment` |
| ✕ in Bannern | `clear_redraft_error`, `clear_redraft_warning`, `clear_redraft_save_message` |

**Aufbau:** Erklärtext → Fehler-/Warn-Banner → Info-Hinweis → 4 Statistik-Kacheln
(Anmeldungen, Commish, mögliche 12er-Ligen, Nachrücker) → Save-Banner →
Überschreib-Warnung (nur bei vorhandener Preview) → Button-Zeile mit
Zeitstempeln → Ergebnis: Liga-Karten (`_redraft_league_card` mit
`_redraft_player_row`) + Nachrücker-Liste (`_redraft_nachruecker_row`) oder
gestrichelte Leerzustands-Box.

**Datenschutz in der UI:** E-Mail und Änderungscode werden im Admin-Bereich
bewusst **nicht** angezeigt; `_fetch_redraft_registrations` selektiert sie
gar nicht.

---

## 7. Erweiterungs-Hinweise

- **Ligengröße ändern:** `AdminState.redraft_league_size` (Default 12).
  Die Computed Vars und `_build_assignment` lesen die Var; die UI-Texte
  („12er-Ligen“, „/ 12“) und `RedraftRegistrationState.full_leagues_count`
  müssten mitgezogen werden.
- **Deterministische Auslosung:** Seed einführen, im Run speichern
  (`notes` oder neue Spalte) und in `_build_assignment` an `random.Random(seed)`
  übergeben.
- **Mehr als drei Wünsche:** `RedraftRegistrationState` um Felder erweitern
  (`teammate4_input`, `_normalize_mates`) — `_build_assignment` verarbeitet
  beliebig lange `mitspieler`-Listen bereits.
- **Aktive Auslosung öffentlich zeigen:** neue Seite/State, die
  `redraft_assignment_runs_2026` mit `is_active = true` liest und über
  `assignment_run_id` die Spieler joint. `league_invite_link` erst anzeigen,
  wenn er nicht `""` ist.
