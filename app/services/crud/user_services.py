"""
Servicio de gestión de usuarios para la aplicación Prezagia.

Este módulo proporciona funciones para crear, obtener, actualizar y eliminar
usuarios en la base de datos de Supabase.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.db.supabase import get_supabase
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.password_utils import get_password_hash
from app.core.logger import logger
from app.core.exceptions import DatabaseError, ResourceNotFoundError, ResourceExistsError


async def create_user(user_data: UserCreate, hashed_password: str) -> Dict[str, Any]:
    """
    Crea un nuevo usuario en la base de datos.
    
    Args:
        user_data: Datos del usuario a crear
        hashed_password: Contraseña ya hasheada
    
    Returns:
        Dict: Datos del usuario creado
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
        ResourceExistsError: Si el email ya está registrado
    """
    logger.info(f"Creando nuevo usuario con email: {user_data.email}")
    supabase = get_supabase()
    
    try:
        # Primero crear el usuario en el sistema de auth de Supabase
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
        })
        
        # Obtener el ID del usuario creado
        user_id = auth_response.user.id
        logger.debug(f"Usuario registrado en Auth de Supabase con ID: {user_id}")
        
        # Crear el registro en la tabla de usuarios
        user_data_dict = {
            "id": user_id,
            "email": user_data.email,
            "nombre": user_data.nombre,
            "fecha_nacimiento": user_data.fecha_nacimiento.isoformat(),
            "hora_nacimiento": user_data.hora_nacimiento.isoformat(),
            "lugar_nacimiento_lat": user_data.lugar_nacimiento_lat,
            "lugar_nacimiento_lng": user_data.lugar_nacimiento_lng,
            "lugar_nacimiento_nombre": user_data.lugar_nacimiento_nombre,
            "fecha_registro": datetime.utcnow().isoformat(),
            "is_active": True,
            "is_admin": False
        }
        
        response = supabase.table("usuarios").insert(user_data_dict).execute()
        
        if not response.data:
            raise DatabaseError("No se pudo crear el usuario en la tabla usuarios")
        
        # Crear configuración por defecto para el usuario
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
            "premium_status": False,
            "remaining_queries": 10,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("configuraciones").insert(config_data).execute()
        
        logger.info(f"Usuario creado exitosamente: {user_id}")
        return response.data[0]
        
    except Exception as e:
        logger.error(f"Error al crear usuario: {str(e)}")
        # Intentar limpiar datos parciales si el error ocurre después de crear auth
        if 'user_id' in locals():
            try:
                # No podemos eliminar el usuario de Auth sin permisos admin
                # pero podemos eliminar los registros de las tablas relacionadas
                supabase.table("usuarios").delete().eq("id", user_id).execute()
                supabase.table("configuraciones").delete().eq("usuario_id", user_id).execute()
                logger.warning(f"Limpieza de datos parciales para usuario fallido {user_id}")
            except Exception as cleanup_error:
                logger.error(f"Error en limpieza de datos: {str(cleanup_error)}")
        
        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
            raise ResourceExistsError("usuario", user_data.email)
        raise DatabaseError(f"Error al crear usuario: {str(e)}")


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por su email.
    
    Args:
        email: Email del usuario
    
    Returns:
        Optional[Dict]: Datos del usuario o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando usuario con email: {email}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("usuarios").select("*").eq("email", email).execute()
        
        if response.data and len(response.data) > 0:
            logger.debug(f"Usuario encontrado con email: {email}")
            return response.data[0]
        
        logger.debug(f"Usuario no encontrado con email: {email}")
        return None
        
    except Exception as e:
        logger.error(f"Error al buscar usuario por email {email}: {str(e)}")
        raise DatabaseError(f"Error al buscar usuario por email: {str(e)}")


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un usuario por su ID.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Optional[Dict]: Datos del usuario o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando usuario con ID: {user_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("usuarios").select("*").eq("id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.debug(f"Usuario encontrado: {user_id}")
            return response.data[0]
        
        logger.warning(f"Usuario no encontrado: {user_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error al buscar usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al buscar usuario: {str(e)}")


async def update_user(user_id: str, user_data: UserUpdate) -> Dict[str, Any]:
    """
    Actualiza los datos de un usuario.
    
    Args:
        user_id: ID del usuario
        user_data: Nuevos datos del usuario
    
    Returns:
        Dict: Datos actualizados del usuario
    
    Raises:
        ResourceNotFoundError: Si el usuario no existe
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Actualizando usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que el usuario existe
        user = await get_user_by_id(user_id)
        if not user:
            logger.warning(f"Intento de actualizar usuario inexistente: {user_id}")
            raise ResourceNotFoundError("Usuario", user_id)
        
        # Convertir el esquema a un diccionario y eliminar valores None
        update_data = user_data.dict(exclude_unset=True)
        logger.debug(f"Campos a actualizar: {', '.join(update_data.keys())}")
        
        # Convertir objetos datetime a strings ISO para Supabase
        if "fecha_nacimiento" in update_data and update_data["fecha_nacimiento"]:
            update_data["fecha_nacimiento"] = update_data["fecha_nacimiento"].isoformat()
        
        if "hora_nacimiento" in update_data and update_data["hora_nacimiento"]:
            update_data["hora_nacimiento"] = update_data["hora_nacimiento"].isoformat()
        
        # Actualizar datos
        response = supabase.table("usuarios").update(update_data).eq("id", user_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise DatabaseError(f"No se pudo actualizar el usuario {user_id}")
        
        logger.info(f"Usuario actualizado correctamente: {user_id}")
        return response.data[0]
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al actualizar usuario: {str(e)}")


async def delete_user(user_id: str) -> bool:
    """
    Elimina un usuario por su ID.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        bool: True si se eliminó correctamente
    
    Raises:
        ResourceNotFoundError: Si el usuario no existe
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Eliminando usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que el usuario existe
        user = await get_user_by_id(user_id)
        if not user:
            logger.warning(f"Intento de eliminar usuario inexistente: {user_id}")
            raise ResourceNotFoundError("Usuario", user_id)
        
        # Primero eliminar las relaciones en otras tablas
        # Configuraciones
        logger.debug(f"Eliminando configuraciones del usuario: {user_id}")
        supabase.table("configuraciones").delete().eq("usuario_id", user_id).execute()
        
        # Perfiles astrológicos
        logger.debug(f"Eliminando perfiles astrológicos del usuario: {user_id}")
        supabase.table("perfiles_astrologicos").delete().eq("usuario_id", user_id).execute()
        
        # Consultas (cartas, predicciones, etc.)
        logger.debug(f"Eliminando consultas del usuario: {user_id}")
        supabase.table("consultas").delete().eq("usuario_id", user_id).execute()
        
        # Finalmente eliminar el usuario
        logger.debug(f"Eliminando registro del usuario: {user_id}")
        response = supabase.table("usuarios").delete().eq("id", user_id).execute()
        
        if not response.data and not response.count:
            raise DatabaseError(f"No se pudo eliminar el usuario {user_id}")
        
        # No podemos eliminar el usuario de Auth de Supabase sin permisos de admin
        logger.warning(f"No se eliminó el usuario de Auth de Supabase (requiere permisos de admin): {user_id}")
        
        logger.info(f"Usuario eliminado correctamente: {user_id}")
        return True
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al eliminar usuario: {str(e)}")


async def get_users(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Obtiene una lista paginada de usuarios.
    
    Args:
        skip: Número de registros a saltar
        limit: Número máximo de registros a devolver
    
    Returns:
        List[Dict]: Lista de usuarios
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Obteniendo lista de usuarios (skip={skip}, limit={limit})")
    supabase = get_supabase()
    
    try:
        # Obtener el total de registros (para paginación)
        count_response = supabase.table("usuarios").select("id", count="exact").execute()
        total = count_response.count if hasattr(count_response, 'count') else 0
        
        # Obtener los registros paginados
        response = supabase.table("usuarios").select("*").range(skip, skip + limit - 1).execute()
        
        logger.debug(f"Se obtuvieron {len(response.data)} usuarios de un total de {total}")
        return response.data
        
    except Exception as e:
        logger.error(f"Error al obtener lista de usuarios: {str(e)}")
        raise DatabaseError(f"Error al obtener lista de usuarios: {str(e)}")