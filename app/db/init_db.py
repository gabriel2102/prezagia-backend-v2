# app/db/init_db.py
from app.db.supabase import get_supabase
import os
import json


def init_db() -> None:
    """
    Inicializa la base de datos con las tablas y datos iniciales necesarios.
    
    Nota: En Supabase, normalmente crearías las tablas a través del panel de control,
    pero este script puede usarse para configuración inicial o para pruebas.
    """
    try:
        # Verificar conexión a Supabase
        supabase = get_supabase()
        
        # Inicializar datos de ejemplo si es necesario
        # Por ejemplo, crear un usuario administrador, etc.
        
        print("Inicialización de BD completada")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        raise e