from __future__ import annotations

from supabase import Client

from src.database.client import get_supabase_client


def get_supabase() -> Client | None:
    """Compatibility wrapper around the Streamlit-cached Supabase client."""
    return get_supabase_client()
