import reflex as rx
import time
from app.sleeper_api import get_trending_players
from app.player_cache import enrich_trending
from app.supabase_client import get_supabase_client
import logging
from datetime import datetime


class CommunityState(rx.State):
    polls: list[dict[str, str | int | bool | list[dict[str, str | int]]]] = []
    news_items: list[dict[str, str | int]] = []
    polls_loaded: bool = False
    news_loaded: bool = False
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
    def load_polls(self):
        client = get_supabase_client()
        if not client:
            return
        try:
            polls_res = (
                client.table("polls")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            if polls_res and polls_res.data:
                new_polls = []
                for p in polls_res.data:
                    answers = p.get("answers", [])
                    stats = p.get("stats", [])
                    options = []
                    total = 0
                    for i, ans in enumerate(answers):
                        votes = stats[i] if i < len(stats) else 0
                        options.append({"text": str(ans), "votes": int(votes)})
                        total += int(votes)
                    new_polls.append(
                        {
                            "id": str(p["id"]),
                            "question": p.get("poll", ""),
                            "options": options,
                            "total_votes": total,
                            "is_active": True,
                        }
                    )
                self.polls = new_polls
                self.polls_loaded = True
        except Exception as e:
            logging.exception(f"Error loading polls from Supabase: {e}")

    @rx.event
    def load_news(self):
        client = get_supabase_client()
        if not client:
            return
        try:
            news_res = (
                client.table("news")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            if news_res and news_res.data:
                new_items = []
                for n in news_res.data:
                    created = n.get("created_at", "")
                    date_str = ""
                    if created:
                        try:
                            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                            date_str = dt.strftime("%d. %B %Y")
                        except Exception:
                            logging.exception("Unexpected error")
                            date_str = created[:10]
                    new_items.append(
                        {
                            "id": str(n.get("id", "")),
                            "title": n.get("header", ""),
                            "content": n.get("text", ""),
                            "date": date_str,
                        }
                    )
                self.news_items = new_items
                self.news_loaded = True
        except Exception as e:
            logging.exception(f"Error loading news from Supabase: {e}")

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
        client = get_supabase_client()
        if client:
            try:
                poll_id_int = int(poll_id)
                poll_res = (
                    client.table("polls")
                    .select("stats")
                    .eq("id", poll_id_int)
                    .limit(1)
                    .execute()
                )
                if poll_res and poll_res.data:
                    current_stats = poll_res.data[0].get("stats", [])
                    if option_index < len(current_stats):
                        current_stats[option_index] = (
                            int(current_stats[option_index]) + 1
                        )
                        client.table("polls").update({"stats": current_stats}).eq(
                            "id", poll_id_int
                        ).execute()
            except Exception as e:
                logging.exception(f"Error updating poll vote in Supabase: {e}")

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
        client = get_supabase_client()
        if client:
            try:
                client.table("dynasty_waitinglist").insert(
                    {
                        "sleeper_name": self.reg_sleeper_username or self.reg_team_name,
                        "dynasty": self.reg_preferred_league == "Dynasty",
                        "dynasty_idp": False,
                        "dynasty_bb": self.reg_preferred_league == "Best Ball",
                    }
                ).execute()
            except Exception as e:
                logging.exception(f"Error inserting registration into Supabase: {e}")
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
    def init_community(self):
        yield CommunityState.load_polls
        yield CommunityState.load_news

    @rx.event
    def init_trending(self):
        yield CommunityState.fetch_trending