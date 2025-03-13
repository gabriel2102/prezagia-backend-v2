from supabase import create_client
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.test
load_dotenv(".env.test")

# Obtener credenciales de Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Verificar si las credenciales están bien cargadas
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ ERROR: No se encontraron las credenciales de Supabase en .env.test")

# Crear cliente de Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    """ Inicializa la base de datos creando usuarios de prueba. """
    try:
        # Verificar si la tabla "users" tiene datos
        response = supabase.table("users").select("*").limit(1).execute()

        if len(response.data) == 0:
            print("⚠️ No hay usuarios en la base de datos. Agregando usuario de prueba...")

            user_data = {
                "email": "admin@example.com",
                "password": "hashedpassword",
                "role": "admin",
                "name": "Admin User",
                "lastname": "Admin",
                "birthdate": "1990-01-01",
                "gender": "M",
                "is_active": True,
                "is_verified": True
            }

            supabase.table("users").insert([user_data]).execute()

            print("✅ Usuario de prueba agregado correctamente.")
        else:
            print("✅ La base de datos ya tiene datos, no es necesario inicializar.")

    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")

if __name__ == "__main__":
    init_db()
