"""
Rutas para cartas astrales en la API de Prezagia.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Annotated, Optional

from app.core.logger import logger
from app.schemas.user import UserResponse
from app.schemas.astrology import (
    ChartCreate,
    ChartResponse,
    ChartDetail,
    ChartType,
    ChartFilter
)
from app.services.security import get_current_user
from app.services.astrology.calculations import calculate_chart
from app.services.astrology.interpretation import interpret_chart
from app.services.crud.query_service import (
    save_chart_query,
    get_chart_by_id,
    get_user_charts,
    delete_chart
)

router = APIRouter()

@router.post("", response_model=ChartResponse, status_code=status.HTTP_201_CREATED)
async def create_chart(
    chart_data: ChartCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Crea una nueva carta astral basada en los datos proporcionados.
    """
    try:
        # Calcular la carta astral
        chart_calculation = await calculate_chart(
            birth_date=chart_data.birth_date,
            birth_time=chart_data.birth_time,
            latitude=chart_data.latitude,
            longitude=chart_data.longitude,
            chart_type=chart_data.chart_type
        )
        
        # Interpretar la carta astral
        chart_interpretation = await interpret_chart(
            chart_calculation=chart_calculation,
            chart_type=chart_data.chart_type,
            interpretation_depth=chart_data.interpretation_depth
        )
        
        # Guardar la consulta en la base de datos
        chart = await save_chart_query(
            user_id=current_user.id,
            chart_data=chart_data,
            calculation_result=chart_calculation,
            interpretation=chart_interpretation
        )
        
        logger.info(f"Carta astral creada para usuario {current_user.id}, tipo: {chart_data.chart_type}")
        return chart
        
    except Exception as e:
        logger.error(f"Error al crear carta astral: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la carta astral: {str(e)}"
        )


@router.get("", response_model=List[ChartResponse])
async def read_user_charts(
    chart_type: Optional[ChartType] = None,
    name: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Obtiene todas las cartas astrales del usuario actual con filtros opcionales.
    """
    # Preparar filtros
    filters = ChartFilter(
        chart_type=chart_type,
        name=name
    )
    
    # Obtener cartas astrales
    charts = await get_user_charts(
        user_id=current_user.id,
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    logger.debug(f"Usuario {current_user.id} solicitó sus cartas astrales. Total: {len(charts)}")
    return charts


@router.get("/{chart_id}", response_model=ChartDetail)
async def read_chart_detail(
    chart_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Obtiene detalles completos de una carta astral específica.
    """
    # Obtener la carta astral de la base de datos
    chart = await get_chart_by_id(chart_id)
    
    # Verificar que existe
    if not chart:
        logger.warning(f"Intento de acceso a carta astral inexistente ID: {chart_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carta astral no encontrada"
        )
    
    # Verificar que pertenece al usuario actual
    if chart.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó acceder a carta astral {chart_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a esta carta astral"
        )
    
    logger.debug(f"Usuario {current_user.id} solicitó detalles de carta astral {chart_id}")
    return chart


@router.post("/{chart_id}/interpret", response_model=ChartDetail)
async def reinterpret_chart(
    chart_id: str,
    interpretation_depth: int = Query(2, ge=1, le=5),
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Reinterpreta una carta astral existente con una profundidad diferente.
    """
    # Obtener la carta astral de la base de datos
    chart = await get_chart_by_id(chart_id)
    
    # Verificar que existe
    if not chart:
        logger.warning(f"Intento de reinterpretar carta astral inexistente ID: {chart_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carta astral no encontrada"
        )
    
    # Verificar que pertenece al usuario actual
    if chart.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó reinterpretar carta astral {chart_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar esta carta astral"
        )
    
    try:
        # Reinterpretar la carta astral
        chart_interpretation = await interpret_chart(
            chart_calculation=chart.calculation_result,
            chart_type=chart.chart_type,
            interpretation_depth=interpretation_depth
        )
        
        # Actualizar la interpretación en la base de datos
        # (Aquí se debería implementar la actualización de la interpretación)
        
        logger.info(f"Carta astral {chart_id} reinterpretada con profundidad {interpretation_depth}")
        
        # Devolver la carta con la nueva interpretación
        chart.interpretation = chart_interpretation
        return chart
        
    except Exception as e:
        logger.error(f"Error al reinterpretar carta astral: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reinterpretar la carta astral: {str(e)}"
        )


@router.delete("/{chart_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_chart(
    chart_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Elimina una carta astral existente.
    """
    # Obtener la carta astral de la base de datos
    chart = await get_chart_by_id(chart_id)
    
    # Verificar que existe
    if not chart:
        logger.warning(f"Intento de eliminar carta astral inexistente ID: {chart_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carta astral no encontrada"
        )
    
    # Verificar que pertenece al usuario actual
    if chart.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó eliminar carta astral {chart_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar esta carta astral"
        )
    
    # Eliminar la carta astral
    await delete_chart(chart_id)
    
    logger.info(f"Carta astral {chart_id} eliminada por usuario {current_user.id}")
    return None