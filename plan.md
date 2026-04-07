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

## Phase 3: Rebrand to "Stoned Lack" + Supabase Polls + News
- [ ] Rename all branding from "FF Hub" / "Fantasy Football Hub" to "Stoned Lack" podcast branding
- [ ] Create Supabase-backed polls system: store polls/options/votes (requires user to create `polls`, `poll_options`, `poll_votes` tables — provide SQL + fallback to local state)
- [ ] Build news system reading from Supabase (requires `news` table — provide SQL + fallback to local state with sample data)
- [ ] Update Community page: real polls from Supabase (with vote tracking), news feed section
- [ ] Wire community registration to existing `dynasty_waitinglist` and `user_registration` tables
