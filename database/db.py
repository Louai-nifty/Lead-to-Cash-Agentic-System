from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_client():
    """Return Supabase client (reuse same connection)."""
    return client