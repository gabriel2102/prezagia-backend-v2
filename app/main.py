# app/main.py
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import os

from app.api.routes import auth, users, charts, predictions, compatibility
from app.core.config import settings
from app.core.logger import logger
from app.db.init_db import init_db

# Inicialización de recursos
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # Inicializar recursos al iniciar la aplicación
    logger.info("Iniciando Prezagia - Aplicación de astrología con IA")
    logger.info(f"Entorno: {settings.ENVIRONMENT}")
    
    # Inicializar la base de datos y conexión con Supabase
    try:
        init_db()
        logger.info("Conexión a base de datos establecida correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {str(e)}")
    
    # Crear directorios necesarios
    os.makedirs(settings.SKYFIELD_DATA_DIR, exist_ok=True)
    logger.info(f"Directorio de datos de Skyfield: {settings.SKYFIELD_DATA_DIR}")
    
    yield
    
    # Liberar recursos al cerrar la aplicación
    logger.info("Cerrando Prezagia y liberando recursos...")

# Crear la aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para la aplicación de astrología Prezagia con cálculos astronómicos precisos e IA",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware para logging de solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para registrar detalles de todas las solicitudes HTTP."""
    # Generar ID único para la solicitud
    request_id = os.urandom(6).hex()
    
    # Registrar inicio de la solicitud
    logger.debug(f"Solicitud {request_id} iniciada: {request.method} {request.url.path}")
    
    # Medir tiempo de respuesta
    start_time = time.time()
    
    # Procesar la solicitud
    try:
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        formatted_process_time = f"{process_time:.4f}"
        
        # Registrar fin de la solicitud
        logger.debug(
            f"Solicitud {request_id} completada: {request.method} {request.url.path} "
            f"- Estado: {response.status_code} - Tiempo: {formatted_process_time}s"
        )
        
        # Añadir encabezado con tiempo de proceso
        response.headers["X-Process-Time"] = formatted_process_time
        response.headers["X-Request-ID"] = request_id
        
        return response
    except Exception as e:
        # Registrar errores de solicitud
        process_time = time.time() - start_time
        logger.error(
            f"Solicitud {request_id} fallida: {request.method} {request.url.path} "
            f"- Error: {str(e)} - Tiempo: {process_time:.4f}s"
        )
        raise

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers para diferentes endpoints
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(compatibility.router, prefix="/api/compatibility", tags=["compatibility"])

@app.get("/", tags=["root"])
async def root():
    """
    Endpoint raíz para verificar que la API está funcionando.
    """
    logger.info("Acceso al endpoint raíz")
    return {
        "app": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "API para aplicación de astrología con cálculos astronómicos precisos e IA",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """
    Endpoint para verificar la salud de la aplicación.
    """
    logger.debug("Health check realizado")
    return {
        "status": "healthy", 
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }