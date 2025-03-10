"""
Esquemas de usuario para la aplicación Prezagia.

Este módulo define los modelos de datos relacionados con la gestión de usuarios.
"""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, EmailStr, root_validator
from uuid import UUID

from app.schemas.schema_base import BaseResponseModel


class UserBase(BaseModel):
    """Modelo base para usuarios."""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del usuario")


class UserCreate(UserBase):
    """Modelo para crear un nuevo usuario."""
    password: str = Field(..., min_length=8, description="Contraseña del usuario")
    fecha_nacimiento: date = Field(..., description="Fecha de nacimiento")
    hora_nacimiento: time = Field(..., description="Hora de nacimiento")
    lugar_nacimiento_lat: float = Field(..., ge=-90, le=90, description="Latitud del lugar de nacimiento")
    lugar_nacimiento_lng: float = Field(..., ge=-180, le=180, description="Longitud del lugar de nacimiento")
    lugar_nacimiento_nombre: Optional[str] = Field(None, description="Nombre del lugar de nacimiento")
    
    @validator('hora_nacimiento')
    def validate_birth_time(cls, v):
        """Validar que la hora de nacimiento tenga segundos y microsegundos en cero."""
        if v.second != 0 or v.microsecond != 0:
            return time(v.hour, v.minute, 0)
        return v


class UserLogin(BaseModel):
    """Modelo para iniciar sesión."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Modelo para actualizar datos de usuario."""
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    fecha_nacimiento: Optional[date] = None
    hora_nacimiento: Optional[time] = None
    lugar_nacimiento_lat: Optional[float] = Field(None, ge=-90, le=90)
    lugar_nacimiento_lng: Optional[float] = Field(None, ge=-180, le=180)
    lugar_nacimiento_nombre: Optional[str] = None
    
    @validator('hora_nacimiento')
    def validate_birth_time(cls, v):
        if v and (v.second != 0 or v.microsecond != 0):
            return time(v.hour, v.minute, 0)
        return v


class UserResponse(BaseResponseModel):
    """Modelo para respuestas de usuario."""
    email: EmailStr
    nombre: str
    fecha_nacimiento: date
    hora_nacimiento: time
    lugar_nacimiento_lat: float
    lugar_nacimiento_lng: float
    lugar_nacimiento_nombre: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    fecha_registro: datetime
    
    class Config:
        orm_mode = True


class TokenData(BaseModel):
    """Datos contenidos en el token JWT."""
    email: Optional[str] = None
    user_id: Optional[str] = None
    exp: Optional[int] = None
    is_refresh: Optional[bool] = False


class TokenResponse(BaseModel):
    """Respuesta con token de acceso."""
    access_token: str
    token_type: str
    user_id: str
    email: str