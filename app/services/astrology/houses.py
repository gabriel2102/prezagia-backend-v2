"""
Servicios de cálculo de casas astrológicas para la aplicación Prezagia.

Este módulo implementa algoritmos para calcular las cúspides de las casas astrológicas
usando diferentes sistemas (Placidus, Koch, Equal, etc.) basados en los datos astronómicos.
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.core.logger import logger
from app.core.exceptions import CalculationError


def calculate_houses(t, latitude: float, longitude: float, system: str = "placidus") -> Dict[str, Any]:
    """
    Calcula las casas astrológicas para un momento y lugar específicos
    con el sistema elegido.
    
    Args:
        t: Tiempo de Skyfield
        latitude: Latitud del lugar en grados
        longitude: Longitud del lugar en grados
        system: Sistema de casas a utilizar
    
    Returns:
        Dict: Información sobre las casas astrológicas
    """
    try:
        # Elegir el sistema de casas apropiado
        if system.lower() == "placidus":
            return calculate_placidus_houses(t, latitude, longitude)
        elif system.lower() == "koch":
            return calculate_koch_houses(t, latitude, longitude)
        elif system.lower() == "equal":
            return calculate_equal_houses(t, latitude, longitude)
        elif system.lower() == "whole_sign":
            return calculate_whole_sign_houses(t, latitude, longitude)
        else:
            # Por defecto, usar Placidus
            logger.warning(f"Sistema de casas '{system}' no implementado, utilizando Placidus por defecto")
            return calculate_placidus_houses(t, latitude, longitude)
            
    except Exception as e:
        logger.error(f"Error al calcular casas astrológicas con sistema {system}: {str(e)}")
        raise CalculationError(message=f"Error al calcular las casas astrológicas: {str(e)}", 
                              calculation_type="casas")


def calculate_placidus_houses(t, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calcula las casas astrológicas usando el sistema Placidus.
    
    Args:
        t: Tiempo de Skyfield
        latitude: Latitud del lugar en grados
        longitude: Longitud del lugar en grados
    
    Returns:
        Dict: Información sobre las casas astrológicas
    """
    try:
        from skyfield.api import load, wgs84
        from skyfield.framelib import ecliptic_frame
        
        # Crear ubicación terrestre
        location = wgs84.latlon(latitude, longitude)
        
        # Obtener la hora sideral local
        from skyfield.earthlib import sidereal_time
        gst = sidereal_time(t.ut1)
        lst = (gst + longitude/15) % 24
        lst_degrees = (lst * 15) % 360
        
        # Convertir a radianes para cálculos
        lat_rad = np.radians(latitude)
        
        # Calcular la oblicuidad de la eclíptica (ε)
        ecliptic_obliquity = 23.4393 - 0.0000004 * (t.tt - 2451545.0) / 36525
        epsilon_rad = np.radians(ecliptic_obliquity)
        
        # Calcular el ascendente
        lst_rad = np.radians(lst_degrees)
        tan_asc = np.cos(epsilon_rad) * np.sin(lst_rad) / (np.cos(lst_rad) * np.sin(lat_rad) + np.sin(epsilon_rad) * np.sin(lst_rad) * np.cos(lat_rad))
        asc_rad = np.arctan(tan_asc)
        
        # Convertir a grados y ajustar el cuadrante
        asc_deg = np.degrees(asc_rad)
        
        # Ajustar el cuadrante basado en LST
        if 90 <= lst_degrees < 270:
            asc_deg += 180
        
        # Normalizar a 0-360 grados
        asc_deg = asc_deg % 360
        
        # Calcular el Medio Cielo (MC)
        tan_mc = np.tan(lst_rad) / np.cos(epsilon_rad)
        mc_rad = np.arctan(tan_mc)
        
        # Convertir a grados y ajustar el cuadrante
        mc_deg = np.degrees(mc_rad)
        
        # Ajustar el cuadrante basado en LST
        if 90 <= lst_degrees < 270:
            mc_deg += 180
        
        # Normalizar a 0-360 grados
        mc_deg = mc_deg % 360
        
        # Casa 7 (Descendente - opuesto al Ascendente)
        desc_deg = (asc_deg + 180) % 360
        
        # Casa 4 (Imum Coeli - opuesto al Medio Cielo)
        ic_deg = (mc_deg + 180) % 360
        
        # Algoritmo de Placidus para casas intermedias
        # Este es un algoritmo simplificado - en la práctica es más complejo
        
        # Funciones auxiliares para el sistema Placidus
        def placidus_house_cusp(ra_mc, declination, latitude, house_number):
            """
            Calcula una cúspide de casa intermedia usando la fórmula de Placidus.
            """
            # Convertir todo a radianes
            ra_mc_rad = np.radians(ra_mc)
            declination_rad = np.radians(declination)
            latitude_rad = np.radians(latitude)
            
            # Calcular el factor de la casa
            house_factor = (house_number - 1) / 3.0
            
            # Calcular la semi-arco diurno/nocturno
            if house_number < 7:  # Casas diurnas
                semi_arc = np.arccos(-np.tan(declination_rad) * np.tan(latitude_rad))
            else:  # Casas nocturnas
                semi_arc = np.arccos(np.tan(declination_rad) * np.tan(latitude_rad))
            
            # Calcular la ascensión recta de la cúspide
            if house_number < 4 or (house_number > 6 and house_number < 10):
                ra_cusp = ra_mc_rad - semi_arc * house_factor
            else:
                ra_cusp = ra_mc_rad + semi_arc * (1 - house_factor)
            
            # Convertir de ascensión recta a longitud eclíptica
            # Esta es una aproximación simplificada
            lon_cusp = np.degrees(ra_cusp) % 360
            
            return lon_cusp
        
        # Calcular casas intermedias simplificadas
        # Para una implementación completa, se necesitaría un algoritmo más sofisticado
        cusps = {
            "1": asc_deg,
            "4": ic_deg, 
            "7": desc_deg,
            "10": mc_deg
        }
        
        # Simplificación - interpolar linealmente entre las casas cardinales
        cusps["2"] = (2*cusps["1"] + cusps["4"]) / 3
        cusps["3"] = (cusps["1"] + 2*cusps["4"]) / 3
        cusps["5"] = (2*cusps["4"] + cusps["7"]) / 3
        cusps["6"] = (cusps["4"] + 2*cusps["7"]) / 3
        cusps["8"] = (2*cusps["7"] + cusps["10"]) / 3
        cusps["9"] = (cusps["7"] + 2*cusps["10"]) / 3
        cusps["11"] = (2*cusps["10"] + cusps["1"] + 360) / 3 % 360
        cusps["12"] = (cusps["10"] + 2*(cusps["1"] + 360)) / 3 % 360
        
        # Normalizar todos los valores a 0-360
        for house in cusps:
            cusps[house] = cusps[house] % 360
        
        # Construir resultado
        result = {
            "system": "placidus",
            "houses": {}
        }
        
        # Determinar el signo zodiacal para cada cúspide
        for house, degree in cusps.items():
            sign_number = int(degree / 30)
            signs = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", 
                    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
            sign = signs[sign_number]
            position_in_sign = degree % 30
            
            result["houses"][house] = {
                "cusp": degree,
                "sign": sign,
                "degree": f"{int(position_in_sign)}° {int(position_in_sign * 60) % 60}' {sign}",
                "planets": []  # Lista de planetas en esta casa, se rellenará después
            }
        
        return result
    
    except Exception as e:
        logger.error(f"Error en cálculo de casas Placidus: {str(e)}")
        raise CalculationError(message=f"Error al calcular casas Placidus: {str(e)}", 
                              calculation_type="casas_placidus")


def calculate_koch_houses(t, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calcula las casas astrológicas usando el sistema Koch.
    
    Args:
        t: Tiempo de Skyfield
        latitude: Latitud del lugar en grados
        longitude: Longitud del lugar en grados
    
    Returns:
        Dict: Información sobre las casas astrológicas
    """
    try:
        # Simplificación - usar el mismo código que Placidus por ahora
        # En una implementación real, aquí iría el algoritmo específico para Koch
        result = calculate_placidus_houses(t, latitude, longitude)
        result["system"] = "koch"
        
        logger.info("Sistema Koch aproximado con Placidus")
        return result
    
    except Exception as e:
        logger.error(f"Error en cálculo de casas Koch: {str(e)}")
        raise CalculationError(message=f"Error al calcular casas Koch: {str(e)}", 
                              calculation_type="casas_koch")


def calculate_equal_houses(t, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calcula las casas astrológicas usando el sistema de Casas Iguales.
    
    Args:
        t: Tiempo de Skyfield
        latitude: Latitud del lugar en grados
        longitude: Longitud del lugar en grados
    
    Returns:
        Dict: Información sobre las casas astrológicas
    """
    try:
        from skyfield.api import load, wgs84
        from skyfield.framelib import ecliptic_frame
        
        # Calcular el ascendente primero
        # Crear ubicación terrestre
        location = wgs84.latlon(latitude, longitude)
        
        # Obtener la hora sideral local
        from skyfield.earthlib import sidereal_time
        gst = sidereal_time(t.ut1)
        lst = (gst + longitude/15) % 24
        lst_degrees = (lst * 15) % 360
        
        # Convertir a radianes para cálculos
        lat_rad = np.radians(latitude)
        
        # Calcular la oblicuidad de la eclíptica (ε)
        ecliptic_obliquity = 23.4393 - 0.0000004 * (t.tt - 2451545.0) / 36525
        epsilon_rad = np.radians(ecliptic_obliquity)
        
        # Calcular el ascendente
        lst_rad = np.radians(lst_degrees)
        tan_asc = np.cos(epsilon_rad) * np.sin(lst_rad) / (np.cos(lst_rad) * np.sin(lat_rad) + np.sin(epsilon_rad) * np.sin(lst_rad) * np.cos(lat_rad))
        asc_rad = np.arctan(tan_asc)
        
        # Convertir a grados y ajustar el cuadrante
        asc_deg = np.degrees(asc_rad)
        
        # Ajustar el cuadrante basado en LST
        if 90 <= lst_degrees < 270:
            asc_deg += 180
        
        # Normalizar a 0-360 grados
        asc_deg = asc_deg % 360
        
        # En el sistema de Casas Iguales, cada casa tiene 30 grados exactos
        # y el Ascendente es el inicio de la primera casa
        
        # Construir resultado
        result = {
            "system": "equal",
            "houses": {}
        }
        
        # Calcular todas las cúspides, empezando por el Ascendente
        for i in range(1, 13):
            cusp_degree = (asc_deg + (i-1) * 30) % 360
            sign_number = int(cusp_degree / 30)
            signs = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", 
                    "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
            sign = signs[sign_number]
            position_in_sign = cusp_degree % 30
            
            result["houses"][str(i)] = {
                "cusp": cusp_degree,
                "sign": sign,
                "degree": f"{int(position_in_sign)}° {int(position_in_sign * 60) % 60}' {sign}",
                "planets": []  # Lista de planetas en esta casa, se rellenará después
            }
        
        return result
    
    except Exception as e:
        logger.error(f"Error en cálculo de casas Iguales: {str(e)}")
        raise CalculationError(message=f"Error al calcular casas Iguales: {str(e)}", 
                              calculation_type="casas_iguales")


def calculate_whole_sign_houses(t, latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Calcula las casas astrológicas usando el sistema de Casas de Signo Completo.
    
    Args:
        t: Tiempo de Skyfield
        latitude: Latitud del lugar en grados
        longitude: Longitud del lugar en grados
    
    Returns:
        Dict: Información sobre las casas astrológicas
    """
    try:
        from skyfield.api import load, wgs84
        from skyfield.framelib import ecliptic_frame
        
        # Calcular el ascendente primero
        # Crear ubicación terrestre
        location = wgs84.latlon(latitude, longitude)
        
        # Obtener la hora sideral local
        from skyfield.earthlib import sidereal_time
        gst = sidereal_time(t.ut1)
        lst = (gst + longitude/15) % 24
        lst_degrees = (lst * 15) % 360
        
        # Convertir a radianes para cálculos
        lat_rad = np.radians(latitude)
        
        # Calcular la oblicuidad de la eclíptica (ε)
        ecliptic_obliquity = 23.4393 - 0.0000004 * (t.tt - 2451545.0) / 36525
        epsilon_rad = np.radians(ecliptic_obliquity)
        
        # Calcular el ascendente
        lst_rad = np.radians(lst_degrees)
        tan_asc = np.cos(epsilon_rad) * np.sin(lst_rad) / (np.cos(lst_rad) * np.sin(lat_rad) + np.sin(epsilon_rad) * np.sin(lst_rad) * np.cos(lat_rad))
        asc_rad = np.arctan(tan_asc)
        
        # Convertir a grados y ajustar el cuadrante
        asc_deg = np.degrees(asc_rad)
        
        # Ajustar el cuadrante basado en LST
        if 90 <= lst_degrees < 270:
            asc_deg += 180
        
        # Normalizar a 0-360 grados
        asc_deg = asc_deg % 360
        
        # Determinar el signo ascendente
        signs = ["Aries", "Tauro", "Géminis", "Cáncer", "Leo", "Virgo", 
                "Libra", "Escorpio", "Sagitario", "Capricornio", "Acuario", "Piscis"]
        asc_sign_num = int(asc_deg / 30)
        
        # En el sistema de Casas de Signo Completo, cada casa corresponde a un signo completo
        # La primera casa corresponde al signo donde cae el Ascendente
        
        # Construir resultado
        result = {
            "system": "whole_sign",
            "houses": {}
        }
        
        # Calcular todas las cúspides
        for i in range(1, 13):
            # La cúspide de cada casa es el inicio del signo correspondiente
            sign_num = (asc_sign_num + i - 1) % 12
            cusp_degree = sign_num * 30
            sign = signs[sign_num]
            
            result["houses"][str(i)] = {
                "cusp": cusp_degree,
                "sign": sign,
                "degree": f"0° 0' {sign}",
                "planets": []  # Lista de planetas en esta casa, se rellenará después
            }
        
        return result
    
    except Exception as e:
        logger.error(f"Error en cálculo de casas de Signo Completo: {str(e)}")
        raise CalculationError(message=f"Error al calcular casas de Signo Completo: {str(e)}", 
                              calculation_type="casas_signo_completo")


def assign_planets_to_houses(planet_positions: Dict[str, Dict[str, Any]], houses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Asigna planetas a las casas astrológicas según sus posiciones.
    
    Args:
        planet_positions: Diccionario con posiciones planetarias
        houses: Información sobre las casas astrológicas
    
    Returns:
        Dict: Casas astrológicas actualizadas con planetas asignados
    """
    try:
        result = houses.copy()
        system = houses["system"]
        
        # Obtener la lista de cúspides ordenadas por número de casa
        house_nums = sorted([int(num) for num in houses["houses"].keys()])
        house_cusps = [houses["houses"][str(num)]["cusp"] for num in house_nums]
        
        # Asignar cada planeta a una casa
        for planet, data in planet_positions.items():
            longitude = data["longitude"]
            assigned = False
            
            # Método diferente según el sistema de casas
            if system == "whole_sign":
                # Para casas de signo completo, simplemente verificar en qué signo está el planeta
                sign_num = int(longitude / 30)
                asc_sign_num = int(houses["houses"]["1"]["cusp"] / 30)
                house_num = (sign_num - asc_sign_num + 1) % 12
                if house_num == 0:
                    house_num = 12
                
                result["houses"][str(house_num)]["planets"].append(planet)
                assigned = True
            
            else:
                # Para otros sistemas, verificar entre cuáles cúspides cae el planeta
                for i in range(len(house_nums)):
                    house_num = house_nums[i]
                    next_house = house_nums[(i + 1) % len(house_nums)]
                    house_cusp = house_cusps[i]
                    next_cusp = house_cusps[(i + 1) % len(house_cusps)]
                    
                    # Verificar si el planeta está en esta casa
                    if next_cusp < house_cusp:  # Casa cruza 0°
                        if longitude >= house_cusp or longitude < next_cusp:
                            result["houses"][str(house_num)]["planets"].append(planet)
                            assigned = True
                            break
                    else:  # Caso normal
                        if house_cusp <= longitude < next_cusp:
                            result["houses"][str(house_num)]["planets"].append(planet)
                            assigned = True
                            break
            
            # Si no se pudo asignar (no debería ocurrir), asignar a la casa 1 por defecto
            if not assigned:
                logger.warning(f"No se pudo asignar {planet} a ninguna casa, asignado a casa 1 por defecto")
                result["houses"]["1"]["planets"].append(planet)
        
        return result
        
    except Exception as e:
        logger.error(f"Error al asignar planetas a casas: {str(e)}")
        # En caso de error, devolver las casas sin modificar
        return houses