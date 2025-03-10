"""
Módulo core de Prezagia con configuración, excepciones y componentes fundamentales.
"""

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    PrezagiaException,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    ResourceExistsError,
    CalculationError,
    InterpretationError,
    ExternalServiceError,
    RateLimitError,
    ConfigurationError
)