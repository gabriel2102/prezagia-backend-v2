"""
Pruebas para los endpoints de predicciones astrológicas de la API de Prezagia.
"""
import pytest
from fastapi.testclient import TestClient


def test_create_prediction(client, auth_token, test_data, mock_chart_calculation, mock_claude_api):
    """Prueba la creación de una predicción astrológica."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.post("/api/predictions", json=test_data["prediction"], headers=headers)
    
    assert response.status_code == 201
    assert "id" in response.json()
    assert "prediction_type" in response.json()
    assert "prediction_period" in response.json()
    assert "name" in response.json()
    assert "summary" in response.json()
    
    # Guardar el ID para pruebas posteriores
    test_data["prediction_id"] = response.json()["id"]


def test_create_prediction_unauthorized(client, test_data):
    """Prueba que no se puede crear una predicción sin autenticación."""
    response = client.post("/api/predictions", json=test_data["prediction"])
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_get_prediction_by_id(client, auth_token, test_data):
    """Prueba la obtención de una predicción por ID."""
    # Primero crear una predicción si no existe
    if "prediction_id" not in test_data:
        test_create_prediction(client, auth_token, test_data, None, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get(f"/api/predictions/{test_data['prediction_id']}", headers=headers)
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == test_data["prediction_id"]
    assert "prediction_type" in response.json()
    assert "transits" in response.json()
    assert "interpretation" in response.json()
    assert "enhanced_prediction" in response.json()


def test_get_nonexistent_prediction(client, auth_token):
    """Prueba la obtención de una predicción que no existe."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get("/api/predictions/nonexistent-id", headers=headers)
    
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "no encontrada" in response.json()["detail"].lower()


def test_get_user_predictions(client, auth_token, test_data):
    """Prueba la obtención de todas las predicciones de un usuario."""
    # Primero crear una predicción si no existe
    if "prediction_id" not in test_data:
        test_create_prediction(client, auth_token, test_data, None, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.get("/api/predictions", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Debe haber al menos una predicción (la que acabamos de crear)
    assert len(response.json()) >= 1
    
    # Verificar que la predicción creada está en la lista
    prediction_ids = [prediction["id"] for prediction in response.json()]
    assert test_data["prediction_id"] in prediction_ids


def test_get_user_predictions_with_filters(client, auth_token, test_data):
    """Prueba la obtención de predicciones con filtros."""
    # Primero crear una predicción si no existe
    if "prediction_id" not in test_data:
        test_create_prediction(client, auth_token, test_data, None, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Filtrar por tipo de predicción
    response = client.get("/api/predictions?prediction_type=general", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(prediction["prediction_type"] == "general" for prediction in response.json())
    
    # Filtrar por período
    response = client.get("/api/predictions?period=month", headers=headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert all(prediction["prediction_period"] == "month" for prediction in response.json())


def test_refine_prediction(client, auth_token, test_data, mock_claude_api):
    """Prueba el refinamiento de una predicción."""
    # Primero crear una predicción si no existe
    if "prediction_id" not in test_data:
        test_create_prediction(client, auth_token, test_data, None, None)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    focus_areas = ["health", "spirituality"]
    
    response = client.post(
        f"/api/predictions/{test_data['prediction_id']}/refine",
        json=focus_areas,
        headers=headers
    )
    
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["id"] == test_data["prediction_id"]
    assert "enhanced_prediction" in response.json()
    
    # Verificar que las áreas de enfoque están en la respuesta
    assert "focus_areas" in response.json()["enhanced_prediction"]


def test_delete_prediction(client, auth_token, test_data):
    """Prueba la eliminación de una predicción."""
    # Primero crear una predicción específica para eliminar
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Crear una nueva predicción para eliminar
    create_response = client.post("/api/predictions", json=test_data["prediction"], headers=headers)
    assert create_response.status_code == 201
    prediction_id_to_delete = create_response.json()["id"]
    
    # Eliminar la predicción
    delete_response = client.delete(f"/api/predictions/{prediction_id_to_delete}", headers=headers)
    
    assert delete_response.status_code == 204
    
    # Verificar que la predicción ya no existe
    get_response = client.get(f"/api/predictions/{prediction_id_to_delete}", headers=headers)
    assert get_response.status_code == 404


def test_delete_nonexistent_prediction(client, auth_token):
    """Prueba la eliminación de una predicción que no existe."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = client.delete("/api/predictions/nonexistent-id", headers=headers)
    
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "no encontrada" in response.json()["detail"].lower()