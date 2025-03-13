"""
Esquemas para configuraciones de usuario en la aplicación Prezagia.

Este módulo define los modelos de datos relacionados con las preferencias
y configuraciones personalizadas de los usuarios.
"""

from datetime import datetime, time
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

from app.schemas.schema_base import BaseResponseModel


class NotificationPreferences(BaseModel):
    """Preferencias de notificaciones."""
    daily_horoscope: bool = Field(True, description="Recibir horóscopo diario")
    important_transits: bool = Field(True, description="Recibir alertas de tránsitos importantes")
    weekly_forecast: bool = Field(True, description="Recibir previsión semanal")
    special_events: bool = Field(True, description="Recibir notificaciones sobre eventos especiales")
    email_notifications: bool = Field(True, description="Recibir notificaciones por email")
    push_notifications: bool = Field(True, description="Recibir notificaciones push")


class DisplayPreferences(BaseModel):
    """Preferencias de visualización."""
    theme: Literal["light", "dark", "auto"] = Field("auto", description="Tema de la interfaz")
    chart_style: Literal["modern", "classic", "minimalist"] = Field("modern", description="Estilo de las cartas astrales")
    language: Literal["es", "en"] = Field("es", description="Idioma de la aplicación")
    date_format: Literal["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"] = Field("DD/MM/YYYY", description="Formato de fecha")
    time_format: Literal["24h", "12h"] = Field("24h", description="Formato de hora")
    zodiac_system: Literal["tropical", "sidereal"] = Field("tropical", description="Sistema del zodíaco")
    house_system: Literal["placidus", "koch", "equal", "whole_sign", "porphyry", "regiomontanus", "campanus", "alcabitius"] = Field("placidus", description="Sistema de casas")


class InterpretationPreferences(BaseModel):
    """Preferencias de interpretación."""
    interpretation_depth: int = Field(3, ge=1, le=5, description="Profundidad de interpretación (1-5)")
    include_modern_planets: bool = Field(True, description="Incluir planetas modernos (Urano, Neptuno, Plutón)")
    include_asteroids: bool = Field(False, description="Incluir asteroides (Quirón, Ceres, etc.)")
    include_arabic_parts: bool = Field(False, description="Incluir partes árabes")
    include_fixed_stars: bool = Field(False, description="Incluir estrellas fijas")
    focus_areas: List[str] = Field(["personality", "career", "relationships"], description="Áreas de enfoque predeterminadas")


class ConfigurationBase(BaseModel):
    """Modelo base para configuraciones de usuario."""
    user_id: str = Field(..., description="ID del usuario")
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences, description="Preferencias de notificaciones")
    display_preferences: DisplayPreferences = Field(default_factory=DisplayPreferences, description="Preferencias de visualización")
    interpretation_preferences: InterpretationPreferences = Field(default_factory=InterpretationPreferences, description="Preferencias de interpretación")
    daily_horoscope_time: Optional[time] = Field(None, description="Hora para recibir el horóscopo diario")
    premium_status: bool = Field(False, description="Indica si el usuario tiene cuenta premium")
    premium_expiry: Optional[datetime] = Field(None, description="Fecha de expiración de la cuenta premium")
    remaining_queries: int = Field(10, description="Consultas gratuitas restantes")
    query_reset_date: Optional[datetime] = Field(None, description="Fecha de reinicio del contador de consultas")


class ConfigurationCreate(ConfigurationBase):
    """Modelo para crear una nueva configuración."""
    pass


class ConfigurationUpdate(BaseModel):
    """Modelo para actualizar una configuración existente."""
    notification_preferences: Optional[NotificationPreferences] = None
    display_preferences: Optional[DisplayPreferences] = None
    interpretation_preferences: Optional[InterpretationPreferences] = None
    daily_horoscope_time: Optional[time] = None
    premium_status: Optional[bool] = None
    premium_expiry: Optional[datetime] = None
    remaining_queries: Optional[int] = None
    query_reset_date: Optional[datetime] = None


class ConfigurationResponse(BaseResponseModel, ConfigurationBase):
    """Modelo para respuestas de configuración."""
    
    class Config:
        orm_mode = True