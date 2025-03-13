"""
Pruebas para los endpoints de autenticación de la API de Prezagia.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Prueba que el endpoint de health funciona correctamente."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Prueba que el endpoint raíz devuelve información básica."""
    response = client.get("/")
    assert response.status_code == 200
    assert "app" in response.json()
    assert "status" in response.json()
    assert response.json()["status"] == "online"


def test_register_user(client, test_data):
    """Prueba el registro de un nuevo usuario."""
    # Generar email único para evitar conflictos
    import random
    test_data["user"]["email"] = f"test_register_{random.randint(1000, 9999)}@test.com"
    
    response = client.post("/api/auth/register", json=test_data["user"])
    
    assert response.status_code == 201
    assert "id" in response.json()
    assert "email" in response.json()
    assert response.json()["email"] == test_data["user"]["email"]


def test_register_duplicate_email(client, test_data, auth_token):
    """Prueba que no se puede registrar un email duplicado."""
    # Intentar registrar con el mismo email del fixture auth_token
    response = client.post("/api/auth/register", json=test_data["user"])
    
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "correo electrónico ya está registrado" in response.json()["detail"].lower()


def test_login_success(client, test_data, auth_token):
    """Prueba el inicio de sesión exitoso."""
    login_data = {
        "username": "admin@example.com",
        "password": "hashedpassword"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert "user_id" in response.json()
    assert "email" in response.json()
    assert response.json()["email"] == test_data["user"]["email"]
    
    # Verificar que se establece una cookie para el refresh token
    assert "refresh_token" in response.cookies


def test_login_invalid_credentials(client):
    """Prueba el inicio de sesión con credenciales inválidas."""
    login_data = {
        "username": "invalid@test.com",
        "password": "invalidpassword"
    }
    
    response = client.post("/api/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "credenciales incorrectas" in response.json()["detail"].lower()


def test_get_me(client, auth_token):
    """Prueba la obtención del perfil del usuario autenticado."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get("/api/auth/me", headers=headers)
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert "email" in response.json()
    assert "nombre" in response.json()


def test_get_me_no_token(client):
    """Prueba que no se puede acceder al perfil sin token."""
    response = client.get("/api/auth/me")
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_refresh_token(client, auth_token):
    """Prueba el refresco de token."""
    # Primero necesitamos hacer login para obtener un refresh token en la cookie
    # Extraer email del JWT token (simplified for test)
    from jose import jwt
    from app.core.config import settings
    
    decoded = jwt.decode(auth_token, options={"verify_signature": False})
    email = decoded["sub"]
    
    login_data = {
        "username": email,
        "password": "Password123!"  # Usando la contraseña por defecto de test_data
    }
    
    login_response = client.post("/api/auth/login", data=login_data)
    assert login_response.status_code == 200
    
    # Ahora probar el endpoint de refresh
    refresh_response = client.post("/api/auth/refresh")
    
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()
    assert "refresh_token" in refresh_response.cookies


def test_logout(client, auth_token):
    """Prueba el cierre de sesión."""
    response = client.post("/api/auth/logout")
    
    assert response.status_code == 200
    assert "message" in response.json()
    assert "sesión cerrada" in response.json()["message"].lower()
    
    # Verificar que se elimina la cookie del refresh token
    assert "refresh_token" in response.cookies
    assert response.cookies["refresh_token"] == ""  # Cookie vacía significa eliminada