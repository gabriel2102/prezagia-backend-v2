"""
Servicio de gestión de configuraciones de usuario para la aplicación Prezagia.

Este módulo proporciona funciones para obtener, actualizar y gestionar las
configuraciones personalizadas de los usuarios.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.db.supabase import get_supabase
from app.schemas.configuration import ConfigurationCreate, ConfigurationUpdate
from app.core.logger import logger
from app.core.exceptions import DatabaseError, ResourceNotFoundError


async def get_user_configuration(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración de un usuario por su ID.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Optional[Dict]: Configuración del usuario o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Obteniendo configuración para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("configuraciones").select("*").eq("usuario_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.debug(f"Configuración encontrada para usuario: {user_id}")
            return response.data[0]
        
        logger.warning(f"Configuración no encontrada para usuario: {user_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error al obtener configuración para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener configuración: {str(e)}")


async def create_default_configuration(user_id: str) -> Dict[str, Any]:
    """
    Crea una configuración predeterminada para un usuario.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Dict: Configuración creada
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Creando configuración predeterminada para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Verificar si ya existe una configuración
        existing = await get_user_configuration(user_id)
        if existing:
            logger.warning(f"Ya existe una configuración para el usuario: {user_id}")
            return existing
        
        # Crear configuración por defecto
        now = datetime.utcnow()
        
        config_data = {
            "usuario_id": user_id,
            "notification_preferences": {
                "daily_horoscope": True,
                "important_transits": True,
                "weekly_forecast": True,
                "special_events": True,
                "email_notifications": True,
                "push_notifications": True
            },
            "display_preferences": {
                "theme": "dark",
                "chart_style": "modern",
                "language": "es",
                "date_format": "DD/MM/YYYY",
                "time_format": "24h",
                "zodiac_system": "tropical",
                "house_system": "placidus"
            },
            "interpretation_preferences": {
                "interpretation_depth": 3,
                "include_modern_planets": True,
                "include_asteroids": False,
                "include_arabic_parts": False,
                "include_fixed_stars": False,
                "focus_areas": ["personality", "career", "relationships"]
            },
            "daily_horoscope_time": "08:00:00",
            "premium_status": False,
            "premium_expiry": None,
            "remaining_queries": 10,
            "query_reset_date": (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        response = supabase.table("configuraciones").insert(config_data).execute()
        
        if not response.data:
            raise DatabaseError("No se pudo crear la configuración predeterminada")
        
        logger.info(f"Configuración predeterminada creada para usuario: {user_id}")
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error al crear configuración predeterminada para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al crear configuración: {str(e)}")


async def update_user_configuration(user_id: str, config_data: ConfigurationUpdate) -> Dict[str, Any]:
    """
    Actualiza la configuración de un usuario.
    
    Args:
        user_id: ID del usuario
        config_data: Nuevos datos de configuración
    
    Returns:
        Dict: Configuración actualizada
    
    Raises:
        ResourceNotFoundError: Si la configuración no existe
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Actualizando configuración para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que la configuración existe
        existing = await get_user_configuration(user_id)
        if not existing:
            logger.warning(f"Configuración no encontrada para usuario: {user_id}")
            # Crear configuración predeterminada si no existe
            return await create_default_configuration(user_id)
        
        # Convertir el esquema a un diccionario y eliminar valores None
        update_data = config_data.dict(exclude_unset=True)
        logger.debug(f"Campos a actualizar: {', '.join(update_data.keys()) if update_data else 'ninguno'}")
        
        if not update_data:
            logger.warning("No hay datos para actualizar")
            return existing
        
        # Añadir timestamp de actualización
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Actualizar configuración
        response = supabase.table("configuraciones").update(update_data).eq("usuario_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise DatabaseError(f"No se pudo actualizar la configuración del usuario {user_id}")
        
        logger.info(f"Configuración actualizada correctamente para usuario: {user_id}")
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error al actualizar configuración para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al actualizar configuración: {str(e)}")


async def update_query_count(user_id: str, decrement: bool = True) -> Dict[str, Any]:
    """
    Actualiza el contador de consultas disponibles para un usuario.
    
    Args:
        user_id: ID del usuario
        decrement: Si es True, decrementa el contador. Si es False, restablece el contador.
    
    Returns:
        Dict: Configuración actualizada
    
    Raises:
        ResourceNotFoundError: Si la configuración no existe
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Actualizando contador de consultas para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Obtener configuración actual
        config = await get_user_configuration(user_id)
        if not config:
            logger.warning(f"Configuración no encontrada para usuario: {user_id}")
            # Crear configuración predeterminada si no existe
            config = await create_default_configuration(user_id)
        
        now = datetime.utcnow()
        update_data = {}
        
        # Verificar si es necesario reiniciar el contador
        reset_date = datetime.fromisoformat(config["query_reset_date"].replace("Z", "+00:00")) if config.get("query_reset_date") else None
        
        if not reset_date or now >= reset_date or not decrement:
            # Reiniciar contador
            max_queries = 50 if config.get("premium_status", False) else 10
            update_data["remaining_queries"] = max_queries
            update_data["query_reset_date"] = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            logger.info(f"Reiniciando contador de consultas para usuario {user_id}: {max_queries} consultas disponibles")
        elif decrement and config.get("remaining_queries", 0) > 0:
            # Decrementar contador
            update_data["remaining_queries"] = config["remaining_queries"] - 1
            logger.debug(f"Decrementando contador de consultas para usuario {user_id}: {update_data['remaining_queries']} restantes")
        
        if update_data:
            # Actualizar timestamp
            update_data["updated_at"] = now.isoformat()
            
            # Actualizar en base de datos
            response = supabase.table("configuraciones").update(update_data).eq("usuario_id", user_id).execute()
            
            if not response.data or len(response.data) == 0:
                raise DatabaseError(f"No se pudo actualizar el contador de consultas para el usuario {user_id}")
            
            return response.data[0]
        
        return config
        
    except Exception as e:
        logger.error(f"Error al actualizar contador de consultas para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al actualizar contador de consultas: {str(e)}")


async def check_query_limit(user_id: str) -> Dict[str, Any]:
    """
    Verifica si un usuario ha alcanzado su límite de consultas diarias.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Dict: Información sobre el límite de consultas
        {
            "can_query": bool,  # Si el usuario puede realizar más consultas
            "remaining_queries": int,  # Consultas restantes
            "reset_time": str,  # Cuándo se restablecerá el contador
            "is_premium": bool  # Si el usuario tiene estatus premium
        }
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Verificando límite de consultas para usuario: {user_id}")
    
    try:
        # Obtener configuración actual
        config = await get_user_configuration(user_id)
        if not config:
            logger.warning(f"Configuración no encontrada para usuario: {user_id}")
            # Crear configuración predeterminada si no existe
            config = await create_default_configuration(user_id)
        
        now = datetime.utcnow()
        
        # Verificar si es necesario reiniciar el contador
        reset_date_str = config.get("query_reset_date")
        if reset_date_str:
            reset_date = datetime.fromisoformat(reset_date_str.replace("Z", "+00:00"))
        else:
            # Si no hay fecha de reinicio, establecerla para mañana
            reset_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        remaining_queries = config.get("remaining_queries", 0)
        is_premium = config.get("premium_status", False)
        
        # Si ya pasó la fecha de reinicio, actualizar el contador
        if now >= reset_date:
            updated_config = await update_query_count(user_id, decrement=False)
            remaining_queries = updated_config.get("remaining_queries", 0)
            reset_date_str = updated_config.get("query_reset_date")
            if reset_date_str:
                reset_date = datetime.fromisoformat(reset_date_str.replace("Z", "+00:00"))
        
        # Preparar respuesta
        result = {
            "can_query": remaining_queries > 0,
            "remaining_queries": remaining_queries,
            "reset_time": reset_date.isoformat(),
            "is_premium": is_premium,
            "max_daily_queries": 50 if is_premium else 10
        }
        
        logger.debug(f"Verificación de límite completada: {remaining_queries} consultas restantes para usuario {user_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error al verificar límite de consultas para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al verificar límite de consultas: {str(e)}")


async def update_premium_status(user_id: str, premium_status: bool, 
                            premium_expiry: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Actualiza el estado premium de un usuario.
    
    Args:
        user_id: ID del usuario
        premium_status: Nuevo estado premium
        premium_expiry: Fecha de expiración del estado premium
    
    Returns:
        Dict: Configuración actualizada
    
    Raises:
        ResourceNotFoundError: Si la configuración no existe
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Actualizando estado premium para usuario {user_id}: {premium_status}")
    supabase = get_supabase()
    
    try:
        # Verificar que la configuración existe
        config = await get_user_configuration(user_id)
        if not config:
            logger.warning(f"Configuración no encontrada para usuario: {user_id}")
            # Crear configuración predeterminada si no existe
            config = await create_default_configuration(user_id)
        
        # Preparar datos de actualización
        update_data = {
            "premium_status": premium_status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if premium_expiry:
            update_data["premium_expiry"] = premium_expiry.isoformat()
        elif premium_status:
            # Si se activa premium sin fecha de expiración, establecer por defecto a 30 días
            expiry = datetime.utcnow() + timedelta(days=30)
            update_data["premium_expiry"] = expiry.isoformat()
        else:
            # Si se desactiva premium, eliminar fecha de expiración
            update_data["premium_expiry"] = None
        
        # Si se activa premium, restablecer contador de consultas
        if premium_status:
            update_data["remaining_queries"] = 50  # Límite para usuarios premium
        
        # Actualizar en base de datos
        response = supabase.table("configuraciones").update(update_data).eq("usuario_id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise DatabaseError(f"No se pudo actualizar el estado premium para el usuario {user_id}")
        
        logger.info(f"Estado premium actualizado para usuario {user_id}: {premium_status}")
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error al actualizar estado premium para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al actualizar estado premium: {str(e)}")