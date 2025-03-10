"""
Servicios de cálculo de aspectos astrológicos para la aplicación Prezagia.

Este módulo implementa funciones para calcular e interpretar los aspectos
entre planetas y puntos significativos en las cartas astrales.
"""

from typing import Dict, Any, List, Optional, Tuple
import math

from app.core.logger import logger
from app.core.exceptions import CalculationError


# Definición de aspectos principales y sus ángulos
MAJOR_ASPECTS = {
    "conjunción": 0.0,
    "sextil": 60.0,
    "cuadratura": 90.0,
    "trígono": 120.0,
    "oposición": 180.0
}

# Aspectos menores
MINOR_ASPECTS = {
    "semisextil": 30.0,
    "semicuadratura": 45.0,
    "sesquicuadratura": 135.0,
    "quincuncio": 150.0
}

# Orbes (tolerancias) para cada aspecto
DEFAULT_ORBS = {
    # Aspectos mayores
    "conjunción": 8.0,
    "sextil": 4.0,
    "cuadratura": 6.0,
    "trígono": 6.0,
    "oposición": 8.0,
    
    # Aspectos menores
    "semisextil": 2.0,
    "semicuadratura": 2.0,
    "sesquicuadratura": 2.0,
    "quincuncio": 3.0
}

# Orbes especiales para luminarias (Sol y Luna)
LUMINARY_ORBS = {
    "conjunción": 10.0,
    "sextil": 6.0,
    "cuadratura": 8.0,
    "trígono": 8.0,
    "oposición": 10.0,
    
    "semisextil": 3.0,
    "semicuadratura": 3.0,
    "sesquicuadratura": 3.0,
    "quincuncio": 4.0
}


def calculate_aspect(longitude1: float, longitude2: float, 
                    planet1: str = "", planet2: str = "", 
                    use_minor_aspects: bool = True,
                    custom_orbs: Dict[str, float] = None) -> Optional[Dict[str, Any]]:
    """
    Calcula el aspecto entre dos posiciones planetarias.
    
    Args:
        longitude1: Longitud eclíptica del primer planeta en grados
        longitude2: Longitud eclíptica del segundo planeta en grados
        planet1: Nombre del primer planeta (para ajustar orbes)
        planet2: Nombre del segundo planeta (para ajustar orbes)
        use_minor_aspects: Si se deben considerar aspectos menores
        custom_orbs: Diccionario opcional con orbes personalizados
    
    Returns:
        Optional[Dict]: Información sobre el aspecto, o None si no hay aspecto
    """
    try:
        # Calcular la diferencia angular más corta entre las dos longitudes
        diff = abs((longitude2 - longitude1 + 180) % 360 - 180)
        
        # Determinar qué aspectos verificar
        aspects_to_check = MAJOR_ASPECTS.copy()
        if use_minor_aspects:
            aspects_to_check.update(MINOR_ASPECTS)
        
        # Determinar las orbes a usar
        if custom_orbs:
            orbs = custom_orbs
        else:
            # Usar orbes ampliadas si alguno de los planetas es un luminar (Sol o Luna)
            if planet1 in ["sun", "moon"] or planet2 in ["sun", "moon"]:
                orbs = LUMINARY_ORBS
            else:
                orbs = DEFAULT_ORBS
        
        # Verificar cada aspecto posible
        aspect_found = None
        min_diff = float('inf')
        
        for aspect_name, aspect_angle in aspects_to_check.items():
            # Verificar si la diferencia está dentro de la orbe permitida
            angle_diff = abs(diff - aspect_angle)
            
            if angle_diff <= orbs.get(aspect_name, DEFAULT_ORBS.get(aspect_name, 0)):
                # Si encontramos múltiples aspectos, elegir el más exacto
                if angle_diff < min_diff:
                    aspect_found = aspect_name
                    min_diff = angle_diff
                    exact_angle = aspect_angle
        
        # Si no encontramos ningún aspecto, devolver None
        if not aspect_found:
            return None
        
        # Determinar la naturaleza del aspecto
        aspect_nature = determine_aspect_nature(aspect_found, planet1, planet2)
        
        # Determinar si el aspecto es aplicativo (se acerca a la exactitud) o separativo (se aleja)
        is_applying = determine_if_applying(longitude1, longitude2, exact_angle, planet1, planet2)
        
        # Calcular la potencia del aspecto (basada en qué tan exacto es)
        power = calculate_aspect_power(min_diff, aspect_found, orbs, planet1, planet2)
        
        # Preparar el resultado
        return {
            "aspect_type": aspect_found,
            "exact_angle": exact_angle,
            "actual_angle": diff,
            "orb": min_diff,
            "planet1": planet1,
            "planet2": planet2,
            "applying": is_applying,
            "separating": not is_applying,
            "nature": aspect_nature,
            "power": power
        }
    
    except Exception as e:
        logger.error(f"Error al calcular aspecto entre {planet1} y {planet2}: {str(e)}")
        return None


def determine_aspect_nature(aspect_type: str, planet1: str = "", planet2: str = "") -> str:
    """
    Determina la naturaleza del aspecto (favorable, desafiante, ambivalente).
    
    Args:
        aspect_type: Tipo de aspecto
        planet1: Primer planeta
        planet2: Segundo planeta
    
    Returns:
        str: Naturaleza del aspecto
    """
    # Aspectos generalmente favorables
    if aspect_type in ["trígono", "sextil"]:
        return "favorable"
    
    # Aspectos generalmente desafiantes
    elif aspect_type in ["cuadratura", "oposición", "semicuadratura", "sesquicuadratura"]:
        return "desafiante"
    
    # Aspectos ambivalentes
    elif aspect_type in ["quincuncio", "semisextil"]:
        return "ambivalente"
    
    # Conjunción: depende de los planetas involucrados
    elif aspect_type == "conjunción":
        # Planetas generalmente benéficos
        benefics = ["venus", "jupiter"]
        # Planetas generalmente maléficos
        malefics = ["mars", "saturn"]
        
        # Si ambos son benéficos
        if planet1 in benefics and planet2 in benefics:
            return "favorable"
        # Si ambos son maléficos
        elif planet1 in malefics and planet2 in malefics:
            return "desafiante"
        # Si uno es benéfico y otro maléfico
        elif (planet1 in benefics and planet2 in malefics) or (planet1 in malefics and planet2 in benefics):
            return "ambivalente"
        # Si son neutrales o no se especifican
        else:
            return "neutral"
    
    # Por defecto, neutral
    return "neutral"


def determine_if_applying(longitude1: float, longitude2: float, aspect_angle: float, 
                        planet1: str = "", planet2: str = "") -> bool:
    """
    Determina si un aspecto es aplicativo (se acerca a la exactitud) o separativo (se aleja).
    
    Args:
        longitude1: Longitud del primer planeta
        longitude2: Longitud del segundo planeta
        aspect_angle: Ángulo exacto del aspecto
        planet1: Nombre del primer planeta
        planet2: Nombre del segundo planeta
    
    Returns:
        bool: True si el aspecto es aplicativo, False si es separativo
    """
    # Esta es una simplificación. La determinación real requiere conocer
    # la velocidad y dirección de movimiento de los planetas.
    
    # Para este ejemplo simplificado, asumimos que:
    # - Si la diferencia actual es menor que el ángulo exacto, se está acercando (aplicando)
    # - Si es mayor, se está alejando (separando)
    # Esto no es preciso en todos los casos, especialmente con planetas retrógrados
    
    diff = abs((longitude2 - longitude1 + 180) % 360 - 180)
    
    return diff < aspect_angle


def calculate_aspect_power(orb: float, aspect_type: str, orbs: Dict[str, float], 
                          planet1: str = "", planet2: str = "") -> float:
    """
    Calcula la potencia o fortaleza de un aspecto (0-10).
    
    Args:
        orb: Diferencia angular respecto al aspecto exacto
        aspect_type: Tipo de aspecto
        orbs: Diccionario de orbes máximas
        planet1: Primer planeta
        planet2: Segundo planeta
    
    Returns:
        float: Potencia del aspecto (0-10)
    """
    # Obtener la orbe máxima para este tipo de aspecto
    max_orb = orbs.get(aspect_type, DEFAULT_ORBS.get(aspect_type, 0))
    
    if max_orb == 0:
        return 0.0
    
    # Calcular potencia base en función de qué tan exacto es el aspecto
    # 10 = aspecto exacto, 0 = en el límite de la orbe
    base_power = 10 * (1 - orb / max_orb)
    
    # Ajustar según la importancia del aspecto
    if aspect_type in ["conjunción", "oposición"]:
        aspect_multiplier = 1.0
    elif aspect_type in ["trígono", "cuadratura"]:
        aspect_multiplier = 0.9
    elif aspect_type == "sextil":
        aspect_multiplier = 0.8
    else:  # Aspectos menores
        aspect_multiplier = 0.7
    
    # Ajustar según la importancia de los planetas
    planet_multiplier = 1.0
    
    # Luminarias tienen más peso
    if "sun" in [planet1, planet2]:
        planet_multiplier *= 1.2
    if "moon" in [planet1, planet2]:
        planet_multiplier *= 1.1
    
    # Calcular potencia final
    power = base_power * aspect_multiplier * planet_multiplier
    
    # Limitar a rango 0-10
    return min(10, max(0, power))


def find_all_aspects(planet_positions: Dict[str, Dict[str, Any]], 
                    include_minor_aspects: bool = True) -> List[Dict[str, Any]]:
    """
    Encuentra todos los aspectos entre un conjunto de planetas.
    
    Args:
        planet_positions: Diccionario con posiciones planetarias
        include_minor_aspects: Si se deben incluir aspectos menores
    
    Returns:
        List[Dict]: Lista de aspectos encontrados
    """
    aspects = []
    planets = list(planet_positions.keys())
    
    # Verificar aspectos entre cada par de planetas
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            planet1 = planets[i]
            planet2 = planets[j]
            
            # Obtener longitudes
            lon1 = planet_positions[planet1]["longitude"]
            lon2 = planet_positions[planet2]["longitude"]
            
            # Calcular aspecto
            aspect = calculate_aspect(
                longitude1=lon1,
                longitude2=lon2,
                planet1=planet1,
                planet2=planet2,
                use_minor_aspects=include_minor_aspects
            )
            
            # Si hay aspecto, añadirlo a la lista
            if aspect:
                aspects.append(aspect)
    
    return aspects


def analyze_aspect_pattern(aspects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analiza los aspectos para identificar patrones significativos (Gran Trígono, T-Cuadrada, etc.)
    
    Args:
        aspects: Lista de aspectos
    
    Returns:
        Dict: Patrones encontrados y sus detalles
    """
    patterns = {
        "grand_trine": [],  # Gran Trígono
        "t_square": [],     # T-Cuadrada
        "grand_cross": [],  # Gran Cruz
        "yod": [],          # Yod (Dedo de Dios)
        "mystic_rectangle": [],  # Rectángulo Místico
        "kite": []          # Cometa
    }
    
    # Esta función requeriría un algoritmo complejo para detectar estos patrones
    # Lo que sigue es un esbozo simplificado que deberías expandir
    
    # Buscar Gran Trígono (3 planetas en trígono mutuo)
    trigones = [a for a in aspects if a["aspect_type"] == "trígono"]
    
    # Buscar T-Cuadrada (2 planetas en oposición, ambos en cuadratura con un tercero)
    oppositions = [a for a in aspects if a["aspect_type"] == "oposición"]
    squares = [a for a in aspects if a["aspect_type"] == "cuadratura"]
    
    # Buscar Yod (2 planetas en sextil, ambos en quincuncio con un tercero)
    sextiles = [a for a in aspects if a["aspect_type"] == "sextil"]
    quincunxes = [a for a in aspects if a["aspect_type"] == "quincuncio"]
    
    # Aquí vendría el algoritmo para encontrar estos patrones
    # Por simplicidad, no lo implementamos completamente
    
    return patterns


def filter_significant_aspects(aspects: List[Dict[str, Any]], 
                             min_power: float = 5.0,
                             focus_planets: List[str] = None) -> List[Dict[str, Any]]:
    """
    Filtra los aspectos más significativos basándose en su potencia e importancia.
    
    Args:
        aspects: Lista de aspectos
        min_power: Potencia mínima para incluir un aspecto
        focus_planets: Lista de planetas en los que enfocar el análisis
    
    Returns:
        List[Dict]: Lista filtrada de aspectos
    """
    if not focus_planets:
        # Planetas personales + luminarias + ASC/MC como predeterminados
        focus_planets = ["sun", "moon", "mercury", "venus", "mars", "ascendant", "midheaven"]
    
    # Filtrar aspectos por potencia y planetas de enfoque
    significant = []
    
    for aspect in aspects:
        # Verificar si el aspecto involucra planetas de enfoque
        involves_focus = aspect["planet1"] in focus_planets or aspect["planet2"] in focus_planets
        
        # Incluir el aspecto si es potente o involucra planetas de enfoque
        if aspect["power"] >= min_power or involves_focus:
            significant.append(aspect)
    
    # Ordenar por potencia descendente
    significant.sort(key=lambda x: x["power"], reverse=True)
    
    return significant