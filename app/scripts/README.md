# Wartungsskripte

## Wöchentliche Liga-Synchronisierung

Das Skript `weekly_sync.py` synchronisiert alle Ligen aus der Supabase-Tabelle
`leagues` mit der Sleeper-API. Es ist idempotent und kann jederzeit erneut
ausgeführt werden.

### Was wird synchronisiert?

Für jede Liga aus der Tabelle `leagues`:

- **`leagues`**: Metadaten (Name, Saison, `roster_positions`) aktualisiert;
  bestehender `league_type` wird bewahrt.
- **`managers`**: Aus Sleeper-Usern und Rostern upsertet
  (`on_conflict=league_id,roster_id`).
- **`rosters`**: Aktuelle NFL-Woche mit `wins`, `losses`, `ties`, `fpts_for`,
  `fpts_against` und `json_data` (Spieler, Starter, Reserve, Taxi) upsertet
  (`on_conflict=league_id,roster_id,week`).
- **`matchup_week_stats`**: Wochen 1 bis zur aktuellen NFL-Woche upsertet
  (`on_conflict=league_id,week,roster_id`).
- **`drafts`**: Alle Drafts der Liga upsertet (`on_conflict=draft_id`).

Dieselben Spaltennamen und Konfliktregeln wie in der App-Admin-Logik.

### Voraussetzungen

Die Umgebungsvariablen `SUPABASE_URL` und `SUPABASE_KEY` müssen gesetzt sein,
z.B. in einer `.env`-Datei im Projekt-Root:


SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGciOi...


### Aufruf

Aus dem Projekt-Root:

bash
python -m app.scripts.weekly_sync


Optionen:

bash
# Nur die ersten 10 Ligen synchronisieren (Test/Debug)
python -m app.scripts.weekly_sync --limit 10

# Nur bestimmte Ligen synchronisieren (mehrfach möglich)
python -m app.scripts.weekly_sync --league-id 1313986550769422336
python -m app.scripts.weekly_sync --league-id 111 --league-id 222

# Matchups oder Drafts überspringen
python -m app.scripts.weekly_sync --skip-matchups
python -m app.scripts.weekly_sync --skip-drafts


### Ausgabe

Fortschritt pro Liga, Erfolgs-/Fehlerzähler und eine Abschluss-Zusammenfassung.
Einzelne Liga-Fehler werden protokolliert; die Verarbeitung der übrigen Ligen
wird fortgesetzt. Der Exit-Code ist `0` bei komplettem Erfolg, `1` bei
teilweisen Fehlern, `2` bei fehlenden Credentials.

### Empfohlener Cronjob (wöchentlich)


# Dienstags 09:00 Uhr
0 9 * * 2 cd /pfad/zum/projekt && /usr/bin/python -m app.scripts.weekly_sync >> logs/weekly_sync.log 2>&1

