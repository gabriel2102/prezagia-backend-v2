"""
Servicio de integración con Claude AI para la aplicación Prezagia.

Este módulo proporciona funciones para interactuar con la API de Claude
y mejorar las interpretaciones astrológicas con inteligencia artificial.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
import anthropic
import requests

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import ExternalServiceError
from app.schemas.astrology import (
    PredictionType, PredictionPeriod,
    CompatibilityType
)


class ClaudeAPIClient:
    """Cliente para interactuar con la API de Claude."""
    
    def __init__(self, api_key: str = None, api_url: str = None):
        """
        Inicializa el cliente de Claude AI.
        
        Args:
            api_key: Clave de API de Claude. Si es None, usa la de configuración.
            api_url: URL base de la API. Si es None, usa la de configuración.
        """
        self.api_key = api_key or settings.CLAUDE_API_KEY
        self.api_url = api_url or settings.CLAUDE_API_URL
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Verificar que tenemos credenciales
        if not self.api_key:
            logger.error("No se ha configurado la clave de API de Claude")
        
        logger.debug("Cliente de Claude AI inicializado")
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000, 
                          temperature: float = 0.7, model: str = "claude-3-opus-20240229") -> str:
        """
        Genera texto con Claude AI a partir de un prompt.
        
        Args:
            prompt: Texto de entrada para Claude
            max_tokens: Número máximo de tokens en la respuesta
            temperature: Temperatura para la generación (0.0 - 1.0)
            model: Modelo de Claude a utilizar
        
        Returns:
            str: Texto generado por Claude
        
        Raises:
            ExternalServiceError: Si ocurre un error al comunicarse con Claude
        """
        try:
            logger.debug(f"Enviando prompt a Claude AI (modelo: {model}, temperatura: {temperature})")
            
            # Llamar a la API de Claude
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system="You are an expert astrologer helping with detailed astrological interpretations. Your responses should be detailed, accurate, and personalized.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraer la respuesta
            response_text = message.content[0].text
            
            logger.debug(f"Respuesta recibida de Claude AI ({len(response_text)} caracteres)")
            return response_text
            
        except anthropic.APIError as e:
            logger.error(f"Error en la API de Claude: {str(e)}")
            raise ExternalServiceError("Claude AI", f"Error en la API: {str(e)}", 
                                     status_code=e.status_code if hasattr(e, 'status_code') else None)
        except Exception as e:
            logger.error(f"Error al generar texto con Claude AI: {str(e)}")
            raise ExternalServiceError("Claude AI", f"Error inesperado: {str(e)}")
    
    async def format_as_json(self, text: str) -> Dict[str, Any]:
        """
        Intenta formatear el texto recibido como JSON.
        
        Args:
            text: Texto que debería contener un JSON
        
        Returns:
            Dict: Objeto JSON parseado
        
        Raises:
            ExternalServiceError: Si no se puede parsear el JSON
        """
        try:
            # Buscar el inicio y fin del JSON en el texto
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                # Si no hay llaves, intentar buscar corchetes para arrays
                start_idx = text.find('[')
                end_idx = text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Si no se encuentra un formato JSON claro, intentar con todo el texto
                return json.loads(text)
                
        except json.JSONDecodeError as e:
            logger.warning(f"No se pudo parsear respuesta de Claude como JSON: {str(e)}")
            
            # Crear un diccionario simple con el texto completo
            return {
                "text": text,
                "error": "No se pudo parsear como JSON estructurado"
            }


# Instancia global del cliente
claude_client = ClaudeAPIClient()


async def generate_prediction_with_claude(transits: Dict[str, Any], 
                                        interpretation: Dict[str, Any],
                                        prediction_type: PredictionType,
                                        prediction_period: PredictionPeriod,
                                        focus_areas: List[str] = None) -> Dict[str, Any]:
    """
    Genera una predicción astrológica mejorada con Claude AI.
    
    Args:
        transits: Datos de tránsitos planetarios
        interpretation: Interpretación básica preliminar
        prediction_type: Tipo de predicción
        prediction_period: Período de la predicción
        focus_areas: Áreas específicas a enfatizar (opcional)
    
    Returns:
        Dict: Predicción mejorada por Claude
    """
    try:
        logger.info(f"Generando predicción con Claude AI (tipo: {prediction_type}, período: {prediction_period})")
        
        # Preparar el prompt para Claude
        natal_data = transits.get("natal_chart", {})
        
        prompt = f"""
        Como astrólogo experto, genera una predicción detallada basada en los siguientes datos:
        
        ## TIPO DE PREDICCIÓN
        {prediction_type.value}
        
        ## PERÍODO
        {prediction_period.value}
        
        ## CARTA NATAL
        - Sol en {natal_data.get("sun_sign", "N/A")}
        - Luna en {natal_data.get("moon_sign", "N/A")}
        - Ascendente en {natal_data.get("rising_sign", "N/A")}
        - Elemento dominante: {natal_data.get("dominant_element", "N/A")}
        - Modalidad dominante: {natal_data.get("dominant_modality", "N/A")}
        
        ## TRÁNSITOS SIGNIFICATIVOS
        """
        
        # Añadir tránsitos significativos al prompt
        significant_transits = transits.get("significant_transits", [])
        for i, transit in enumerate(significant_transits[:10]):  # Limitar a 10 tránsitos para no sobrecargar
            prompt += f"""
            {i+1}. {transit.get('transit_planet', 'N/A').capitalize()} en {transit.get('aspect_type', 'N/A')} 
               con {transit.get('natal_planet', 'N/A').capitalize()} natal
            """
        
        # Añadir áreas de enfoque si existen
        if focus_areas and len(focus_areas) > 0:
            prompt += "\n\n## ÁREAS DE ENFOQUE\n"
            for area in focus_areas:
                prompt += f"- {area}\n"
        
        # Añadir instrucciones específicas
        prompt += f"""
        ## INSTRUCCIONES
        
        Por favor, genera una predicción astrológica estructurada que incluya:
        
        1. Un RESUMEN general conciso de las tendencias para este período.
        2. Una sección de TRÁNSITOS CLAVE detallando los más importantes y su impacto.
        3. Recomendaciones específicas para aprovechar las energías favorables.
        4. Advertencias sobre posibles desafíos y cómo manejarlos.
        
        Devuelve la información en formato JSON con los siguientes campos:
        - summary: resumen general
        - key_transits: array de tránsitos clave y sus efectos
        - opportunities: oportunidades a aprovechar
        - challenges: posibles desafíos
        - recommendations: consejos prácticos
        """
        
        if focus_areas and len(focus_areas) > 0:
            prompt += """
            - focus_areas: un objeto con interpretaciones específicas para cada área de enfoque solicitada
            """
        
        prompt += """
        Asegúrate de que la predicción sea detallada pero práctica, evitando generalidades vagas.
        """
        
        # Enviar el prompt a Claude y obtener respuesta
        response_text = await claude_client.generate_text(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
            model="claude-3-opus-20240229"
        )
        
        # Intentar formatear la respuesta como JSON
        prediction_data = await claude_client.format_as_json(response_text)
        
        # Verificar que tenemos las claves necesarias
        required_keys = ["summary", "key_transits", "opportunities", "challenges", "recommendations"]
        missing_keys = [key for key in required_keys if key not in prediction_data]
        
        if missing_keys:
            logger.warning(f"Faltan claves en la respuesta de Claude: {', '.join(missing_keys)}")
            # Añadir claves faltantes con valores por defecto
            for key in missing_keys:
                prediction_data[key] = "Información no disponible" if key == "summary" else []
        
        # Añadir interpretaciones de áreas de enfoque si fueron solicitadas
        if focus_areas and len(focus_areas) > 0 and "focus_areas" not in prediction_data:
            prediction_data["focus_areas"] = {}
            for area in focus_areas:
                prediction_data["focus_areas"][area] = f"Interpretación para {area} no disponible"
        
        logger.info("Predicción generada exitosamente con Claude AI")
        return prediction_data
        
    except ExternalServiceError:
        # Reenviar errores específicos de Claude
        raise
    except Exception as e:
        logger.error(f"Error al generar predicción con Claude: {str(e)}")
        
        # Devolver una respuesta de respaldo basada en la interpretación original
        backup_response = {
            "summary": interpretation.get("summary", "No hay resumen disponible"),
            "key_transits": [],
            "opportunities": [],
            "challenges": [],
            "recommendations": ["Consulta con un astrólogo profesional para una interpretación más detallada."],
            "error": f"No se pudo generar la predicción con IA: {str(e)}"
        }
        
        if focus_areas and len(focus_areas) > 0:
            backup_response["focus_areas"] = {}
            for area in focus_areas:
                backup_response["focus_areas"][area] = interpretation.get("focus_areas", {}).get(area, f"Información sobre {area} no disponible")
        
        return backup_response


async def enhance_compatibility_with_claude(compatibility_calculation: Dict[str, Any], 
                                          interpretation: Dict[str, Any],
                                          compatibility_type: CompatibilityType,
                                          focus_areas: List[str] = None,
                                          person1_name: str = "Persona 1", 
                                          person2_name: str = "Persona 2") -> Dict[str, Any]:
    """
    Mejora un análisis de compatibilidad con Claude AI.
    
    Args:
        compatibility_calculation: Datos del cálculo de compatibilidad
        interpretation: Interpretación básica preliminar
        compatibility_type: Tipo de compatibilidad
        focus_areas: Áreas específicas a enfatizar (opcional)
        person1_name: Nombre de la primera persona
        person2_name: Nombre de la segunda persona
    
    Returns:
        Dict: Análisis de compatibilidad mejorado por Claude
    """
    try:
        logger.info(f"Generando análisis de compatibilidad con Claude AI (tipo: {compatibility_type})")
        
        # Preparar el prompt para Claude
        chart1 = compatibility_calculation.get("chart1", {})
        chart2 = compatibility_calculation.get("chart2", {})
        
        prompt = f"""
        Como astrólogo experto, genera un análisis de compatibilidad detallado entre {person1_name} y {person2_name} basado en los siguientes datos:
        
        ## TIPO DE COMPATIBILIDAD
        {compatibility_type.value}
        
        ## PERFIL DE {person1_name}
        - Sol en {chart1.get("sun_sign", "N/A")}
        - Luna en {chart1.get("moon_sign", "N/A")}
        - Ascendente en {chart1.get("rising_sign", "N/A")}
        - Elemento dominante: {chart1.get("dominant_element", "N/A")}
        - Modalidad dominante: {chart1.get("dominant_modality", "N/A")}
        
        ## PERFIL DE {person2_name}
        - Sol en {chart2.get("sun_sign", "N/A")}
        - Luna en {chart2.get("moon_sign", "N/A")}
        - Ascendente en {chart2.get("rising_sign", "N/A")}
        - Elemento dominante: {chart2.get("dominant_element", "N/A")}
        - Modalidad dominante: {chart2.get("dominant_modality", "N/A")}
        
        ## ASPECTOS IMPORTANTES ENTRE LAS CARTAS
        """
        
        # Añadir aspectos importantes al prompt
        synastry_aspects = compatibility_calculation.get("synastry_aspects", [])
        for i, aspect in enumerate(synastry_aspects[:10]):  # Limitar a 10 aspectos para no sobrecargar
            prompt += f"""
            {i+1}. {aspect.get('planet1', 'N/A').capitalize()} de {person1_name} en {aspect.get('aspect_type', 'N/A')} 
               con {aspect.get('planet2', 'N/A').capitalize()} de {person2_name}
            """
        
        # Añadir puntuación de compatibilidad
        score = compatibility_calculation.get("compatibility_score", 50)
        prompt += f"\n\n## PUNTUACIÓN DE COMPATIBILIDAD\n{score}/100\n"
        
        # Añadir fortalezas y desafíos
        strengths = compatibility_calculation.get("strengths", [])
        if strengths:
            prompt += "\n## FORTALEZAS DE LA RELACIÓN\n"
            for strength in strengths[:5]:  # Limitar a 5 fortalezas
                prompt += f"- {strength}\n"
        
        challenges = compatibility_calculation.get("challenges", [])
        if challenges:
            prompt += "\n## DESAFÍOS DE LA RELACIÓN\n"
            for challenge in challenges[:5]:  # Limitar a 5 desafíos
                prompt += f"- {challenge}\n"
        
        # Añadir áreas de enfoque si existen
        if focus_areas and len(focus_areas) > 0:
            prompt += "\n\n## ÁREAS DE ENFOQUE\n"
            for area in focus_areas:
                prompt += f"- {area}\n"
        
        # Añadir instrucciones específicas
        prompt += f"""
        ## INSTRUCCIONES
        
        Por favor, genera un análisis de compatibilidad estructurado que incluya:
        
        1. Un RESUMEN general conciso de la dinámica entre {person1_name} y {person2_name}.
        2. Una sección de PUNTOS FUERTES detallando los aspectos positivos de la relación.
        3. Una sección de DESAFÍOS detallando posibles áreas de fricción.
        4. Recomendaciones específicas para mejorar la relación.
        
        Devuelve la información en formato JSON con los siguientes campos:
        - summary: resumen general
        - strengths: array de puntos fuertes
        - challenges: array de desafíos
        - dynamics: dinámica general de la relación
        - recommendations: consejos prácticos
        """
        
        if focus_areas and len(focus_areas) > 0:
            prompt += """
            - focus_areas: un objeto con interpretaciones específicas para cada área de enfoque solicitada
            """
        
        prompt += f"""
        Asegúrate de que el análisis sea detallado, equilibrado y específico para un tipo de relación {compatibility_type.value}.
        """
        
        # Enviar el prompt a Claude y obtener respuesta
        response_text = await claude_client.generate_text(
            prompt=prompt,
            max_tokens=2500,
            temperature=0.7,
            model="claude-3-opus-20240229"
        )
        
        # Intentar formatear la respuesta como JSON
        compatibility_data = await claude_client.format_as_json(response_text)
        
        # Verificar que tenemos las claves necesarias
        required_keys = ["summary", "strengths", "challenges", "dynamics", "recommendations"]
        missing_keys = [key for key in required_keys if key not in compatibility_data]
        
        if missing_keys:
            logger.warning(f"Faltan claves en la respuesta de Claude: {', '.join(missing_keys)}")
            # Añadir claves faltantes con valores por defecto
            for key in missing_keys:
                compatibility_data[key] = "Información no disponible" if key == "summary" or key == "dynamics" else []
        
        # Añadir interpretaciones de áreas de enfoque si fueron solicitadas
        if focus_areas and len(focus_areas) > 0 and "focus_areas" not in compatibility_data:
            compatibility_data["focus_areas"] = {}
            for area in focus_areas:
                compatibility_data["focus_areas"][area] = f"Interpretación para {area} no disponible"
        
        logger.info("Análisis de compatibilidad generado exitosamente con Claude AI")
        return compatibility_data
        
    except ExternalServiceError:
        # Reenviar errores específicos de Claude
        raise
    except Exception as e:
        logger.error(f"Error al generar análisis de compatibilidad con Claude: {str(e)}")
        
        # Devolver una respuesta de respaldo basada en la interpretación original
        backup_response = {
            "summary": interpretation.get("summary", "No hay resumen disponible"),
            "strengths": interpretation.get("strengths", []),
            "challenges": interpretation.get("challenges", []),
            "dynamics": f"Información sobre la dinámica entre {person1_name} y {person2_name} no disponible",
            "recommendations": ["Consulta con un astrólogo profesional para una interpretación más detallada."],
            "error": f"No se pudo generar el análisis con IA: {str(e)}"
        }
        
        if focus_areas and len(focus_areas) > 0:
            backup_response["focus_areas"] = {}
            for area in focus_areas:
                backup_response["focus_areas"][area] = interpretation.get("focus_areas", {}).get(area, f"Información sobre {area} no disponible")
        
        return backup_response


async def enhance_chart_interpretation(chart_calculation: Dict[str, Any],
                                     interpretation: Dict[str, Any],
                                     chart_type: str,
                                     personality_keywords: List[str] = None) -> Dict[str, Any]:
    """
    Mejora la interpretación de una carta astral con Claude AI.
    
    Args:
        chart_calculation: Datos del cálculo de la carta
        interpretation: Interpretación básica preliminar
        chart_type: Tipo de carta (natal, tránsito, etc.)
        personality_keywords: Palabras clave de personalidad para enfocar la interpretación
    
    Returns:
        Dict: Interpretación mejorada por Claude
    """
    try:
        logger.info(f"Mejorando interpretación de carta {chart_type} con Claude AI")
        
        # Preparar el prompt para Claude
        prompt = f"""
        Como astrólogo experto, genera una interpretación detallada de una carta astral {chart_type} basada en los siguientes datos:
        
        ## DATOS BÁSICOS
        - Sol en {chart_calculation.get("sun_sign", "N/A")}
        - Luna en {chart_calculation.get("moon_sign", "N/A")}
        - Ascendente en {chart_calculation.get("rising_sign", "N/A")}
        - Elemento dominante: {chart_calculation.get("dominant_element", "N/A")}
        - Modalidad dominante: {chart_calculation.get("dominant_modality", "N/A")}
        
        ## PLANETAS EN SIGNOS
        """
        
        # Añadir posiciones planetarias
        planets = chart_calculation.get("planets", {})
        for planet, data in planets.items():
            prompt += f"- {planet.capitalize()} en {data.get('sign', 'N/A')}"
            if data.get("retrograde", False):
                prompt += " (Retrógrado)"
            prompt += "\n"
        
        # Añadir aspectos importantes
        prompt += "\n## ASPECTOS IMPORTANTES\n"
        aspects = chart_calculation.get("aspects", [])
        for i, aspect in enumerate(aspects[:10]):  # Limitar a 10 aspectos
            prompt += f"- {aspect.get('planet1', 'N/A').capitalize()} en {aspect.get('aspect_type', 'N/A')} con {aspect.get('planet2', 'N/A').capitalize()}\n"
        
        # Añadir palabras clave de personalidad si existen
        if personality_keywords and len(personality_keywords) > 0:
            prompt += "\n## ENFOQUE DE PERSONALIDAD\n"
            for keyword in personality_keywords:
                prompt += f"- {keyword}\n"
        
        # Añadir instrucciones específicas
        prompt += """
        ## INSTRUCCIONES
        
        Por favor, genera una interpretación astrológica estructurada que incluya:
        
        1. Un PERFIL GENERAL que capte la esencia de la carta.
        2. Una sección de FORTALEZAS detallando los puntos fuertes según la carta.
        3. Una sección de DESAFÍOS detallando áreas de crecimiento.
        4. Una sección sobre PROPÓSITO DE VIDA y dirección sugerida.
        5. Recomendaciones prácticas basadas en la configuración astrológica.
        
        Devuelve la información en formato JSON con los siguientes campos:
        - profile: perfil general
        - strengths: array de fortalezas
        - challenges: array de desafíos
        - life_purpose: propósito de vida
        - planet_interpretations: objeto con interpretaciones individuales de los planetas principales
        - recommendations: consejos prácticos
        
        Asegúrate de que la interpretación sea detallada, práctica y específica para esta configuración astrológica.
        """
        
        # Enviar el prompt a Claude y obtener respuesta
        response_text = await claude_client.generate_text(
            prompt=prompt,
            max_tokens=3000,
            temperature=0.7,
            model="claude-3-opus-20240229"
        )
        
        # Intentar formatear la respuesta como JSON
        enhanced_interpretation = await claude_client.format_as_json(response_text)
        
        # Verificar que tenemos las claves necesarias
        required_keys = ["profile", "strengths", "challenges", "life_purpose", "planet_interpretations", "recommendations"]
        missing_keys = [key for key in required_keys if key not in enhanced_interpretation]
        
        if missing_keys:
            logger.warning(f"Faltan claves en la respuesta de Claude: {', '.join(missing_keys)}")
            # Añadir claves faltantes con valores por defecto
            for key in missing_keys:
                if key in ["profile", "life_purpose"]:
                    enhanced_interpretation[key] = "Información no disponible"
                elif key == "planet_interpretations":
                    enhanced_interpretation[key] = {}
                else:
                    enhanced_interpretation[key] = []
        
        # Fusionar con la interpretación original
        merged_interpretation = interpretation.copy()
        
        # Actualizar con la interpretación mejorada
        for key, value in enhanced_interpretation.items():
            merged_interpretation[key] = value
        
        logger.info("Interpretación de carta mejorada exitosamente con Claude AI")
        return merged_interpretation
        
    except ExternalServiceError:
        # Reenviar errores específicos de Claude
        raise
    except Exception as e:
        logger.error(f"Error al mejorar interpretación con Claude: {str(e)}")
        # Devolver la interpretación original sin cambios
        return interpretation