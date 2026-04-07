import reflex as rx
import time
from app.sleeper_api import get_trending_players
from app.player_cache import enrich_trending
from app.supabase_client import get_supabase_client


class CommunityState(rx.State):
    polls: list[dict[str, str | int | bool | list[dict[str, str | int]]]] = [
        {
            "id": "poll_1",
            "question": "Who will be the top QB in 2025?",
            "options": [
                {"text": "Patrick Mahomes", "votes": 42},
                {"text": "Josh Allen", "votes": 156},
                {"text": "Lamar Jackson", "votes": 89},
                {"text": "C.J. Stroud", "votes": 104},
            ],
            "total_votes": 391,
            "is_active": True,
        },
        {
            "id": "poll_2",
            "question": "Which team improved the most this offseason?",
            "options": [
                {"text": "Bears", "votes": 210},
                {"text": "Texans", "votes": 315},
                {"text": "Commanders", "votes": 405},
            ],
            "total_votes": 930,
            "is_active": True,
        },
        {
            "id": "poll_3",
            "question": "Favorite podcast segment?",
            "options": [
                {"text": "Waiver Wire Adds", "votes": 500},
                {"text": "Start/Sit", "votes": 420},
                {"text": "Mailbag", "votes": 280},
            ],
            "total_votes": 1200,
            "is_active": False,
        },
    ]
    voted_polls: list[str] = []
    reg_team_name: str = ""
    reg_email: str = ""
    reg_sleeper_username: str = ""
    reg_preferred_league: str = "Redraft"
    registration_submitted: bool = False
    registrations: list[dict[str, str]] = []
    episodes: list[dict[str, str | int]] = [
        {
            "id": "ep_105",
            "episode_number": 105,
            "title": "Waiver Wire Gold: Week 10 Winners",
            "description": "Breaking down the top adds for Week 10. Who to spend your FAAB on and who to avoid.",
            "date": "Nov 12, 2024",
            "duration": "45:20",
            "link": "#",
        },
        {
            "id": "ep_104",
            "episode_number": 104,
            "title": "Mid-Season Review & Predictions",
            "description": "Halfway through the fantasy season. We look at the biggest surprises and disappointments.",
            "date": "Nov 5, 2024",
            "duration": "52:10",
            "link": "#",
        },
        {
            "id": "ep_103",
            "episode_number": 103,
            "title": "Trade Deadline Special",
            "description": "Buy low, sell high! The best trade targets before your league's deadline hits.",
            "date": "Oct 29, 2024",
            "duration": "48:05",
            "link": "#",
        },
        {
            "id": "ep_102",
            "episode_number": 102,
            "title": "Injury Replacements & Stashes",
            "description": "How to navigate the recent wave of injuries and which backups need to be rostered.",
            "date": "Oct 22, 2024",
            "duration": "41:30",
            "link": "#",
        },
        {
            "id": "ep_101",
            "episode_number": 101,
            "title": "Panic Meter: Which Stars Are Busts?",
            "description": "Evaluating struggling early-round picks. Is it time to panic or hold steady?",
            "date": "Oct 15, 2024",
            "duration": "50:15",
            "link": "#",
        },
    ]
    trending_adds: list[dict[str, str | int]] = []
    trending_drops: list[dict[str, str | int]] = []
    trending_timeframe: str = "24h"

    @rx.event
    def vote_poll(self, poll_id: str, option_index: int):
        if poll_id in self.voted_polls:
            return
        for poll in self.polls:
            if poll["id"] == poll_id:
                options = poll["options"]
                options[option_index]["votes"] += 1
                poll["total_votes"] += 1
                self.voted_polls.append(poll_id)
                break

    @rx.event
    def submit_registration(self):
        if not self.reg_team_name or not self.reg_email:
            return rx.toast("Please fill in team name and email.", duration=3000)
        new_reg = {
            "team_name": self.reg_team_name,
            "email": self.reg_email,
            "sleeper_username": self.reg_sleeper_username,
            "preferred_league": self.reg_preferred_league,
            "timestamp": str(time.time()),
        }
        self.registrations.append(new_reg)
        self.registration_submitted = True
        self.reg_team_name = ""
        self.reg_email = ""
        self.reg_sleeper_username = ""
        return rx.toast("Registration successful!", duration=3000)

    @rx.event
    def change_trending_timeframe(self, timeframe: str):
        self.trending_timeframe = timeframe
        yield CommunityState.fetch_trending

    @rx.event
    def fetch_trending(self):
        hours = 24 if self.trending_timeframe == "24h" else 48
        adds = get_trending_players(trend_type="add", lookback_hours=hours, limit=25)
        drops = get_trending_players(trend_type="drop", lookback_hours=hours, limit=25)
        if adds:
            self.trending_adds = enrich_trending(adds)
        if drops:
            self.trending_drops = enrich_trending(drops)

    @rx.event
    def init_trending(self):
        yield CommunityState.fetch_trending