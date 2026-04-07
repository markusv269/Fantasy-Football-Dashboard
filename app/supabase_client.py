import os
import logging
from supabase import create_client

_supabase_client = None


def get_supabase_client():
    """
    Initialize Supabase client if credentials exist.
    """
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        logging.warning("Supabase credentials not found. Using local state.")
        return None
    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        logging.exception(f"Failed to initialize Supabase client: {e}")
        return None