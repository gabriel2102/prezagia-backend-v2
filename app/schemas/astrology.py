"""
Esquemas para cartas astrales, predicciones y análisis de compatibilidad en la aplicación Prezagia.

Este módulo define los modelos de datos relacionados con los cálculos e interpretaciones astrológicas.
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Union, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator

from app.schemas.schema_base import BaseResponseModel


# Enumeraciones
class ChartType(str, Enum):
    """Tipos de cartas astrales."""
    NATAL = "natal"
    TRANSIT = "transit"
    PROGRESSION = "progression"
    SOLAR_RETURN = "solar_return"
    LUNAR_RETURN = "lunar_return"
    COMPOSITE = "composite"
    SYNASTRY = "synastry"


class PredictionType(str, Enum):
    """Tipos de predicciones astrológicas."""
    GENERAL = "general"
    CAREER = "career"
    LOVE = "love"
    HEALTH = "health"
    MONEY = "money"
    PERSONAL_GROWTH = "personal_growth"
    SPIRITUALITY = "spirituality"


class PredictionPeriod(str, Enum):
    """Períodos para predicciones."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    CUSTOM = "custom"


class CompatibilityType(str, Enum):
    """Tipos de análisis de compatibilidad."""
    ROMANTIC = "romantic"
    FRIENDSHIP = "friendship"
    PROFESSIONAL = "professional"
    FAMILY = "family"
    GENERAL = "general"


# Esquemas para cartas astrales
class ChartBase(BaseModel):
    """Modelo base para cartas astrales."""
    chart_type: ChartType = Field(..., description="Tipo de carta astral")
    name: Optional[str] = Field(None, description="Nombre asignado a la carta astral")
    description: Optional[str] = Field(None, description="Descripción de la carta astral")
    interpretation_depth: int = Field(3, ge=1, le=5, description="Profundidad de interpretación (1-5)")


class ChartCreate(ChartBase):
    """Modelo para crear una nueva carta astral."""
    birth_date: date = Field(..., description="Fecha de nacimiento")
    birth_time: time = Field(..., description="Hora de nacimiento")
    latitude: float = Field(..., ge=-90, le=90, description="Latitud del lugar")
    longitude: float = Field(..., ge=-180, le=180, description="Longitud del lugar")
    location_name: Optional[str] = Field(None, description="Nombre del lugar")
    
    # Para cartas que requieren una segunda fecha (retornos, progresiones, etc.)
    secondary_date: Optional[date] = Field(None, description="Fecha secundaria (para retornos, tránsitos, etc.)")
    
    # Para cartas que involucran a dos personas (sinastría, carta compuesta)
    person2_birth_date: Optional[date] = Field(None, description="Fecha de nacimiento de la segunda persona")
    person2_birth_time: Optional[time] = Field(None, description="Hora de nacimiento de la segunda persona")
    person2_latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitud del lugar de la segunda persona")
    person2_longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitud del lugar de la segunda persona")
    person2_location_name: Optional[str] = Field(None, description="Nombre del lugar de la segunda persona")
    
    @root_validator
    def validate_chart_requirements(cls, values):
        """Validar que los campos requeridos estén presentes según el tipo de carta."""
        chart_type = values.get('chart_type')
        
        # Verificar campos requeridos para cartas que necesitan una fecha secundaria
        if chart_type in [ChartType.TRANSIT, ChartType.PROGRESSION, ChartType.SOLAR_RETURN, ChartType.LUNAR_RETURN]:
            if not values.get('secondary_date'):
                raise ValueError(f"El tipo de carta {chart_type} requiere una fecha secundaria")
        
        # Verificar campos requeridos para cartas que involucran a dos personas
        if chart_type in [ChartType.SYNASTRY, ChartType.COMPOSITE]:
            required_fields = ['person2_birth_date', 'person2_birth_time', 'person2_latitude', 'person2_longitude']
            missing_fields = [field for field in required_fields if not values.get(field)]
            
            if missing_fields:
                raise ValueError(f"El tipo de carta {chart_type} requiere los siguientes campos: {', '.join(missing_fields)}")
        
        return values


class ChartFilter(BaseModel):
    """Modelo para filtrar cartas astrales."""
    chart_type: Optional[ChartType] = None
    name: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class ChartResponse(BaseResponseModel):
    """Modelo para respuestas básicas de cartas astrales."""
    user_id: str
    chart_type: ChartType
    name: Optional[str]
    description: Optional[str]
    interpretation_depth: int
    created_at: datetime
    
    # Datos básicos calculados
    sun_sign: str
    moon_sign: str
    rising_sign: Optional[str]
    
    # Resumen
    summary: Optional[str]
    
    class Config:
        orm_mode = True


class ChartDetail(ChartResponse):
    """Modelo para detalles completos de una carta astral."""
    birth_date: date
    birth_time: time
    latitude: float
    longitude: float
    location_name: Optional[str]
    
    # Datos secundarios (si aplica)
    secondary_date: Optional[date]
    person2_birth_date: Optional[date]
    person2_birth_time: Optional[time]
    person2_latitude: Optional[float]
    person2_longitude: Optional[float]
    person2_location_name: Optional[str]
    
    # Resultado del cálculo
    calculation_result: Dict[str, Any]
    
    # Interpretación completa
    interpretation: Dict[str, Any]
    
    class Config:
        orm_mode = True


# Esquemas para predicciones
class PredictionBase(BaseModel):
    """Modelo base para predicciones astrológicas."""
    prediction_type: PredictionType = Field(..., description="Tipo de predicción")
    prediction_period: PredictionPeriod = Field(..., description="Período de la predicción")
    name: Optional[str] = Field(None, description="Nombre asignado a la predicción")
    description: Optional[str] = Field(None, description="Descripción de la predicción")
    focus_areas: List[str] = Field(default_factory=list, description="Áreas de enfoque específicas")


class PredictionCreate(PredictionBase):
    """Modelo para crear una nueva predicción."""
    birth_date: date = Field(..., description="Fecha de nacimiento")
    birth_time: time = Field(..., description="Hora de nacimiento")
    birth_latitude: float = Field(..., ge=-90, le=90, description="Latitud del lugar de nacimiento")
    birth_longitude: float = Field(..., ge=-180, le=180, description="Longitud del lugar de nacimiento")
    birth_location_name: Optional[str] = Field(None, description="Nombre del lugar de nacimiento")
    
    prediction_date: date = Field(..., description="Fecha para la predicción")
    
    # Período personalizado (opcional)
    end_date: Optional[date] = Field(None, description="Fecha de fin para período personalizado")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validar que la fecha de fin sea posterior a la fecha de predicción."""
        if v and 'prediction_date' in values and v <= values['prediction_date']:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de predicción")
        return v
    
    @root_validator
    def validate_custom_period(cls, values):
        """Validar que para períodos personalizados se proporcione una fecha de fin."""
        if values.get('prediction_period') == PredictionPeriod.CUSTOM and not values.get('end_date'):
            raise ValueError("Para predicciones con período personalizado, debe proporcionar una fecha de fin")
        return values


class PredictionFilter(BaseModel):
    """Modelo para filtrar predicciones."""
    prediction_type: Optional[PredictionType] = None
    period: Optional[PredictionPeriod] = None
    name: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None


class PredictionResponse(BaseResponseModel):
    """Modelo para respuestas básicas de predicciones."""
    user_id: str
    prediction_type: PredictionType
    prediction_period: PredictionPeriod
    name: Optional[str]
    description: Optional[str]
    prediction_date: date
    end_date: Optional[date]
    focus_areas: List[str]
    created_at: datetime
    
    # Resumen
    summary: str
    
    class Config:
        orm_mode = True


class PredictionDetail(PredictionResponse):
    """Modelo para detalles completos de una predicción."""
    birth_date: date
    birth_time: time
    birth_latitude: float
    birth_longitude: float
    birth_location_name: Optional[str]
    
    # Datos calculados
    transits: Dict[str, Any]
    
    # Interpretación básica
    interpretation: Dict[str, Any]
    
    # Interpretación mejorada con Claude
    enhanced_prediction: Dict[str, Any]
    
    class Config:
        orm_mode = True


# Esquemas para análisis de compatibilidad
class CompatibilityBase(BaseModel):
    """Modelo base para análisis de compatibilidad."""
    compatibility_type: CompatibilityType = Field(..., description="Tipo de compatibilidad")
    name: Optional[str] = Field(None, description="Nombre asignado al análisis")
    description: Optional[str] = Field(None, description="Descripción del análisis")
    focus_areas: List[str] = Field(default_factory=list, description="Áreas de enfoque específicas")


class CompatibilityCreate(CompatibilityBase):
    """Modelo para crear un nuevo análisis de compatibilidad."""
    person1_name: str = Field(..., description="Nombre de la primera persona")
    person1_birth_date: date = Field(..., description="Fecha de nacimiento de la primera persona")
    person1_birth_time: time = Field(..., description="Hora de nacimiento de la primera persona")
    person1_latitude: float = Field(..., ge=-90, le=90, description="Latitud del lugar de nacimiento de la primera persona")
    person1_longitude: float = Field(..., ge=-180, le=180, description="Longitud del lugar de nacimiento de la primera persona")
    person1_location_name: Optional[str] = Field(None, description="Nombre del lugar de nacimiento de la primera persona")
    
    person2_name: str = Field(..., description="Nombre de la segunda persona")
    person2_birth_date: date = Field(..., description="Fecha de nacimiento de la segunda persona")
    person2_birth_time: time = Field(..., description="Hora de nacimiento de la segunda persona")
    person2_latitude: float = Field(..., ge=-90, le=90, description="Latitud del lugar de nacimiento de la segunda persona")
    person2_longitude: float = Field(..., ge=-180, le=180, description="Longitud del lugar de nacimiento de la segunda persona")
    person2_location_name: Optional[str] = Field(None, description="Nombre del lugar de nacimiento de la segunda persona")


class CompatibilityFilter(BaseModel):
    """Modelo para filtrar análisis de compatibilidad."""
    compatibility_type: Optional[CompatibilityType] = None
    name: Optional[str] = None
    person1_name: Optional[str] = None
    person2_name: Optional[str] = None


class CompatibilityResponse(BaseResponseModel):
    """Modelo para respuestas básicas de análisis de compatibilidad."""
    user_id: str
    compatibility_type: CompatibilityType
    name: Optional[str]
    description: Optional[str]
    person1_name: str
    person2_name: str
    focus_areas: List[str]
    created_at: datetime
    
    # Resumen y puntuación
    compatibility_score: float = Field(..., ge=0, le=100, description="Puntuación de compatibilidad (0-100)")
    summary: str
    
    class Config:
        orm_mode = True


class CompatibilityDetail(CompatibilityResponse):
    """Modelo para detalles completos de un análisis de compatibilidad."""
    person1_birth_date: date
    person1_birth_time: time
    person1_latitude: float
    person1_longitude: float
    person1_location_name: Optional[str]
    
    person2_birth_date: date
    person2_birth_time: time
    person2_latitude: float
    person2_longitude: float
    person2_location_name: Optional[str]
    
    # Resultado del cálculo
    calculation_result: Dict[str, Any]
    
    # Interpretación básica
    interpretation: Dict[str, Any]
    
    # Interpretación mejorada con Claude
    enhanced_interpretation: Dict[str, Any]
    
    class Config:
        orm_mode = True


# Modelos adicionales para elementos astrológicos

class Planet(BaseModel):
    """Datos de posición de un planeta en una carta astral."""
    name: str
    sign: str
    degree: float
    house: Optional[int]
    retrograde: bool = False
    speed: float
    
    # Coordenadas
    longitude: float
    latitude: Optional[float]
    declination: Optional[float]
    
    # Información adicional específica de planetas
    dignity: Optional[str] = None
    debility: Optional[str] = None
    
    # Posición especial (ej: "Cazimi", "Combust", "Under the Sun's beams")
    special_position: Optional[str] = None


class Aspect(BaseModel):
    """Aspecto entre dos planetas o puntos de una carta astral."""
    aspect_type: str  # Conjunción, oposición, trígono, cuadratura, sextil, etc.
    planet1: str
    planet2: str
    orb: float
    exact: bool
    applying: bool = False
    separating: bool = False
    nature: Optional[str] = None  # Benéfico, maléfico, neutro
    power: Optional[float] = None  # Fuerza del aspecto (0-10)
    description: Optional[str] = None


class House(BaseModel):
    """Casa astrológica en una carta astral."""
    number: int
    sign: str
    degree_start: float
    degree_end: float
    cusp: float
    planets: List[str] = Field(default_factory=list)
    ruler: str
    co_ruler: Optional[str] = None
    description: Optional[str] = None