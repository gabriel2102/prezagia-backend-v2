"""
Módulo de servicios CRUD para la aplicación Prezagia.

Este paquete contiene los servicios para la gestión de datos (CRUD)
para las diferentes entidades del sistema.
"""

# Exportar funciones del servicio de usuarios
from app.services.crud.user_service import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
    delete_user,
    get_users
)

# Exportar funciones del servicio de perfiles
from app.services.crud.profile_service import (
    create_profile,
    get_profile_by_id,
    get_profile_by_user_id,
    update_profile,
    delete_profile,
    get_profiles_by_user_ids
)

# Exportar funciones del servicio de configuración
from app.services.crud.config_service import (
    get_user_configuration,
    create_default_configuration,
    update_user_configuration,
    update_query_count,
    check_query_limit,
    update_premium_status
)

# Exportar funciones del servicio de consultas
from app.services.crud.query_service import (
    # Cartas astrales
    save_chart_query,
    get_chart_by_id,
    get_user_charts,
    delete_chart,
    
    # Predicciones
    save_prediction_query,
    get_prediction_by_id,
    get_user_predictions,
    delete_prediction,
    
    # Compatibilidad
    save_compatibility_query,
    get_compatibility_by_id,
    get_user_compatibilities,
    delete_compatibility,
    
    # Funciones generales
    get_recent_queries,
    update_query_favorite,
    get_user_favorite_queries,
    search_user_queries
)

# Para simplificar las importaciones
__all__ = [
    # Usuario
    'create_user', 'get_user_by_email', 'get_user_by_id', 'update_user', 'delete_user', 'get_users',
    
    # Perfil
    'create_profile', 'get_profile_by_id', 'get_profile_by_user_id', 'update_profile', 
    'delete_profile', 'get_profiles_by_user_ids',
    
    # Configuración
    'get_user_configuration', 'create_default_configuration', 'update_user_configuration',
    'update_query_count', 'check_query_limit', 'update_premium_status',
    
    # Consultas - Cartas
    'save_chart_query', 'get_chart_by_id', 'get_user_charts', 'delete_chart',
    
    # Consultas - Predicciones
    'save_prediction_query', 'get_prediction_by_id', 'get_user_predictions', 'delete_prediction',
    
    # Consultas - Compatibilidad
    'save_compatibility_query', 'get_compatibility_by_id', 'get_user_compatibilities', 'delete_compatibility',
    
    # Consultas - General
    'get_recent_queries', 'update_query_favorite', 'get_user_favorite_queries', 'search_user_queries'
]