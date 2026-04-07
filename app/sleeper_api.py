import requests
import logging

BASE_URL = "https://api.sleeper.app/v1"


def _get(path: str):
    """Helper method to fetch JSON data from Sleeper API."""
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=10)
        if r.status_code == 404:
            logging.warning(f"Sleeper API 404 Not Found for {path}")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.exception(f"Error fetching {path}: {e}")
        return None


def get_nfl_state():
    """Fetch the current NFL state."""
    return _get("/state/nfl")


def get_league(league_id: str):
    """Fetch a specific league's details."""
    return _get(f"/league/{league_id}")


def get_rosters(league_id: str):
    """Fetch all rosters for a specific league."""
    return _get(f"/league/{league_id}/rosters")


def get_league_users(league_id: str):
    """Fetch all users for a specific league."""
    return _get(f"/league/{league_id}/users")


def get_matchups(league_id: str, week: int):
    """Fetch matchups for a specific league and week."""
    return _get(f"/league/{league_id}/matchups/{week}")


def get_trending_players(
    sport: str = "nfl",
    trend_type: str = "add",
    lookback_hours: int = 24,
    limit: int = 25,
):
    """Fetch trending players (add or drop)."""
    return _get(
        f"/players/{sport}/trending/{trend_type}?lookback_hours={lookback_hours}&limit={limit}"
    )


def get_winners_bracket(league_id: str):
    """Fetch the winners bracket for a specific league."""
    return _get(f"/league/{league_id}/winners_bracket")


def get_losers_bracket(league_id: str):
    """Fetch the losers bracket for a specific league."""
    return _get(f"/league/{league_id}/losers_bracket")


def get_league_drafts(league_id: str):
    """Fetch all drafts for a specific league."""
    return _get(f"/league/{league_id}/drafts")


def get_draft(draft_id: str):
    """Fetch details for a specific draft."""
    return _get(f"/draft/{draft_id}")


def get_draft_picks(draft_id: str):
    """Fetch picks for a specific draft."""
    return _get(f"/draft/{draft_id}/picks")