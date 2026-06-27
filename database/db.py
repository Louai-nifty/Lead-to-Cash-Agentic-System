from supabase import create_client
import os
from dotenv import load_dotenv
from postgrest.exceptions import APIError

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_client():
    """Return Supabase client (reuse same connection)."""
    return client