"""
Excepciones personalizadas para la aplicación Prezagia.

Este módulo define excepciones específicas que pueden ser utilizadas
en toda la aplicación para manejar diferentes tipos de errores
de manera consistente.
"""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any, List


class PrezagiaException(Exception):
    """Excepción base para todas las excepciones de Prezagia."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DatabaseError(PrezagiaException):
    """Excepción para errores relacionados con la base de datos."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        super().__init__(message)


class ValidationError(PrezagiaException):
    """Excepción para errores de validación de datos."""
    
    def __init__(self, message: str, field: Optional[str] = None, errors: Optional[List[Dict[str, Any]]] = None):
        self.field = field
        self.errors = errors or []
        super().__init__(message)


class AuthenticationError(PrezagiaException):
    """Excepción para errores de autenticación."""
    
    def __init__(self, message: str = "Error de autenticación"):
        super().__init__(message)


class AuthorizationError(PrezagiaException):
    """Excepción para errores de autorización."""
    
    def __init__(self, message: str = "No tiene permisos para realizar esta acción"):
        super().__init__(message)


class ResourceNotFoundError(PrezagiaException):
    """Excepción para recursos no encontrados."""
    
    def __init__(self, resource_type: str, resource_id: Optional[str] = None):
        message = f"{resource_type} no encontrado"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(message)


class ResourceExistsError(PrezagiaException):
    """Excepción para cuando un recurso ya existe."""
    
    def __init__(self, resource_type: str, identifier: Optional[str] = None):
        message = f"{resource_type} ya existe"
        if identifier:
            message += f": {identifier}"
        super().__init__(message)


class CalculationError(PrezagiaException):
    """Excepción para errores en los cálculos astrológicos."""
    
    def __init__(self, message: str, calculation_type: Optional[str] = None):
        self.calculation_type = calculation_type
        error_msg = message
        if calculation_type:
            error_msg = f"Error en cálculo de {calculation_type}: {message}"
        super().__init__(error_msg)


class InterpretationError(PrezagiaException):
    """Excepción para errores en las interpretaciones astrológicas."""
    
    def __init__(self, message: str, interpretation_type: Optional[str] = None):
        self.interpretation_type = interpretation_type
        error_msg = message
        if interpretation_type:
            error_msg = f"Error en interpretación de {interpretation_type}: {message}"
        super().__init__(error_msg)


class ExternalServiceError(PrezagiaException):
    """Excepción para errores en servicios externos (Claude AI, etc)."""
    
    def __init__(self, service_name: str, message: str, status_code: Optional[int] = None):
        self.service_name = service_name
        self.status_code = status_code
        error_msg = f"Error en servicio externo {service_name}: {message}"
        if status_code:
            error_msg += f" (código: {status_code})"
        super().__init__(error_msg)


class RateLimitError(PrezagiaException):
    """Excepción para cuando se excede el límite de consultas."""
    
    def __init__(self, 
                 limit: int, 
                 message: str = "Se ha excedido el límite de consultas diarias", 
                 reset_time: Optional[str] = None):
        self.limit = limit
        self.reset_time = reset_time
        error_msg = message
        if reset_time:
            error_msg += f". El límite se restablecerá en: {reset_time}"
        super().__init__(error_msg)


class ConfigurationError(PrezagiaException):
    """Excepción para errores de configuración."""
    
    def __init__(self, config_name: str, message: str):
        self.config_name = config_name
        error_msg = f"Error de configuración ({config_name}): {message}"
        super().__init__(error_msg)


# Funciones auxiliares para convertir excepciones en respuestas HTTP

def http_exception_handler(exc: PrezagiaException) -> HTTPException:
    """
    Convierte las excepciones de Prezagia en excepciones HTTP de FastAPI.
    
    Args:
        exc: Excepción de Prezagia
        
    Returns:
        HTTPException: Excepción HTTP de FastAPI
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    headers = None
    
    # Asignar códigos de estado HTTP basados en el tipo de excepción
    if isinstance(exc, ResourceNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AuthenticationError):
        status_code = status.HTTP_401_UNAUTHORIZED
        headers = {"WWW-Authenticate": "Bearer"}
    elif isinstance(exc, AuthorizationError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ResourceExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, RateLimitError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        
    # Preparar detalles adicionales para la respuesta
    detail = {"message": exc.message}
    
    # Agregar información específica según el tipo de excepción
    if isinstance(exc, ValidationError) and (exc.errors or exc.field):
        detail["errors"] = exc.errors
        if exc.field:
            detail["field"] = exc.field
    elif isinstance(exc, RateLimitError):
        detail["limit"] = exc.limit
        if exc.reset_time:
            detail["reset_time"] = exc.reset_time
    elif isinstance(exc, ExternalServiceError):
        detail["service"] = exc.service_name
        if exc.status_code:
            detail["service_status_code"] = exc.status_code
            
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=headers
    )