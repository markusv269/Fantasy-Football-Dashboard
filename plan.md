# previous_league_id aus Sleeper synchronisieren

## Phase 1: Datenprüfung und Aktualisierung ✅
- [x] Supabase-Zugriff und vorhandene League-Daten prüfen
- [x] Sleeper-Daten je Liga abrufen und previous_league_id normalisieren
- [x] Supabase-Spalte previous_league_id für alle Ligen aktualisieren

## Phase 2: Künftige Synchronisierung anpassen ✅
- [x] Liga-Metadaten-Sync um previous_league_id erweitern
- [x] Admin- und Wartungssynchronisierung konsistent halten
- [x] Fehlerfälle ohne vorherige Liga sauber als None behandeln

## Phase 3: Validierung ✅
- [x] Stichproben gegen Sleeper-API und Supabase prüfen
- [x] Sicherstellen, dass leere Werte als None gespeichert werden
- [x] Sync-Hilfslogik mit realen Daten validieren
