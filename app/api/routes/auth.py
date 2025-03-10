"""
Rutas de autenticación para la API de Prezagia.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, Annotated

from app.core.logger import logger
from app.schemas.user import UserCreate, UserResponse, TokenResponse, UserLogin
from app.services.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_refresh_token
)
from app.services.crud.user_service import create_user, get_user_by_email

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Registra un nuevo usuario en el sistema.
    """
    # Verificar si el correo ya está registrado
    existing_user = await get_user_by_email(user_data.email)
    if existing_user:
        logger.warning(f"Intento de registro con email ya existente: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )
    
    # Importar get_password_hash desde utils
    from app.utils.password_utils import get_password_hash
    
    # Hashear la contraseña antes de guardarla
    hashed_password = get_password_hash(user_data.password)
    
    # Crear el usuario en la base de datos
    new_user = await create_user(user_data, hashed_password)
    
    logger.info(f"Nuevo usuario registrado: {user_data.email}")
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    Autentica al usuario y devuelve tokens de acceso y refresco.
    """
    # Autenticar usuario
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Intento de inicio de sesión fallido para: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar tokens
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    refresh_token = create_access_token(data={"sub": user.email, "user_id": user.id, "refresh": True}, expires_delta_minutes=60*24*7)  # 7 días
    
    # Establecer cookie HTTP-only para el refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,  # Solo HTTPS
        samesite="lax",
        max_age=60*60*24*7,  # 7 días en segundos
        path="/api/auth/refresh"
    )
    
    logger.info(f"Usuario autenticado correctamente: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None)
):
    """
    Refresca el token de acceso usando el token de refresco.
    """
    if not refresh_token:
        logger.warning("Intento de refresco de token sin token de refresco")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco no proporcionado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar token de refresco
    user = await verify_refresh_token(refresh_token)
    if not user:
        logger.warning("Intento de refresco con token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar nuevos tokens
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    new_refresh_token = create_access_token(data={"sub": user.email, "user_id": user.id, "refresh": True}, expires_delta_minutes=60*24*7)
    
    # Actualizar cookie de refresh token
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60*60*24*7,
        path="/api/auth/refresh"
    )
    
    logger.info(f"Token refrescado para usuario: {user.email}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Cierra la sesión del usuario eliminando el token de refresco.
    """
    # Eliminar cookie de refresh token
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth/refresh",
        secure=True,
        httponly=True
    )
    
    logger.info("Usuario cerró sesión")
    return {"message": "Sesión cerrada correctamente"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[UserResponse, Depends(get_current_user)]):
    """
    Devuelve la información del usuario autenticado.
    """
    logger.debug(f"Usuario {current_user.email} solicitó su información")
    return current_user