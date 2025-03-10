"""
Rutas para predicciones astrológicas en la API de Prezagia.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Annotated, Optional
from datetime import date

from app.core.logger import logger
from app.schemas.user import UserResponse
from app.schemas.astrology import (
    PredictionCreate,
    PredictionResponse,
    PredictionDetail,
    PredictionType,
    PredictionPeriod,
    PredictionFilter
)
from app.services.security import get_current_user
from app.services.astrology.calculations import calculate_transits
from app.services.astrology.interpretation import interpret_prediction
from app.services.claude_api import generate_prediction_with_claude
from app.services.crud.query_service import (
    save_prediction_query,
    get_prediction_by_id,
    get_user_predictions,
    delete_prediction
)

router = APIRouter()

@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    prediction_data: PredictionCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Crea una nueva predicción astrológica basada en los datos proporcionados.
    """
    try:
        # Calcular tránsitos planetarios para el período de predicción
        transits = await calculate_transits(
            birth_date=prediction_data.birth_date,
            birth_time=prediction_data.birth_time,
            birth_latitude=prediction_data.birth_latitude,
            birth_longitude=prediction_data.birth_longitude,
            prediction_date=prediction_data.prediction_date,
            prediction_period=prediction_data.prediction_period
        )
        
        # Interpretar los tránsitos para la predicción
        interpretation = await interpret_prediction(
            transits=transits,
            prediction_type=prediction_data.prediction_type,
            prediction_period=prediction_data.prediction_period
        )
        
        # Mejorar la predicción con Claude AI
        enhanced_prediction = await generate_prediction_with_claude(
            transits=transits,
            interpretation=interpretation,
            prediction_type=prediction_data.prediction_type,
            prediction_period=prediction_data.prediction_period,
            focus_areas=prediction_data.focus_areas
        )
        
        # Guardar la consulta en la base de datos
        prediction = await save_prediction_query(
            user_id=current_user.id,
            prediction_data=prediction_data,
            transits=transits,
            interpretation=interpretation,
            enhanced_prediction=enhanced_prediction
        )
        
        logger.info(f"Predicción creada para usuario {current_user.id}, tipo: {prediction_data.prediction_type}")
        return prediction
        
    except Exception as e:
        logger.error(f"Error al crear predicción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la predicción: {str(e)}"
        )


@router.get("", response_model=List[PredictionResponse])
async def read_user_predictions(
    prediction_type: Optional[PredictionType] = None,
    period: Optional[PredictionPeriod] = None,
    name: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Obtiene todas las predicciones del usuario actual con filtros opcionales.
    """
    # Preparar filtros
    filters = PredictionFilter(
        prediction_type=prediction_type,
        period=period,
        name=name,
        from_date=from_date,
        to_date=to_date
    )
    
    # Obtener predicciones
    predictions = await get_user_predictions(
        user_id=current_user.id,
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    logger.debug(f"Usuario {current_user.id} solicitó sus predicciones. Total: {len(predictions)}")
    return predictions


@router.get("/{prediction_id}", response_model=PredictionDetail)
async def read_prediction_detail(
    prediction_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Obtiene detalles completos de una predicción específica.
    """
    # Obtener la predicción de la base de datos
    prediction = await get_prediction_by_id(prediction_id)
    
    # Verificar que existe
    if not prediction:
        logger.warning(f"Intento de acceso a predicción inexistente ID: {prediction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predicción no encontrada"
        )
    
    # Verificar que pertenece al usuario actual
    if prediction.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó acceder a predicción {prediction_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a esta predicción"
        )
    
    logger.debug(f"Usuario {current_user.id} solicitó detalles de predicción {prediction_id}")
    return prediction


@router.post("/{prediction_id}/refine", response_model=PredictionDetail)
async def refine_prediction(
    prediction_id: str,
    focus_areas: List[str],
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Refina una predicción existente enfocándose en áreas específicas.
    """
    # Obtener la predicción de la base de datos
    prediction = await get_prediction_by_id(prediction_id)
    
    # Verificar que existe
    if not prediction:
        logger.warning(f"Intento de refinar predicción inexistente ID: {prediction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predicción no encontrada"
        )
    
    # Verificar que pertenece al usuario actual
    if prediction.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó refinar predicción {prediction_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta predicción"
        )
    
    try:
        # Refinar la predicción con Claude AI
        refined_prediction = await generate_prediction_with_claude(
            transits=prediction.transits,
            interpretation=prediction.interpretation,
            prediction_type=prediction.prediction_type,
            prediction_period=prediction.prediction_period,
            focus_areas=focus_areas
        )
        
        # Actualizar la predicción en la base de datos
        # (Aquí se debería implementar la actualización de la predicción)
        
        logger.info(f"Predicción {prediction_id} refinada con áreas de enfoque: {', '.join(focus_areas)}")
        
        # Devolver la predicción con la nueva interpretación
        prediction.enhanced_prediction = refined_prediction
        return prediction
        
    except Exception as e:
        logger.error(f"Error al refinar predicción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al refinar la predicción: {str(e)}"
        )


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_prediction(
    prediction_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Elimina una predicción existente.
    """
    # Obtener la predicción de la base de datos
    prediction = await get_prediction_by_id(prediction_id)
    
    # Verificar que existe
    if not prediction:
        logger.warning(f"Intento de eliminar predicción inexistente ID: {prediction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predicción no encontrada"
        )
    
    # Verificar que pertenece al usuario actual
    if prediction.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó eliminar predicción {prediction_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta predicción"
        )
    
    # Eliminar la predicción
    await delete_prediction(prediction_id)
    
    logger.info(f"Predicción {prediction_id} eliminada por usuario {current_user.id}")
    return None