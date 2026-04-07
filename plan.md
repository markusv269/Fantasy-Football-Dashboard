# Fantasy Football Community Hub — Feature Update

## Phase 1: Drafts → Sleeper Draftboard & League Detail Modal ✅ (previously completed)
- [x] Core layout, navigation, league overview
- [x] Matchups, rosters, standings pages
- [x] Community features & Supabase integration
- [x] 2026 draft overview & player data resolution

## Phase 2: Draft Clicks → Sleeper Draftboard + League Card Detail Modal ✅
- [x] Make draft cards (upcoming + historical) open Sleeper draftboard in new tab: `https://sleeper.com/draft/nfl/{draft_id}`
- [x] Build league detail modal/overlay when clicking a league card on Home/Leagues pages
- [x] Modal shows: standings table (from Supabase rosters), recent matchups (from matchup_week_stats), league champion, roster positions
- [x] Fetch league standings from Supabase `rosters` table (week=0 for season totals) + `managers` for display names
- [x] Fetch recent matchups from `matchup_week_stats` + pair by matchup_id + resolve team names via `managers`
- [x] Show league champion from `league_champion` table if available

## Phase 3: Rebrand to "Stoned Lack" + Supabase Polls + News ✅
- [x] Rename all branding from "FF Hub" / "Fantasy Football Hub" to "Stoned Lack" podcast branding
- [x] Supabase-backed polls system: reads from `polls` table (poll, answers jsonb, stats jsonb), votes persist to DB
- [x] News system reading from Supabase `news` table (header, text, created_at)
- [x] Updated Community page: real polls from Supabase (with vote tracking), news feed section
- [x] Wire community registration to existing `dynasty_waitinglist` table
- [x] Migrated dynasty_leagues_2026.txt to Supabase leagues table (36 leagues inserted, file removed)
- [x] Draft state reads 2026 league IDs from Supabase instead of txt file
