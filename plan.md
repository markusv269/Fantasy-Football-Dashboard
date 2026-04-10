# Stoned Lack — User-Centric Redesign + Centralized Theming

## Phase 1: Centralized CSS Theme System + Sleeper User Identity ✅
- [x] Create centralized theme config (Python dict/module) with all color tokens for dark/light mode
- [x] Refactor ThemeState to provide CSS class helpers so pages don't repeat rx.cond patterns
- [x] Create UserState with sleeper_username (persisted in LocalStorage), Sleeper user_id lookup
- [x] Update layout.py to use centralized theme classes throughout sidebar, header, mobile nav
- [x] Remove add/remove league UI from Home and Leagues pages (move to admin later)

## Phase 2: User-Aware Leagues, Matchups, Standings, Rosters ✅
- [x] Leagues page: split into "My Leagues" and "Other Leagues" based on user's Sleeper membership
- [x] Home page: show user's leagues prominently, sleeper username input if not set, personalized welcome
- [x] Matchups page: auto-select user's league, highlight user's matchup
- [x] Standings page: highlight user's team row
- [x] Rosters page: user context awareness

## Phase 3: Drafts + Community + All Pages Final Polish ✅
- [x] Drafts page: apply centralized theme tokens from app.theme
- [x] Community page: apply centralized theme tokens from app.theme
- [x] Trending page: apply centralized theme tokens from app.theme
- [x] League detail modal: apply centralized theme tokens from app.theme
- [x] Final QA — all pages use centralized theme, no per-page rx.cond color logic
