"""
Módulo de esquemas Pydantic para validación de datos en Prezagia.
"""

from app.schemas.schema_base import BaseResponseModel, DateTimeModelMixin, IDModelMixin
from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserLogin, TokenResponse
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.schemas.query import QueryCreate, QueryResponse, QueryUpdate, QueryFilter, QueryDetail
from app.schemas.configuration import ConfigurationCreate, ConfigurationResponse, ConfigurationUpdate
from app.schemas.astrology import (
    ChartType, PredictionType, PredictionPeriod, CompatibilityType,
    ChartCreate, ChartResponse, ChartDetail, ChartFilter,
    PredictionCreate, PredictionResponse, PredictionDetail, PredictionFilter,
    CompatibilityCreate, CompatibilityResponse, CompatibilityDetail, CompatibilityFilter
)