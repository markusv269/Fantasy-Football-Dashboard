# Wöchentliche Supabase-Synchronisierung aller Ligen

## Phase 1: Datenbankzugriff und Synchronisierungsumfang prüfen ✅
- [x] Supabase-Zugang und vorhandene Ligadaten validieren
- [x] Tabellenumfang für Drafts, Roster, Matchups und Manager anhand der bestehenden App-Logik bestätigen
- [x] Synchronisierungsstrategie für alle Ligen und aktuelle NFL-Woche festlegen

## Phase 2: Wiederverwendbares Wartungsskript erstellen ✅
- [x] Skript für wöchentliche Synchronisierung aller Ligen ergänzen
- [x] Fortschrittsausgabe, Fehlerzählung und sichere Wiederholbarkeit einbauen
- [x] Bestehende Datenbankspalten und Konfliktregeln der App beibehalten

## Phase 3: Synchronisierung ausführen und validieren
- [ ] Synchronisierung gegen echte Supabase- und Sleeper-Daten ausführen
- [ ] Ergebniszahlen und Fehler prüfen
- [ ] Abschlussstatus und Nutzungshinweis bereitstellen

## Designrichtung
- Keine UI-Änderungen; Fokus auf robuste Datenpflege, klare Konsolenausgabe und sichere Wiederholbarkeit ohne Mock-Daten.
