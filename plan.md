# league_sort für Dynasty-Vorgängerketten ergänzen

## Phase 1: Datenanalyse ✅
- [x] Vorhandene 2025-Dynasty-Ligen mit league_sort prüfen
- [x] Vorgängerketten über previous_league_id ermitteln
- [x] Konflikte oder fehlende Vorgänger erkennen

## Phase 2: Datenbankaktualisierung ✅
- [x] league_sort der 2025-Dynasty-Basisligen als Quelle verwenden
- [x] Alle Vorgängerligen in früheren Jahren mit derselben Nummerierung aktualisieren
- [x] Mehrdeutige oder widersprüchliche Zuordnungen sicher behandeln

## Phase 3: Validierung ✅
- [x] Aktualisierte Vorgängerketten gegen Supabase prüfen
- [x] Sicherstellen, dass 2025-Basisnummerierungen unverändert bleiben
- [x] Ergebnis mit Anzahl aktualisierter und übersprungener Ligen zusammenfassen
