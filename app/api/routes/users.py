"""
Rutas de usuarios para la API de Prezagia.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Annotated, Optional

from app.core.logger import logger
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services.security import get_current_user
from app.services.crud.user_service import (
    get_user_by_id,
    update_user,
    delete_user,
    get_users
)
from app.services.crud.profile_service import (
    create_profile,
    get_profile_by_user_id,
    update_profile,
    get_profiles_by_user_ids
)

router = APIRouter()

@router.get("", response_model=List[UserResponse])
async def read_users(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Obtiene la lista de usuarios.
    Solo accesible para administradores.
    """
    # Verificar si el usuario actual es administrador
    if not current_user.is_admin:
        logger.warning(f"Usuario no administrador {current_user.email} intentó acceder a lista de usuarios")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    users = await get_users(skip=skip, limit=limit)
    logger.debug(f"Administrador {current_user.email} solicitó lista de usuarios. Total: {len(users)}")
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Obtiene información detallada de un usuario específico.
    Los usuarios pueden ver solo su propia información, los administradores pueden ver cualquiera.
    """
    # Verificar permisos
    if current_user.id != user_id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.email} intentó acceder a información de usuario {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a esta información"
        )
    
    user = await get_user_by_id(user_id)
    if not user:
        logger.warning(f"Intento de acceso a usuario inexistente ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    logger.debug(f"Usuario {current_user.email} solicitó información de usuario {user_id}")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: str,
    user_data: UserUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Actualiza la información de un usuario.
    Los usuarios pueden actualizar solo su propia información, los administradores pueden actualizar cualquiera.
    """
    # Verificar permisos
    if current_user.id != user_id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.email} intentó actualizar información de usuario {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    # Verificar que el usuario existe
    user = await get_user_by_id(user_id)
    if not user:
        logger.warning(f"Intento de actualizar usuario inexistente ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar usuario
    updated_user = await update_user(user_id, user_data)
    logger.info(f"Usuario {user_id} actualizado por {current_user.email}")
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_account(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Elimina una cuenta de usuario.
    Los usuarios pueden eliminar solo su propia cuenta, los administradores pueden eliminar cualquiera.
    """
    # Verificar permisos
    if current_user.id != user_id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.email} intentó eliminar cuenta de usuario {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    # Verificar que el usuario existe
    user = await get_user_by_id(user_id)
    if not user:
        logger.warning(f"Intento de eliminar usuario inexistente ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Eliminar usuario
    await delete_user(user_id)
    logger.info(f"Usuario {user_id} eliminado por {current_user.email}")
    return None


# Rutas para perfiles astrológicos de usuarios

@router.post("/profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile_data: ProfileCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Crea un perfil astrológico para el usuario actual o para otro usuario si es administrador.
    """
    # Verificar permisos si se intenta crear perfil para otro usuario
    if profile_data.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.email} intentó crear perfil para usuario {profile_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    # Verificar si ya existe un perfil para el usuario
    existing_profile = await get_profile_by_user_id(profile_data.user_id)
    if existing_profile:
        logger.warning(f"Intento de crear perfil duplicado para usuario {profile_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un perfil para este usuario"
        )
    
    # Crear perfil
    profile = await create_profile(profile_data)
    logger.info(f"Perfil creado para usuario {profile_data.user_id}")
    return profile


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def read_user_profile(
    user_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Obtiene el perfil astrológico de un usuario.
    Los usuarios pueden ver solo su propio perfil, los administradores pueden ver cualquiera.
    """
    # Verificar permisos
    if current_user.id != user_id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.email} intentó acceder al perfil de usuario {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a esta información"
        )
    
    profile = await get_profile_by_user_id(user_id)
    if not profile:
        logger.warning(f"Intento de acceso a perfil inexistente para usuario ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )
    
    logger.debug(f"Usuario {current_user.email} solicitó perfil de usuario {user_id}")
    return profile


@router.put("/profile/{user_id}", response_model=ProfileResponse)
async def update_user_profile(
    user_id: str,
    profile_data: ProfileUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Actualiza el perfil astrológico de un usuario.
    Los usuarios pueden actualizar solo su propio perfil, los administradores pueden actualizar cualquiera.
    """
    # Verificar permisos
    if current_user.id != user_id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.email} intentó actualizar perfil de usuario {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    
    # Verificar que el perfil existe
    profile = await get_profile_by_user_id(user_id)
    if not profile:
        logger.warning(f"Intento de actualizar perfil inexistente para usuario ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil no encontrado"
        )
    
    # Actualizar perfil
    updated_profile = await update_profile(profile.id, profile_data)
    logger.info(f"Perfil de usuario {user_id} actualizado por {current_user.email}")
    return updated_profile