"""
Esquemas para consultas astrológicas en la aplicación Prezagia.

Este módulo define los modelos de datos relacionados con las consultas
que realizan los usuarios (historial de búsquedas, etc.)
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

from app.schemas.schema_base import BaseResponseModel


class QueryBase(BaseModel):
    """Modelo base para consultas guardadas."""
    user_id: str = Field(..., description="ID del usuario que realiza la consulta")
    query_type: str = Field(..., description="Tipo de consulta")
    query_name: Optional[str] = Field(None, description="Nombre asignado a la consulta")
    query_description: Optional[str] = Field(None, description="Descripción de la consulta")
    is_favorite: bool = Field(False, description="Indica si la consulta está marcada como favorita")


class QueryCreate(QueryBase):
    """Modelo para crear una nueva consulta."""
    query_data: Dict[str, Any] = Field(..., description="Datos específicos de la consulta")
    result_summary: Optional[str] = Field(None, description="Resumen del resultado de la consulta")


class QueryUpdate(BaseModel):
    """Modelo para actualizar una consulta existente."""
    query_name: Optional[str] = None
    query_description: Optional[str] = None
    is_favorite: Optional[bool] = None
    result_summary: Optional[str] = None


class QueryResponse(BaseResponseModel, QueryBase):
    """Modelo para respuestas de consultas."""
    query_date: datetime = Field(..., description="Fecha y hora de la consulta")
    result_summary: Optional[str] = None
    
    class Config:
        orm_mode = True


class QueryFilter(BaseModel):
    """Modelo para filtrar consultas."""
    query_type: Optional[str] = None
    query_name: Optional[str] = None
    is_favorite: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class QueryDetail(QueryResponse):
    """Modelo para detalles completos de una consulta."""
    query_data: Dict[str, Any] = Field(..., description="Datos específicos de la consulta")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Datos completos del resultado")
    
    class Config:
        orm_mode = True