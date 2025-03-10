"""
Utilidades para manejo de contraseñas.

Este módulo proporciona funciones para la generación y verificación de hashes
de contraseñas, desacoplando estas funcionalidades para evitar importaciones circulares.
"""

from passlib.context import CryptContext

# Configuración de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con el hash.
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de contraseña almacenado
    
    Returns:
        bool: True si la contraseña coincide con el hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro para una contraseña.
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        str: Hash de la contraseña
    """
    return pwd_context.hash(password)