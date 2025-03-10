"""
Módulo que contiene todas las rutas de la API de Prezagia.
"""

# Importar todos los routers para facilitar importación desde main.py
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.charts import router as charts_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.compatibility import router as compatibility_router

# Exportar como variables públicas
__all__ = [
    "auth",
    "users",
    "charts",
    "predictions",
    "compatibility"
]