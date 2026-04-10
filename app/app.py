import reflex as rx
from app.pages.home import home_page
from app.pages.leagues import leagues_page
from app.pages.matchups import matchups_page
from app.pages.standings import standings_page
from app.pages.rosters import rosters_page
from app.pages.community import community_page
from app.pages.trending import trending_page
from app.pages.drafts import drafts_page
from app.pages.waitinglist import waitinglist_page
from app.states.app_state import AppState
from app.states.matchups_state import MatchupsState
from app.states.community_state import CommunityState
from app.states.draft_state import DraftState
from app.states.league_detail_state import LeagueDetailState
from app.states.theme_state import ThemeState
from app.states.user_state import UserState
from app.states.waitlist_state import WaitlistState

app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(home_page, route="/", on_load=[AppState.init_app, UserState.init_user])
app.add_page(
    leagues_page, route="/leagues", on_load=[AppState.init_app, UserState.init_user]
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
app.add_page(community_page, route="/community", on_load=CommunityState.init_community)
app.add_page(trending_page, route="/trending", on_load=CommunityState.init_trending)
app.add_page(drafts_page, route="/drafts", on_load=DraftState.init_drafts)
app.add_page(
    waitinglist_page, route="/waitinglist", on_load=WaitlistState.init_waitlist
)