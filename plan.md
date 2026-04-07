# Fantasy Football Community Hub

## Phase 1: Core Layout, Navigation & League Overview ✅
- [x] Build responsive shell: sidebar navigation, header with podcast branding, main content area
- [x] Create landing/home page with community highlights, podcast info, and league cards
- [x] Build league overview page that fetches league details from Sleeper API for multiple configured leagues
- [x] Implement NFL state display (current week, season) in the header
- [x] Add league selector/switcher component

## Phase 2: Matchups, Rosters & Standings Pages ✅
- [x] Build matchups page: fetch and display weekly matchups per league with scores, team names, opponent pairing
- [x] Build standings page: fetch rosters, compute W/L/T records, display ranked standings table
- [x] Build roster detail page: show full roster for a selected team (starters, bench, reserve)
- [x] Add week selector for matchups navigation
- [x] Connect user/owner display names to roster data via Sleeper API joins

## Phase 3: Community Features & Supabase Integration ✅
- [x] Build community page with polls/surveys section (UI with local state, Supabase-ready)
- [x] Build league registration/sign-up form for new leagues
- [x] Add trending players section (Sleeper trending add/drop API)
- [x] Add podcast episode highlights / links section
- [x] Wire Supabase client for polls, registrations, and community data (functional once credentials are added)

## Phase 4: 2026 League Migration & Draft Overview ✅
- [x] Load 2026 dynasty + redraft league IDs from uploaded file into app state
- [x] Fetch live league/draft data from Sleeper API for all 2026 leagues on page load
- [x] Build Drafts page: overview of all drafts (past 2025 from Supabase + upcoming 2026 from Sleeper API)
- [x] Draft cards show: league name, draft type (linear/snake), status badge (complete/drafting/pre_draft), start date, rounds, teams
- [x] Separate sections for "Upcoming Drafts" (scheduled with dates) and "Unscheduled Drafts" (TBD)
- [x] Historical section: completed 2025 drafts from Supabase with pick summaries

## Phase 5: NFL Player Data Resolution — Replace Player IDs with Names/Team/Position ✅
- [x] Create player cache module that fetches bulk player data from Sleeper API (GET /players/nfl) once and caches in memory
- [x] Add helper to resolve player_id → {full_name, team, position} using the cache
- [x] Update trending data (AppState + CommunityState) to enrich player_id entries with name, team, position fields
- [x] Update Home page trending section to display player name, team, position instead of "Player {id}"
- [x] Update Trending page to display resolved player names with team/position badges
- [x] Update Roster detail page to show player names, team, position instead of raw player IDs for starters and reserve/IR lists
