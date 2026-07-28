# GitHub Actions — Scheduled Database Sync

Diese Verzeichnisstruktur enthält **Templates** für die GitHub-Actions-
Workflows, die die Supabase-Datenbank mit den Sleeper-APIs synchron halten.
Sie nutzen ausschließlich die bereits vorhandenen Skripte in `app/scripts/`
und keine Mock-Daten.

> **Installation:** Kopiere jede `*.yml.txt`-Datei aus diesem Ordner nach
> `.github/workflows/` im Repository-Root und benenne sie in `*.yml` um.
> Die Templates sind hier als `.txt` abgelegt, weil das Codegenerierungs-
> Environment nur Dateien unter `app/` mit `.py/.md/.css/.txt` erzeugen
> darf. Der Inhalt ist final und einsatzbereit — nach dem Kopieren sind
> keine weiteren Änderungen nötig.

## Benötigte Repository-Secrets

Alle Workflows brauchen genau zwei Secrets. Ohne sie bricht jeder Job
kontrolliert mit einem `::error::`-Hinweis ab, bevor Python startet.

- `SUPABASE_URL`
- `SUPABASE_KEY`

Anlegen unter *Settings → Secrets and variables → Actions → New repository
secret*.

## Übersicht

| Workflow | Datei | Zeitplan | Verwendetes Skript | Zweck |
| --- | --- | --- | --- | --- |
| Matchups & Roster (gezielt, häufig, in-season) | `sync-matchups-rosters-frequent.yml` | Alle 3 h in Aug–Feb | `app.scripts.targeted_sync --modes managers,rosters,matchups` | Aktuelle Woche: Matchups, Roster, Manager |
| Matchups & Roster (legacy) | `sync-matchups-frequent.yml` | Alle 3 h in Aug–Feb | `app.scripts.weekly_sync --skip-drafts` | Alt-Workflow, ruft wöchentlichen Vollzug ohne Drafts auf |
| Daily Full Sync | `sync-daily.yml` | Täglich 06:00 UTC | `app.scripts.weekly_sync` | Metadaten, Manager, Roster, Matchups, Drafts |
| Daily Drafts Sync | `sync-drafts-daily.yml` | Täglich 05:30 UTC | `app.scripts.targeted_sync --modes drafts` | Nur `drafts`-Metadaten |
| Draft Picks (häufig, Draft-Saison) | `sync-draft-picks-frequent.yml` | Alle 2 h in Apr–Sep | `app.scripts.targeted_sync --modes draft_picks` | Aktualisiert `draft_picks` (delete+insert pro Draft) |
| Weekly NFL Players | `sync-nfl-players-weekly.yml` | Di 03:00 UTC | `app.scripts.targeted_sync --modes nfl_players` | Sleeper NFL-Katalog (~11k Zeilen) |
| Weekly Avatar Sync | `sync-avatars-weekly.yml` | Mo 04:00 UTC | `app.scripts.sync_league_avatars` | Nur `leagues.avatar` aktualisieren |
| Manual Targeted Sync | `sync-targeted-manual.yml` | Nur `workflow_dispatch` | `app.scripts.targeted_sync` | Beliebige Modi + Batch/Wochen-Fenster |
| Manual Full Sync (legacy) | `sync-manual.yml` | Nur `workflow_dispatch` | `app.scripts.weekly_sync` | Gezielte Batches / einzelne Ligen (Vollzug) |

## Warum diese Intervalle?

- **Alle 3 Stunden in der Saison**: `matchup_week_stats` und `rosters`
  ändern sich während NFL-Spielen aktiv. Ein 3-h-Takt ist häufig genug, um
  Live-Scoring nachzuziehen, aber weit unter Sleepers Rate-Limits.
- **Nur Aug–Feb per Cron-Monatsliste** (`8,9,10,11,12,1,2`): Offseason-
  Daten bewegen sich kaum — der tägliche Lauf reicht dann aus.
- **Täglich 06:00 UTC**: Zentraler Vollzug — deckt neue Drafts, geänderte
  Ligen-Metadaten und Manager-Wechsel innerhalb von 24 h ab.
- **Wöchentlich für Avatare**: League-Avatare ändern sich selten. Ein
  Fehlgriff (leerer Wert) würde bestehende Bilder überschreiben — daher
  konservativ.

## Manuelle Läufe (`workflow_dispatch`)

Alle Workflows lassen sich in der Actions-UI manuell starten.
`sync-manual.yml` bietet zusätzlich Eingabefelder, die 1:1 an
`weekly_sync.py` durchgereicht werden:

- `league_ids`: Komma-Liste von Sleeper-IDs (z. B. `12345,67890`).
- `offset` / `start` / `end` / `limit`: Batch-Fenster wie im Skript.
- `skip_matchups`, `skip_drafts`, `verbose_http`: entsprechende Flags.

Wenn `league_ids` gesetzt ist, ignoriert das Skript die Batch-Parameter —
das ist im Skript selbst so implementiert.

## Concurrency

Jeder wiederkehrende Workflow nutzt eine feste `concurrency.group`, damit
kein zweiter Lauf parallel startet, während ein vorheriger Sync noch läuft.
Manuelle Läufe (`sync-manual.yml`) verwenden `${{ github.run_id }}` in der
Gruppe, sodass gezielte Batches ungehindert nebeneinander laufen können.

## Gezieltes Sync-Skript (`targeted_sync`)

Das Skript `app/scripts/targeted_sync.py` erlaubt es, einzelne Datentypen
gezielt zu synchronisieren, ohne dass ein voller Ligen-Durchlauf laufen
muss. Es akzeptiert eine Kommaliste von Modi über `--modes` und teilt sich
Batch- (`--offset`, `--start`, `--end`, `--limit`, `--league-id`) sowie
Wochen-Optionen (`--week-mode single|range|all|current` mit `--week`,
`--week-start`, `--week-end`). Ein `--dry-run` Flag zeigt an, was
ausgeführt würde, ohne die Datenbank zu berühren.

Unterstützte Modi:

- `metadata` — leagues (Name, Saison, roster_positions, previous_league_id, avatar)
- `managers` — managers (User + Roster-Owner)
- `rosters` — rosters (pro Woche, Spieler/Starter/Reserve/Taxi)
- `matchups` — matchup_week_stats (pro Woche)
- `drafts` — drafts (Metadaten; on_conflict draft_id)
- `draft_picks` — draft_picks (delete+insert pro Draft)
- `nfl_players` — kompletter Sleeper NFL-Katalog
- `all` — alle Modi oben (analog zum wöchentlichen Vollzug)

Beispiele:

```bash
# Nur aktuelle NFL-Woche für Matchups + Roster
python -m app.scripts.targeted_sync --modes matchups,rosters

# Alle 19 Wochen für eine bestimmte Liga
python -m app.scripts.targeted_sync --modes matchups,rosters \
    --league-id 1313986550769422336 --week-mode all

# Nur Draft-Metadaten + Picks aktualisieren
python -m app.scripts.targeted_sync --modes drafts,draft_picks

# NFL-Spieler-Katalog aktualisieren
python -m app.scripts.targeted_sync --modes nfl_players

# Trockenlauf für einen Batch
python -m app.scripts.targeted_sync --modes managers \
    --offset 100 --limit 50 --dry-run
```

Alle Operationen sind idempotent und können jederzeit erneut ausgeführt
werden. Es werden ausschließlich die echten Sleeper- und Supabase-APIs
verwendet — keine Mock-Daten.

## Verhältnis zum wöchentlichen Vollzug (`weekly_sync`)

`weekly_sync.py` bleibt für den täglichen Vollzug erhalten und deckt alle
Modi in einem einzigen Durchlauf pro Liga ab. Die neuen gezielten
Workflows (Matchups+Roster häufig, Drafts täglich, Draft Picks in der
Draft-Saison, NFL-Spieler wöchentlich) rufen stattdessen
`targeted_sync.py` mit exakt den benötigten Modi auf und vermeiden so
unnötige API-Zugriffe.
