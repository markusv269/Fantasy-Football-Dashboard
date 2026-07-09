# Vorgänger-Ligen aus Sleeper nach Supabase übernehmen

## Phase 1: Datenzugriff und Umfang prüfen ✅
- [x] Supabase-Verbindung mit vorhandenen Zugangsdaten validieren
- [x] Alle bestehenden Liga-IDs aus der Datenbank laden
- [x] Sleeper-Ligadaten abrufen und vorhandene Vorgänger-Referenzen bestimmen

## Phase 2: Vorgänger-Ligen synchronisieren ✅
- [x] Vorgänger-Ligen rekursiv anhand der Sleeper-Referenz ermitteln
- [x] Neue Vorgänger-Ligen in Supabase speichern
- [x] Zugehörige Manager-, Roster-, Matchup- und Draft-Daten soweit verfügbar synchronisieren
- [x] Duplikate und bereits vorhandene Ligen überspringen

## Phase 3: Ergebnis validieren ✅
- [x] Anzahl gefundener, eingefügter und übersprungener Vorgänger-Ligen prüfen
- [x] Stichprobe der neu gespeicherten Ligen aus Supabase laden
- [x] Abschlussstatus dokumentieren

## Designrichtung
- Keine UI-Änderung erforderlich; bestehendes Admin-/Liga-Datenmodell wird unverändert genutzt.
