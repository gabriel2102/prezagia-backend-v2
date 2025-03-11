"""
Rutas para análisis de compatibilidad astrológica en la API de Prezagia.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Annotated, Optional

from app.core.logger import logger
from app.schemas.user import UserResponse
from app.schemas.astrology import (
    CompatibilityCreate,
    CompatibilityResponse,
    CompatibilityDetail,
    CompatibilityType,
    CompatibilityFilter
)
from app.services.security import get_current_user
from app.services.astrology.calculations import calculate_compatibility
from app.services.astrology.interpretation import interpret_compatibility
from app.services.claude_api import enhance_compatibility_with_claude
from app.services.crud.query_service import (
    save_compatibility_query,
    get_compatibility_by_id,
    get_user_compatibilities,
    delete_compatibility
)

router = APIRouter()

@router.post("", response_model=CompatibilityResponse, status_code=status.HTTP_201_CREATED)
async def create_compatibility(
    compatibility_data: CompatibilityCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Crea un nuevo análisis de compatibilidad astrológica basado en los datos proporcionados.
    """
    try:
        # Calcular la compatibilidad entre los perfiles
        compatibility_calculation = await calculate_compatibility(
            person1_birth_date=compatibility_data.person1_birth_date,
            person1_birth_time=compatibility_data.person1_birth_time,
            person1_latitude=compatibility_data.person1_latitude,
            person1_longitude=compatibility_data.person1_longitude,
            person2_birth_date=compatibility_data.person2_birth_date,
            person2_birth_time=compatibility_data.person2_birth_time,
            person2_latitude=compatibility_data.person2_latitude,
            person2_longitude=compatibility_data.person2_longitude,
            compatibility_type=compatibility_data.compatibility_type
        )
        
        # Interpretar la compatibilidad
        interpretation = await interpret_compatibility(
            compatibility_calculation=compatibility_calculation,
            compatibility_type=compatibility_data.compatibility_type,
            focus_areas=compatibility_data.focus_areas
        )
        
        # Mejorar la interpretación con Claude AI
        enhanced_interpretation = await enhance_compatibility_with_claude(
            compatibility_calculation=compatibility_calculation,
            interpretation=interpretation,
            compatibility_type=compatibility_data.compatibility_type,
            focus_areas=compatibility_data.focus_areas,
            person1_name=compatibility_data.person1_name,
            person2_name=compatibility_data.person2_name
        )
        
        # Guardar la consulta en la base de datos
        compatibility = await save_compatibility_query(
            user_id=current_user.id,
            compatibility_data=compatibility_data,
            calculation_result=compatibility_calculation,
            interpretation=interpretation,
            enhanced_interpretation=enhanced_interpretation
        )
        
        logger.info(f"Análisis de compatibilidad creado para usuario {current_user.id}, tipo: {compatibility_data.compatibility_type}")
        return compatibility
        
    except Exception as e:
        logger.error(f"Error al crear análisis de compatibilidad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el análisis de compatibilidad: {str(e)}"
        )


@router.get("", response_model=List[CompatibilityResponse])
async def read_user_compatibilities(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    compatibility_type: Optional[CompatibilityType] = None,
    name: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Obtiene todos los análisis de compatibilidad del usuario actual con filtros opcionales.
    """
    # Preparar filtros
    filters = CompatibilityFilter(
        compatibility_type=compatibility_type,
        name=name
    )
    
    # Obtener análisis de compatibilidad
    compatibilities = await get_user_compatibilities(
        user_id=current_user.id,
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    logger.debug(f"Usuario {current_user.id} solicitó sus análisis de compatibilidad. Total: {len(compatibilities)}")
    return compatibilities


@router.get("/{compatibility_id}", response_model=CompatibilityDetail)
async def read_compatibility_detail(
    compatibility_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Obtiene detalles completos de un análisis de compatibilidad específico.
    """
    # Obtener el análisis de compatibilidad de la base de datos
    compatibility = await get_compatibility_by_id(compatibility_id)
    
    # Verificar que existe
    if not compatibility:
        logger.warning(f"Intento de acceso a compatibilidad inexistente ID: {compatibility_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis de compatibilidad no encontrado"
        )
    
    # Verificar que pertenece al usuario actual
    if compatibility.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó acceder a compatibilidad {compatibility_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este análisis de compatibilidad"
        )
    
    logger.debug(f"Usuario {current_user.id} solicitó detalles de compatibilidad {compatibility_id}")
    return compatibility


@router.post("/{compatibility_id}/focus", response_model=CompatibilityDetail)
async def refocus_compatibility(
    compatibility_id: str,
    focus_areas: List[str],
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Reenfoca un análisis de compatibilidad existente en áreas específicas.
    """
    # Obtener el análisis de compatibilidad de la base de datos
    compatibility = await get_compatibility_by_id(compatibility_id)
    
    # Verificar que existe
    if not compatibility:
        logger.warning(f"Intento de reenfocar compatibilidad inexistente ID: {compatibility_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis de compatibilidad no encontrado"
        )
    
    # Verificar que pertenece al usuario actual
    if compatibility.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó reenfocar compatibilidad {compatibility_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para modificar este análisis de compatibilidad"
        )
    
    try:
        # Reenfocar el análisis de compatibilidad con Claude AI
        enhanced_interpretation = await enhance_compatibility_with_claude(
            compatibility_calculation=compatibility.calculation_result,
            interpretation=compatibility.interpretation,
            compatibility_type=compatibility.compatibility_type,
            focus_areas=focus_areas,
            person1_name=compatibility.person1_name,
            person2_name=compatibility.person2_name
        )
        
        # Actualizar la interpretación en la base de datos
        # (Aquí se debería implementar la actualización de la interpretación)
        
        logger.info(f"Compatibilidad {compatibility_id} reenfocada en: {', '.join(focus_areas)}")
        
        # Devolver la compatibilidad con la nueva interpretación
        compatibility.enhanced_interpretation = enhanced_interpretation
        compatibility.focus_areas = focus_areas
        return compatibility
        
    except Exception as e:
        logger.error(f"Error al reenfocar análisis de compatibilidad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al reenfocar el análisis de compatibilidad: {str(e)}"
        )


@router.delete("/{compatibility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_compatibility(
    compatibility_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)]
):
    """
    Elimina un análisis de compatibilidad existente.
    """
    # Obtener el análisis de compatibilidad de la base de datos
    compatibility = await get_compatibility_by_id(compatibility_id)
    
    # Verificar que existe
    if not compatibility:
        logger.warning(f"Intento de eliminar compatibilidad inexistente ID: {compatibility_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análisis de compatibilidad no encontrado"
        )
    
    # Verificar que pertenece al usuario actual
    if compatibility.user_id != current_user.id and not current_user.is_admin:
        logger.warning(f"Usuario {current_user.id} intentó eliminar compatibilidad {compatibility_id} de otro usuario")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este análisis de compatibilidad"
        )
    
    # Eliminar el análisis de compatibilidad
    await delete_compatibility(compatibility_id)
    
    logger.info(f"Análisis de compatibilidad {compatibility_id} eliminado por usuario {current_user.id}")
    return None