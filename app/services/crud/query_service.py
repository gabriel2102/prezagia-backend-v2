"""
Servicio de gestión de consultas astrológicas para la aplicación Prezagia.

Este módulo proporciona funciones para guardar, obtener y gestionar consultas
astrológicas como cartas natales, predicciones y análisis de compatibilidad.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date

from app.db.supabase import get_supabase
from app.schemas.astrology import (
    ChartCreate, ChartFilter,
    PredictionCreate, PredictionFilter,
    CompatibilityCreate, CompatibilityFilter
)
from app.schemas.query import QueryFilter
from app.core.logger import logger
from app.core.exceptions import DatabaseError, ResourceNotFoundError


#==============================================================================
# Funciones para cartas astrales
#==============================================================================

async def save_chart_query(user_id: str, chart_data: ChartCreate, 
                         calculation_result: Dict[str, Any],
                         interpretation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guarda una consulta de carta astral en la base de datos.
    
    Args:
        user_id: ID del usuario que realiza la consulta
        chart_data: Datos de la carta astral
        calculation_result: Resultado del cálculo astronómico
        interpretation: Interpretación de la carta
    
    Returns:
        Dict: Datos de la carta guardada
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Guardando consulta de carta astral para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Preparar datos para la tabla de consultas
        now = datetime.utcnow().isoformat()
        
        # Crear un resumen de la carta
        summary = (f"Carta {chart_data.chart_type.value} con Sol en {calculation_result.get('sun_sign', 'N/A')}, "
                  f"Luna en {calculation_result.get('moon_sign', 'N/A')} y "
                  f"Ascendente en {calculation_result.get('rising_sign', 'N/A')}")
        
        # Datos comunes para todas las consultas
        query_data = {
            "user_id": user_id,
            "query_type": f"chart_{chart_data.chart_type.value}",
            "query_name": chart_data.name or f"Carta {chart_data.chart_type.value} - {now}",
            "query_description": chart_data.description,
            "query_date": now,
            "is_favorite": False,
            "result_summary": summary,
            "query_data": chart_data.dict(),
            "result_data": {
                "calculation_result": calculation_result,
                "interpretation": interpretation
            },
            "created_at": now,
            "updated_at": now
        }
        
        # Guardar en la tabla de consultas
        response = supabase.table("consultas").insert(query_data).execute()
        
        if not response.data:
            raise DatabaseError("No se pudo guardar la consulta de carta astral")
        
        # Preparar respuesta con formato adecuado para la API
        chart_response = {
            "id": response.data[0]["id"],
            "user_id": user_id,
            "chart_type": chart_data.chart_type,
            "name": chart_data.name,
            "description": chart_data.description,
            "interpretation_depth": chart_data.interpretation_depth,
            "created_at": now,
            "sun_sign": calculation_result.get("sun_sign", "N/A"),
            "moon_sign": calculation_result.get("moon_sign", "N/A"),
            "rising_sign": calculation_result.get("rising_sign", "N/A"),
            "summary": summary,
            "calculation_result": calculation_result,
            "interpretation": interpretation
        }
        
        logger.info(f"Consulta de carta astral guardada exitosamente: {response.data[0]['id']}")
        return chart_response
        
    except Exception as e:
        logger.error(f"Error al guardar consulta de carta astral: {str(e)}")
        raise DatabaseError(f"Error al guardar consulta de carta astral: {str(e)}")


async def get_chart_by_id(chart_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una carta astral por su ID.
    
    Args:
        chart_id: ID de la carta astral
    
    Returns:
        Optional[Dict]: Datos de la carta o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando carta astral con ID: {chart_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("consultas").select("*").eq("id", chart_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.debug(f"Carta astral no encontrada: {chart_id}")
            return None
        
        query_data = response.data[0]
        
        # Verificar que es una consulta de tipo carta astral
        if not query_data["query_type"].startswith("chart_"):
            logger.warning(f"Consulta {chart_id} no es una carta astral")
            return None
        
        # Formatear respuesta para la API
        chart_type = query_data["query_type"].replace("chart_", "")
        chart_data = query_data["query_data"]
        result_data = query_data["result_data"]
        
        chart_response = {
            "id": query_data["id"],
            "user_id": query_data["user_id"],
            "chart_type": chart_type,
            "name": query_data["query_name"],
            "description": query_data["query_description"],
            "interpretation_depth": chart_data.get("interpretation_depth", 3),
            "created_at": query_data["created_at"],
            "birth_date": chart_data.get("birth_date"),
            "birth_time": chart_data.get("birth_time"),
            "latitude": chart_data.get("latitude"),
            "longitude": chart_data.get("longitude"),
            "location_name": chart_data.get("location_name"),
            "secondary_date": chart_data.get("secondary_date"),
            "person2_birth_date": chart_data.get("person2_birth_date"),
            "person2_birth_time": chart_data.get("person2_birth_time"),
            "person2_latitude": chart_data.get("person2_latitude"),
            "person2_longitude": chart_data.get("person2_longitude"),
            "person2_location_name": chart_data.get("person2_location_name"),
            "sun_sign": result_data.get("calculation_result", {}).get("sun_sign", "N/A"),
            "moon_sign": result_data.get("calculation_result", {}).get("moon_sign", "N/A"),
            "rising_sign": result_data.get("calculation_result", {}).get("rising_sign", "N/A"),
            "summary": query_data["result_summary"],
            "calculation_result": result_data.get("calculation_result", {}),
            "interpretation": result_data.get("interpretation", {})
        }
        
        logger.debug(f"Carta astral recuperada: {chart_id}")
        return chart_response
        
    except Exception as e:
        logger.error(f"Error al obtener carta astral {chart_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener carta astral: {str(e)}")


async def get_user_charts(user_id: str, filters: ChartFilter = None, 
                       skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Obtiene todas las cartas astrales de un usuario con filtros opcionales.
    
    Args:
        user_id: ID del usuario
        filters: Filtros a aplicar
        skip: Número de registros a omitir (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        List[Dict]: Lista de cartas astrales
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Obteniendo cartas astrales para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Iniciar la consulta
        query = supabase.table("consultas").select("*")
        
        # Filtro por usuario
        query = query.eq("user_id", user_id)
        
        # Filtrar solo consultas de tipo carta astral
        if filters and filters.chart_type:
            query = query.eq("query_type", f"chart_{filters.chart_type.value}")
        else:
            query = query.like("query_type", "chart_%")
        
        # Filtros adicionales
        if filters:
            if filters.name:
                query = query.ilike("query_name", f"%{filters.name}%")
            
            if filters.from_date:
                query = query.gte("created_at", filters.from_date.isoformat())
            
            if filters.to_date:
                query = query.lte("created_at", filters.to_date.isoformat())
        
        # Ordenar por fecha de creación descendente
        query = query.order("created_at", desc=True)
        
        # Aplicar paginación
        query = query.range(skip, skip + limit - 1)
        
        # Ejecutar consulta
        response = query.execute()
        
        charts = []
        for query_data in response.data:
            # Formatear respuesta para la API
            chart_type = query_data["query_type"].replace("chart_", "")
            result_data = query_data["result_data"]
            
            chart_response = {
                "id": query_data["id"],
                "user_id": query_data["user_id"],
                "chart_type": chart_type,
                "name": query_data["query_name"],
                "description": query_data["query_description"],
                "created_at": query_data["created_at"],
                "sun_sign": result_data.get("calculation_result", {}).get("sun_sign", "N/A"),
                "moon_sign": result_data.get("calculation_result", {}).get("moon_sign", "N/A"),
                "rising_sign": result_data.get("calculation_result", {}).get("rising_sign", "N/A"),
                "summary": query_data["result_summary"]
            }
            
            charts.append(chart_response)
        
        logger.debug(f"Se encontraron {len(charts)} cartas astrales para el usuario {user_id}")
        return charts
        
    except Exception as e:
        logger.error(f"Error al obtener cartas astrales del usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener cartas astrales: {str(e)}")


async def delete_chart(chart_id: str) -> bool:
    """
    Elimina una carta astral por su ID.
    
    Args:
        chart_id: ID de la carta astral
    
    Returns:
        bool: True si se eliminó correctamente
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
        ResourceNotFoundError: Si la carta no existe
    """
    logger.info(f"Eliminando carta astral: {chart_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que la carta existe
        chart = await get_chart_by_id(chart_id)
        if not chart:
            logger.warning(f"Intento de eliminar carta astral inexistente: {chart_id}")
            raise ResourceNotFoundError("Carta astral", chart_id)
        
        # Eliminar la carta
        response = supabase.table("consultas").delete().eq("id", chart_id).execute()
        
        logger.info(f"Carta astral eliminada correctamente: {chart_id}")
        return True
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar carta astral {chart_id}: {str(e)}")
        raise DatabaseError(f"Error al eliminar carta astral: {str(e)}")


#==============================================================================
# Funciones para predicciones astrológicas
#==============================================================================

async def save_prediction_query(user_id: str, prediction_data: PredictionCreate, 
                             transits: Dict[str, Any],
                             interpretation: Dict[str, Any],
                             enhanced_prediction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guarda una consulta de predicción astrológica en la base de datos.
    
    Args:
        user_id: ID del usuario que realiza la consulta
        prediction_data: Datos de la predicción
        transits: Datos de tránsitos calculados
        interpretation: Interpretación básica
        enhanced_prediction: Predicción mejorada con IA
    
    Returns:
        Dict: Datos de la predicción guardada
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Guardando consulta de predicción para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Preparar datos para la tabla de consultas
        now = datetime.utcnow().isoformat()
        
        # Crear un resumen de la predicción
        summary = (f"Predicción {prediction_data.prediction_type.value} para "
                  f"{prediction_data.prediction_period.value} desde {prediction_data.prediction_date}")
        
        # Datos comunes para todas las consultas
        query_data = {
            "user_id": user_id,
            "query_type": f"prediction_{prediction_data.prediction_type.value}",
            "query_name": prediction_data.name or f"Predicción {prediction_data.prediction_type.value} - {now}",
            "query_description": prediction_data.description,
            "query_date": now,
            "is_favorite": False,
            "result_summary": enhanced_prediction.get("summary", summary),
            "query_data": prediction_data.dict(),
            "result_data": {
                "transits": transits,
                "interpretation": interpretation,
                "enhanced_prediction": enhanced_prediction
            },
            "created_at": now,
            "updated_at": now
        }
        
        # Guardar en la tabla de consultas
        response = supabase.table("consultas").insert(query_data).execute()
        
        if not response.data:
            raise DatabaseError("No se pudo guardar la consulta de predicción")
        
        # Preparar respuesta con formato adecuado para la API
        prediction_response = {
            "id": response.data[0]["id"],
            "user_id": user_id,
            "prediction_type": prediction_data.prediction_type,
            "prediction_period": prediction_data.prediction_period,
            "name": prediction_data.name,
            "description": prediction_data.description,
            "prediction_date": prediction_data.prediction_date,
            "end_date": prediction_data.end_date,
            "focus_areas": prediction_data.focus_areas,
            "created_at": now,
            "summary": enhanced_prediction.get("summary", summary),
            "birth_date": prediction_data.birth_date,
            "birth_time": prediction_data.birth_time,
            "birth_latitude": prediction_data.birth_latitude,
            "birth_longitude": prediction_data.birth_longitude,
            "birth_location_name": prediction_data.birth_location_name,
            "transits": transits,
            "interpretation": interpretation,
            "enhanced_prediction": enhanced_prediction
        }
        
        logger.info(f"Consulta de predicción guardada exitosamente: {response.data[0]['id']}")
        return prediction_response
        
    except Exception as e:
        logger.error(f"Error al guardar consulta de predicción: {str(e)}")
        raise DatabaseError(f"Error al guardar consulta de predicción: {str(e)}")


async def get_prediction_by_id(prediction_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una predicción astrológica por su ID.
    
    Args:
        prediction_id: ID de la predicción
    
    Returns:
        Optional[Dict]: Datos de la predicción o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando predicción con ID: {prediction_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("consultas").select("*").eq("id", prediction_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.debug(f"Predicción no encontrada: {prediction_id}")
            return None
        
        query_data = response.data[0]
        
        # Verificar que es una consulta de tipo predicción
        if not query_data["query_type"].startswith("prediction_"):
            logger.warning(f"Consulta {prediction_id} no es una predicción")
            return None
        
        # Formatear respuesta para la API
        prediction_type = query_data["query_type"].replace("prediction_", "")
        prediction_data = query_data["query_data"]
        result_data = query_data["result_data"]
        
        prediction_response = {
            "id": query_data["id"],
            "user_id": query_data["user_id"],
            "prediction_type": prediction_type,
            "prediction_period": prediction_data.get("prediction_period"),
            "name": query_data["query_name"],
            "description": query_data["query_description"],
            "prediction_date": prediction_data.get("prediction_date"),
            "end_date": prediction_data.get("end_date"),
            "focus_areas": prediction_data.get("focus_areas", []),
            "created_at": query_data["created_at"],
            "birth_date": prediction_data.get("birth_date"),
            "birth_time": prediction_data.get("birth_time"),
            "birth_latitude": prediction_data.get("birth_latitude"),
            "birth_longitude": prediction_data.get("birth_longitude"),
            "birth_location_name": prediction_data.get("birth_location_name"),
            "summary": query_data["result_summary"],
            "transits": result_data.get("transits", {}),
            "interpretation": result_data.get("interpretation", {}),
            "enhanced_prediction": result_data.get("enhanced_prediction", {})
        }
        
        logger.debug(f"Predicción recuperada: {prediction_id}")
        return prediction_response
        
    except Exception as e:
        logger.error(f"Error al obtener predicción {prediction_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener predicción: {str(e)}")


async def get_user_predictions(user_id: str, filters: PredictionFilter = None, 
                            skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Obtiene todas las predicciones de un usuario con filtros opcionales.
    
    Args:
        user_id: ID del usuario
        filters: Filtros a aplicar
        skip: Número de registros a omitir (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        List[Dict]: Lista de predicciones
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Obteniendo predicciones para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Iniciar la consulta
        query = supabase.table("consultas").select("*")
        
        # Filtro por usuario
        query = query.eq("user_id", user_id)
        
        # Filtrar solo consultas de tipo predicción
        if filters and filters.prediction_type:
            query = query.eq("query_type", f"prediction_{filters.prediction_type.value}")
        else:
            query = query.like("query_type", "prediction_%")
        
        # Filtros adicionales
        if filters:
            if filters.name:
                query = query.ilike("query_name", f"%{filters.name}%")
            
            if filters.from_date:
                query = query.gte("created_at", filters.from_date.isoformat())
            
            if filters.to_date:
                query = query.lte("created_at", filters.to_date.isoformat())
        
        # Ordenar por fecha de creación descendente
        query = query.order("created_at", desc=True)
        
        # Aplicar paginación
        query = query.range(skip, skip + limit - 1)
        
        # Ejecutar consulta
        response = query.execute()
        
        predictions = []
        for query_data in response.data:
            # Formatear respuesta para la API
            prediction_type = query_data["query_type"].replace("prediction_", "")
            prediction_data = query_data["query_data"]
            
            prediction_response = {
                "id": query_data["id"],
                "user_id": query_data["user_id"],
                "prediction_type": prediction_type,
                "prediction_period": prediction_data.get("prediction_period"),
                "name": query_data["query_name"],
                "description": query_data["query_description"],
                "prediction_date": prediction_data.get("prediction_date"),
                "end_date": prediction_data.get("end_date"),
                "focus_areas": prediction_data.get("focus_areas", []),
                "created_at": query_data["created_at"],
                "summary": query_data["result_summary"]
            }
            
            predictions.append(prediction_response)
        
        logger.debug(f"Se encontraron {len(predictions)} predicciones para el usuario {user_id}")
        return predictions
        
    except Exception as e:
        logger.error(f"Error al obtener predicciones del usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener predicciones: {str(e)}")


async def delete_prediction(prediction_id: str) -> bool:
    """
    Elimina una predicción por su ID.
    
    Args:
        prediction_id: ID de la predicción
    
    Returns:
        bool: True si se eliminó correctamente
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
        ResourceNotFoundError: Si la predicción no existe
    """
    logger.info(f"Eliminando predicción: {prediction_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que la predicción existe
        prediction = await get_prediction_by_id(prediction_id)
        if not prediction:
            logger.warning(f"Intento de eliminar predicción inexistente: {prediction_id}")
            raise ResourceNotFoundError("Predicción", prediction_id)
        
        # Eliminar la predicción
        response = supabase.table("consultas").delete().eq("id", prediction_id).execute()
        
        logger.info(f"Predicción eliminada correctamente: {prediction_id}")
        return True
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar predicción {prediction_id}: {str(e)}")
        raise DatabaseError(f"Error al eliminar predicción: {str(e)}")


#==============================================================================
# Funciones para análisis de compatibilidad
#==============================================================================

async def save_compatibility_query(user_id: str, compatibility_data: CompatibilityCreate, 
                                calculation_result: Dict[str, Any],
                                interpretation: Dict[str, Any],
                                enhanced_interpretation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Guarda una consulta de compatibilidad astrológica en la base de datos.
    
    Args:
        user_id: ID del usuario que realiza la consulta
        compatibility_data: Datos de la compatibilidad
        calculation_result: Resultado del cálculo
        interpretation: Interpretación básica
        enhanced_interpretation: Interpretación mejorada con IA
    
    Returns:
        Dict: Datos de la compatibilidad guardada
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.info(f"Guardando consulta de compatibilidad para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Preparar datos para la tabla de consultas
        now = datetime.utcnow().isoformat()
        
        # Calcular puntuación de compatibilidad (ejemplo)
        compatibility_score = calculation_result.get("compatibility_score", 50.0)
        
        # Crear un resumen de la compatibilidad
        summary = (f"Compatibilidad {compatibility_data.compatibility_type.value} entre "
                  f"{compatibility_data.person1_name} y {compatibility_data.person2_name}")
        
        # Datos comunes para todas las consultas
        query_data = {
            "user_id": user_id,
            "query_type": f"compatibility_{compatibility_data.compatibility_type.value}",
            "query_name": compatibility_data.name or f"Compatibilidad {compatibility_data.compatibility_type.value} - {now}",
            "query_description": compatibility_data.description,
            "query_date": now,
            "is_favorite": False,
            "result_summary": enhanced_interpretation.get("summary", summary),
            "query_data": compatibility_data.dict(),
            "result_data": {
                "calculation_result": calculation_result,
                "interpretation": interpretation,
                "enhanced_interpretation": enhanced_interpretation,
                "compatibility_score": compatibility_score
            },
            "created_at": now,
            "updated_at": now
        }
        
        # Guardar en la tabla de consultas
        response = supabase.table("consultas").insert(query_data).execute()
        
        if not response.data:
            raise DatabaseError("No se pudo guardar la consulta de compatibilidad")
        
        # Preparar respuesta con formato adecuado para la API
        compatibility_response = {
            "id": response.data[0]["id"],
            "user_id": user_id,
            "compatibility_type": compatibility_data.compatibility_type,
            "name": compatibility_data.name,
            "description": compatibility_data.description,
            "person1_name": compatibility_data.person1_name,
            "person2_name": compatibility_data.person2_name,
            "focus_areas": compatibility_data.focus_areas,
            "created_at": now,
            "compatibility_score": compatibility_score,
            "summary": enhanced_interpretation.get("summary", summary),
            "person1_birth_date": compatibility_data.person1_birth_date,
            "person1_birth_time": compatibility_data.person1_birth_time,
            "person1_latitude": compatibility_data.person1_latitude,
            "person1_longitude": compatibility_data.person1_longitude,
            "person1_location_name": compatibility_data.person1_location_name,
            "person2_birth_date": compatibility_data.person2_birth_date,
            "person2_birth_time": compatibility_data.person2_birth_time,
            "person2_latitude": compatibility_data.person2_latitude,
            "person2_longitude": compatibility_data.person2_longitude,
            "person2_location_name": compatibility_data.person2_location_name,
            "calculation_result": calculation_result,
            "interpretation": interpretation,
            "enhanced_interpretation": enhanced_interpretation
        }
        
        logger.info(f"Consulta de compatibilidad guardada exitosamente: {response.data[0]['id']}")
        return compatibility_response
        
    except Exception as e:
        logger.error(f"Error al guardar consulta de compatibilidad: {str(e)}")
        raise DatabaseError(f"Error al guardar consulta de compatibilidad: {str(e)}")


async def get_compatibility_by_id(compatibility_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un análisis de compatibilidad por su ID.
    
    Args:
        compatibility_id: ID de la compatibilidad
    
    Returns:
        Optional[Dict]: Datos de la compatibilidad o None si no existe
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando compatibilidad con ID: {compatibility_id}")
    supabase = get_supabase()
    
    try:
        response = supabase.table("consultas").select("*").eq("id", compatibility_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.debug(f"Compatibilidad no encontrada: {compatibility_id}")
            return None
        
        query_data = response.data[0]
        
        # Verificar que es una consulta de tipo compatibilidad
        if not query_data["query_type"].startswith("compatibility_"):
            logger.warning(f"Consulta {compatibility_id} no es una compatibilidad")
            return None
        
        # Formatear respuesta para la API
        compatibility_type = query_data["query_type"].replace("compatibility_", "")
        compatibility_data = query_data["query_data"]
        result_data = query_data["result_data"]
        
        compatibility_response = {
            "id": query_data["id"],
            "user_id": query_data["user_id"],
            "compatibility_type": compatibility_type,
            "name": query_data["query_name"],
            "description": query_data["query_description"],
            "person1_name": compatibility_data.get("person1_name"),
            "person2_name": compatibility_data.get("person2_name"),
            "focus_areas": compatibility_data.get("focus_areas", []),
            "created_at": query_data["created_at"],
            "compatibility_score": result_data.get("compatibility_score", 50.0),
            "summary": query_data["result_summary"],
            "person1_birth_date": compatibility_data.get("person1_birth_date"),
            "person1_birth_time": compatibility_data.get("person1_birth_time"),
            "person1_latitude": compatibility_data.get("person1_latitude"),
            "person1_longitude": compatibility_data.get("person1_longitude"),
            "person1_location_name": compatibility_data.get("person1_location_name"),
            "person2_birth_date": compatibility_data.get("person2_birth_date"),
            "person2_birth_time": compatibility_data.get("person2_birth_time"),
            "person2_latitude": compatibility_data.get("person2_latitude"),
            "person2_longitude": compatibility_data.get("person2_longitude"),
            "person2_location_name": compatibility_data.get("person2_location_name"),
            "calculation_result": result_data.get("calculation_result", {}),
            "interpretation": result_data.get("interpretation", {}),
            "enhanced_interpretation": result_data.get("enhanced_interpretation", {})
        }
        
        logger.debug(f"Compatibilidad recuperada: {compatibility_id}")
        return compatibility_response
        
    except Exception as e:
        logger.error(f"Error al obtener compatibilidad {compatibility_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener compatibilidad: {str(e)}")


async def get_user_compatibilities(user_id: str, filters: CompatibilityFilter = None, 
                               skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Obtiene todos los análisis de compatibilidad de un usuario con filtros opcionales.
    
    Args:
        user_id: ID del usuario
        filters: Filtros a aplicar
        skip: Número de registros a omitir (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        List[Dict]: Lista de análisis de compatibilidad
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Obteniendo compatibilidades para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Iniciar la consulta
        query = supabase.table("consultas").select("*")
        
        # Filtro por usuario
        query = query.eq("user_id", user_id)
        
        # Filtrar solo consultas de tipo compatibilidad
        if filters and filters.compatibility_type:
            query = query.eq("query_type", f"compatibility_{filters.compatibility_type.value}")
        else:
            query = query.like("query_type", "compatibility_%")
        
        # Filtros adicionales
        if filters:
            if filters.name:
                query = query.ilike("query_name", f"%{filters.name}%")
            
            if filters.person1_name:
                # Filtrar por contenido en campos JSON
                query = query.like("query_data->>person1_name", f"%{filters.person1_name}%")
            
            if filters.person2_name:
                query = query.like("query_data->>person2_name", f"%{filters.person2_name}%")
        
        # Ordenar por fecha de creación descendente
        query = query.order("created_at", desc=True)
        
        # Aplicar paginación
        query = query.range(skip, skip + limit - 1)
        
        # Ejecutar consulta
        response = query.execute()
        
        compatibilities = []
        for query_data in response.data:
            # Formatear respuesta para la API
            compatibility_type = query_data["query_type"].replace("compatibility_", "")
            compatibility_data = query_data["query_data"]
            result_data = query_data["result_data"]
            
            compatibility_response = {
                "id": query_data["id"],
                "user_id": query_data["user_id"],
                "compatibility_type": compatibility_type,
                "name": query_data["query_name"],
                "description": query_data["query_description"],
                "person1_name": compatibility_data.get("person1_name", "Persona 1"),
                "person2_name": compatibility_data.get("person2_name", "Persona 2"),
                "focus_areas": compatibility_data.get("focus_areas", []),
                "created_at": query_data["created_at"],
                "compatibility_score": result_data.get("compatibility_score", 50.0),
                "summary": query_data["result_summary"]
            }
            
            compatibilities.append(compatibility_response)
        
        logger.debug(f"Se encontraron {len(compatibilities)} compatibilidades para el usuario {user_id}")
        return compatibilities
        
    except Exception as e:
        logger.error(f"Error al obtener compatibilidades del usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener compatibilidades: {str(e)}")


async def delete_compatibility(compatibility_id: str) -> bool:
    """
    Elimina un análisis de compatibilidad por su ID.
    
    Args:
        compatibility_id: ID de la compatibilidad
    
    Returns:
        bool: True si se eliminó correctamente
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
        ResourceNotFoundError: Si la compatibilidad no existe
    """
    logger.info(f"Eliminando compatibilidad: {compatibility_id}")
    supabase = get_supabase()
    
    try:
        # Verificar que la compatibilidad existe
        compatibility = await get_compatibility_by_id(compatibility_id)
        if not compatibility:
            logger.warning(f"Intento de eliminar compatibilidad inexistente: {compatibility_id}")
            raise ResourceNotFoundError("Compatibilidad", compatibility_id)
        
        # Eliminar la compatibilidad
        response = supabase.table("consultas").delete().eq("id", compatibility_id).execute()
        
        logger.info(f"Compatibilidad eliminada correctamente: {compatibility_id}")
        return True
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar compatibilidad {compatibility_id}: {str(e)}")
        raise DatabaseError(f"Error al eliminar compatibilidad: {str(e)}")


#==============================================================================
# Funciones generales para consultas
#==============================================================================

async def get_recent_queries(user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Obtiene las consultas más recientes de un usuario, independientemente del tipo.
    
    Args:
        user_id: ID del usuario
        limit: Número máximo de consultas a devolver
    
    Returns:
        List[Dict]: Lista de consultas recientes
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Obteniendo consultas recientes para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Consulta para obtener las consultas más recientes
        response = supabase.table("consultas") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        recent_queries = []
        for query_data in response.data:
            # Determinar el tipo de consulta para formatear apropiadamente
            query_type = query_data["query_type"]
            
            # Datos básicos comunes a todos los tipos
            query_response = {
                "id": query_data["id"],
                "user_id": query_data["user_id"],
                "query_type": query_type,
                "name": query_data["query_name"],
                "description": query_data["query_description"],
                "created_at": query_data["created_at"],
                "summary": query_data["result_summary"]
            }
            
            recent_queries.append(query_response)
        
        logger.debug(f"Se encontraron {len(recent_queries)} consultas recientes para el usuario {user_id}")
        return recent_queries
        
    except Exception as e:
        logger.error(f"Error al obtener consultas recientes del usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener consultas recientes: {str(e)}")


async def update_query_favorite(query_id: str, is_favorite: bool) -> Dict[str, Any]:
    """
    Marca o desmarca una consulta como favorita.
    
    Args:
        query_id: ID de la consulta
        is_favorite: Estado de favorito
    
    Returns:
        Dict: Datos actualizados de la consulta
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
        ResourceNotFoundError: Si la consulta no existe
    """
    logger.info(f"Actualizando estado favorito de consulta {query_id}: {is_favorite}")
    supabase = get_supabase()
    
    try:
        # Verificar que la consulta existe
        response = supabase.table("consultas").select("*").eq("id", query_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Intento de actualizar consulta inexistente: {query_id}")
            raise ResourceNotFoundError("Consulta", query_id)
        
        # Actualizar estado de favorito
        update_response = supabase.table("consultas") \
            .update({"is_favorite": is_favorite}) \
            .eq("id", query_id) \
            .execute()
        
        if not update_response.data or len(update_response.data) == 0:
            raise DatabaseError(f"No se pudo actualizar la consulta {query_id}")
        
        logger.info(f"Estado favorito de consulta {query_id} actualizado correctamente")
        return update_response.data[0]
        
    except ResourceNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar estado favorito de consulta {query_id}: {str(e)}")
        raise DatabaseError(f"Error al actualizar estado favorito: {str(e)}")


async def get_user_favorite_queries(user_id: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Obtiene todas las consultas favoritas de un usuario.
    
    Args:
        user_id: ID del usuario
        skip: Número de registros a omitir (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        List[Dict]: Lista de consultas favoritas
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Obteniendo consultas favoritas para usuario: {user_id}")
    supabase = get_supabase()
    
    try:
        # Consulta para obtener las consultas favoritas
        response = supabase.table("consultas") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("is_favorite", True) \
            .order("created_at", desc=True) \
            .range(skip, skip + limit - 1) \
            .execute()
        
        favorite_queries = []
        for query_data in response.data:
            # Determinar el tipo de consulta para formatear apropiadamente
            query_type = query_data["query_type"]
            
            # Datos básicos comunes a todos los tipos
            query_response = {
                "id": query_data["id"],
                "user_id": query_data["user_id"],
                "query_type": query_type,
                "name": query_data["query_name"],
                "description": query_data["query_description"],
                "created_at": query_data["created_at"],
                "summary": query_data["result_summary"]
            }
            
            favorite_queries.append(query_response)
        
        logger.debug(f"Se encontraron {len(favorite_queries)} consultas favoritas para el usuario {user_id}")
        return favorite_queries
        
    except Exception as e:
        logger.error(f"Error al obtener consultas favoritas del usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al obtener consultas favoritas: {str(e)}")


async def search_user_queries(user_id: str, search_term: str, 
                           filters: QueryFilter = None,
                           skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Busca consultas de un usuario por término de búsqueda y filtros opcionales.
    
    Args:
        user_id: ID del usuario
        search_term: Término de búsqueda
        filters: Filtros adicionales
        skip: Número de registros a omitir (paginación)
        limit: Número máximo de registros a devolver
    
    Returns:
        List[Dict]: Lista de consultas que coinciden con la búsqueda
    
    Raises:
        DatabaseError: Si ocurre algún error en la base de datos
    """
    logger.debug(f"Buscando consultas para usuario {user_id} con término: {search_term}")
    supabase = get_supabase()
    
    try:
        # Iniciar la consulta
        query = supabase.table("consultas").select("*")
        
        # Filtro por usuario
        query = query.eq("user_id", user_id)
        
        # Buscar en nombre y descripción
        if search_term:
            query = query.or_(f"query_name.ilike.%{search_term}%,query_description.ilike.%{search_term}%,result_summary.ilike.%{search_term}%")
        
        # Aplicar filtros adicionales
        if filters:
            if filters.query_type:
                query = query.like("query_type", f"{filters.query_type}%")
            
            if filters.query_name:
                query = query.ilike("query_name", f"%{filters.query_name}%")
            
            if filters.is_favorite is not None:
                query = query.eq("is_favorite", filters.is_favorite)
            
            if filters.start_date:
                query = query.gte("created_at", filters.start_date.isoformat())
            
            if filters.end_date:
                query = query.lte("created_at", filters.end_date.isoformat())
        
        # Ordenar por fecha de creación descendente
        query = query.order("created_at", desc=True)
        
        # Aplicar paginación
        query = query.range(skip, skip + limit - 1)
        
        # Ejecutar consulta
        response = query.execute()
        
        search_results = []
        for query_data in response.data:
            # Determinar el tipo de consulta para formatear apropiadamente
            query_type = query_data["query_type"]
            
            # Datos básicos comunes a todos los tipos
            query_response = {
                "id": query_data["id"],
                "user_id": query_data["user_id"],
                "query_type": query_type,
                "name": query_data["query_name"],
                "description": query_data["query_description"],
                "created_at": query_data["created_at"],
                "is_favorite": query_data["is_favorite"],
                "summary": query_data["result_summary"]
            }
            
            search_results.append(query_response)
        
        logger.debug(f"Se encontraron {len(search_results)} consultas que coinciden con la búsqueda")
        return search_results
        
    except Exception as e:
        logger.error(f"Error al buscar consultas para usuario {user_id}: {str(e)}")
        raise DatabaseError(f"Error al buscar consultas: {str(e)}")