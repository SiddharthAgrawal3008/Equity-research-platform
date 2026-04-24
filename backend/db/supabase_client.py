import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


def save_research_result(session_id: str, user_id: str, ticker: str, data: dict) -> None:
    supabase = get_supabase()
    supabase.table("research_results").insert({
        "session_id": session_id,
        "user_id": user_id,
        "ticker": ticker.upper(),
        "data": data,
    }).execute()
