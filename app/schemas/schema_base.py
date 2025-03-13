"""
Esquemas base para la aplicación Prezagia.

Este módulo define esquemas base reutilizables utilizados por otros modelos.
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class DateTimeModelMixin(BaseModel):
    """Mixin para modelos que incluyen campos de fecha y hora."""
    created_at: Optional[datetime] = Field(default=None, description="Fecha y hora de creación")
    updated_at: Optional[datetime] = Field(default=None, description="Fecha y hora de última actualización")


class IDModelMixin(BaseModel):
    """Mixin para modelos que incluyen un ID."""
    id: Optional[str] = Field(default=None, description="Identificador único")


class BaseResponseModel(IDModelMixin, DateTimeModelMixin):
    """
    Modelo base para todas las respuestas que incluyen id, created_at y updated_at.
    """
    pass