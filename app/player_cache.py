import requests
import logging

_player_cache: dict[str, dict] = {}


def get_player_cache() -> dict[str, dict]:
    global _player_cache
    if len(_player_cache) > 0:
        return _player_cache
    try:
        r = requests.get("https://api.sleeper.app/v1/players/nfl", timeout=30)
        r.raise_for_status()
        data = r.json()
        for pid, p in data.items():
            first = p.get("first_name", "") or ""
            last = p.get("last_name", "") or ""
            full_name = f"{first} {last}".strip()
            if not full_name and "search_full_name" in p:
                full_name = p.get("search_full_name")
            _player_cache[str(pid)] = {
                "full_name": full_name or f"Player {pid}",
                "first_name": first,
                "last_name": last,
                "team": p.get("team") or "FA",
                "position": p.get("position") or "?",
                "status": p.get("status") or "Active",
            }
    except Exception as e:
        logging.exception(f"Error fetching player cache: {e}")
    return _player_cache


def resolve_player(player_id: str) -> dict:
    cache = get_player_cache()
    pid_str = str(player_id)
    if pid_str in cache:
        return cache[pid_str]
    return {"full_name": f"Player {pid_str}", "team": "FA", "position": "?"}


def enrich_trending(trending_list: list[dict]) -> list[dict]:
    enriched = []
    for t in trending_list:
        pid = str(t.get("player_id", ""))
        p_data = resolve_player(pid)
        new_t = dict(t)
        new_t["full_name"] = p_data["full_name"]
        new_t["team"] = p_data["team"]
        new_t["position"] = p_data["position"]
        enriched.append(new_t)
    return enriched


def enrich_roster_players(player_ids: list[str]) -> list[dict]:
    res = []
    for pid in player_ids:
        p_data = resolve_player(pid)
        res.append(
            {
                "player_id": str(pid),
                "full_name": p_data["full_name"],
                "team": p_data["team"],
                "position": p_data["position"],
            }
        )
    return res