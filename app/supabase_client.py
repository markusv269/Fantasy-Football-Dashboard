import os
import logging
from supabase import create_client

_supabase_client = None
_supabase_cache_key: tuple[str, str] | None = None


def get_supabase_client():
    """
    Initialize (or reinitialize) the Supabase client.

    Robust against environment updates: if SUPABASE_URL or SUPABASE_KEY
    change at runtime (e.g. after a redeploy or secret rotation), the
    cached client is rebuilt so we never hold a stale connection.
    """
    global _supabase_client, _supabase_cache_key
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        logging.warning("Supabase credentials not found. Using local state.")
        _supabase_client = None
        _supabase_cache_key = None
        return None
    current_key = (url, key)
    if _supabase_client is not None and _supabase_cache_key == current_key:
        return _supabase_client
    try:
        _supabase_client = create_client(url, key)
        _supabase_cache_key = current_key
        return _supabase_client
    except Exception as e:
        logging.exception(f"Failed to initialize Supabase client: {e}")
        _supabase_client = None
        _supabase_cache_key = None
        return None


def reset_supabase_client():
    """Force the next `get_supabase_client()` call to rebuild the client."""
    global _supabase_client, _supabase_cache_key
    _supabase_client = None
    _supabase_cache_key = None
