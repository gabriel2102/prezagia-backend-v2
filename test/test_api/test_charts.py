"""
Pruebas para los endpoints de cartas astrales de la API de Prezagia.
"""
import pytest
from fastapi.testclient import TestClient


def test_create_chart(client, auth_token, test_data, mock_chart_calculation):
    """Prueba la creación de una carta astral."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.post("/api/charts", json=test_data["chart"], headers=headers)
    
    assert response.status_code == 201
    assert "id" in response.json()
    assert "chart_type" in response.json()
    assert "name" in response.json()
    assert "sun_sign" in response.json()
    assert "moon_sign" in response.json()
    assert "rising_sign" in response.json()
    
    # Guardar el ID para pruebas posteriores
    test_data["chart_id"] = response.json()["id"]


def test_create_chart_unauthorized(client, test_data):
    """Prueba que no se puede crear una carta sin autenticación."""
    response = client.post("/api/charts", json=test_data["chart"])
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_chart_by_id(client, auth_token, test_data):
    """Prueba la obtención de una carta astral por ID."""
    # Primero crear una carta si no existe
    if "chart_id" not in test_data:
        test_create_chart(client, auth_token, test_data, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get(f"/api/charts/{test_data['chart_id']}", headers=headers)
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == test_data["chart_id"]
    assert "chart_type" in response.json()
    assert "calculation_result" in response.json()
    assert "interpretation" in response.json()


def test_get_nonexistent_chart(client, auth_token):
    """Prueba la obtención de una carta que no existe."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get("/api/charts/nonexistent-id", headers=headers)
    
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "no encontrada" in response.json()["detail"].lower()


def test_get_user_charts(client, auth_token, test_data):
    """Prueba la obtención de todas las cartas de un usuario."""
    # Primero crear una carta si no existe
    if "chart_id" not in test_data:
        test_create_chart(client, auth_token, test_data, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get("/api/charts", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Debe haber al menos una carta (la que acabamos de crear)
    assert len(response.json()) >= 1
    
    # Verificar que la carta creada está en la lista
    chart_ids = [chart["id"] for chart in response.json()]
    assert test_data["chart_id"] in chart_ids


def test_get_user_charts_with_filters(client, auth_token, test_data):
    """Prueba la obtención de cartas con filtros."""
    # Primero crear una carta si no existe
    if "chart_id" not in test_data:
        test_create_chart(client, auth_token, test_data, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Filtrar por tipo de carta
    response = client.get("/api/charts?chart_type=natal", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(chart["chart_type"] == "natal" for chart in response.json())
    
    # Filtrar por nombre (parcial)
    partial_name = test_data["chart"]["name"][:10]
    response = client.get(f"/api/charts?name={partial_name}", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Al menos una carta debe contener el nombre parcial
    assert any(partial_name in chart["name"] for chart in response.json())


def test_reinterpret_chart(client, auth_token, test_data):
    """Prueba la reinterpretación de una carta astral."""
    # Primero crear una carta si no existe
    if "chart_id" not in test_data:
        test_create_chart(client, auth_token, test_data, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.post(
        f"/api/charts/{test_data['chart_id']}/interpret?interpretation_depth=4",
        headers=headers
    )
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == test_data["chart_id"]
    assert "interpretation" in response.json()


def test_delete_chart(client, auth_token, test_data):
    """Prueba la eliminación de una carta astral."""
    # Primero crear una carta específica para eliminar
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Crear una nueva carta para eliminar
    create_response = client.post("/api/charts", json=test_data["chart"], headers=headers)
    assert create_response.status_code == 201
    chart_id_to_delete = create_response.json()["id"]
    
    # Eliminar la carta
    delete_response = client.delete(f"/api/charts/{chart_id_to_delete}", headers=headers)
    
    assert delete_response.status_code == 204
    
    # Verificar que la carta ya no existe
    get_response = client.get(f"/api/charts/{chart_id_to_delete}", headers=headers)
    assert get_response.status_code == 404


def test_delete_nonexistent_chart(client, auth_token):
    """Prueba la eliminación de una carta que no existe."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.delete("/api/charts/nonexistent-id", headers=headers)
    
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "no encontrada" in response.json()["detail"].lower()