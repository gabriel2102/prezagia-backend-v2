# app/core/config.py
import os
import secrets
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Información general del proyecto
    PROJECT_NAME: str = "Prezagia"
    API_V1_STR: str = "/api/v1"
    
    # Entorno (development, production)
    ENVIRONMENT: str = "development"
    
    # Dirección de logs
    LOGS_DIR: str = "./logs"
    
    # Nivel de Log
    LOG_LEVEL: str = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Clave secreta para JWT y otras operaciones criptográficas
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # Token JWT - 60 minutos * 24 horas * 8 días = 8 días
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # Lista de orígenes permitidos para CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Configuración de la base de datos Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # Configuración de Claude API
    CLAUDE_API_KEY: str
    CLAUDE_API_URL: str = "https://api.anthropic.com/v1"

    # Configuración de email
    EMAILS_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_TEST_USER: Optional[str] = None

    # Dirección para archivos de datos astronómicos de Skyfield
    SKYFIELD_DATA_DIR: str = "./data/skyfield"
    
    # Variables para límites de consultas
    MAX_DAILY_QUERIES: int = 10  # Consultas gratuitas diarias
    PREMIUM_MAX_DAILY_QUERIES: int = 50  # Consultas para usuarios premium

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instancia de configuración
settings = Settings()

# Asegurarse de que los directorios necesarios existan
os.makedirs(settings.SKYFIELD_DATA_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)