# SL2026 Supabase-Struktur und Sleeper-Synchronisation

## Phase 1: Verbindung und Zielstruktur prüfen ✅
- [x] Verfügbare Supabase-Zugangsdaten und Rechte validieren
- [x] Bestehende Tabellenstruktur der Zielverbindung erfassen
- [x] Prüfen, ob Schema-Erstellung über die aktuelle Verbindung möglich ist
- [x] Fehlende Tabellen oder Rechte als Blocker dokumentieren

## Phase 2: Datenquellen und Sync-Umfang vorbereiten ✅
- [x] Aktive SL2026-Ligen aus der Zielverbindung bestimmen
- [x] Sleeper-Endpunkte für Ligen, Manager, Roster, Matchups und Drafts validieren
- [x] Daten-Mapping für vorhandene Tabellen festlegen
- [x] Konfliktstrategie für Aktualisierung und Upserts festlegen

## Phase 3: Synchronisation durchführen ✅
- [x] Liga-Metadaten mit Sleeper-Daten aktualisieren
- [x] Manager- und Roster-Daten aktualisieren
- [x] Matchup-Daten für relevante Wochen aktualisieren
- [x] Draft-Daten aktualisieren
- [x] Champion-/Abschlussdaten aktualisieren, soweit verfügbar

## Phase 4: Validierung ✅
- [x] Tabellenzählungen und Beispielzeilen nach der Synchronisation prüfen
- [x] Datenkonsistenz zwischen Ligen, Managern, Rostern und Matchups prüfen
- [x] App-relevante Ladeevents mit den synchronisierten Daten testen
- [x] Abschlussstatus dokumentieren

## Notizen
- Direkte Schema-Erstellung ist mit der aktuell verfügbaren Supabase-REST-Verbindung nicht möglich, weil keine Postgres-Verbindungs-URL verfügbar ist.
- Die vorhandenen Tabellen sind über Supabase les- und schreibbar und wurden synchronisiert.
- SL2026 umfasst 36 Ligen in der Zielverbindung.
- Synchronisierte SL2026-Zählungen: 432 Manager, 6756 Roster-Zeilen, 6696 Matchup-Zeilen, 37 Draft-Zeilen.
- Einige 2026-Ligen liefern aktuell keine Sleeper-Matchups; diese wurden mit Roster-Daten ohne Matchup-Zeilen belassen.
- App-Import und Ligadetail-Ladeevent wurden erfolgreich validiert.
