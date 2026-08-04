# Stoned Lack Fantasy — Entwicklerhandbuch

> **Zielgruppe:** Entwickler/innen, die diese Reflex-App weiterentwickeln, debuggen
> oder erweitern. Dieses Handbuch beschreibt **jede Python-Datei** des Projekts,
> die Datenflüsse, die externen Schnittstellen (Supabase, Sleeper, YouTube) und die
> Verdrahtung von Seiten, Routen und State-Klassen.

## Inhaltsverzeichnis

| Dokument | Inhalt |
| --- | --- |
| `app/docs/README.md` (dieses Dokument) | Projektstruktur, Einstiegspunkte, Konfiguration, Hilfsmodule, externe Datenquellen, Skripte, Konventionen |
| [`app/docs/states.md`](states.md) | Alle State-Klassen: Variablen, Computed Vars, Events, private Helper, DB-/API-Abhängigkeiten, Seiteneffekte |
| [`app/docs/pages_und_komponenten.md`](pages_und_komponenten.md) | Alle Seiten & Komponenten: genutzte States, ausgelöste Events, Routen/`on_load`, Editier-Hinweise |
| [`app/docs/redraft_auslosung.md`](redraft_auslosung.md) | Redraft-2026-Anmeldung, Auslosungs-Algorithmus, Commish-Fallback, Persistenz in Supabase |
| [`app/docs/datenmodell.md`](datenmodell.md) | Alle verwendeten Supabase-Tabellen und Spalten, Konflikt-Keys, Sleeper-Endpunkte |

---

## 1. Überblick

Die App ist ein Fantasy-Football-Portal für die „Stoned Lack Army“. Sie liest
Liga-, Roster-, Matchup- und Draftdaten aus einer **Supabase-Postgres-Datenbank**,
ergänzt sie bei Bedarf live über die **Sleeper-API** und zeigt zusätzlich
Community-Inhalte (News, Polls, YouTube-Feed) an. Ein passwortgeschützter
**Admin-Bereich** synchronisiert Sleeper → Supabase und berechnet die
Redraft-Ligaeinteilung.

**Tech-Stack**

- `reflex==0.9.6.post1` (siehe `requirements.txt`)
- Reflex-Plugins: `TailwindV3Plugin`, `SitemapPlugin` (siehe `rxconfig.py`)
- Radix-basierte Reflex-Kernkomponenten (`rx.card`, `rx.table`, `rx.select`, …)
  in Kombination mit Tailwind-Klassen
- `supabase` (Python-Client) für alle Datenbankzugriffe
- `requests` für Sleeper-API und YouTube-RSS
- `python-dotenv` für lokale Umgebungsvariablen

**Design-Sprache** (siehe `app/theme.py`)

- Akzentfarbe: `#DC2626` (Rot), Hover `#B91C1C`
- Dark/Light über Reflex-`color_mode` (`rx.color_mode_cond`), Helper `t(dark, light)`
- Karten mit linkem roten Rand (`border-l-4 border-l-[#DC2626]`) für Hero-/Primär-Blöcke
- Schrift: `Inter` (über `head_components` in `app/app.py` geladen)

---

## 2. Projektstruktur

```text
.
├─ rxconfig.py                  # Reflex-Konfiguration (app_name="app", Plugins)
├─ requirements.txt             # Python-Abhängigkeiten
├─ apt-packages.txt             # (leer) System-Pakete für Deployment
├─ plan.md / knowledge.md / rules.md   # geschützte Kontextdateien – NICHT ändern
├─ assets/
│  ├─ placeholder.svg           # einziges Platzhalter-Bild
│  ├─ favicon.ico
│  └─ SLR2025.ipynb             # historisches Notebook (Vorlage des Auslosungs-Algorithmus)
├─ tests/
│  ├─ __init__.py               # geschützt
│  └─ clean_lock.py             # Wartungsskript: reflex.lock/.web entfernen
└─ app/
   ├─ app.py                    # EINZIGER Einstiegspunkt: rx.App + alle add_page-Aufrufe
   ├─ theme.py                  # Farb-/Klassen-Konstanten, t()-Helper
   ├─ avatar_utils.py           # Sleeper-Liga-Avatar-URLs (Python + Var-Variante)
   ├─ league_types.py           # Normalisierung von league_type / league_types
   ├─ player_cache.py           # In-Process-Cache des Sleeper-NFL-Spielerkatalogs
   ├─ sleeper_api.py            # Dünner Wrapper um api.sleeper.app/v1
   ├─ supabase_client.py        # Lazy Supabase-Client mit Env-Cache-Invalidierung
   ├─ youtube_feed.py           # YouTube-RSS-Parser mit TTL-Cache
   ├─ components/
   │  ├─ layout.py              # Sidebar, Mobile-Drawer, Header, layout()-Wrapper
   │  └─ league_modal.py        # Liga-Detail-Dialog (aktuell nicht eingebunden)
   ├─ pages/                    # 14 Seitenmodule (jeweils eine Funktion -> rx.Component)
   ├─ states/                   # 15 State-Module (eine Klasse pro Datei)
   ├─ scripts/
   │  ├─ weekly_sync.py         # CLI: wöchentliche Vollsynchronisierung
   │  ├─ sync_league_avatars.py # CLI: Avatare sicher nachziehen (nur UPDATE)
   │  └─ README.md              # Bedienungsanleitung der Skripte
   └─ docs/                     # DIESE Dokumentation
```

**Wichtige Struktur-Regeln des Projekts**

1. `app/app.py` ist die **einzige** Datei, die `app.add_page(...)` aufruft.
2. Jede State-Klasse liegt in **einer eigenen** Datei unter `app/states/`.
3. Importe sind **absolut** ab `app` (`from app.states.user_state import UserState`).
4. Seiten importieren `layout()` aus `app/components/layout.py` und wickeln ihren
   Inhalt damit ein — dadurch erscheinen Sidebar/Header auf jeder Seite.

---

## 3. Einstiegspunkte

### 3.1 `rxconfig.py`

```python
dotenv.load_dotenv()          # lädt .env, BEVOR Reflex startet
config = rx.Config(app_name="app", plugins=[TailwindV3Plugin(), SitemapPlugin()])
```

Der `dotenv`-Aufruf steht bewusst **vor** dem `import reflex`, damit
`SUPABASE_URL`/`SUPABASE_KEY` beim ersten Zugriff verfügbar sind.

### 3.2 `app/app.py`

Enthält:

1. Die Imports **aller** Seiten- und State-Module (nur so werden sie kompiliert).
2. `app = rx.App(theme=..., head_components=[...])`
   - `theme=rx.theme(has_background=False, radius="large", accent_color="red", appearance="light")`
   - `head_components`: Preconnect + Inter-Webfont
3. Alle Routen-Registrierungen.

#### Routentabelle (Reihenfolge wie in `app.py`)

| Route | Seitenfunktion | `on_load` |
| --- | --- | --- |
| `/` | `home_page` | `AppState.init_app`, `UserState.init_user`, `CommunityState.load_news`, `CommunityState.load_polls`, `CommunityState.fetch_youtube_feed` |
| `/leagues/[lid]` | `league_detail_page` | `LeaguePageState.load_league` |
| `/leagues` | `leagues_page` | `AppState.init_app`, `UserState.init_user`, `LeaguesState.load_leagues` |
| `/matchups` | `matchups_page` | `AppState.init_app`, `MatchupsState.init_matchups` |
| `/standings` | `standings_page` | `AppState.init_app`, `MatchupsState.init_standings` |
| `/rosters` | `rosters_page` | `AppState.init_app`, `MatchupsState.init_standings` |
| `/community` | `community_page` | `CommunityState.init_community` |
| `/trending` | `trending_page` | `CommunityState.init_trending` |
| `/drafts` | `drafts_page` | `DraftState.init_drafts` |
| `/adp` | `adp_draftboard_page` | `AdpState.init_adp` |
| `/waitinglist` | `waitinglist_page` | `WaitlistState.init_waitlist` |
| `/redraft-registration` | `redraft_registration_page` | `RedraftRegistrationState.init_page` |
| `/archive` | `archive_page` | `AppState.init_app`, `UserState.init_user`, `ArchiveState.load_archive` |
| `/admin` | `admin_page` | `AdminState.init_admin` |

> **Achtung Reihenfolge:** Die dynamische Route `/leagues/[lid]` wird **vor**
> `/leagues` registriert. Diese Reihenfolge muss beibehalten werden, sonst greift
> das Matching der dynamischen Route nicht.

> **Dynamischer Parameter:** Der Platzhalter heißt `lid` (nicht `league_id`), weil
> `league_id` sonst mit State-Vars kollidieren würde
> (`DynamicRouteArgShadowsStateVarError`). `LeaguePageState._extract_route_id()`
> liest beide Schlüssel (`lid`, `league_id`) defensiv aus.

---

## 4. Konfiguration & Umgebungsvariablen

| Variable | Verwendung | Fallback |
| --- | --- | --- |
| `SUPABASE_URL` | `app/supabase_client.py` | ohne Wert: `get_supabase_client()` gibt `None` zurück, App läuft mit leeren Listen |
| `SUPABASE_KEY` | dito | dito |
| `ADMIN_PASSWORD_HASH` | `app/states/admin_auth_state.py` (PBKDF2-SHA256-Hex, 200 000 Iterationen, Salt `stoned_lack_admin_v1_salt`) | — |
| `ADMIN_PASSWORD` | Klartext-Alternative, wird beim Start gehasht | — |
| *(kein Env gesetzt)* | Fallback-Passwort `stonedlack2026` | nur für lokale Nutzung gedacht |
| `REFLEX_UPLOADED_FILES_DIR` | (aktuell nicht genutzt — es gibt keine Uploads) | `./uploaded_files` |

**Hash generieren** (gleiche Parameter wie `_hash_password`):

```python
import hashlib
hashlib.pbkdf2_hmac("sha256", b"MEIN_PASSWORT",
                    b"stoned_lack_admin_v1_salt", 200_000).hex()
```

> Der Client in `supabase_client.py` cached die Instanz zusammen mit dem Tupel
> `(url, key)`. Ändern sich die Env-Werte zur Laufzeit (Redeploy, Secret-Rotation),
> wird der Client automatisch neu gebaut. `reset_supabase_client()` erzwingt das
> manuell.

---

## 5. Hilfsmodule im Detail

### 5.1 `app/supabase_client.py`

- `get_supabase_client() -> Client | None` — Lazy Singleton mit Env-Cache-Key.
  **Gibt `None` zurück**, wenn Credentials fehlen. **Jeder** Aufrufer muss das
  prüfen (`if not client: return`) — dieses Muster ist im gesamten Code konsistent.
- `reset_supabase_client()` — Cache invalidieren.

### 5.2 `app/sleeper_api.py`

Dünner Wrapper um `https://api.sleeper.app/v1`. `_get(path)` fängt Fehler,
loggt via `logging.exception` und gibt `None` zurück (404 → Warnung + `None`).

| Funktion | Endpunkt |
| --- | --- |
| `get_nfl_state()` | `/state/nfl` |
| `get_league(league_id)` | `/league/{id}` |
| `get_rosters(league_id)` | `/league/{id}/rosters` |
| `get_league_users(league_id)` | `/league/{id}/users` |
| `get_matchups(league_id, week)` | `/league/{id}/matchups/{week}` |
| `get_trending_players(sport, trend_type, lookback_hours, limit)` | `/players/{sport}/trending/{type}` |
| `get_winners_bracket` / `get_losers_bracket` | `/league/{id}/winners_bracket` bzw. `losers_bracket` (aktuell ungenutzt) |
| `get_league_drafts(league_id)` | `/league/{id}/drafts` |
| `get_draft(draft_id)` | `/draft/{id}` |
| `get_draft_picks(draft_id)` | `/draft/{id}/picks` |
| `get_all_nfl_players()` | `/players/nfl` (≈ 11 000 Spieler, Timeout 60 s) |

Zusätzlich (außerhalb dieses Moduls) werden direkt per `requests` abgefragt:
`https://api.sleeper.app/v1/user/{username}` in `UserState.resolve_user`,
`WaitlistState.validate_sleeper_name`, `RedraftRegistrationState.validate_sleeper`
und `_resolve_teammates`.

### 5.3 `app/player_cache.py`

Modul-globaler Cache `_player_cache: dict[str, dict]`, gefüllt beim ersten
`get_player_cache()`-Aufruf aus `/players/nfl`.

- `resolve_player(player_id)` → `{full_name, team, position}` (Fallback
  `Player {id}` / `FA` / `?`).
- `enrich_trending(list)` → ergänzt `full_name`, `team`, `position`.
- `enrich_roster_players(player_ids)` → Liste von Dicts mit `player_id`.

> **Seiteneffekt:** Der erste Aufruf lädt mehrere MB JSON und blockiert den
> Event-Handler. Der Cache lebt pro Serverprozess und wird nie invalidiert.
> Nach Sleeper-Spielerwechseln erst nach Neustart aktuell.

### 5.4 `app/league_types.py`

Historisch gab es nur die Textspalte `leagues.league_type`
(`redraft|dynasty|bestball`). Neu kommt `leagues.league_types` hinzu, das
Text **oder** Liste sein kann. Unterstützte Werte:
`redraft, dynasty, bestball, idp, idp_only`.

| API | Zweck |
| --- | --- |
| `normalize_league_types(new_val, legacy_val) -> (primary, types_list)` | Zentrale Normalisierung. `primary` bleibt rückwärtskompatibel (Basisformat `redraft/dynasty/bestball` gewinnt), `types_list` enthält alle Formen dedupliziert, Legacy-Tokens vorn. |
| `add_types_col(select_cols)` | Fügt `league_types` zur Select-Liste hinzu (idempotent). |
| `is_missing_league_types_column_error(exc)` | Erkennt „Spalte existiert nicht“ (42703 / PGRST) → Retry ohne Spalte. |
| `has_type(types, form)` | Bequeme Prüfung. |
| `SUPPORTED_TYPES` | Tupel aller erlaubten Werte. |

Intern: `_clean`, `_scan_tokens` (Longest-Match-Scan für kaputte Werte wie
`'dynasty["dynasty","bestball"]'`), `_extract_list` (Liste / JSON / CSV / Freitext).

**Standardmuster in allen States:**

```python
try:
    res = client.table("leagues").select(add_types_col(base_cols)).execute()
except Exception as e:
    if is_missing_league_types_column_error(e):
        res = client.table("leagues").select(base_cols).execute()   # still retry
    else:
        logging.exception(...); raise
```

### 5.5 `app/avatar_utils.py`

> **Hinweis:** Die Datei enthält den Docstring und `league_avatar_url` **zweimal**
> (historisch gewachsen). Die zweite Definition gewinnt; Verhalten ist identisch.
> Beim Aufräumen darauf achten, dass `PLACEHOLDER_URL` und alle drei Funktionen
> erhalten bleiben.

| Funktion | Kontext |
| --- | --- |
| `league_avatar_url(avatar) -> str` | **Python**-Seite (Skripte, Backend). Volle URL → unverändert; Sleeper-ID → `https://sleepercdn.com/avatars/thumbs/{id}`; leer/`null` → `PLACEHOLDER_URL`. |
| `league_avatar_src(avatar) -> rx.Var` | **Frontend**-Variante, kompiliert nach JS (`rx.cond`-Kette). Für `rx.image(src=...)`. |
| `league_avatar_image(avatar, size="40px", **kwargs)` | Fertige runde `rx.image`-Komponente. In `admin`, `archive`, `leagues`, `drafts`, `league_detail` verwendet. |

`PLACEHOLDER_URL = https://sleepercdn.com/images/v2/icons/league/nfl/purple.png`

### 5.6 `app/youtube_feed.py`

- Kanal-ID: `UCMD4pfyYl2hxHez34eqnfkQ`, RSS: `feeds/videos.xml?channel_id=...`
- `fetch_youtube_feed(limit=15)` → Liste von Dicts:
  `video_id, title, published, date_str, link, thumbnail, description[:300], views, is_short, type`
- `is_short` wird über `"/shorts/" in link` erkannt.
- Modul-Cache `_feed_cache` mit `CACHE_TTL = 600` s; bei Fehler wird der alte
  Cache-Inhalt zurückgegeben (nie leere Liste, wenn schon einmal geladen wurde).

### 5.7 `app/theme.py`

Konstanten + `t(dark, light)`-Helper (`rx.color_mode_cond`). Wichtige Exporte,
die in Seiten benutzt werden: `t`, `TEXT_PRIMARY`, `TEXT_SECONDARY`, `TEXT_MUTED`,
`BRAND_RED`, sowie ungenutzte, aber vorbereitete Klassen-Presets
(`CARD`, `INPUT`, `TABLE_*`, `BTN_*`, `BADGE_SUBTLE`, `EMPTY_STATE`, `SELECT`, `H1..H3`).

> **Regel:** `class_name` darf **nie** per f-String mit einem State-Var
> zusammengesetzt werden. Erlaubt sind reine Python-String-Konkatenationen mit
> `t(...)`-Vars (`"border " + t("border-gray-800", "border-gray-200")`) und
> vollständige `rx.cond(...)`-Zweige.

---

## 6. Externe Datenquellen — Zusammenfassung

| Quelle | Von wo aufgerufen | Caching | Fehlerverhalten |
| --- | --- | --- | --- |
| Supabase (Postgres) | alle States, beide CLI-Skripte | keins (bis auf `AdpState._ADP_RESULTS_CACHE`) | `None`-Client → leere Daten; Exceptions werden geloggt und in Status-Banner übersetzt |
| Sleeper API | `app/sleeper_api.py`, direkte `requests`-Aufrufe für `/user/{name}` | `player_cache` für den Spielerkatalog | `_get` → `None`; UI zeigt „nicht gefunden“ |
| YouTube RSS | `app/youtube_feed.py` (aufgerufen von `CommunityState.fetch_youtube_feed`) | 600 s TTL | letzter Cache-Stand |
| DiceBear/Sleeper-CDN (Bilder) | direkt im `src` der Bilder | Browser | Platzhalter-URL |

---

## 7. Wartungsskripte

Ausführliche Bedienungsanleitung: `app/scripts/README.md`.

### 7.1 `python -m app.scripts.weekly_sync`

Synchronisiert **alle** Ligen aus `leagues` mit Sleeper:

1. `_sync_league_metadata` — `leagues` upsert (`on_conflict=league_id`);
   bestehender `league_type` wird **bewahrt** (Fallback `dynasty`), `avatar`
   und `previous_league_id` werden gesetzt. Fällt bei fehlender `avatar`-Spalte
   automatisch auf einen Upsert ohne `avatar` zurück.
2. `_sync_managers` — `managers` upsert (`on_conflict=league_id,roster_id`).
3. `_sync_rosters` — `rosters` upsert (`on_conflict=league_id,roster_id,week`)
   inkl. `json_data` (`players/starters/reserve/taxi`).
4. `_sync_matchup_weeks` — Woche 1..aktuelle NFL-Woche in `matchup_week_stats`
   (`on_conflict=league_id,week,roster_id`).
5. `_sync_drafts` — `drafts` upsert (`on_conflict=draft_id`).

Batch-Optionen: `--limit`, `--offset`, `--start`, `--end`, `--league-id`
(mehrfach), `--skip-matchups`, `--skip-drafts`, `--verbose-http`.
Exit-Codes: `0` alles ok, `1` Teilfehler, `2` fehlende Credentials.

### 7.2 `python -m app.scripts.sync_league_avatars`

Zieht **nur** `leagues.avatar` nach. Führt ausschließlich
`UPDATE ... WHERE league_id = ?` aus — **niemals INSERT** (damit NOT-NULL-Constraints
wie `league_name` nicht verletzt werden). Parallelisiert die Sleeper-Abfragen
(`--workers`, Default 16). Optionen: `--limit`, `--offset`, `--league-id`,
`--clear-empty` (leeren Sleeper-Avatar als `NULL` speichern), `--dry-run`,
`--samples`.

### 7.3 `python tests/clean_lock.py`

Löscht `reflex.lock/` und `.web/` bei „persisted lockfile is out of sync“.

---

## 8. Konventionen für Änderungen

### 8.1 UI-Code (`app/pages/*`, `app/components/*`)

- **Keine** `if/else`, Schleifen oder List-Comprehensions in Funktionen, die
  `rx.Component` zurückgeben → `rx.cond` (2 Fälle), `rx.match` (≥ 3 Fälle),
  `rx.foreach` (Iteration).
  *Ausnahme im Bestand:* statische Python-Listen ohne State-Bezug werden mit
  `*[... for item in nav_items]` entpackt (`layout.py`, `_week_range()` in
  `leagues.py`) — das ist zur Compile-Zeit aufgelöst und erlaubt.
- Keine arbiträren Python-Funktionen auf State-Vars im Frontend — nur
  Var-Operationen (`.to(str)`, `.to_string()`, `.length()`, `.contains()`,
  `.upper()`, Arithmetik, `rx.cond`).
- Floats immer formatiert ausgeben (`f"{x:.2f}"`, `f"{x:.1f}%"`).
- Badges/Pills brauchen `w-fit`.
- Tabellen: Wrapper mit `overflow_x="auto"` + `border_radius` + Border-Klasse.

### 8.2 State-Code (`app/states/*`)

- Alle Vars **stark typisiert** und mit Default. Kein `Any`.
- Zugriff auf andere States nur per `await self.get_state(OtherState)` in
  `async`-Handlern; Import **innerhalb** des Handlers, um Zirkularität zu vermeiden.
- Methoden mit `_`-Präfix sind Helper (nicht als Event-Trigger nutzbar).
- `reset`, `set_state`, `get_substate`, `__init__` sind reservierte Namen.
- Lange Läufe: `self.is_loading = True; yield` als Erstes, `finally:` setzt zurück.

### 8.3 Neue Seite hinzufügen — Checkliste

1. `app/states/<feature>_state.py` mit einer Klasse anlegen.
2. `app/pages/<feature>.py` mit `def <feature>_page() -> rx.Component: return layout(...)`.
3. In `app/app.py` importieren **und** `app.add_page(..., route="/…", on_load=…)` ergänzen
   (dynamische Routen vor gleichnamigen statischen).
4. Navigationseintrag in `nav_items` (`app/components/layout.py`) hinzufügen —
   dieselbe Liste versorgt Desktop-Sidebar **und** Mobile-Drawer.
5. Dokumentation in `app/docs/pages_und_komponenten.md` und ggf. `states.md` ergänzen.

### 8.4 Bekannte Altlasten / Aufräum-Kandidaten

| Fund | Auswirkung |
| --- | --- |
| `app/avatar_utils.py` definiert Docstring + `league_avatar_url` doppelt | harmlos, zweite Definition gewinnt |
| `app/components/league_modal.py` + `LeagueDetailState` werden von **keiner** Seite gerendert (nur in `app.py` importiert) | toter Code; ersetzt durch die eigene Seite `/leagues/[lid]` |
| `AdminState._OBSOLETE_ASSIGNMENT_SOURCE` (String-Literal mit altem Algorithmus) | nur Dokumentation im Code, wird nie ausgeführt |
| `AppState.search_query`, `AppState.filter_type` | nirgends gelesen |
| `CommunityState.reg_*`, `submit_registration`, `registrations` | Alt-Formular, durch `/waitinglist` ersetzt |
| `MatchupsState.week_options` | Computed Var ohne Verwendung |
| `LeaguePageState.top_standings`, `roster_cards` | berechnet, aber von der Seite nicht gerendert (`full_standings` und `matchup_pairs` werden genutzt) |
| `get_winners_bracket` / `get_losers_bracket` | ungenutzte API-Wrapper |

> Vor dem Löschen prüfen, ob nicht ein zukünftiges Feature darauf aufbaut.
> Wird `LeagueDetailState` entfernt, muss auch der Import in `app/app.py`
> verschwinden (sonst ImportError).
