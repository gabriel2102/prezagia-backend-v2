"""
Pruebas unitarias para el módulo de cálculos astrológicos de Prezagia.
"""
import pytest
import asyncio
from datetime import datetime, date, time
from app.services.astrology.calculations import (
    get_zodiac_sign,
    get_sign_element,
    get_sign_modality,
    calculate_chart,
    calculate_transits,
    calculate_compatibility
)
from app.schemas.astrology import ChartType, PredictionPeriod, CompatibilityType


def test_get_zodiac_sign():
    """Prueba la función para obtener el signo zodiacal a partir de una longitud."""
    # Verificar algunos valores conocidos
    assert get_zodiac_sign(0) == "Aries"  # 0° es el inicio de Aries
    assert get_zodiac_sign(45) == "Tauro"  # 45° está en Tauro
    assert get_zodiac_sign(175) == "Virgo"  # 175° está en Virgo
    assert get_zodiac_sign(350) == "Piscis"  # 350° está en Piscis
    
    # Verificar los límites de los signos
    assert get_zodiac_sign(29.9) == "Aries"  # Justo antes del cambio a Tauro
    assert get_zodiac_sign(30) == "Tauro"    # Justo en el cambio a Tauro
    
    # Verificar valores fuera del rango 0-360
    assert get_zodiac_sign(-30) == "Piscis"  # -30° equivale a 330°
    assert get_zodiac_sign(380) == "Aries"   # 380° equivale a 20°


def test_get_sign_element():
    """Prueba la función para obtener el elemento de un signo zodiacal."""
    # Elementos de Fuego
    assert get_sign_element("Aries") == "Fuego"
    assert get_sign_element("Leo") == "Fuego"
    assert get_sign_element("Sagitario") == "Fuego"
    
    # Elementos de Tierra
    assert get_sign_element("Tauro") == "Tierra"
    assert get_sign_element("Virgo") == "Tierra"
    assert get_sign_element("Capricornio") == "Tierra"
    
    # Elementos de Aire
    assert get_sign_element("Géminis") == "Aire"
    assert get_sign_element("Libra") == "Aire"
    assert get_sign_element("Acuario") == "Aire"
    
    # Elementos de Agua
    assert get_sign_element("Cáncer") == "Agua"
    assert get_sign_element("Escorpio") == "Agua"
    assert get_sign_element("Piscis") == "Agua"
    
    # Signo inválido
    assert get_sign_element("InvalidSign") == "Desconocido"


def test_get_sign_modality():
    """Prueba la función para obtener la modalidad de un signo zodiacal."""
    # Modalidad Cardinal
    assert get_sign_modality("Aries") == "Cardinal"
    assert get_sign_modality("Cáncer") == "Cardinal"
    assert get_sign_modality("Libra") == "Cardinal"
    assert get_sign_modality("Capricornio") == "Cardinal"
    
    # Modalidad Fija
    assert get_sign_modality("Tauro") == "Fijo"
    assert get_sign_modality("Leo") == "Fijo"
    assert get_sign_modality("Escorpio") == "Fijo"
    assert get_sign_modality("Acuario") == "Fijo"
    
    # Modalidad Mutable
    assert get_sign_modality("Géminis") == "Mutable"
    assert get_sign_modality("Virgo") == "Mutable"
    assert get_sign_modality("Sagitario") == "Mutable"
    assert get_sign_modality("Piscis") == "Mutable"
    
    # Signo inválido
    assert get_sign_modality("InvalidSign") == "Desconocido"


@pytest.mark.asyncio
async def test_calculate_chart():
    """Prueba la función para calcular una carta astral."""
    # Datos para la prueba
    birth_date = date(1990, 1, 1)
    birth_time = time(12, 0, 0)
    latitude = 40.416775
    longitude = -3.703790
    chart_type = ChartType.NATAL
    
    # Calcular la carta
    try:
        chart_data = await calculate_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            chart_type=chart_type
        )
        
        # Verificar que la respuesta contiene los campos esperados
        assert "type" in chart_data
        assert "date" in chart_data
        assert "time" in chart_data
        assert "planets" in chart_data
        assert "points" in chart_data
        assert "houses" in chart_data
        assert "aspects" in chart_data
        assert "sun_sign" in chart_data
        assert "moon_sign" in chart_data
        assert "rising_sign" in chart_data
        
        # Verificar que los planetas principales están presentes
        assert "sun" in chart_data["planets"]
        assert "moon" in chart_data["planets"]
        assert "mercury" in chart_data["planets"]
        assert "venus" in chart_data["planets"]
        assert "mars" in chart_data["planets"]
        
        # Verificar que los puntos principales están presentes
        assert "ascendant" in chart_data["points"]
        assert "midheaven" in chart_data["points"]
        
        # Verificar el tipo de carta
        assert chart_data["type"] == chart_type
        
    except Exception as e:
        pytest.fail(f"La función calculate_chart falló con el error: {str(e)}")


@pytest.mark.asyncio
async def test_calculate_transits():
    """Prueba la función para calcular tránsitos planetarios."""
    # Datos para la prueba
    birth_date = date(1990, 1, 1)
    birth_time = time(12, 0, 0)
    birth_latitude = 40.416775
    birth_longitude = -3.703790
    prediction_date = date.today()
    prediction_period = PredictionPeriod.MONTH
    
    # Calcular los tránsitos
    try:
        transit_data = await calculate_transits(
            birth_date=birth_date,
            birth_time=birth_time,
            birth_latitude=birth_latitude,
            birth_longitude=birth_longitude,
            prediction_date=prediction_date,
            prediction_period=prediction_period
        )
        
        # Verificar que la respuesta contiene los campos esperados
        assert "natal_chart" in transit_data
        assert "prediction_period" in transit_data
        assert "start_date" in transit_data
        assert "end_date" in transit_data
        assert "transit_positions_start" in transit_data
        assert "transit_positions_end" in transit_data
        assert "transit_aspects" in transit_data
        assert "significant_transits" in transit_data
        
        # Verificar que la carta natal está completa
        natal_chart = transit_data["natal_chart"]
        assert "sun_sign" in natal_chart
        assert "moon_sign" in natal_chart
        assert "rising_sign" in natal_chart
        
        # Verificar que hay planetas en los tránsitos
        transit_positions = transit_data["transit_positions_start"]
        assert "sun" in transit_positions
        assert "moon" in transit_positions
        assert "jupiter" in transit_positions
        assert "saturn" in transit_positions
        
        # Verificar el período de predicción
        assert transit_data["prediction_period"] == prediction_period
        
    except Exception as e:
        pytest.fail(f"La función calculate_transits falló con el error: {str(e)}")


@pytest.mark.asyncio
async def test_calculate_compatibility():
    """Prueba la función para calcular compatibilidad astrológica."""
    # Datos para la prueba
    person1_birth_date = date(1990, 1, 1)
    person1_birth_time = time(12, 0, 0)
    person1_latitude = 40.416775
    person1_longitude = -3.703790
    
    person2_birth_date = date(1992, 5, 15)
    person2_birth_time = time(15, 30, 0)
    person2_latitude = 41.385064
    person2_longitude = 2.173404
    
    compatibility_type = CompatibilityType.ROMANTIC
    
    # Calcular la compatibilidad
    try:
        compatibility_data = await calculate_compatibility(
            person1_birth_date=person1_birth_date,
            person1_birth_time=person1_birth_time,
            person1_latitude=person1_latitude,
            person1_longitude=person1_longitude,
            person2_birth_date=person2_birth_date,
            person2_birth_time=person2_birth_time,
            person2_latitude=person2_latitude,
            person2_longitude=person2_longitude,
            compatibility_type=compatibility_type
        )
        
        # Verificar que la respuesta contiene los campos esperados
        assert "compatibility_type" in compatibility_data
        assert "chart1" in compatibility_data
        assert "chart2" in compatibility_data
        assert "synastry_aspects" in compatibility_data
        assert "composite_chart" in compatibility_data
        assert "compatibility_score" in compatibility_data
        assert "strengths" in compatibility_data
        assert "challenges" in compatibility_data
        
        # Verificar que las cartas individuales están completas
        chart1 = compatibility_data["chart1"]
        chart2 = compatibility_data["chart2"]
        
        assert "sun_sign" in chart1
        assert "moon_sign" in chart1
        assert "rising_sign" in chart1
        
        assert "sun_sign" in chart2
        assert "moon_sign" in chart2
        assert "rising_sign" in chart2
        
        # Verificar que hay aspectos entre las cartas
        assert len(compatibility_data["synastry_aspects"]) > 0
        
        # Verificar que la puntuación de compatibilidad es un número entre 0 y 100
        assert 0 <= compatibility_data["compatibility_score"] <= 100
        
        # Verificar que hay fortalezas y desafíos
        assert isinstance(compatibility_data["strengths"], list)
        assert isinstance(compatibility_data["challenges"], list)
        
        # Verificar el tipo de compatibilidad
        assert compatibility_data["compatibility_type"] == compatibility_type
        
    except Exception as e:
        pytest.fail(f"La función calculate_compatibility falló con el error: {str(e)}")