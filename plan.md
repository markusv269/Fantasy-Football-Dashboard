# Supabase-Datenverknüpfungen reparieren

## Phase 1: Verbindung und Datenmodell prüfen ✅
- [x] Aktuelle Supabase-Verbindung mit vorhandenen Zugangsdaten validieren
- [x] Relevante Tabellen, Spalten und Beispieldaten prüfen
- [x] Abweichungen zwischen Datenmodell und App-Ladepfaden identifizieren
- [x] Kritische leere oder fehlerhafte Datenpfade priorisieren

## Phase 2: Datenzugriffe und Verknüpfungen anpassen ✅
- [x] Tabellen- und Feldzugriffe robust an die aktuelle Datenstruktur anpassen
- [x] Liga-, Manager-, Roster-, Matchup-, Draft-, News- und Wartelisten-Verknüpfungen stabilisieren
- [x] Fehlerfälle, fehlende Felder und leere Ergebnismengen sauber behandeln
- [x] Ladezustände und Fallbacks für externe Datenpfade absichern

## Phase 3: Validierung und Buildprüfung ✅
- [x] Wichtige Lade-Events mit echten Supabase-Daten testen
- [x] Datenverknüpfungen über mehrere Seitenpfade prüfen
- [x] Reflex-Build erneut validieren
- [x] Planabschluss dokumentieren

## Designrichtung
- Bestehendes hell/dunkel kompatibles Design bleibt unverändert; Fokus liegt auf Datenstabilität, robuster Fehlerbehandlung und korrekten Verknüpfungen.
