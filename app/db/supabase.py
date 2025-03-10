# app/db/supabase.py
from typing import Generator
import supabase
from postgrest.exceptions import APIError

from app.core.config import settings

# Cliente de Supabase
supabase_client = supabase.create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

def get_supabase() -> supabase.Client:
    """
    Función para obtener un cliente de Supabase.
    """
    return supabase_client