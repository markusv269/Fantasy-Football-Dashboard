# Wartelisten-Registrierungslogik erweitern

## Phase 1: Datenverhalten und Sortierung aktualisieren ✅
- [x] Aktuelle Wartelisten-Spalten und Beispielwerte für Format-Registrierungen prüfen
- [x] Format-Anmeldung so anpassen, dass die jeweiligen Registrierungsfelder gesetzt oder geleert werden
- [x] Wartelisten-Sortierung je Format anhand der jeweiligen Registrierungsfelder umstellen
- [x] Bestehende Einträge weiterhin robust mit Fallbacks anzeigen

## Phase 2: Formular-Austragung ergänzen ✅
- [x] Bestehende Anmeldung im Formular eindeutig erkennen
- [x] Separaten Button für vollständige Austragung aus der Warteliste anzeigen
- [x] Austragung mit Ladezustand, Statusmeldung und Statistiken-Refresh umsetzen
- [x] Formularzustand nach erfolgreicher Austragung sauber zurücksetzen

## Phase 3: Validierung und Buildprüfung ✅
- [x] Format-Update-Events mit echten Supabase-Daten validieren
- [x] Austragungs-Event mit sicherem Testpfad validieren
- [x] Wartelisten-Seite und Datenlisten prüfen
- [x] Reflex-Build validieren

## Designrichtung
- Bestehendes hell/dunkel kompatibles Design beibehalten; die neue Austragungsaktion wird als dezenter, klar abgegrenzter Danger-Button im vorhandenen Kartenlayout ergänzt.
