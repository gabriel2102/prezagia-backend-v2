# app/core/logger.py
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import sys

from app.core.config import settings


# Crear directorio de logs si no existe
def setup_logging():
    """
    Configura el sistema de logging para la aplicación.
    - Registra eventos en consola
    - Guarda logs en archivos rotativos (un nuevo archivo cada día o cuando alcanza cierto tamaño)
    - Diferentes niveles de log para desarrollo y producción
    """
    # Crear directorio de logs si no existe
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Nombre de archivo basado en la fecha actual
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"prezagia_{today}.log")
    
    # Configurar el nivel de log basado en el entorno
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    
    # Configurar formato de logs
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Eliminar handlers existentes para evitar duplicados
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Handler para archivo rotativo
    # Rota el archivo cuando alcanza 10MB o al inicio de cada día
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,  # Mantener hasta 10 archivos de backup
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # Crear un logger específico para la aplicación
    app_logger = logging.getLogger("prezagia")
    
    # Log de inicio
    app_logger.info(f"Iniciando Prezagia - Entorno: {settings.ENVIRONMENT}")
    
    return app_logger


# Exportar logger
logger = setup_logging()