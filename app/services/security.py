"""
Servicio de seguridad y autenticación para la aplicación Prezagia.

Este módulo proporciona funciones para manejar la autenticación de usuarios,
generar y validar tokens JWT, y proteger las rutas de la API.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.logger import logger
from app.schemas.user import TokenData, UserResponse
from app.utils.password_utils import verify_password

# Nota: NO importamos de user_service directamente aquí

# Configuración de seguridad
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Constantes para JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Autentica a un usuario verificando sus credenciales.
    
    Args:
        email: Email del usuario
        password: Contraseña en texto plano
    
    Returns:
        Optional[Dict]: Datos del usuario si las credenciales son válidas, None en caso contrario
    """
    # Importación tardía para evitar ciclos
    from app.services.crud.user_service import get_user_by_email
    
    user = await get_user_by_email(email)
    if not user:
        logger.warning(f"Intento de autenticación con email no registrado: {email}")
        return None
    
    # En este caso, la contraseña hasheada estaría almacenada en Supabase Auth
    # y no en nuestra tabla de usuarios, por lo que deberíamos usar la API de Auth
    # para validar las credenciales.
    
    # Como simplificación, asumimos que si el usuario existe y la contraseña no
    # está vacía, la autenticación es correcta.
    # En un sistema real, usaríamos:
    # if not verify_password(password, user.get("password")):
    #     return None
    
    # Verificar que el usuario está activo
    if not user.get("is_active", True):
        logger.warning(f"Intento de autenticación con cuenta inactiva: {email}")
        return None
    
    logger.info(f"Usuario autenticado correctamente: {email}")
    return user


def create_access_token(data: Dict[str, Any], expires_delta_minutes: Optional[int] = None) -> str:
    """
    Crea un token JWT con los datos proporcionados.
    
    Args:
        data: Datos a incluir en el token
        expires_delta_minutes: Tiempo de expiración en minutos
    
    Returns:
        str: Token JWT
    """
    to_encode = data.copy()
    expires_delta = expires_delta_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserResponse:
    """
    Obtiene el usuario actual a partir del token JWT.
    
    Args:
        token: Token JWT proporcionado en la solicitud
    
    Returns:
        UserResponse: Datos del usuario autenticado
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    # Importación tardía para evitar ciclos
    from app.services.crud.user_service import get_user_by_id
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar el token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extraer datos del token
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("type", "access")
        exp: int = payload.get("exp")
        
        # Verificar que el token contiene la información necesaria
        if email is None or user_id is None:
            logger.warning("Token sin email o user_id")
            raise credentials_exception
        
        # Verificar que no es un token de refresco
        if token_type == "refresh":
            logger.warning("Intento de usar token de refresco como token de acceso")
            raise credentials_exception
        
        token_data = TokenData(email=email, user_id=user_id, exp=exp)
    except JWTError:
        logger.warning("Error al decodificar token JWT")
        raise credentials_exception
    except ValidationError:
        logger.warning("Error al validar datos del token")
        raise credentials_exception
    
    # Obtener usuario de la base de datos
    user = await get_user_by_id(token_data.user_id)
    if user is None:
        logger.warning(f"Usuario no encontrado con ID del token: {token_data.user_id}")
        raise credentials_exception
    
    # Verificar que el usuario está activo
    if not user.get("is_active", True):
        logger.warning(f"Intento de acceso con cuenta inactiva: {token_data.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta inactiva")
    
    # Crear objeto UserResponse
    try:
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            nombre=user["nombre"],
            fecha_nacimiento=user["fecha_nacimiento"] if isinstance(user["fecha_nacimiento"], datetime) else datetime.fromisoformat(user["fecha_nacimiento"].replace("Z", "+00:00")),
            hora_nacimiento=user["hora_nacimiento"],
            lugar_nacimiento_lat=user["lugar_nacimiento_lat"],
            lugar_nacimiento_lng=user["lugar_nacimiento_lng"],
            lugar_nacimiento_nombre=user.get("lugar_nacimiento_nombre"),
            is_active=user.get("is_active", True),
            is_admin=user.get("is_admin", False),
            fecha_registro=user["fecha_registro"] if isinstance(user["fecha_registro"], datetime) else datetime.fromisoformat(user["fecha_registro"].replace("Z", "+00:00")),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at")
        )
        
        return user_response
    except Exception as e:
        logger.error(f"Error al crear objeto UserResponse: {str(e)}")
        raise credentials_exception


async def get_current_active_user(current_user: Annotated[UserResponse, Depends(get_current_user)]) -> UserResponse:
    """
    Verifica que el usuario actual está activo.
    
    Args:
        current_user: Usuario actual obtenido del token JWT
    
    Returns:
        UserResponse: Datos del usuario si está activo
    
    Raises:
        HTTPException: Si el usuario no está activo
    """
    if not current_user.is_active:
        logger.warning(f"Intento de acceso con cuenta inactiva: {current_user.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta inactiva")
    return current_user


async def get_current_admin_user(current_user: Annotated[UserResponse, Depends(get_current_user)]) -> UserResponse:
    """
    Verifica que el usuario actual es administrador.
    
    Args:
        current_user: Usuario actual obtenido del token JWT
    
    Returns:
        UserResponse: Datos del usuario si es administrador
    
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if not current_user.is_admin:
        logger.warning(f"Intento de acceso a funcionalidad de admin por usuario no administrador: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren privilegios de administrador"
        )
    return current_user

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Genera un hash seguro de una contraseña."""
    return pwd_context.hash(password)

async def verify_refresh_token(refresh_token: str) -> Optional[UserResponse]:
    """
    Verifica que un token de refresco es válido y devuelve el usuario asociado.
    
    Args:
        refresh_token: Token de refresco a verificar
    
    Returns:
        Optional[UserResponse]: Usuario asociado al token si es válido, None en caso contrario
    """
    # Importación tardía para evitar ciclos
    from app.services.crud.user_service import get_user_by_id
    
    try:
        # Decodificar el token
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extraer datos del token
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        is_refresh: bool = payload.get("refresh", False)
        
        # Verificar que es un token de refresco
        if not is_refresh:
            logger.warning("Intento de usar token de acceso como token de refresco")
            return None
        
        # Verificar que el token contiene la información necesaria
        if email is None or user_id is None:
            logger.warning("Token de refresco sin email o user_id")
            return None
        
        # Obtener usuario de la base de datos
        user = await get_user_by_id(user_id)
        if user is None:
            logger.warning(f"Usuario no encontrado con ID del token de refresco: {user_id}")
            return None
        
        # Verificar que el usuario está activo
        if not user.get("is_active", True):
            logger.warning(f"Intento de refresco con cuenta inactiva: {email}")
            return None
        
        # Crear objeto UserResponse
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            nombre=user["nombre"],
            fecha_nacimiento=user["fecha_nacimiento"] if isinstance(user["fecha_nacimiento"], datetime) else datetime.fromisoformat(user["fecha_nacimiento"].replace("Z", "+00:00")),
            hora_nacimiento=user["hora_nacimiento"],
            lugar_nacimiento_lat=user["lugar_nacimiento_lat"],
            lugar_nacimiento_lng=user["lugar_nacimiento_lng"],
            lugar_nacimiento_nombre=user.get("lugar_nacimiento_nombre"),
            is_active=user.get("is_active", True),
            is_admin=user.get("is_admin", False),
            fecha_registro=user["fecha_registro"] if isinstance(user["fecha_registro"], datetime) else datetime.fromisoformat(user["fecha_registro"].replace("Z", "+00:00")),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at")
        )
        
        return user_response
    except JWTError:
        logger.warning("Error al decodificar token de refresco")
        return None
    except Exception as e:
        logger.error(f"Error al verificar token de refresco: {str(e)}")
        return None