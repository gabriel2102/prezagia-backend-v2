"""
Pruebas unitarias para el módulo de interpretaciones astrológicas de Prezagia.
"""
import pytest
import asyncio
from datetime import datetime, date, time
from app.schemas.astrology import (
    ChartType, 
    PredictionType, 
    PredictionPeriod, 
    CompatibilityType
)
from app.services.astrology.interpretation import (
    interpret_chart,
    interpret_prediction,
    interpret_compatibility
)


# Datos de muestra para las pruebas
SAMPLE_CHART_CALCULATION = {
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

SAMPLE_TRANSITS = {
    "natal_chart": SAMPLE_CHART_CALCULATION,
    "prediction_period": "month",
    "start_date": "2023-01-01",
    "end_date": "2023-02-01",
    "transit_positions_start": {
        "jupiter": {"sign": "Aries", "longitude": 5.2, "retrograde": False},
        "saturn": {"sign": "Acuario", "longitude": 315.8, "retrograde": False}
    },
    "significant_transits": [
        {
            "transit_planet": "jupiter",
            "natal_planet": "sun",
            "aspect_type": "trígono",
            "orb": 1.2
        }
    ]
}

SAMPLE_COMPATIBILITY_CALCULATION = {
    "chart1": SAMPLE_CHART_CALCULATION,
    "chart2": {
        "sun_sign": "Tauro", 
        "moon_sign": "Cáncer",
        "rising_sign": "Leo"
    },
    "synastry_aspects": [
        {
            "planet1": "sun",
            "planet2": "moon",
            "aspect_type": "sextil",
            "orb": 1.5
        }
    ],
    "compatibility_score": 75.5,
    "strengths": [
        "Comunicación fluida", 
        "Compatibilidad emocional"
    ],
    "challenges": [
        "Posibles conflictos de autonomía",
        "Diferencias en valores materiales"
    ]
}


@pytest.mark.asyncio
async def test_interpret_chart():
    """Prueba la función para interpretar una carta astral."""
    chart_type = ChartType.NATAL
    interpretation_depth = 3
    
    try:
        interpretation = await interpret_chart(
            chart_calculation=SAMPLE_CHART_CALCULATION,
            chart_type=chart_type,
            interpretation_depth=interpretation_depth
        )
        
        # Verificar que la respuesta contiene los campos esperados
        assert "summary" in interpretation
        assert "personality" in interpretation
        assert "strengths" in interpretation
        assert "challenges" in interpretation
        assert "planets" in interpretation
        assert "houses" in interpretation
        assert "aspects" in interpretation
        assert "recommendations" in interpretation
        
        # Verificar que hay interpretaciones para los planetas principales
        planet_interpretations = interpretation["planets"]
        assert "sun" in planet_interpretations
        assert "moon" in planet_interpretations
        assert "ascendant" in planet_interpretations
        
        # Verificar que la profundidad de interpretación afecta al volumen de contenido
        assert len(interpretation["summary"]) > 20  # Debe tener un resumen mínimo
        assert len(interpretation["strengths"]) >= 2  # Al menos dos fortalezas
        assert len(interpretation["challenges"]) >= 2  # Al menos dos desafíos
        
    except Exception as e:
        pytest.fail(f"La función interpret_chart falló con el error: {str(e)}")


@pytest.mark.asyncio
async def test_interpret_prediction():
    """Prueba la función para interpretar una predicción astrológica."""
    prediction_type = PredictionType.GENERAL
    prediction_period = PredictionPeriod.MONTH
    
    try:
        interpretation = await interpret_prediction(
            transits=SAMPLE_TRANSITS,
            prediction_type=prediction_type,
            prediction_period=prediction_period
        )
        
        # Verificar que la respuesta contiene los campos esperados
        assert "summary" in interpretation
        assert "transit_interpretations" in interpretation
        assert "period_themes" in interpretation
        assert "opportunities" in interpretation
        assert "challenges" in interpretation
        assert "recommendations" in interpretation
        
        # Verificar que hay interpretaciones para los tránsitos significativos
        transit_interpretations = interpretation["transit_interpretations"]
        assert len(transit_interpretations) > 0
        
        # Verificar que la interpretación incluye temas para el período
        assert len(interpretation["period_themes"]) > 0
        
        # Verificar que hay oportunidades y desafíos
        assert len(interpretation["opportunities"]) > 0
        assert len(interpretation["challenges"]) > 0
        
        # Verificar que hay recomendaciones
        assert len(interpretation["recommendations"]) > 0
        
    except Exception as e:
        pytest.fail(f"La función interpret_prediction falló con el error: {str(e)}")


@pytest.mark.asyncio
async def test_interpret_compatibility():
    """Prueba la función para interpretar compatibilidad astrológica."""
    compatibility_type = CompatibilityType.ROMANTIC
    focus_areas = ["communication", "intimacy"]
    
    try:
        interpretation = await interpret_compatibility(
            compatibility_calculation=SAMPLE_COMPATIBILITY_CALCULATION,
            compatibility_type=compatibility_type,
            focus_areas=focus_areas
        )
        
        # Verificar que la respuesta contiene los campos esperados
        assert "summary" in interpretation
        assert "compatibilities" in interpretation
        assert "strengths" in interpretation
        assert "challenges" in interpretation
        assert "dynamics" in interpretation
        assert "recommendations" in interpretation
        
        # Verificar que las áreas de enfoque están presentes
        assert "focus_areas" in interpretation
        focus_area_interpretations = interpretation["focus_areas"]
        assert "communication" in focus_area_interpretations
        assert "intimacy" in focus_area_interpretations
        
        # Verificar que hay fortalezas y desafíos
        assert len(interpretation["strengths"]) > 0
        assert len(interpretation["challenges"]) > 0
        
        # Verificar que hay una dinámica de relación
        assert len(interpretation["dynamics"]) > 0
        
        # Verificar que hay recomendaciones
        assert len(interpretation["recommendations"]) > 0
        
    except Exception as e:
        pytest.fail(f"La función interpret_compatibility falló con el error: {str(e)}")


@pytest.mark.asyncio
async def test_interpret_chart_different_depths():
    """Prueba la interpretación de cartas con diferentes profundidades."""
    chart_type = ChartType.NATAL
    
    try:
        # Interpretación básica (profundidad 1)
        basic_interp = await interpret_chart(
            chart_calculation=SAMPLE_CHART_CALCULATION,
            chart_type=chart_type,
            interpretation_depth=1
        )
        
        # Interpretación detallada (profundidad 5)
        detailed_interp = await interpret_chart(
            chart_calculation=SAMPLE_CHART_CALCULATION,
            chart_type=chart_type,
            interpretation_depth=5
        )
        
        # La interpretación detallada debe tener más contenido
        assert len(str(detailed_interp)) > len(str(basic_interp))
        
        # La interpretación detallada debe tener más fortalezas y desafíos
        assert len(detailed_interp["strengths"]) >= len(basic_interp["strengths"])
        assert len(detailed_interp["challenges"]) >= len(basic_interp["challenges"])
        
        # La interpretación detallada debe tener más recomendaciones
        assert len(detailed_interp["recommendations"]) >= len(basic_interp["recommendations"])
        
    except Exception as e:
        pytest.fail(f"La prueba de profundidades de interpretación falló con el error: {str(e)}")