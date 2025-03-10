"""
Esquemas de perfil astrológico para la aplicación Prezagia.

Este módulo define los modelos de datos relacionados con los perfiles astrológicos de los usuarios.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator

from app.schemas.schema_base import BaseResponseModel


class ProfileBase(BaseModel):
    """Modelo base para perfiles astrológicos."""
    user_id: str = Field(..., description="ID del usuario al que pertenece el perfil")
    sun_sign: str = Field(..., description="Signo solar")
    moon_sign: str = Field(..., description="Signo lunar")
    rising_sign: str = Field(..., description="Signo ascendente")
    mercury_sign: Optional[str] = Field(None, description="Signo de Mercurio")
    venus_sign: Optional[str] = Field(None, description="Signo de Venus")
    mars_sign: Optional[str] = Field(None, description="Signo de Marte")
    jupiter_sign: Optional[str] = Field(None, description="Signo de Júpiter")
    saturn_sign: Optional[str] = Field(None, description="Signo de Saturno")
    uranus_sign: Optional[str] = Field(None, description="Signo de Urano")
    neptune_sign: Optional[str] = Field(None, description="Signo de Neptuno")
    pluto_sign: Optional[str] = Field(None, description="Signo de Plutón")
    
    dominant_element: Optional[str] = Field(None, description="Elemento dominante (Fuego, Tierra, Aire, Agua)")
    dominant_modality: Optional[str] = Field(None, description="Modalidad dominante (Cardinal, Fijo, Mutable)")
    
    # Campos para casas astrológicas
    houses: Optional[Dict[str, str]] = Field(None, description="Signos en cada casa astrológica")
    
    # Aspectos importantes
    aspects: Optional[List[Dict[str, Any]]] = Field(None, description="Aspectos importantes en la carta natal")
    
    # Puntos sensibles
    north_node: Optional[str] = Field(None, description="Nodo Norte")
    south_node: Optional[str] = Field(None, description="Nodo Sur")
    lilith: Optional[str] = Field(None, description="Lilith")
    chiron: Optional[str] = Field(None, description="Quirón")
    
    # Resumen personalizado
    personality_summary: Optional[str] = Field(None, description="Resumen de la personalidad según la carta natal")
    key_challenges: Optional[List[str]] = Field(None, description="Desafíos clave según la carta natal")
    key_strengths: Optional[List[str]] = Field(None, description="Fortalezas clave según la carta natal")


class ProfileCreate(ProfileBase):
    """Modelo para crear un nuevo perfil astrológico."""
    pass


class ProfileUpdate(BaseModel):
    """Modelo para actualizar un perfil astrológico."""
    sun_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    rising_sign: Optional[str] = None
    mercury_sign: Optional[str] = None
    venus_sign: Optional[str] = None
    mars_sign: Optional[str] = None
    jupiter_sign: Optional[str] = None
    saturn_sign: Optional[str] = None
    uranus_sign: Optional[str] = None
    neptune_sign: Optional[str] = None
    pluto_sign: Optional[str] = None
    
    dominant_element: Optional[str] = None
    dominant_modality: Optional[str] = None
    
    houses: Optional[Dict[str, str]] = None
    aspects: Optional[List[Dict[str, Any]]] = None
    
    north_node: Optional[str] = None
    south_node: Optional[str] = None
    lilith: Optional[str] = None
    chiron: Optional[str] = None
    
    personality_summary: Optional[str] = None
    key_challenges: Optional[List[str]] = None
    key_strengths: Optional[List[str]] = None


class ProfileResponse(BaseResponseModel, ProfileBase):
    """Modelo para respuestas de perfil astrológico."""
    
    class Config:
        orm_mode = True