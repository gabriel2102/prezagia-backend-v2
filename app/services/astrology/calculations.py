"""
Servicios de cálculos astronómicos para la aplicación Prezagia.

Este módulo utiliza la biblioteca Skyfield para realizar cálculos astronómicos precisos
que sirven como base para las interpretaciones astrológicas.
"""

from datetime import datetime, date, time
from typing import Dict, Any, List, Optional, Tuple
import os
import numpy as np
import requests

from skyfield.api import load, wgs84, Star, load_file
from skyfield.data import hipparcos
from skyfield.elementslib import osculating_elements_of
from skyfield.framelib import ecliptic_frame
from skyfield.searchlib import find_discrete, find_maxima
from skyfield.timelib import Time

from app.core.logger import logger
from app.core.config import settings
from app.core.exceptions import CalculationError
from app.schemas.astrology import ChartType, PredictionPeriod

from datetime import timedelta
from app.schemas.astrology import CompatibilityType



# Configuraciones
SKYFIELD_DATA_DIR = settings.SKYFIELD_DATA_DIR


# Cargar datos necesarios para los cálculos
def load_ephemeris():
    """
    Carga las efemérides planetarias desde Skyfield.

    Returns:
        tuple: (ts, eph) donde ts es el objeto timescale y eph es el objeto ephemeris
    """
    try:
        # Crear el directorio de datos si no existe
        os.makedirs(SKYFIELD_DATA_DIR, exist_ok=True)

        # Cargar el objeto timescale
        ts = load.timescale()

        # Cargar efemérides directamente desde Skyfield (sin descargar manualmente)
        logger.info("Cargando efemérides DE421 desde Skyfield...")
        eph = load("de421.bsp")  # ❌ Elimina cualquier intento de descarga manual
        
        logger.info("Efemérides cargadas correctamente desde Skyfield")
        return ts, eph

    except Exception as e:
        logger.error(f"Error al cargar efemérides: {str(e)}")
        raise CalculationError(message=f"Error al cargar efemérides: {str(e)}", 
                              calculation_type="carga_datos")

# Objetos globales para cálculos astronómicos
try:
    ts, eph = load_ephemeris()
    
    # Cuerpos celestes principales
    sun = eph['sun']
    moon = eph['moon']
    earth = eph['earth']
    mercury = eph['mercury']
    venus = eph['venus']
    mars = eph['mars']
    jupiter = eph['jupiter barycenter']
    saturn = eph['saturn barycenter']
    uranus = eph['uranus barycenter']
    neptune = eph['neptune barycenter']
    pluto = eph['pluto barycenter']
    
    # Diccionario de planetas
    planets = {
        'sun': sun,
        'moon': moon,
        'mercury': mercury,
        'venus': venus,
        'mars': mars,
        'jupiter': jupiter,
        'saturn': saturn,
        'uranus': uranus,
        'neptune': neptune,
        'pluto': pluto
    }

    logger.info("Objetos astronómicos cargados correctamente")

except Exception as e:
    logger.error(f"Error al inicializar objetos astronómicos: {str(e)}")

# Signos del zodíaco
ZODIAC_SIGNS = [
    "Aries", "Tauro", "Géminis", "Cáncer", 
    "Leo", "Virgo", "Libra", "Escorpio", 
    "Sagitario", "Capricornio", "Acuario", "Piscis"
]

# Aspectos astrológicos
ASPECTS = {
    "conjunción": 0.0,
    "semisextil": 30.0,
    "semicuadratura": 45.0,
    "sextil": 60.0,
    "cuadratura": 90.0,
    "trígono": 120.0,
    "sesquicuadratura": 135.0,
    "quincuncio": 150.0,
    "oposición": 180.0
}

# Tolerancias (orbs) para cada aspecto
ASPECT_ORBS = {
    "conjunción": 8.0,
    "semisextil": 2.0,
    "semicuadratura": 2.0,
    "sextil": 4.0,
    "cuadratura": 6.0,
    "trígono": 6.0,
    "sesquicuadratura": 2.0,
    "quincuncio": 3.0,
    "oposición": 8.0
}


def get_zodiac_sign(longitude: float) -> str:
    """
    Determina el signo del zodíaco basado en la longitud eclíptica.
    
    Args:
        longitude: Longitud eclíptica en grados (0 a 360)
    
    Returns:
        str: Nombre del signo zodiacal
    """
    # Normalizar la longitud a 0-360
    longitude = longitude % 360
    
    # Cada signo ocupa 30 grados
    sign_index = int(longitude / 30)
    
    return ZODIAC_SIGNS[sign_index]


def get_sign_element(sign: str) -> str:
    """
    Obtiene el elemento (Fuego, Tierra, Aire, Agua) correspondiente a un signo zodiacal.
    
    Args:
        sign: Nombre del signo zodiacal
    
    Returns:
        str: Elemento correspondiente
    """
    elements = {
        "Aries": "Fuego",
        "Leo": "Fuego",
        "Sagitario": "Fuego",
        "Tauro": "Tierra",
        "Virgo": "Tierra",
        "Capricornio": "Tierra",
        "Géminis": "Aire",
        "Libra": "Aire",
        "Acuario": "Aire",
        "Cáncer": "Agua",
        "Escorpio": "Agua",
        "Piscis": "Agua"
    }
    
    return elements.get(sign, "Desconocido")


def get_sign_modality(sign: str) -> str:
    """
    Obtiene la modalidad (Cardinal, Fijo, Mutable) correspondiente a un signo zodiacal.
    
    Args:
        sign: Nombre del signo zodiacal
    
    Returns:
        str: Modalidad correspondiente
    """
    modalities = {
        "Aries": "Cardinal",
        "Cáncer": "Cardinal",
        "Libra": "Cardinal",
        "Capricornio": "Cardinal",
        "Tauro": "Fijo",
        "Leo": "Fijo",
        "Escorpio": "Fijo",
        "Acuario": "Fijo",
        "Géminis": "Mutable",
        "Virgo": "Mutable",
        "Sagitario": "Mutable",
        "Piscis": "Mutable"
    }
    
    return modalities.get(sign, "Desconocido")


def get_planet_dignity(planet: str, sign: str) -> Optional[str]:
    """
    Determina la dignidad de un planeta en un signo particular.
    
    Args:
        planet: Nombre del planeta
        sign: Nombre del signo
    
    Returns:
        Optional[str]: Dignidad del planeta (Domicilio, Exaltación, Caída, Exilio) o None
    """
    # Domicilios planetarios
    rulerships = {
        "sun": ["Leo"],
        "moon": ["Cáncer"],
        "mercury": ["Géminis", "Virgo"],
        "venus": ["Tauro", "Libra"],
        "mars": ["Aries", "Escorpio"],
        "jupiter": ["Sagitario", "Piscis"],
        "saturn": ["Capricornio", "Acuario"],
        "uranus": ["Acuario"],
        "neptune": ["Piscis"],
        "pluto": ["Escorpio"]
    }
    
    # Exaltaciones
    exaltations = {
        "sun": "Aries",
        "moon": "Tauro",
        "mercury": "Virgo",
        "venus": "Piscis",
        "mars": "Capricornio",
        "jupiter": "Cáncer",
        "saturn": "Libra",
        "uranus": "Escorpio",
        "neptune": "Leo",
        "pluto": "Acuario"
    }
    
    # Caídas (opuesto a exaltación)
    falls = {
        "sun": "Libra",
        "moon": "Escorpio",
        "mercury": "Piscis",
        "venus": "Virgo",
        "mars": "Cáncer",
        "jupiter": "Capricornio",
        "saturn": "Aries",
        "uranus": "Tauro",
        "neptune": "Acuario",
        "pluto": "Leo"
    }
    
    # Exilios (opuesto a domicilio)
    detriments = {
        "sun": ["Acuario"],
        "moon": ["Capricornio"],
        "mercury": ["Sagitario", "Piscis"],
        "venus": ["Aries", "Escorpio"],
        "mars": ["Libra", "Tauro"],
        "jupiter": ["Géminis", "Virgo"],
        "saturn": ["Cáncer", "Leo"],
        "uranus": ["Leo"],
        "neptune": ["Virgo"],
        "pluto": ["Tauro"]
    }
    
    # Verificar dignidades
    if planet in rulerships and sign in rulerships[planet]:
        return "Domicilio"
    elif planet in exaltations and sign == exaltations[planet]:
        return "Exaltación"
    elif planet in falls and sign == falls[planet]:
        return "Caída"
    elif planet in detriments and sign in detriments[planet]:
        return "Exilio"
    
    return None


def calculate_planet_position(planet_key: str, t) -> Dict[str, Any]:
    """
    Calcula la posición de un planeta en un momento dado.
    
    Args:
        planet_key: Clave del planeta en el diccionario de planetas
        t: Tiempo de Skyfield
    
    Returns:
        Dict: Información sobre la posición del planeta
    """
    try:
        # Obtener el planeta
        planet = planets[planet_key]
        
        # Calcular la posición geocéntrica
        astrometric = earth.at(t).observe(planet)
        ecliptic = astrometric.ecliptic_latlon()

        # Extraer coordenadas eclípticas
        lat, lon, _ = ecliptic
        
        # Convertir a grados
        longitude = lon._degrees % 360
        latitude = lat._degrees
        
        # Determinar el signo zodiacal
        sign = get_zodiac_sign(longitude)
        
        # Calcular la posición dentro del signo (0-30 grados)
        position_in_sign = longitude % 30
        
        # Determinar si está retrógrado (para planetas)
        is_retrograde = False
        if planet_key not in ['sun', 'moon']:
            # Calcular la velocidad para determinar si es retrógrado
            t1 = ts.tt(jd=t.tt + 1)
            astrometric1 = earth.at(t1).observe(planet)
            ecliptic1 = astrometric1.ecliptic_latlon()
            lon1 = ecliptic1[1]._degrees
            
            # Determinar velocidad y si está retrógrado
            speed = lon1 - longitude
            is_retrograde = speed < 0
        
        # Calcular la dignidad del planeta en el signo
        dignity = get_planet_dignity(planet_key, sign)
        
        # Construir el resultado
        result = {
            "name": planet_key,
            "sign": sign,
            "longitude": longitude,
            "latitude": latitude,
            "position_in_sign": position_in_sign,
            "degree": f"{int(position_in_sign)}° {int((position_in_sign % 30) * 60) % 60}' {sign}",
            "retrograde": is_retrograde,
            "speed": speed if 'speed' in locals() else None,
            "dignity": dignity
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error al calcular posición del planeta {planet_key}: {str(e)}")
        raise CalculationError(message=f"Error al calcular posición de {planet_key}: {str(e)}", 
                              calculation_type="posición_planetaria")


def calculate_ascendant(t: Time, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calcula el ascendente (signo zodiacal que asciende en el horizonte) para un momento y ubicación dados.

    Args:
        t (Time): Objeto de tiempo de Skyfield.
        latitude (float): Latitud en grados.
        longitude (float): Longitud en grados.

    Returns:
        Dict: Información sobre el ascendente.
    """
    try:
        # Obtener la hora sidérea local (LST) usando la función corregida
        lst_degrees = get_sidereal_time(t, longitude) * 15  # Convertir horas a grados

        # Convertir a radianes para cálculos trigonométricos
        lat_rad = np.radians(latitude)

        # Calcular la oblicuidad de la eclíptica (ε)
        ecliptic_obliquity = 23.4393 - 0.0000004 * (t.tt - 2451545.0) / 36525  # Oblicuidad promedio
        epsilon_rad = np.radians(ecliptic_obliquity)

        # Calcular la tangente del ascendente
        tan_asc = (
            np.cos(epsilon_rad) * np.sin(np.radians(lst_degrees))
        ) / (
            np.cos(np.radians(lst_degrees)) * np.sin(lat_rad)
            + np.sin(epsilon_rad) * np.sin(np.radians(lst_degrees)) * np.cos(lat_rad)
        )

        # Convertir la tangente a grados
        asc_rad = np.arctan(tan_asc)
        asc_deg = np.degrees(asc_rad)

        # Ajustar el cuadrante según LST
        if 90 <= lst_degrees < 270:
            asc_deg += 180

        # Normalizar el ángulo a 0-360°
        asc_deg = asc_deg % 360

        # Determinar el signo zodiacal del ascendente
        sign = get_zodiac_sign(asc_deg)

        # Posición dentro del signo zodiacal (0-30°)
        position_in_sign = asc_deg % 30

        return {
            "longitude": asc_deg,
            "sign": sign,
            "position_in_sign": position_in_sign,
            "degree": f"{int(position_in_sign)}° {int(position_in_sign * 60) % 60}' {sign}"
        }

    except Exception as e:
        logger.error(f"Error al calcular ascendente: {str(e)}")
        raise CalculationError(message=f"Error al calcular el ascendente: {str(e)}", calculation_type="ascendente")


def calculate_midheaven(t: Time, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calcula el Medio Cielo (MC) para un momento y lugar específicos.

    Args:
        t (Time): Objeto de tiempo de Skyfield.
        latitude (float): Latitud en grados.
        longitude (float): Longitud en grados.

    Returns:
        Dict: Información sobre el Medio Cielo (MC).
    """
    try:
        # Obtener la hora sidérea local (LST) usando la función corregida
        lst_degrees = get_sidereal_time(t, longitude) * 15  # Convertir horas a grados

        # Convertir LST a radianes
        lst_rad = np.radians(lst_degrees)

        # Calcular la oblicuidad de la eclíptica (ε)
        ecliptic_obliquity = 23.4393 - 0.0000004 * (t.tt - 2451545.0) / 36525  # Oblicuidad promedio
        epsilon_rad = np.radians(ecliptic_obliquity)

        # Calcular la tangente del Medio Cielo (MC)
        tan_mc = np.tan(lst_rad) / np.cos(epsilon_rad)

        # Convertir la tangente a grados
        mc_rad = np.arctan(tan_mc)
        mc_deg = np.degrees(mc_rad)

        # Ajustar el cuadrante basado en LST
        if 90 <= lst_degrees < 270:
            mc_deg += 180

        # Normalizar el ángulo a 0-360°
        mc_deg = mc_deg % 360

        # Determinar el signo zodiacal del Medio Cielo
        sign = get_zodiac_sign(mc_deg)

        # Posición dentro del signo zodiacal (0-30°)
        position_in_sign = mc_deg % 30

        return {
            "longitude": mc_deg,
            "sign": sign,
            "position_in_sign": position_in_sign,
            "degree": f"{int(position_in_sign)}° {int(position_in_sign * 60) % 60}' {sign}"
        }

    except Exception as e:
        logger.error(f"Error al calcular medio cielo: {str(e)}")
        raise CalculationError(message=f"Error al calcular el medio cielo: {str(e)}", calculation_type="medio_cielo")


def calculate_houses(t, latitude: float, longitude: float, system: str = "placidus") -> Dict[str, Any]:
    """
    Calcula las casas astrológicas para un momento y lugar específicos.
    
    Args:
        t: Tiempo de Skyfield
        latitude: Latitud del lugar en grados
        longitude: Longitud del lugar en grados
        system: Sistema de casas a utilizar
    
    Returns:
        Dict: Información sobre las casas astrológicas
    """
    try:
        # Obtener el ascendente y medio cielo
        asc = calculate_ascendant(t, latitude, longitude)
        mc = calculate_midheaven(t, latitude, longitude)
        
        result = {
            "system": system,
            "houses": {}
        }
        
        # Implementación simplificada para el sistema Placidus
        # Nota: Un cálculo completo requeriría algoritmos más complejos para cada sistema de casas
        if system.lower() == "placidus":
            # Casa 1 (Ascendente)
            result["houses"]["1"] = {
                "cusp": asc["longitude"],
                "sign": asc["sign"],
                "degree": asc["degree"]
            }
            
            # Casa 10 (Medio Cielo)
            result["houses"]["10"] = {
                "cusp": mc["longitude"],
                "sign": mc["sign"],
                "degree": mc["degree"]
            }
            
            # Casa 7 (Descendente - opuesto al Ascendente)
            desc_longitude = (asc["longitude"] + 180) % 360
            desc_sign = get_zodiac_sign(desc_longitude)
            desc_position = desc_longitude % 30
            
            result["houses"]["7"] = {
                "cusp": desc_longitude,
                "sign": desc_sign,
                "degree": f"{int(desc_position)}° {int(desc_position * 60) % 60}' {desc_sign}"
            }
            
            # Casa 4 (Imum Coeli - opuesto al Medio Cielo)
            ic_longitude = (mc["longitude"] + 180) % 360
            ic_sign = get_zodiac_sign(ic_longitude)
            ic_position = ic_longitude % 30
            
            result["houses"]["4"] = {
                "cusp": ic_longitude,
                "sign": ic_sign,
                "degree": f"{int(ic_position)}° {int(ic_position * 60) % 60}' {ic_sign}"
            }
            
            # Para las demás casas, se utiliza una aproximación simple
            # En un sistema real, se realizan cálculos específicos para cada casa
            # según el sistema elegido
            
            # Calcular las casas intermedias
            house_cusps = []
            for i in range(1, 13):
                if i == 1:
                    house_cusps.append(asc["longitude"])
                elif i == 4:
                    house_cusps.append(ic_longitude)
                elif i == 7:
                    house_cusps.append(desc_longitude)
                elif i == 10:
                    house_cusps.append(mc["longitude"])
                else:
                    # Interpolación simple para otras casas
                    if i < 4:
                        # Casas 2 y 3
                        segment = (ic_longitude - asc["longitude"]) % 360
                        step = segment / 3
                        cusp = (asc["longitude"] + step * (i - 1)) % 360
                    elif i < 7:
                        # Casas 5 y 6
                        segment = (desc_longitude - ic_longitude) % 360
                        step = segment / 3
                        cusp = (ic_longitude + step * (i - 4)) % 360
                    elif i < 10:
                        # Casas 8 y 9
                        segment = (mc["longitude"] - desc_longitude) % 360
                        step = segment / 3
                        cusp = (desc_longitude + step * (i - 7)) % 360
                    else:
                        # Casas 11 y 12
                        segment = (asc["longitude"] - mc["longitude"]) % 360
                        step = segment / 3
                        cusp = (mc["longitude"] + step * (i - 10)) % 360
                    
                    house_cusps.append(cusp)
            
            # Guardar todas las casas
            for i in range(2, 13):
                if str(i) not in result["houses"]:
                    cusp = house_cusps[i-1]
                    sign = get_zodiac_sign(cusp)
                    position = cusp % 30
                    
                    result["houses"][str(i)] = {
                        "cusp": cusp,
                        "sign": sign,
                        "degree": f"{int(position)}° {int(position * 60) % 60}' {sign}"
                    }
        
        # Añadir información sobre signos en cada casa y planetas
        for i in range(1, 13):
            house_num = str(i)
            cusp = result["houses"][house_num]["cusp"]
            next_house = str(1 if i == 12 else i + 1)
            next_cusp = result["houses"][next_house]["cusp"]
            
            # Determinar los signos que caen en esta casa
            signs_in_house = []
            temp_cusp = cusp
            while True:
                sign = get_zodiac_sign(temp_cusp)
                if sign not in signs_in_house:
                    signs_in_house.append(sign)
                
                # Avanzar 30 grados (un signo)
                temp_cusp = (temp_cusp + 30) % 360
                
                # Si hemos dado una vuelta completa o alcanzado la siguiente cúspide, salir
                if temp_cusp == cusp or (temp_cusp >= next_cusp and temp_cusp < cusp + 360):
                    break
            
            result["houses"][house_num]["signs"] = signs_in_house
            
            # La lista de planetas en cada casa se rellenará después
            result["houses"][house_num]["planets"] = []
        
        return result
    
    except Exception as e:
        logger.error(f"Error al calcular casas astrológicas: {str(e)}")
        raise CalculationError(message=f"Error al calcular las casas astrológicas: {str(e)}", 
                              calculation_type="casas")


def calculate_aspect(planet1_pos: Dict[str, Any], planet2_pos: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calcula el aspecto entre dos planetas o puntos de la carta.
    
    Args:
        planet1_pos: Posición del primer planeta/punto
        planet2_pos: Posición del segundo planeta/punto
    
    Returns:
        Optional[Dict]: Información sobre el aspecto, o None si no hay aspecto
    """
    try:
        # Calcular la diferencia de longitud
        lon1 = planet1_pos["longitude"]
        lon2 = planet2_pos["longitude"]
        
        # Calcular la diferencia angular más corta
        diff = abs((lon2 - lon1 + 180) % 360 - 180)
        
        # Verificar cada tipo de aspecto
        aspect_found = None
        orb = 0
        
        for aspect_name, aspect_angle in ASPECTS.items():
            # Calcular la diferencia del ángulo exacto
            angle_diff = abs(diff - aspect_angle)
            
            # Si la diferencia está dentro de la tolerancia (orb), hay un aspecto
            if angle_diff <= ASPECT_ORBS[aspect_name]:
                # Si encontramos múltiples aspectos posibles, elegir el más exacto
                if aspect_found is None or angle_diff < orb:
                    aspect_found = aspect_name
                    orb = angle_diff
                    exact_angle = aspect_angle
        
        # Si no se encontró ningún aspecto, devolver None
        if aspect_found is None:
            return None
        
        # Determinar si el aspecto es aplicativo o separativo
        is_applying = False
        
        # Solo los planetas que no son luminares (Sol/Luna) pueden ser retrógrados
        if "retrograde" in planet1_pos and "retrograde" in planet2_pos:
            p1_retrograde = planet1_pos.get("retrograde", False)
            p2_retrograde = planet2_pos.get("retrograde", False)
            
            # Lógica para determinar si el aspecto es aplicativo
            # (se está formando) o separativo (se está disolviendo)
            # Esta es una simplificación; la lógica completa es más compleja
            if p1_retrograde and not p2_retrograde:
                is_applying = lon1 > lon2
            elif not p1_retrograde and p2_retrograde:
                is_applying = lon1 < lon2
            elif p1_retrograde and p2_retrograde:
                is_applying = lon1 < lon2
            else:  # Ninguno retrógrado
                is_applying = lon1 > lon2
        
        # Determinar la naturaleza del aspecto
        aspect_nature = "neutral"
        if aspect_found in ["conjunción"]:
            # La conjunción toma la naturaleza del planeta
            if planet1_pos["name"] in ["saturn", "mars", "pluto"]:
                aspect_nature = "desafiante"
            elif planet1_pos["name"] in ["jupiter", "venus"]:
                aspect_nature = "favorable"
            elif planet2_pos["name"] in ["saturn", "mars", "pluto"]:
                aspect_nature = "desafiante"
            elif planet2_pos["name"] in ["jupiter", "venus"]:
                aspect_nature = "favorable"
        elif aspect_found in ["trígono", "sextil"]:
            aspect_nature = "favorable"
        elif aspect_found in ["cuadratura", "oposición", "sesquicuadratura", "semicuadratura"]:
            aspect_nature = "desafiante"
        elif aspect_found in ["quincuncio"]:
            aspect_nature = "ambivalente"
        
        # Preparar el resultado
        result = {
            "aspect_type": aspect_found,
            "exact_angle": exact_angle,
            "actual_angle": diff,
            "orb": orb,
            "planet1": planet1_pos["name"],
            "planet2": planet2_pos["name"],
            "applying": is_applying,
            "separating": not is_applying,
            "nature": aspect_nature,
            "power": max(0, 10 - (orb * 10 / ASPECT_ORBS[aspect_found]))  # Potencia del 0 al 10
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error al calcular aspecto entre {planet1_pos['name']} y {planet2_pos['name']}: {str(e)}")
        return None


def calculate_aspects(planet_positions: Dict[str, Dict[str, Any]], points: Dict[str, Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Calcula todos los aspectos entre planetas y puntos en una carta astral.
    
    Args:
        planet_positions: Posiciones de los planetas
        points: Posiciones de puntos adicionales (ASC, MC, etc.)
    
    Returns:
        List[Dict]: Lista de aspectos encontrados
    """
    aspects = []
    
    # Combinar planetas y puntos
    all_positions = {}
    all_positions.update(planet_positions)
    if points:
        all_positions.update(points)
    
    # Lista de objetos para calcular aspectos
    objects = list(all_positions.keys())
    
    # Calcular aspectos entre todos los objetos
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            obj1 = objects[i]
            obj2 = objects[j]
            
            aspect = calculate_aspect(all_positions[obj1], all_positions[obj2])
            if aspect:
                aspects.append(aspect)
    
    return aspects


def calculate_dominant_element(planet_positions: Dict[str, Dict[str, Any]], houses: Dict[str, Any]) -> str:
    """
    Calcula el elemento dominante en una carta astral.
    
    Args:
        planet_positions: Posiciones de los planetas
        houses: Información sobre las casas astrológicas
    
    Returns:
        str: Elemento dominante (Fuego, Tierra, Aire, Agua)
    """
    # Conteo de elementos
    element_count = {
        "Fuego": 0,
        "Tierra": 0,
        "Aire": 0,
        "Agua": 0
    }
    
    # Pesos para diferentes planetas y puntos
    weights = {
        "sun": 3,
        "moon": 3,
        "ascendant": 3,
        "mercury": 2,
        "venus": 2,
        "mars": 2,
        "jupiter": 1,
        "saturn": 1,
        "uranus": 1,
        "neptune": 1,
        "pluto": 1
    }
    
    # Contar elementos por planeta
    for planet, pos in planet_positions.items():
        element = get_sign_element(pos["sign"])
        weight = weights.get(planet, 1)
        element_count[element] += weight
    
    # También considerar el ascendente
    if "ascendant" in houses:
        element = get_sign_element(houses["ascendant"]["sign"])
        element_count[element] += weights.get("ascendant", 3)
    
    # Encontrar el elemento con mayor conteo
    dominant = max(element_count.items(), key=lambda x: x[1])
    
    return dominant[0]


def calculate_dominant_modality(planet_positions: Dict[str, Dict[str, Any]], houses: Dict[str, Any]) -> str:
    """
    Calcula la modalidad dominante en una carta astral.
    
    Args:
        planet_positions: Posiciones de los planetas
        houses: Información sobre las casas astrológicas
    
    Returns:
        str: Modalidad dominante (Cardinal, Fijo, Mutable)
    """
    # Conteo de modalidades
    modality_count = {
        "Cardinal": 0,
        "Fijo": 0,
        "Mutable": 0
    }
    
    # Pesos para diferentes planetas y puntos
    weights = {
        "sun": 3,
        "moon": 3,
        "ascendant": 3,
        "mercury": 2,
        "venus": 2,
        "mars": 2,
        "jupiter": 1,
        "saturn": 1,
        "uranus": 1,
        "neptune": 1,
        "pluto": 1
    }
    
    # Contar modalidades por planeta
    for planet, pos in planet_positions.items():
        modality = get_sign_modality(pos["sign"])
        weight = weights.get(planet, 1)
        modality_count[modality] += weight
    
    # También considerar el ascendente
    if "ascendant" in houses:
        modality = get_sign_modality(houses["ascendant"]["sign"])
        modality_count[modality] += weights.get("ascendant", 3)
    
    # Encontrar la modalidad con mayor conteo
    dominant = max(modality_count.items(), key=lambda x: x[1])
    
    return dominant[0]


async def calculate_chart(birth_date: date, birth_time: time, 
                         latitude: float, longitude: float,
                         chart_type: ChartType) -> Dict[str, Any]:
    """
    Calcula una carta astral completa.
    
    Args:
        birth_date: Fecha de nacimiento
        birth_time: Hora de nacimiento
        latitude: Latitud del lugar
        longitude: Longitud del lugar
        chart_type: Tipo de carta astral
    
    Returns:
        Dict: Datos completos de la carta astral
    """
    try:
        logger.info(f"Calculando carta {chart_type} para fecha {birth_date} y hora {birth_time}")
        
        # Convertir fecha y hora a formato datetime
        dt = datetime.combine(birth_date, birth_time)
        
        # Convertir a tiempo Skyfield
        t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        
        # Calcular posiciones planetarias
        planet_positions = {}
        for planet_key in planets.keys():
            planet_positions[planet_key] = calculate_planet_position(planet_key, t)
        
        # Calcular ascendente y medio cielo
        asc = calculate_ascendant(t, latitude, longitude)
        mc = calculate_midheaven(t, latitude, longitude)
        
        # Añadir estos puntos a las posiciones
        special_points = {
            "ascendant": asc,
            "midheaven": mc
        }
        
        # Calcular casas astrológicas
        houses = calculate_houses(t, latitude, longitude)
        
        # Asignar planetas a casas
        for planet, pos in planet_positions.items():
            longitude = pos["longitude"]
            
            # Determinar en qué casa está el planeta
            for house_num in range(1, 13):
                house = houses["houses"][str(house_num)]
                next_house = houses["houses"][str(1 if house_num == 12 else house_num + 1)]
                
                # Verificar si el planeta está en esta casa
                if ((house["cusp"] <= longitude < next_house["cusp"]) or 
                    (house["cusp"] > next_house["cusp"] and  # Para el caso donde la casa cruza los 0°
                     (longitude >= house["cusp"] or longitude < next_house["cusp"]))):
                    houses["houses"][str(house_num)]["planets"].append(planet)
                    planet_positions[planet]["house"] = house_num
                    break
        
        # Calcular aspectos
        aspects = calculate_aspects(planet_positions, special_points)
        
        # Calcular elementos y modalidades dominantes
        dominant_element = calculate_dominant_element(planet_positions, special_points)
        dominant_modality = calculate_dominant_modality(planet_positions, special_points)
        
        # Construir el resultado
        chart_data = {
            "type": chart_type,
            "date": birth_date.isoformat(),
            "time": birth_time.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "planets": planet_positions,
            "points": special_points,
            "houses": houses,
            "aspects": aspects,
            "dominant_element": dominant_element,
            "dominant_modality": dominant_modality,
            # Añadir datos específicos del tipo de carta
            "sun_sign": planet_positions["sun"]["sign"],
            "moon_sign": planet_positions["moon"]["sign"],
            "rising_sign": asc["sign"]
        }
        
        logger.info(f"Carta astral calculada con éxito: {chart_type}")
        return chart_data
    
    except Exception as e:
        logger.error(f"Error al calcular carta astral: {str(e)}")
        raise CalculationError(message=f"Error al calcular carta astral: {str(e)}", 
                              calculation_type=chart_type)


async def calculate_transits(birth_date: date, birth_time: time,
                            birth_latitude: float, birth_longitude: float,
                            prediction_date: date, prediction_period: PredictionPeriod) -> Dict[str, Any]:
    """
    Calcula los tránsitos planetarios para un período de predicción.
    
    Args:
        birth_date: Fecha de nacimiento
        birth_time: Hora de nacimiento
        birth_latitude: Latitud del lugar de nacimiento
        birth_longitude: Longitud del lugar de nacimiento
        prediction_date: Fecha inicial para la predicción
        prediction_period: Período de la predicción
    
    Returns:
        Dict: Información sobre los tránsitos planetarios
    """
    try:
        logger.info(f"Calculando tránsitos para período {prediction_period} desde {prediction_date}")
        
        # Calcular la carta natal primero
        natal_chart = await calculate_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=birth_latitude,
            longitude=birth_longitude,
            chart_type=ChartType.NATAL
        )
        
        # Determinar fecha final según el período
        if prediction_period == PredictionPeriod.DAY:
            end_date = prediction_date
        elif prediction_period == PredictionPeriod.WEEK:
            end_date = prediction_date + timedelta(days=7)
        elif prediction_period == PredictionPeriod.MONTH:
            # Aproximación simple de un mes (30 días)
            end_date = prediction_date + timedelta(days=30)
        elif prediction_period == PredictionPeriod.YEAR:
            # Aproximación simple de un año (365 días)
            end_date = prediction_date + timedelta(days=365)
        else:  # CUSTOM o caso por defecto
            # En caso de período personalizado, asumimos una semana
            end_date = prediction_date + timedelta(days=7)
        
        # Convertir fechas a tiempos Skyfield
        start_dt = datetime.combine(prediction_date, time(0, 0, 0))
        end_dt = datetime.combine(end_date, time(23, 59, 59))
        
        start_t = ts.utc(start_dt.year, start_dt.month, start_dt.day, 
                        start_dt.hour, start_dt.minute, start_dt.second)
        end_t = ts.utc(end_dt.year, end_dt.month, end_dt.day, 
                      end_dt.hour, end_dt.minute, end_dt.second)
        
        # Calcular posiciones planetarias al inicio del período
        transit_positions_start = {}
        for planet_key in planets.keys():
            transit_positions_start[planet_key] = calculate_planet_position(planet_key, start_t)
        
        # Calcular posiciones planetarias al final del período
        transit_positions_end = {}
        for planet_key in planets.keys():
            transit_positions_end[planet_key] = calculate_planet_position(planet_key, end_t)
        
        # Calcular aspectos entre tránsitos y carta natal
        transit_aspects = []
        
        for transit_planet, transit_pos in transit_positions_start.items():
            for natal_planet, natal_pos in natal_chart["planets"].items():
                aspect = calculate_aspect(transit_pos, natal_pos)
                if aspect:
                    # Añadir información adicional para distinguir entre natal y tránsito
                    aspect["transit_planet"] = transit_planet
                    aspect["natal_planet"] = natal_planet
                    transit_aspects.append(aspect)
        
        # Identificar tránsitos significativos
        significant_transits = []
        
        # Planetas lentos (más significativos en tránsitos)
        slow_planets = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
        
        # Puntos sensibles de la carta natal
        sensitive_points = ["sun", "moon", "ascendant", "midheaven"]
        
        # Filtrar aspectos más significativos
        for aspect in transit_aspects:
            is_significant = False
            
            # Aspectos de planetas lentos a puntos sensibles
            if aspect["transit_planet"] in slow_planets and aspect["natal_planet"] in sensitive_points:
                is_significant = True
            
            # Aspectos exactos (orbe pequeño)
            elif aspect["orb"] < 1.0:
                is_significant = True
            
            # Aspectos mayores (conjunción, oposición, cuadratura, trígono)
            elif aspect["aspect_type"] in ["conjunción", "oposición", "cuadratura", "trígono"]:
                is_significant = True
            
            if is_significant:
                significant_transits.append(aspect)
        
        # Construir el resultado
        transit_data = {
            "natal_chart": natal_chart,
            "prediction_period": prediction_period,
            "start_date": prediction_date.isoformat(),
            "end_date": end_date.isoformat(),
            "transit_positions_start": transit_positions_start,
            "transit_positions_end": transit_positions_end,
            "transit_aspects": transit_aspects,
            "significant_transits": significant_transits
        }
        
        logger.info(f"Tránsitos calculados con éxito para período {prediction_period}")
        return transit_data
    
    except Exception as e:
        logger.error(f"Error al calcular tránsitos: {str(e)}")
        raise CalculationError(message=f"Error al calcular tránsitos: {str(e)}", 
                              calculation_type="tránsitos")


async def calculate_compatibility(person1_birth_date: date, person1_birth_time: time,
                                 person1_latitude: float, person1_longitude: float,
                                 person2_birth_date: date, person2_birth_time: time,
                                 person2_latitude: float, person2_longitude: float,
                                 compatibility_type: CompatibilityType) -> Dict[str, Any]:
    """
    Calcula la compatibilidad astrológica entre dos personas.
    
    Args:
        person1_birth_date: Fecha de nacimiento de la primera persona
        person1_birth_time: Hora de nacimiento de la primera persona
        person1_latitude: Latitud del lugar de nacimiento de la primera persona
        person1_longitude: Longitud del lugar de nacimiento de la primera persona
        person2_birth_date: Fecha de nacimiento de la segunda persona
        person2_birth_time: Hora de nacimiento de la segunda persona
        person2_latitude: Latitud del lugar de nacimiento de la segunda persona
        person2_longitude: Longitud del lugar de nacimiento de la segunda persona
        compatibility_type: Tipo de compatibilidad a calcular
    
    Returns:
        Dict: Información sobre la compatibilidad
    """
    try:
        logger.info(f"Calculando compatibilidad {compatibility_type} entre dos cartas natales")
        
        # Calcular las cartas natales de ambas personas
        chart1 = await calculate_chart(
            birth_date=person1_birth_date,
            birth_time=person1_birth_time,
            latitude=person1_latitude,
            longitude=person1_longitude,
            chart_type=ChartType.NATAL
        )
        
        chart2 = await calculate_chart(
            birth_date=person2_birth_date,
            birth_time=person2_birth_time,
            latitude=person2_latitude,
            longitude=person2_longitude,
            chart_type=ChartType.NATAL
        )
        
        # Calcular aspectos entre las dos cartas (sinastría)
        synastry_aspects = []
        
        for planet1, pos1 in chart1["planets"].items():
            for planet2, pos2 in chart2["planets"].items():
                aspect = calculate_aspect(pos1, pos2)
                if aspect:
                    # Añadir información de a quién pertenece cada planeta
                    aspect["person1_planet"] = planet1
                    aspect["person2_planet"] = planet2
                    synastry_aspects.append(aspect)
        
        # Añadir aspectos con puntos especiales
        for planet1, pos1 in chart1["planets"].items():
            for point2, pos2 in chart2["points"].items():
                aspect = calculate_aspect(pos1, pos2)
                if aspect:
                    aspect["person1_planet"] = planet1
                    aspect["person2_point"] = point2
                    synastry_aspects.append(aspect)
                    
        for point1, pos1 in chart1["points"].items():
            for planet2, pos2 in chart2["planets"].items():
                aspect = calculate_aspect(pos1, pos2)
                if aspect:
                    aspect["person1_point"] = point1
                    aspect["person2_planet"] = planet2
                    synastry_aspects.append(aspect)
        
        # Calcular puntuación de compatibilidad
        compatibility_score = calculate_compatibility_score(
            chart1, chart2, synastry_aspects, compatibility_type
        )
        
        # Analizar puntos fuertes y desafíos
        strengths, challenges = analyze_compatibility_points(
            chart1, chart2, synastry_aspects, compatibility_type
        )
        
        # Calcular posiciones medias (para carta compuesta)
        composite_positions = calculate_composite_positions(chart1, chart2)
        
        # Construir el resultado
        compatibility_data = {
            "compatibility_type": compatibility_type,
            "chart1": chart1,
            "chart2": chart2,
            "synastry_aspects": synastry_aspects,
            "composite_chart": composite_positions,
            "compatibility_score": compatibility_score,
            "strengths": strengths,
            "challenges": challenges
        }
        
        logger.info(f"Compatibilidad calculada con éxito: puntuación {compatibility_score}")
        return compatibility_data
    
    except Exception as e:
        logger.error(f"Error al calcular compatibilidad: {str(e)}")
        raise CalculationError(message=f"Error al calcular compatibilidad: {str(e)}", 
                              calculation_type="compatibilidad")


def calculate_compatibility_score(chart1: Dict[str, Any], chart2: Dict[str, Any], 
                                 aspects: List[Dict[str, Any]], 
                                 compatibility_type: CompatibilityType) -> float:
    """
    Calcula una puntuación numérica para la compatibilidad.
    
    Args:
        chart1: Carta natal de la primera persona
        chart2: Carta natal de la segunda persona
        aspects: Aspectos entre ambas cartas
        compatibility_type: Tipo de compatibilidad
    
    Returns:
        float: Puntuación de compatibilidad (0-100)
    """
    # Puntuación base
    score = 50.0
    
    # Pesos para diferentes tipos de compatibilidad
    weights = {
        CompatibilityType.ROMANTIC: {
            "sun-moon": 5.0,
            "venus-mars": 5.0,
            "venus-venus": 4.0,
            "moon-moon": 4.0,
            "ascendant-ascendant": 3.0,
            "sun-ascendant": 3.0,
            "moon-ascendant": 3.0,
            "venus-ascendant": 2.0,
            "mars-ascendant": 2.0,
            "sun-venus": 2.0,
            "moon-venus": 2.0,
            "mars-mars": 1.0,
            "mercury-mercury": 1.0
        },
        CompatibilityType.FRIENDSHIP: {
            "sun-sun": 5.0,
            "moon-moon": 4.0,
            "mercury-mercury": 4.0,
            "venus-venus": 3.0,
            "sun-mercury": 3.0,
            "moon-mercury": 3.0,
            "sun-moon": 2.0,
            "jupiter-jupiter": 2.0,
            "mars-jupiter": 1.0
        },
        CompatibilityType.PROFESSIONAL: {
            "sun-sun": 3.0,
            "mercury-mercury": 5.0,
            "mars-mars": 4.0,
            "saturn-saturn": 3.0,
            "sun-mercury": 4.0,
            "mercury-jupiter": 3.0,
            "mars-jupiter": 2.0,
            "sun-saturn": 2.0,
            "mercury-saturn": 2.0,
            "moon-mercury": 1.0
        },
        CompatibilityType.FAMILY: {
            "sun-moon": 5.0,
            "moon-moon": 4.0,
            "saturn-saturn": 3.0,
            "jupiter-jupiter": 3.0,
            "venus-jupiter": 2.0,
            "sun-jupiter": 2.0,
            "moon-saturn": 2.0,
            "venus-saturn": 1.0,
            "mars-saturn": 1.0
        }
    }
    
    # Si es un tipo de compatibilidad general, usar un promedio de todos los tipos
    if compatibility_type == CompatibilityType.GENERAL:
        all_weights = {}
        for type_weights in weights.values():
            for key, value in type_weights.items():
                if key in all_weights:
                    all_weights[key] += value
                else:
                    all_weights[key] = value
        
        # Promediar los pesos
        for key in all_weights:
            all_weights[key] /= len(weights)
        
        current_weights = all_weights
    else:
        current_weights = weights.get(compatibility_type, weights[CompatibilityType.GENERAL])
    
    # Evaluar aspectos
    for aspect in aspects:
        # Determinar los planetas/puntos involucrados
        planet1 = aspect.get("person1_planet", aspect.get("person1_point"))
        planet2 = aspect.get("person2_planet", aspect.get("person2_point"))
        
        if not planet1 or not planet2:
            continue
        
        # Crear clave para buscar en weights (orden no importa)
        pair = sorted([planet1, planet2])
        pair_key = f"{pair[0]}-{pair[1]}"
        
        # Obtener peso para este par de planetas
        weight = current_weights.get(pair_key, 1.0)
        
        # Modificar la puntuación según el tipo de aspecto y su naturaleza
        if aspect["nature"] == "favorable":
            if aspect["aspect_type"] in ["conjunción", "trígono", "sextil"]:
                score += weight * aspect["power"] * 0.5
        elif aspect["nature"] == "desafiante":
            if aspect["aspect_type"] in ["cuadratura", "oposición"]:
                score -= weight * aspect["power"] * 0.3
        elif aspect["nature"] == "ambivalente":
            # Los aspectos ambivalentes tienen un efecto mixto
            score += weight * aspect["power"] * 0.1
    
    # Evaluar elementos y modalidades
    element_compatibility = evaluate_element_compatibility(chart1, chart2)
    modality_compatibility = evaluate_modality_compatibility(chart1, chart2)
    
    score += element_compatibility * 5.0
    score += modality_compatibility * 5.0
    
    # Limitar la puntuación al rango 0-100
    score = max(0, min(score, 100))
    
    return score


def evaluate_element_compatibility(chart1: Dict[str, Any], chart2: Dict[str, Any]) -> float:
    """
    Evalúa la compatibilidad entre los elementos dominantes de dos cartas.
    
    Args:
        chart1: Carta natal de la primera persona
        chart2: Carta natal de la segunda persona
    
    Returns:
        float: Puntuación de compatibilidad de elementos (-1.0 a 1.0)
    """
    element1 = chart1["dominant_element"]
    element2 = chart2["dominant_element"]
    
    # Matriz de compatibilidad de elementos
    # Valores de -1.0 (conflicto) a 1.0 (armonía)
    element_matrix = {
        "Fuego": {"Fuego": 0.5, "Tierra": -0.5, "Aire": 1.0, "Agua": -0.5},
        "Tierra": {"Fuego": -0.5, "Tierra": 0.5, "Aire": -0.5, "Agua": 1.0},
        "Aire": {"Fuego": 1.0, "Tierra": -0.5, "Aire": 0.5, "Agua": -0.5},
        "Agua": {"Fuego": -0.5, "Tierra": 1.0, "Aire": -0.5, "Agua": 0.5}
    }
    
    return element_matrix[element1][element2]


def evaluate_modality_compatibility(chart1: Dict[str, Any], chart2: Dict[str, Any]) -> float:
    """
    Evalúa la compatibilidad entre las modalidades dominantes de dos cartas.
    
    Args:
        chart1: Carta natal de la primera persona
        chart2: Carta natal de la segunda persona
    
    Returns:
        float: Puntuación de compatibilidad de modalidades (-1.0 a 1.0)
    """
    modality1 = chart1["dominant_modality"]
    modality2 = chart2["dominant_modality"]
    
    # Matriz de compatibilidad de modalidades
    # Valores de -1.0 (conflicto) a 1.0 (armonía)
    modality_matrix = {
        "Cardinal": {"Cardinal": -0.5, "Fijo": 0.0, "Mutable": 0.5},
        "Fijo": {"Cardinal": 0.0, "Fijo": -0.5, "Mutable": 0.0},
        "Mutable": {"Cardinal": 0.5, "Fijo": 0.0, "Mutable": 0.0}
    }
    
    return modality_matrix[modality1][modality2]


def analyze_compatibility_points(chart1: Dict[str, Any], chart2: Dict[str, Any],
                                aspects: List[Dict[str, Any]], 
                                compatibility_type: CompatibilityType) -> Tuple[List[str], List[str]]:
    """
    Analiza los puntos fuertes y desafíos de la compatibilidad.
    
    Args:
        chart1: Carta natal de la primera persona
        chart2: Carta natal de la segunda persona
        aspects: Aspectos entre ambas cartas
        compatibility_type: Tipo de compatibilidad
    
    Returns:
        Tuple[List[str], List[str]]: Listas de puntos fuertes y desafíos
    """
    strengths = []
    challenges = []
    
    # Analizar aspectos más importantes
    for aspect in aspects:
        planet1 = aspect.get("person1_planet", aspect.get("person1_point"))
        planet2 = aspect.get("person2_planet", aspect.get("person2_point"))
        
        if not planet1 or not planet2:
            continue
        
        # Construir descripción del aspecto
        description = f"{planet1.capitalize()}-{planet2.capitalize()} en {aspect['aspect_type']}"
        
        # Categorizar según naturaleza y poder del aspecto
        if aspect["nature"] == "favorable" and aspect["power"] > 5:
            strengths.append(description)
        elif aspect["nature"] == "desafiante" and aspect["power"] > 5:
            challenges.append(description)
    
    # Analizar compatibilidad de elementos
    element1 = chart1["dominant_element"]
    element2 = chart2["dominant_element"]
    
    element_comp = evaluate_element_compatibility(chart1, chart2)
    if element_comp > 0:
        strengths.append(f"Compatibilidad favorable entre {element1} y {element2}")
    elif element_comp < 0:
        challenges.append(f"Tensión entre los elementos {element1} y {element2}")
    
    # Analizar compatibilidad de modalidades
    modality1 = chart1["dominant_modality"]
    modality2 = chart2["dominant_modality"]
    
    modality_comp = evaluate_modality_compatibility(chart1, chart2)
    if modality_comp > 0:
        strengths.append(f"Energías complementarias entre {modality1} y {modality2}")
    elif modality_comp < 0:
        challenges.append(f"Posible fricción entre modalidades {modality1} y {modality2}")
    
    # Personalizar según el tipo de compatibilidad
    if compatibility_type == CompatibilityType.ROMANTIC:
        # Verificar aspectos específicos importantes para compatibilidad romántica
        venus_mars = False
        sun_moon = False
        
        for aspect in aspects:
            if ((aspect.get("person1_planet") == "venus" and aspect.get("person2_planet") == "mars") or
                (aspect.get("person1_planet") == "mars" and aspect.get("person2_planet") == "venus")):
                venus_mars = True
                if aspect["nature"] == "favorable":
                    strengths.append("Fuerte atracción física y química entre ambos")
                else:
                    challenges.append("Posible tensión en la expresión física del afecto")
            
            if ((aspect.get("person1_planet") == "sun" and aspect.get("person2_planet") == "moon") or
                (aspect.get("person1_planet") == "moon" and aspect.get("person2_planet") == "sun")):
                sun_moon = True
                if aspect["nature"] == "favorable":
                    strengths.append("Fuerte conexión emocional y complementariedad")
                else:
                    challenges.append("Posibles desajustes en necesidades emocionales básicas")
    
    elif compatibility_type == CompatibilityType.PROFESSIONAL:
        # Enfocarse en aspectos relevantes para trabajo
        mercury_aspects = [a for a in aspects if "mercury" in (a.get("person1_planet", ""), a.get("person2_planet", ""))]
        saturn_aspects = [a for a in aspects if "saturn" in (a.get("person1_planet", ""), a.get("person2_planet", ""))]
        
        if any(a["nature"] == "favorable" for a in mercury_aspects):
            strengths.append("Buena comunicación y entendimiento mutuo")
        
        if any(a["nature"] == "favorable" for a in saturn_aspects):
            strengths.append("Potencial para construir estructuras estables y duraderas")
    
    # Limitar el número de puntos para no sobrecargar la interpretación
    return strengths[:10], challenges[:10]


def calculate_composite_positions(chart1: Dict[str, Any], chart2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula las posiciones para una carta compuesta (promedio de dos cartas).
    
    Args:
        chart1: Carta natal de la primera persona
        chart2: Carta natal de la segunda persona
    
    Returns:
        Dict: Posiciones de la carta compuesta
    """
    composite = {
        "planets": {},
        "points": {},
        "sun_sign": "",
        "moon_sign": "",
        "rising_sign": ""
    }
    
    # Calcular posiciones promedio para planetas
    for planet in chart1["planets"].keys():
        if planet in chart2["planets"]:
            lon1 = chart1["planets"][planet]["longitude"]
            lon2 = chart2["planets"][planet]["longitude"]
            
            # Manejar el caso especial cuando los planetas están en lados opuestos del zodíaco
            if abs(lon2 - lon1) > 180:
                if lon1 < lon2:
                    lon1 += 360
                else:
                    lon2 += 360
            
            # Calcular promedio
            composite_lon = (lon1 + lon2) / 2
            composite_lon %= 360
            
            # Determinar signo y posición en el signo
            sign = get_zodiac_sign(composite_lon)
            position_in_sign = composite_lon % 30
            
            composite["planets"][planet] = {
                "name": planet,
                "sign": sign,
                "longitude": composite_lon,
                "position_in_sign": position_in_sign,
                "degree": f"{int(position_in_sign)}° {int(position_in_sign * 60) % 60}' {sign}"
            }
    
    # Calcular posiciones promedio para puntos especiales
    for point in chart1["points"].keys():
        if point in chart2["points"]:
            lon1 = chart1["points"][point]["longitude"]
            lon2 = chart2["points"][point]["longitude"]
            
            # Manejar el caso especial cuando los puntos están en lados opuestos del zodíaco
            if abs(lon2 - lon1) > 180:
                if lon1 < lon2:
                    lon1 += 360
                else:
                    lon2 += 360
            
            # Calcular promedio
            composite_lon = (lon1 + lon2) / 2
            composite_lon %= 360
            
            # Determinar signo y posición en el signo
            sign = get_zodiac_sign(composite_lon)
            position_in_sign = composite_lon % 30
            
            composite["points"][point] = {
                "name": point,
                "sign": sign,
                "longitude": composite_lon,
                "position_in_sign": position_in_sign,
                "degree": f"{int(position_in_sign)}° {int(position_in_sign * 60) % 60}' {sign}"
            }
    
    # Establecer signos principales
    if "sun" in composite["planets"]:
        composite["sun_sign"] = composite["planets"]["sun"]["sign"]
    
    if "moon" in composite["planets"]:
        composite["moon_sign"] = composite["planets"]["moon"]["sign"]
    
    if "ascendant" in composite["points"]:
        composite["rising_sign"] = composite["points"]["ascendant"]["sign"]
    
    return composite

def get_sidereal_time(t: Time, longitude: float) -> float:
    """
    Calcula el tiempo sidéreo local en horas para una ubicación dada.

    Args:
        t (Time): Objeto de tiempo de Skyfield
        longitude (float): Longitud geográfica en grados

    Returns:
        float: Tiempo sidéreo local en horas
    """
    try:
        # Obtener GMST (Tiempo Sidéreo Medio de Greenwich) desde el objeto Time
        gmst = t.gmst  # Ahora se obtiene directamente de 't'

        # Convertir GMST a Tiempo Sidéreo Local (LST)
        lst = (gmst + longitude / 15) % 24  # 15° de longitud = 1 hora

        return lst
    except Exception as e:
        raise ValueError(f"Error al calcular tiempo sidéreo local: {str(e)}")