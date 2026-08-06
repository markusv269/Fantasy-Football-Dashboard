import reflex as rx
from app.pages.home import home_page
from app.pages.archive import archive_page
from app.pages.fantasyboerse import fantasyboerse_page
from app.states.archive_state import ArchiveState
from app.states.fantasyboerse_state import FantasyBoerseState
from app.pages.leagues import leagues_page
from app.states.leagues_state import LeaguesState
from app.pages.league_detail import league_detail_page
from app.states.league_page_state import LeaguePageState
from app.pages.matchups import matchups_page
from app.pages.standings import standings_page
from app.pages.rosters import rosters_page
from app.pages.community import community_page
from app.pages.trending import trending_page
from app.pages.drafts import drafts_page
from app.pages.adp_draftboard import adp_draftboard_page
from app.states.adp_state import AdpState
from app.pages.waitinglist import waitinglist_page
from app.pages.redraft_registration import redraft_registration_page
from app.states.redraft_registration_state import RedraftRegistrationState
from app.pages.redraft_auslosung import redraft_auslosung_page
from app.states.redraft_auslosung_state import RedraftAuslosungState
from app.pages.admin import admin_page
from app.states.admin_state import AdminState
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.states.community_state import CommunityState
from app.states.draft_state import DraftState
from app.states.league_detail_state import LeagueDetailState
from app.states.theme_state import ThemeState
from app.states.user_state import UserState
from app.states.waitlist_state import WaitlistState

# Standard App configuration.
# Theme is passed here. Note that while deprecated in newer versions,
# for the current lockfile fix, we maintain stability of the app.py
# while adding the environment fix in tests/clean_lock.py.
app = rx.App(
    theme=rx.theme(
        has_background=False,
        radius="large",
        accent_color="red",
        appearance="light",
    ),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)

# Route Registrations
app.add_page(
    home_page,
    route="/",
    on_load=[
        AppState.init_app,
        UserState.init_user,
        CommunityState.load_news,
        CommunityState.load_polls,
        CommunityState.fetch_youtube_feed,
    ],
)
app.add_page(
    league_detail_page,
    route="/leagues/[lid]",
    on_load=LeaguePageState.load_league,
)
app.add_page(
    leagues_page,
    route="/leagues",
    on_load=[
        AppState.init_app,
        UserState.init_user,
        LeaguesState.load_leagues,
    ],
)
app.add_page(
    matchups_page,
    route="/matchups",
    on_load=[AppState.init_app, MatchupsState.init_matchups],
)
app.add_page(
    standings_page,
    route="/standings",
    on_load=[AppState.init_app, MatchupsState.init_standings],
)
app.add_page(
    rosters_page,
    route="/rosters",
    on_load=[AppState.init_app, MatchupsState.init_standings],
)
app.add_page(
    community_page, route="/community", on_load=CommunityState.init_community
)
app.add_page(
    trending_page, route="/trending", on_load=CommunityState.init_trending
)
app.add_page(drafts_page, route="/drafts", on_load=DraftState.init_drafts)
app.add_page(adp_draftboard_page, route="/adp", on_load=AdpState.init_adp)
app.add_page(
    waitinglist_page, route="/waitinglist", on_load=WaitlistState.init_waitlist
)
app.add_page(
    redraft_registration_page,
    route="/redraft-registration",
    on_load=RedraftRegistrationState.init_page,
)
app.add_page(
    redraft_auslosung_page,
    route="/redraft-auslosung",
    on_load=RedraftAuslosungState.init_page,
)
app.add_page(
    archive_page,
    route="/archive",
    on_load=[AppState.init_app, UserState.init_user, ArchiveState.load_archive],
)
app.add_page(
    fantasyboerse_page,
    route="/fantasyboerse",
    on_load=FantasyBoerseState.load_entries,
)
app.add_page(
    admin_page,
    route="/admin",
    on_load=AdminState.init_admin,
)
