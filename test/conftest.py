"""
Configuración para pruebas de Prezagia utilizando pytest.
Este archivo define fixtures compartidos para todas las pruebas.
"""
import os
import sys
import pytest
import asyncio
import json
from datetime import datetime, date, time
from dotenv import load_dotenv

# Cargar variables de entorno desde .env.test
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"Cargadas variables de entorno desde {dotenv_path}")
else:
    print(f"ADVERTENCIA: No se encontró el archivo .env.test en {dotenv_path}")

# Verificar que se cargaron las variables críticas
required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "CLAUDE_API_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"ERROR: Faltan variables de entorno requeridas: {', '.join(missing_vars)}")
    # Establecer valores predeterminados para pruebas
    if "SUPABASE_URL" in missing_vars:
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    if "SUPABASE_KEY" in missing_vars:
        os.environ["SUPABASE_KEY"] = "test-key"
    if "CLAUDE_API_KEY" in missing_vars:
        os.environ["CLAUDE_API_KEY"] = "test-api-key"
    print("Se han establecido valores predeterminados para las variables faltantes.")

# Añadir la raíz del proyecto al path para importaciones
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ahora importamos la aplicación
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.config import settings
from app.db.supabase import get_supabase
from app.services.security import get_password_hash, create_access_token


# Fixture para cliente de prueba
@pytest.fixture
def client():
    """Crea un cliente de prueba para la API FastAPI."""
    with TestClient(app) as test_client:
        yield test_client


# Fixture para cliente asíncrono
@pytest.fixture
async def async_client():
    """Crea un cliente asíncrono para la API FastAPI."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Fixture para datos de prueba
@pytest.fixture
def test_data():
    """Proporciona datos de prueba comunes."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return {
        "user": {
            "email": f"test_user_{timestamp}@test.com",
            "nombre": "Usuario de Prueba",
            "password": "Password123!",
            "fecha_nacimiento": "1990-01-01",
            "hora_nacimiento": "12:00:00",
            "lugar_nacimiento_lat": 40.416775,
            "lugar_nacimiento_lng": -3.703790,
            "lugar_nacimiento_nombre": "Madrid"
        },
        "chart": {
            "chart_type": "natal",
            "name": "Carta Natal de Prueba",
            "description": "Carta para pruebas",
            "birth_date": "1990-01-01",
            "birth_time": "12:00:00",
            "latitude": 40.416775,
            "longitude": -3.703790,
            "location_name": "Madrid",
            "interpretation_depth": 3
        },
        "prediction": {
            "prediction_type": "general",
            "prediction_period": "month",
            "name": "Predicción Mensual de Prueba",
            "description": "Predicción para pruebas",
            "birth_date": "1990-01-01",
            "birth_time": "12:00:00",
            "birth_latitude": 40.416775,
            "birth_longitude": -3.703790,
            "birth_location_name": "Madrid",
            "prediction_date": datetime.now().strftime("%Y-%m-%d"),
            "focus_areas": ["career", "relationships"]
        }
    }


# Fixture para crear un usuario de prueba y obtener su token
@pytest.fixture
async def auth_token(client, test_data):
    """Crea un usuario de prueba y devuelve un token de autenticación."""
    # Registrar usuario
    response = client.post("/api/auth/register", json=test_data["user"])
    
    # Si ya existe, hacer login directamente
    if response.status_code != 201:
        login_data = {
            "username": test_data["user"]["email"],
            "password": test_data["user"]["password"]
        }
        response = client.post("/api/auth/login", data=login_data)
        
        if response.status_code != 200:
            pytest.fail(f"No se pudo crear o autenticar al usuario de prueba: {response.text}")
        
        token_data = response.json()
        return token_data["access_token"]
    
    # Si se creó correctamente, hacer login
    login_data = {
        "username": test_data["user"]["email"],
        "password": test_data["user"]["password"]
    }
    response = client.post("/api/auth/login", data=login_data)
    
    if response.status_code != 200:
        pytest.fail(f"No se pudo autenticar al usuario recién creado: {response.text}")
    
    token_data = response.json()
    return token_data["access_token"]


# Fixture para mocks de funciones de cálculo astrológico
@pytest.fixture
def mock_chart_calculation(monkeypatch):
    """Mock para cálculos astrológicos."""
    async def mock_calculate(*args, **kwargs):
        return {
            "sun_sign": "Capricornio",
            "moon_sign": "Libra",
            "rising_sign": "Géminis",
            "dominant_element": "Tierra",
            "dominant_modality": "Cardinal",
            "planets": {
                "sun": {"sign": "Capricornio", "longitude": 280.5, "retrograde": False},
                "moon": {"sign": "Libra", "longitude": 190.3, "retrograde": False},
                "mercury": {"sign": "Capricornio", "longitude": 275.2, "retrograde": False},
                "venus": {"sign": "Acuario", "longitude": 315.8, "retrograde": False},
                "mars": {"sign": "Escorpio", "longitude": 225.1, "retrograde": False}
            },
            "houses": {
                "system": "placidus",
                "houses": {
                    "1": {"cusp": 65.2, "sign": "Géminis"},
                    "10": {"cusp": 350.4, "sign": "Piscis"}
                }
            },
            "aspects": [
                {"planet1": "sun", "planet2": "moon", "aspect_type": "cuadratura", "orb": 2.5}
            ]
        }
    
    from app.services.astrology import calculations
    monkeypatch.setattr(calculations, "calculate_chart", mock_calculate)
    
    return mock_calculate


# Fixture para mocks de Claude AI
@pytest.fixture
def mock_claude_api(monkeypatch):
    """Mock para respuestas de Claude AI."""
    async def mock_generate_prediction(*args, **kwargs):
        return {
            "summary": "Esta es una predicción de prueba generada por el mock.",
            "key_transits": ["Tránsito 1", "Tránsito 2"],
            "opportunities": ["Oportunidad 1", "Oportunidad 2"],
            "challenges": ["Desafío 1", "Desafío 2"],
            "recommendations": ["Recomendación 1", "Recomendación 2"],
            "focus_areas": {
                "career": "Interpretación para carrera",
                "relationships": "Interpretación para relaciones"
            }
        }
    
    async def mock_enhance_compatibility(*args, **kwargs):
        return {
            "summary": "Este es un análisis de compatibilidad de prueba generado por el mock.",
            "strengths": ["Fortaleza 1", "Fortaleza 2"],
            "challenges": ["Desafío 1", "Desafío 2"],
            "dynamics": "Dinámica de relación de prueba",
            "recommendations": ["Recomendación 1", "Recomendación 2"]
        }
    
    from app.services import claude_api
    monkeypatch.setattr(claude_api, "generate_prediction_with_claude", mock_generate_prediction)
    monkeypatch.setattr(claude_api, "enhance_compatibility_with_claude", mock_enhance_compatibility)
    
    return {
        "generate_prediction": mock_generate_prediction,
        "enhance_compatibility": mock_enhance_compatibility
    }


# Fixture para mock de Supabase
@pytest.fixture
def mock_supabase(monkeypatch):
    """Mock para Supabase."""
    class MockResponse:
        def __init__(self, data=None, count=None):
            self.data = data or []
            self.count = count

    class MockSupabaseTable:
        def __init__(self, table_name):
            self.table_name = table_name
            self.query_chain = []
            self.test_data = {
                "usuarios": [
                    {
                        "id": "test-user-id",
                        "email": "test@example.com",
                        "nombre": "Usuario de Prueba",
                        "fecha_nacimiento": "1990-01-01",
                        "hora_nacimiento": "12:00:00",
                        "lugar_nacimiento_lat": 40.416775,
                        "lugar_nacimiento_lng": -3.703790,
                        "lugar_nacimiento_nombre": "Madrid",
                        "fecha_registro": datetime.now().isoformat(),
                        "is_active": True,
                        "is_admin": False
                    }
                ],
                "consultas": []
            }
        
        def select(self, *args):
            self.query_chain.append(("select", args))
            return self
            
        def insert(self, data):
            self.query_chain.append(("insert", data))
            return self
            
        def update(self, data):
            self.query_chain.append(("update", data))
            return self
            
        def delete(self):
            self.query_chain.append(("delete",))
            return self
            
        def eq(self, column, value):
            self.query_chain.append(("eq", column, value))
            return self
            
        def neq(self, column, value):
            self.query_chain.append(("neq", column, value))
            return self
            
        def gt(self, column, value):
            self.query_chain.append(("gt", column, value))
            return self
            
        def lt(self, column, value):
            self.query_chain.append(("lt", column, value))
            return self
            
        def gte(self, column, value):
            self.query_chain.append(("gte", column, value))
            return self
            
        def lte(self, column, value):
            self.query_chain.append(("lte", column, value))
            return self
            
        def like(self, column, value):
            self.query_chain.append(("like", column, value))
            return self
            
        def ilike(self, column, value):
            self.query_chain.append(("ilike", column, value))
            return self
            
        def in_(self, column, values):
            self.query_chain.append(("in", column, values))
            return self
            
        def order(self, column, desc=False):
            self.query_chain.append(("order", column, desc))
            return self
            
        def limit(self, limit_val):
            self.query_chain.append(("limit", limit_val))
            return self
            
        def range(self, start, end):
            self.query_chain.append(("range", start, end))
            return self
            
        def execute(self):
            # Simular comportamiento basado en las operaciones encadenadas
            # Aquí simplificamos retornando datos de prueba
            if self.table_name == "usuarios" and ("select",) in self.query_chain:
                for op in self.query_chain:
                    if op[0] == "eq" and op[1] == "email" and op[2] == "test@example.com":
                        return MockResponse(data=self.test_data["usuarios"])
            
            # Para inserciones, devolver datos simulados con ID
            if ("insert",) in self.query_chain:
                data = next((op[1] for op in self.query_chain if op[0] == "insert"), {})
                if isinstance(data, dict):
                    if "id" not in data:
                        data["id"] = f"test-id-{datetime.now().timestamp()}"
                    return MockResponse(data=[data])
                elif isinstance(data, list) and data:
                    for item in data:
                        if "id" not in item:
                            item["id"] = f"test-id-{datetime.now().timestamp()}"
                    return MockResponse(data=data)
            
            # Por defecto devolver una respuesta vacía
            return MockResponse(data=[])

    class MockSupabaseAuth:
        def sign_up(self, credentials):
            # Simular registro de usuario
            class User:
                def __init__(self):
                    self.id = f"test-auth-id-{datetime.now().timestamp()}"
                    self.email = credentials.get("email", "test@example.com")
            
            class AuthResponse:
                def __init__(self):
                    self.user = User()
            
            return AuthResponse()

    class MockSupabaseClient:
        def __init__(self):
            self.auth = MockSupabaseAuth()
        
        def table(self, name):
            return MockSupabaseTable(name)

    # Reemplazar la función get_supabase
    from app.db.supabase import get_supabase
    monkeypatch.setattr("app.db.supabase.get_supabase", lambda: MockSupabaseClient())
    
    return MockSupabaseClient()


# Configuración para limpiar después de las pruebas
@pytest.fixture(autouse=True)
def cleanup():
    """Limpia recursos después de cada prueba."""
    yield
    # Aquí podríamos implementar limpieza si fuera necesario
    pass