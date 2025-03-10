"""
Servicio de gestión de perfiles astrológicos para la aplicación Prezagia.

Este módulo proporciona funciones para crear, obtener, actualizar y eliminar
perfiles astrológicos de usuarios en la base de datos de Supabase.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.db.supabase import get_supabase
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.core.logger import logger
from app.core.exceptions import DatabaseError, ResourceNotFoundError, ResourceExistsError


async def create_profile(profile_data: ProfileCreate) -> Dict[str, Any]:
    """
    Crea un nuevo perfil astrológico para un usuario.
    
    Args:
        profile_data: Datos del perfil a crear
    
    Returns:
        Dict: Datos del perfil creado
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
        ResourceExistsError: Si el usuario ya tiene un perfil
    """
    logger.info(f"Creando perfil para usuario: {profile_data.user_id}")
    supabase = get_supabase()
    
    try:
        # Verificar si ya existe un perfil para este usuario
        existing = await get_profile_by_user_id(profile_data.user_id)
        if existing:
            logger.warning(f"Intento de crear perfil duplicado para usuario: {profile_data.user_id}")
            raise ResourceExistsError("perfil astrológico", f"usuario {profile_data.user_id}")
        
        # Preparar datos para inserción
        profile_dict = profile_data.dict()
        
        # Añadir timestamps
        now = datetime.utcnow().isoformat()
        profile_dict["created_at"] = now
        profile_dict["updated_at"] = now
        
        # Crear el perfil
        response = supabase.table("perfiles_astrologicos").insert(profile_dict).execute()
        
        if not response.data:
            raise DatabaseError("No se pudo crear el perfil astrológico")
        
        logger.info(f"Perfil astrológico creado exitosamente para usuario: {profile_data.user_id}")
        return response.data[0]
        
    except ResourceExistsError:
        raise
    except Exception as e:
        logger.error(f"Error al crear perfil astrológico: {str(e)}")
        raise DatabaseError(f"Error al crear perfil astrológico: {str(e)}")


async def get_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un perfil astrológico por su ID.
    
    Args:
        profile_id: ID del perfil
    
    Returns:
        Optional[Dict]: Datos del perfil o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando perfil con ID: {profile_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("perfiles_astrologicos").select("*").eq("id", profile_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.debug(f"Perfil encontrado: {profile_id}")
            return response.data[0]
        
        logger.debug(f"Perfil no encontrado: {profile_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error al buscar perfil {profile_id}: {str(e)}")
        raise DatabaseError(f"Error al buscar perfil: {str(e)}")


async def get_profile_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene el perfil astrológico de un usuario.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Optional[Dict]: Datos del perfil o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando perfil para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("perfiles_astrologicos").select("*").eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.debug(f"Perfil encontrado para usuario: {user_id}")
            return response.data[0]
        
        logger.debug(f"Perfil no encontrado para usuario: {user_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error al buscar perfil para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al buscar perfil: {str(e)}")


async def update_profile(profile_id: str, profile_data: ProfileUpdate) -> Dict[str, Any]:
    """
    Actualiza un perfil astrológico.
    
    Args:
        profile_id: ID del perfil
        profile_data: Nuevos datos del perfil
    
    Returns:
        Dict: Datos actualizados del perfil
    
    Raises:
        ResourceNotFoundError: Si el perfil no existe
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Actualizando perfil: {profile_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que el perfil existe
        profile = await get_profile_by_id(profile_id)
        if not profile:
            logger.warning(f"Intento de actualizar perfil inexistente: {profile_id}")
            raise ResourceNotFoundError("Perfil astrológico", profile_id)
        
        # Convertir el esquema a un diccionario y eliminar valores None
        update_data = profile_data.dict(exclude_unset=True)
        logger.debug(f"Campos a actualizar: {', '.join(update_data.keys()) if update_data else 'ninguno'}")
        
        if not update_data:
            logger.warning("No hay datos para actualizar")
            return profile
        
        # Añadir timestamp de actualización
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Actualizar perfil
        response = supabase.table("perfiles_astrologicos").update(update_data).eq("id", profile_id).execute()
        
        if not response.data or len(response.data) == 0:
            raise DatabaseError(f"No se pudo actualizar el perfil {profile_id}")
        
        logger.info(f"Perfil actualizado correctamente: {profile_id}")
        return response.data[0]
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar perfil {profile_id}: {str(e)}")
        raise DatabaseError(f"Error al actualizar perfil: {str(e)}")


async def delete_profile(profile_id: str) -> bool:
    """
    Elimina un perfil astrológico.
    
    Args:
        profile_id: ID del perfil
    
    Returns:
        bool: True si se eliminó correctamente
    
    Raises:
        ResourceNotFoundError: Si el perfil no existe
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Eliminando perfil: {profile_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que el perfil existe
        profile = await get_profile_by_id(profile_id)
        if not profile:
            logger.warning(f"Intento de eliminar perfil inexistente: {profile_id}")
            raise ResourceNotFoundError("Perfil astrológico", profile_id)
        
        # Eliminar perfil
        response = supabase.table("perfiles_astrologicos").delete().eq("id", profile_id).execute()
        
        logger.info(f"Perfil eliminado correctamente: {profile_id}")
        return True
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar perfil {profile_id}: {str(e)}")
        raise DatabaseError(f"Error al eliminar perfil: {str(e)}")


async def get_profiles_by_user_ids(user_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Obtiene perfiles astrológicos para una lista de IDs de usuarios.
    
    Args:
        user_ids: Lista de IDs de usuarios
    
    Returns:
        List[Dict]: Lista de perfiles astrológicos
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    if not user_ids:
        return []
    
    logger.debug(f"Obteniendo perfiles para {len(user_ids)} usuarios")
    supabase = get_supabase()
    
    try:
        response = supabase.table("perfiles_astrologicos").select("*").in_("user_id", user_ids).execute()
        
        logger.debug(f"Se encontraron {len(response.data)} perfiles")
        return response.data
        
    except Exception as e:
        logger.error(f"Error al obtener perfiles por lista de usuarios: {str(e)}")
        raise DatabaseError(f"Error al obtener perfiles: {str(e)}")