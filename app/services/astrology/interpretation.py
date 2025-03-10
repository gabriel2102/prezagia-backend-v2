"""
Servicios de interpretación astrológica para la aplicación Prezagia.

Este módulo procesa los cálculos astronómicos para proporcionar interpretaciones
astrológicas significativas. Se encarga de traducir los datos técnicos a narrativas
comprensibles para el usuario.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date

from app.core.logger import logger
from app.core.exceptions import InterpretationError
from app.schemas.astrology import ChartType, PredictionType, PredictionPeriod, CompatibilityType


# Diccionario de interpretaciones planetarias por signo
PLANET_SIGN_INTERPRETATIONS = {
    "sun": {
        "Aries": "Tu esencia y fuerza vital se expresan a través de la acción, iniciativa y liderazgo. "
                "Tiendes a ser valiente, directa/o y entusiasta, con un fuerte deseo de nuevos desafíos.",
        "Tauro": "Tu esencia se manifiesta a través de la estabilidad, persistencia y sensualidad. "
                "Valoras la seguridad material y emocional, con un fuerte sentido práctico y artístico.",
        "Géminis": "Tu esencia se expresa a través de la comunicación, curiosidad y versatilidad. "
                 "Eres intelectualmente ágil, social y siempre buscas aprender cosas nuevas.",
        "Cáncer": "Tu esencia se manifiesta a través de la nutrición emocional, protección y empatía. "
                "Eres sensible a los estados de ánimo, con fuerte conexión familiar y gran memoria emocional.",
        "Leo": "Tu esencia brilla a través de la creatividad, dramatismo y liderazgo carismático. "
             "Tienes un fuerte sentido de dignidad personal y buscas reconocimiento por tus contribuciones.",
        "Virgo": "Tu esencia se expresa a través del análisis, perfeccionismo y servicio práctico. "
               "Eres detallista, con gran capacidad para mejorar sistemas y resolver problemas.",
        "Libra": "Tu esencia se manifiesta a través del equilibrio, diplomacia y apreciación estética. "
               "Buscas armonía en las relaciones y tienes un fino sentido de la justicia.",
        "Escorpio": "Tu esencia se expresa a través de la intensidad emocional, resiliencia y transformación. "
                  "Posees una voluntad poderosa, con capacidad para ver más allá de las apariencias.",
        "Sagitario": "Tu esencia brilla a través de la expansión mental, exploración y optimismo. "
                   "Buscas significado filosófico y libertad para aventurarte más allá de fronteras.",
        "Capricornio": "Tu esencia se manifiesta a través de la ambición, disciplina y responsabilidad. "
                     "Eres perseverante, con objetivos a largo plazo y sentido del deber.",
        "Acuario": "Tu esencia se expresa a través de la originalidad, visión de futuro e independencia. "
                 "Tienes una perspectiva única y un interés natural por el bienestar colectivo.",
        "Piscis": "Tu esencia fluye a través de la compasión, intuición y sensibilidad artística. "
                "Posees una rica vida interior y una conexión con dimensiones sutiles de la realidad."
    },
    "moon": {
        "Aries": "Tus emociones son espontáneas, directas y necesitas libertad para expresarlas. "
                "Reaccionas rápidamente ante situaciones y puedes ser impaciente con tus necesidades.",
        "Tauro": "Tus emociones son estables, sensuales y arraigadas en lo concreto. "
                "Necesitas seguridad y comodidad para sentirte emocionalmente satisfecha/o.",
        "Géminis": "Tus emociones se expresan a través del intelecto y la comunicación. "
                 "Necesitas estímulo mental y variedad para sentirte emocionalmente nutrida/o.",
        "Cáncer": "Tus emociones son profundas, fluctuantes y protectoras. "
                "Necesitas conexiones familiares y un hogar seguro para expresar tu mundo interior.",
        "Leo": "Tus emociones son cálidas, expresivas y buscan reconocimiento. "
             "Necesitas aprecio sincero y oportunidades para compartir tu afecto generosamente.",
        "Virgo": "Tus emociones se procesan a través del análisis y el orden. "
               "Necesitas sentirte útil y mantener claridad en tu entorno para estar en equilibrio.",
        "Libra": "Tus emociones buscan armonía y equilibrio en las relaciones. "
               "Necesitas belleza, diplomacia y cooperación para sentirte emocionalmente segura/o.",
        "Escorpio": "Tus emociones son intensas, profundas y transformadoras. "
                  "Necesitas intimidad auténtica y experiencias que te permitan regenerarte.",
        "Sagitario": "Tus emociones se expresan con entusiasmo, honestidad y optimismo. "
                   "Necesitas espacio para crecer y aventuras que alimenten tu espíritu.",
        "Capricornio": "Tus emociones se expresan con reserva, autocontrol y madurez. "
                     "Necesitas estructura y logros concretos para sentirte emocionalmente satisfecha/o.",
        "Acuario": "Tus emociones se procesan a través del intelecto y valores humanitarios. "
                 "Necesitas independencia y originalidad para sentir bienestar emocional.",
        "Piscis": "Tus emociones son fluidas, compasivas e intuitivas. "
                "Necesitas conexión espiritual y expresión creativa para tu bienestar emocional."
    },
    "mercury": {
        "Aries": "Tu mente funciona de manera rápida, directa e intuitiva. "
                "Comunicas con franqueza y prefieres ir directamente al punto.",
        "Tauro": "Tu mente funciona de manera metódica, práctica y orientada a resultados concretos. "
                "Comunicas con calma y valoras las ideas probadas por el tiempo.",
        "Géminis": "Tu mente es curiosa, ágil y adaptable, procesando información de forma versátil. "
                 "Comunicas con elocuencia y disfrutas de la variedad intelectual.",
        "Cáncer": "Tu mente funciona a través de filtros emocionales e intuitivos. "
                "Comunicas con sensibilidad y tu memoria emocional influye en tu pensamiento.",
        "Leo": "Tu mente opera con creatividad, dramatismo y seguridad. "
             "Comunicas con calidez y autoridad natural, sabiendo captar la atención.",
        "Virgo": "Tu mente es analítica, precisa y orientada al detalle. "
               "Comunicas con claridad y tiendes a ser crítica/o y perfeccionista con las ideas.",
        "Libra": "Tu mente busca el equilibrio, comparando diferentes perspectivas. "
               "Comunicas con diplomacia y tienes talento para ver todos los lados de un tema.",
        "Escorpio": "Tu mente opera con profundidad, intensidad y agudeza penetrante. "
                  "Comunicas con impacto y puedes descubrir lo que otros intentan ocultar.",
        "Sagitario": "Tu mente es expansiva, optimista y orientada a las posibilidades. "
                   "Comunicas con entusiasmo y buscas la verdad y el significado más amplio.",
        "Capricornio": "Tu mente funciona de manera estructurada, práctica y disciplinada. "
                     "Comunicas con autoridad y prefieres ideas que tengan aplicación concreta.",
        "Acuario": "Tu mente es original, innovadora y no convencional. "
                 "Comunicas con objetividad intelectual y piensas de forma orientada al futuro.",
        "Piscis": "Tu mente funciona intuitivamente, captando sutilezas y conexiones invisibles. "
                "Comunicas con empatía y tu pensamiento tiende a ser más visual que lineal."
    },
    "venus": {
        "Aries": "Amas con pasión, espontaneidad y un toque de competitividad. "
                "Aprecias la acción directa y buscas relaciones estimulantes.",
        "Tauro": "Amas con sensualidad, constancia y profunda lealtad. "
                "Aprecias los placeres simples y la seguridad en las relaciones.",
        "Géminis": "Amas con curiosidad intelectual y versatilidad. "
                 "Aprecias la comunicación y necesitas variedad en relaciones y gustos.",
        "Cáncer": "Amas con ternura, protección y profunda conexión emocional. "
                "Aprecias la nutrición emocional y los vínculos que evocan seguridad.",
        "Leo": "Amas con generosidad, dramatismo y lealtad apasionada. "
             "Aprecias los gestos románticos y buscas admiración en tus relaciones.",
        "Virgo": "Amas con atención a los detalles y un deseo de ayudar y mejorar. "
               "Aprecias la pulcritud y expresas afecto a través del servicio práctico.",
        "Libra": "Amas con diplomacia, equilibrio y un fino sentido estético. "
               "Aprecias la armonía y buscas relaciones con equidad y belleza.",
        "Escorpio": "Amas con intensidad emocional, profundidad y exclusividad. "
                  "Aprecias la autenticidad y buscas conexiones transformadoras.",
        "Sagitario": "Amas con entusiasmo, optimismo y espíritu libre. "
                   "Aprecias la sinceridad y buscas relaciones que expandan tus horizontes.",
        "Capricornio": "Amas con seriedad, compromiso y sentido de responsabilidad. "
                     "Aprecias la lealtad a largo plazo y maduras en tus relaciones con el tiempo.",
        "Acuario": "Amas con originalidad, independencia y una visión no convencional. "
                 "Aprecias la amistad como base del amor y necesitas libertad personal.",
        "Piscis": "Amas con compasión, romance idealista y entrega desinteresada. "
                "Aprecias la conexión espiritual y puedes sacrificarte por quienes amas."
    },
    "mars": {
        "Aries": "Actúas con iniciativa, coraje y energía directa. "
                "Tu impulso es espontáneo y buscas conquistar nuevos terrenos.",
        "Tauro": "Actúas con determinación, paciencia y persistencia inquebrantable. "
                "Tu impulso es sostenido y trabajas con constancia hacia metas concretas.",
        "Géminis": "Actúas con versatilidad, rapidez mental y habilidad comunicativa. "
                 "Tu impulso se diversifica en múltiples intereses y proyectos.",
        "Cáncer": "Actúas con sensibilidad, protección y tenacidad emocional. "
                "Tu impulso fluctúa con tus estados de ánimo y defiendes lo que te importa.",
        "Leo": "Actúas con dramatismo, confianza y fuerza creativa. "
             "Tu impulso busca reconocimiento y expresas tu voluntad con autoridad.",
        "Virgo": "Actúas con precisión, método y atención al detalle. "
               "Tu impulso se canaliza en el trabajo eficiente y la mejora continua.",
        "Libra": "Actúas con diplomacia, sentido de justicia y consideración. "
               "Tu impulso busca equilibrio y puedes dudar antes de actuar unilateralmente.",
        "Escorpio": "Actúas con intensidad, estrategia y fuerza de voluntad implacable. "
                  "Tu impulso es contenido pero poderoso, operando bajo la superficie.",
        "Sagitario": "Actúas con entusiasmo, visión de futuro y búsqueda de aventura. "
                   "Tu impulso es expansivo y orientado hacia nuevos horizontes.",
        "Capricornio": "Actúas con disciplina, ambición y planificación cuidadosa. "
                     "Tu impulso es controlado y orientado hacia logros a largo plazo.",
        "Acuario": "Actúas con originalidad, independencia y enfoque humanitario. "
                 "Tu impulso puede ser impredecible y orientado hacia el cambio social.",
        "Piscis": "Actúas con intuición, compasión y receptividad a las corrientes sutiles. "
                "Tu impulso fluye de forma no lineal y puedes sacrificarte por ideales."
    }
    # Se pueden añadir interpretaciones para los demás planetas
}

# Interpretaciones de aspectos
ASPECT_INTERPRETATIONS = {
    "sun-moon": {
        "conjunción": "Existe una fuerte integración entre tu voluntad consciente y tus necesidades emocionales. "
                    "Tu personalidad y temperamento trabajan en armonía, aportándote claridad interior.",
        "trígono": "Tu expresión consciente y tus necesidades emocionales fluyen en armonía. "
                 "Te resulta natural equilibrar razón y emoción, dándote estabilidad interna.",
        "sextil": "Hay una oportunidad positiva para integrar tu voluntad y emociones. "
                "Con un poco de esfuerzo, puedes lograr que tu dirección vital y necesidades emocionales se complementen.",
        "cuadratura": "Puede existir tensión entre lo que quieres lograr y lo que necesitas emocionalmente. "
                    "Este desafío te impulsa a desarrollar mayor autoconciencia y flexibilidad interior.",
        "oposición": "Experimentas una polarización entre tu voluntad consciente y tus respuestas emocionales. "
                   "El desafío es integrar estos opuestos para lograr una personalidad más completa."
    },
    "sun-ascendant": {
        "conjunción": "Tu personalidad esencial se expresa naturalmente a través de tu apariencia y comportamiento. "
                    "Hay una fuerte coherencia entre quién eres y cómo te proyectas.",
        "trígono": "Existe un flujo armónico entre tu identidad interna y la forma en que te presentas al mundo. "
                 "Tu auténtica personalidad se refleja fácilmente en tu apariencia y comportamiento.",
        "sextil": "Hay buena comunicación entre tu esencia y tu expresión externa. "
                "Con poco esfuerzo, puedes alinear tu comportamiento con tu verdadero ser.",
        "cuadratura": "Puede haber una disonancia entre quién eres realmente y cómo te presentas. "
                    "Este aspecto te desafía a integrar tu personalidad interna con tu imagen externa.",
        "oposición": "Experimentas una división entre tu identidad esencial y tu comportamiento externo. "
                   "El desafío es reconciliar quién eres con cómo te muestras a los demás."
    },
    "venus-mars": {
        "conjunción": "Existe una fuerte integración entre tus principios femeninos y masculinos. "
                    "La forma en que amas y la forma en que actúas están alineadas, creando pasión y expresión armónica.",
        "trígono": "Hay un flujo armónico entre tus deseos y tus acciones. "
                 "Te resulta natural expresar afecto y asertividad de manera complementaria y fluida.",
        "sextil": "Existe una oportunidad favorable para integrar amor y deseo. "
                "Con poco esfuerzo, puedes alinear cómo atraes y cómo persigues lo que deseas.",
        "cuadratura": "Puede haber tensión entre la forma en que amas y la manera en que actúas. "
                    "Este aspecto desafía a reconciliar tus necesidades de armonía con tus impulsos de acción directa.",
        "oposición": "Experimentas una polaridad entre tus cualidades receptivas y activas. "
                   "El desafío es balancear la forma en que atraes con la manera en que persigues lo que deseas."
    },
    "mercury-jupiter": {
        "conjunción": "Tu mente y tu visión expansiva trabajan juntas en armonía. "
                    "Puedes comunicar grandes ideas de manera accesible y tienes una perspectiva optimista.",
        "trígono": "Hay un flujo benéfico entre tu intelecto y tu visión más amplia. "
                 "Comunicas con optimismo y puedes ver tanto los detalles como el panorama general.",
        "sextil": "Existe una oportunidad favorable para conectar pensamiento y expansión. "
                "Puedes desarrollar la capacidad de traducir grandes conceptos en ideas prácticas.",
        "cuadratura": "Puede haber tensión entre el enfoque en detalles y la visión general. "
                    "Este aspecto desafía a equilibrar precisión con expansión y optimismo.",
        "oposición": "Experimentas una polaridad entre pensamiento analítico y visión sintética. "
                   "El desafío es integrar la atención al detalle con la comprensión de patrones más amplios."
    }
    # Más combinaciones de aspectos se pueden añadir aquí
}

# Interpretaciones de casas
HOUSE_INTERPRETATIONS = {
    "1": "La primera casa representa tu identidad, apariencia física y cómo te proyectas al mundo. "
        "Es la ventana a través de la cual experimentas la realidad y cómo otros te perciben inicialmente.",
    "2": "La segunda casa gobierna tus recursos, valores personales y autoestima. "
        "Relacionada con el dinero, posesiones materiales y talentos que te aportan seguridad.",
    "3": "La tercera casa rige la comunicación cotidiana, el aprendizaje temprano y tu entorno inmediato. "
        "Representa a hermanos, vecinos, y cómo procesas y compartes información.",
    "4": "La cuarta casa simboliza tu hogar, raíces familiares y base emocional. "
        "Representa tus orígenes, tu conexión con el pasado y tu sentido de pertenencia.",
    "5": "La quinta casa gobierna la autoexpresión creativa, romance, hijos y placer. "
        "Es donde buscas alegría, juego y donde brilla tu luz interior más auténtica.",
    "6": "La sexta casa representa el trabajo diario, salud, servicio y rutinas. "
        "Abarca cómo organizas tu vida cotidiana y cómo cuidas tu bienestar físico.",
    "7": "La séptima casa simboliza las relaciones cercanas, asociaciones y matrimonio. "
        "Representa cómo te relacionas con los demás en compromisos uno a uno.",
    "8": "La octava casa gobierna las transformaciones profundas, sexualidad, recursos compartidos y lo oculto. "
        "Donde experimentas pérdidas, ganancias y regeneración.",
    "9": "La novena casa rige la expansión mental, viajes, educación superior y filosofía. "
        "Representa tu búsqueda de significado, creencias y horizontes más amplios.",
    "10": "La décima casa simboliza tu carrera, reputación, ambiciones y figura de autoridad. "
         "Representa tu lugar en la sociedad y tus contribuciones públicas.",
    "11": "La undécima casa gobierna amistades, grupos, objetivos colectivos y esperanzas. "
         "Representa tu conexión con la comunidad y causas más grandes que tú.",
    "12": "La duodécima casa simboliza el subconsciente, espiritualidad, servicio desinteresado y limitaciones. "
         "Es donde te conectas con lo universal y procesas experiencias ocultas."
}

# Signos del zodíaco
ZODIAC_SIGNS = [
    "Aries", "Tauro", "Géminis", "Cáncer", 
    "Leo", "Virgo", "Libra", "Escorpio", 
    "Sagitario", "Capricornio", "Acuario", "Piscis"
]


async def interpret_chart(chart_calculation: Dict[str, Any], chart_type: ChartType, 
                        interpretation_depth: int = 3) -> Dict[str, Any]:
    """
    Interpreta una carta astral basándose en los cálculos astronómicos.
    
    Args:
        chart_calculation: Resultados de los cálculos de la carta astral
        chart_type: Tipo de carta astral
        interpretation_depth: Nivel de profundidad de la interpretación (1-5)
    
    Returns:
        Dict: Interpretación completa de la carta astral
    """
    try:
        logger.info(f"Interpretando carta {chart_type} con profundidad {interpretation_depth}")
        
        # Inicializar el resultado
        interpretation = {
            "summary": "",
            "planets": {},
            "houses": {},
            "aspects": {},
            "dominant_element": {
                "element": chart_calculation["dominant_element"],
                "description": interpret_element(chart_calculation["dominant_element"])
            },
            "dominant_modality": {
                "modality": chart_calculation["dominant_modality"],
                "description": interpret_modality(chart_calculation["dominant_modality"])
            }
        }
        
        # Interpretar planetas en signos
        for planet, data in chart_calculation["planets"].items():
            interpretation["planets"][planet] = {
                "sign": data["sign"],
                "position": data["degree"],
                "house": data.get("house", None),
                "retrograde": data.get("retrograde", False),
                "interpretation": interpret_planet_in_sign(planet, data["sign"], interpretation_depth)
            }
            
            # Si sabemos la casa, añadir interpretación de planeta en casa
            if "house" in data:
                house_interpretation = interpret_planet_in_house(planet, data["house"], interpretation_depth)
                interpretation["planets"][planet]["house_interpretation"] = house_interpretation
        
        # Interpretar casas
        for house_num, house_data in chart_calculation["houses"]["houses"].items():
            planets_in_house = house_data.get("planets", [])
            sign = house_data["sign"]
            
            interpretation["houses"][house_num] = {
                "sign": sign,
                "planets": planets_in_house,
                "cusp": house_data["degree"],
                "interpretation": interpret_house(house_num, sign, planets_in_house, interpretation_depth)
            }
        
        # Interpretar aspectos importantes
        important_aspects = []
        for aspect in chart_calculation["aspects"]:
            # Filtrar aspectos por importancia según profundidad solicitada
            if (interpretation_depth >= 4) or (aspect["power"] > 7) or (aspect["planet1"] in ["sun", "moon", "ascendant"]) or (aspect["planet2"] in ["sun", "moon", "ascendant"]):
                aspect_interp = interpret_aspect(aspect, interpretation_depth)
                if aspect_interp:
                    important_aspects.append({
                        "aspect_type": aspect["aspect_type"],
                        "planet1": aspect["planet1"],
                        "planet2": aspect["planet2"],
                        "orb": aspect["orb"],
                        "power": aspect["power"],
                        "interpretation": aspect_interp
                    })
        
        interpretation["aspects"] = important_aspects
        
        # Generar resumen general
        interpretation["summary"] = generate_chart_summary(chart_calculation, chart_type, interpretation_depth)
        
        logger.info(f"Interpretación de carta completada con {len(important_aspects)} aspectos analizados")
        return interpretation
        
    except Exception as e:
        logger.error(f"Error al interpretar carta astral: {str(e)}")
        raise InterpretationError(message=f"Error al interpretar carta astral: {str(e)}", 
                                 interpretation_type=str(chart_type))


def interpret_planet_in_sign(planet: str, sign: str, depth: int = 3) -> str:
    """
    Interpreta un planeta en un signo específico.
    
    Args:
        planet: Nombre del planeta
        sign: Signo zodiacal
        depth: Nivel de profundidad de la interpretación
    
    Returns:
        str: Interpretación del planeta en el signo
    """
    # Obtener interpretación básica del diccionario
    basic_interp = PLANET_SIGN_INTERPRETATIONS.get(planet, {}).get(sign, "")
    
    if not basic_interp:
        # Si no hay interpretación específica, generar una genérica
        return f"La energía de {planet.capitalize()} se expresa a través de las cualidades de {sign}."
    
    # Para profundidades bajas, devolver solo la interpretación básica
    if depth <= 2:
        return basic_interp
    
    # Para profundidades mayores, añadir detalles adicionales
    if depth >= 3:
        # Aquí se podrían añadir más detalles según la dignidad, posición, etc.
        # Por simplicidad, solo usamos la interpretación básica en este ejemplo
        pass
    
    return basic_interp


def interpret_planet_in_house(planet: str, house: int, depth: int = 3) -> str:
    """
    Interpreta un planeta en una casa específica.
    
    Args:
        planet: Nombre del planeta
        house: Número de casa (1-12)
        depth: Nivel de profundidad de la interpretación
    
    Returns:
        str: Interpretación del planeta en la casa
    """
    # Interpretaciones básicas de planetas en casas
    interpretations = {
        "sun": {
            1: "Tu identidad y vitalidad se expresan fuertemente en tu personalidad y apariencia. "
               "Tiendes a brillar por ti mismo y muestras confianza en tu propia presencia.",
            2: "Tu identidad está ligada a tus recursos y valores personales. "
               "Brillas a través de tus talentos y capacidad para generar seguridad material.",
            3: "Tu identidad se expresa a través de la comunicación y el intelecto. "
               "Brillas compartiendo ideas y en entornos de aprendizaje cotidiano.",
            4: "Tu identidad está enraizada en tu hogar y conexiones familiares. "
               "Brillas en el ámbito privado y tu vida interior es fundamental para tu expresión.",
            5: "Tu identidad se expresa a través de la creatividad y autoexpresión. "
               "Brillas en actividades artísticas, románticas y donde puedas mostrar tu autenticidad.",
            6: "Tu identidad se enfoca en el servicio, trabajo y bienestar. "
               "Brillas cuando puedes ser útil, organizado y contribuir con eficiencia.",
            7: "Tu identidad se realiza a través de relaciones y asociaciones. "
               "Brillas en colaboración y encuentras tu propósito a través de los demás.",
            8: "Tu identidad se expresa a través de transformaciones y profundidad emocional. "
               "Brillas manejando recursos compartidos y experiencias intensas.",
            9: "Tu identidad se manifiesta a través de la expansión mental y espiritual. "
               "Brillas explorando nuevos horizontes filosóficos y culturales.",
            10: "Tu identidad está ligada a tu carrera y ambiciones sociales. "
                "Brillas en roles de autoridad y a través de tus logros públicos.",
            11: "Tu identidad se expresa a través de tu participación en grupos y amistades. "
                "Brillas cuando trabajas por causas colectivas e ideales humanitarios.",
            12: "Tu identidad tiene una dimensión espiritual y subconsciente. "
                "Brillas en soledad creativa y en conexión con lo universal."
        }
        # Añadir más planetas aquí
    }
    
    # Obtener interpretación específica si existe
    house_str = str(house)
    planet_interp = interpretations.get(planet, {}).get(house)
    
    if not planet_interp:
        # Si no hay interpretación específica, crear una genérica basada en la casa
        house_meaning = HOUSE_INTERPRETATIONS.get(house_str, f"La casa {house} representa un área importante de tu vida.")
        return f"Con {planet.capitalize()} en la casa {house}, enfocas su energía en este ámbito de tu vida. {house_meaning}"
    
    return planet_interp


def interpret_house(house_num: str, sign: str, planets: List[str], depth: int = 3) -> str:
    """
    Interpreta una casa astrológica.
    
    Args:
        house_num: Número de la casa (como string, "1"-"12")
        sign: Signo en la cúspide de la casa
        planets: Lista de planetas en la casa
        depth: Nivel de profundidad de la interpretación
    
    Returns:
        str: Interpretación de la casa
    """
    # Obtener significado básico de la casa
    house_meaning = HOUSE_INTERPRETATIONS.get(house_num, f"La casa {house_num} representa un área importante de tu vida.")
    
    # Interpretación básica de cómo el signo influye en la casa
    sign_influence = f"Con {sign} en la cúspide, abordas este área de tu vida con las cualidades de {sign}: "
    
    # Añadir cualidades específicas según el signo
    sign_qualities = {
        "Aries": "iniciativa, coraje y acción directa.",
        "Tauro": "estabilidad, paciencia y enfoque práctico.",
        "Géminis": "curiosidad, adaptabilidad y comunicación.",
        "Cáncer": "sensibilidad, protección y conexión emocional.",
        "Leo": "creatividad, generosidad y autoexpresión.",
        "Virgo": "análisis, perfeccionismo y atención al detalle.",
        "Libra": "equilibrio, diplomacia y sentido estético.",
        "Escorpio": "intensidad, profundidad y capacidad transformadora.",
        "Sagitario": "optimismo, expansión y búsqueda de significado.",
        "Capricornio": "disciplina, ambición y enfoque estructurado.",
        "Acuario": "originalidad, independencia y visión de futuro.",
        "Piscis": "sensibilidad, compasión e intuición."
    }
    
    sign_influence += sign_qualities.get(sign, "cualidades únicas y particulares.")
    
    # Añadir información sobre planetas en la casa
    planets_info = ""
    if planets:
        planets_info = f"\n\nEn esta casa tienes: {', '.join([p.capitalize() for p in planets])}, lo que intensifica y enfoca energía en este ámbito de tu vida."
        
        # Para interpretaciones más profundas, añadir detalles sobre cada planeta
        if depth >= 4 and planets:
            planets_info += "\n"
            for planet in planets:
                planets_info += f"\n- {planet.capitalize()} aquí indica que {get_planet_house_brief(planet, int(house_num))}"
    
    # Combinar toda la información
    interpretation = f"{house_meaning}\n\n{sign_influence}{planets_info}"
    
    return interpretation


def interpret_aspect(aspect: Dict[str, Any], depth: int = 3) -> str:
    """
    Interpreta un aspecto astrológico.
    
    Args:
        aspect: Diccionario con datos del aspecto
        depth: Nivel de profundidad de la interpretación
    
    Returns:
        str: Interpretación del aspecto
    """
    planet1 = aspect["planet1"]
    planet2 = aspect["planet2"]
    aspect_type = aspect["aspect_type"]
    
    # Verificar si existe una interpretación específica para este par de planetas
    key1 = f"{planet1}-{planet2}"
    key2 = f"{planet2}-{planet1}"
    
    if key1 in ASPECT_INTERPRETATIONS and aspect_type in ASPECT_INTERPRETATIONS[key1]:
        return ASPECT_INTERPRETATIONS[key1][aspect_type]
    elif key2 in ASPECT_INTERPRETATIONS and aspect_type in ASPECT_INTERPRETATIONS[key2]:
        return ASPECT_INTERPRETATIONS[key2][aspect_type]
    
    # Si no hay interpretación específica, generar una genérica
    aspect_nature = {
        "conjunción": "unión, fusión e intensificación",
        "sextil": "oportunidad, armonía ligera y facilidad",
        "cuadratura": "tensión, desafío y necesidad de ajuste",
        "trígono": "armonía, fluidez y facilidad natural",
        "oposición": "polarización, integración de opuestos y equilibrio",
        "quincuncio": "ajuste, incomodidad y necesidad de adaptación",
        "semisextil": "irritación leve, ajuste sutil y comunicación incómoda"
    }
    
    planets_meaning = {
        "sun": "tu identidad y voluntad consciente",
        "moon": "tus emociones y necesidades instintivas",
        "mercury": "tu mente y comunicación",
        "venus": "tus valores, placeres y forma de relacionarte",
        "mars": "tu asertividad, impulso y cómo actúas",
        "jupiter": "tu expansión, optimismo y búsqueda de significado",
        "saturn": "tu disciplina, responsabilidad y límites",
        "uranus": "tu originalidad, independencia y capacidad de innovación",
        "neptune": "tu sensibilidad, imaginación y espiritualidad",
        "pluto": "tu poder transformador y capacidad de regeneración",
        "ascendant": "tu personalidad exterior y cómo te proyectas",
        "midheaven": "tu carrera, reputación y propósito público"
    }
    
    nature = aspect_nature.get(aspect_type, "interacción significativa")
    p1_meaning = planets_meaning.get(planet1, f"la energía de {planet1}")
    p2_meaning = planets_meaning.get(planet2, f"la energía de {planet2}")
    
    basic_interp = f"Hay una {nature} entre {p1_meaning} y {p2_meaning}."
    
    # Para profundidades mayores, añadir más detalles
    if depth >= 3:
        if aspect["nature"] == "favorable":
            basic_interp += f"\n\nEste es un aspecto favorable que facilita el flujo de energía entre estas áreas de tu vida."
        elif aspect["nature"] == "desafiante":
            basic_interp += f"\n\nEste aspecto presenta un desafío que te invita a integrar estas energías con conciencia y esfuerzo."
        elif aspect["nature"] == "ambivalente":
            basic_interp += f"\n\nEste aspecto tiene una cualidad mixta, ofreciendo tanto oportunidades como desafíos en la relación entre estas energías."
    
    return basic_interp


def interpret_element(element: str) -> str:
    """
    Interpreta un elemento astrológico.
    
    Args:
        element: Nombre del elemento (Fuego, Tierra, Aire, Agua)
    
    Returns:
        str: Interpretación del elemento
    """
    interpretations = {
        "Fuego": "Tienes una naturaleza energética, entusiasta y orientada a la acción. "
                "El elemento Fuego te aporta vitalidad, pasión y un espíritu aventurero. "
                "Tiendes a expresarte con confianza y buscas experiencias estimulantes y creativas.",
        
        "Tierra": "Tienes una naturaleza práctica, estable y orientada a resultados. "
                 "El elemento Tierra te aporta paciencia, sentido común y perseverancia. "
                 "Tiendes a ser realista y valoras la seguridad material y la fiabilidad.",
        
        "Aire": "Tienes una naturaleza intelectual, comunicativa y sociable. "
              "El elemento Aire te aporta curiosidad, versatilidad y capacidad de análisis. "
              "Tiendes a procesar el mundo a través del pensamiento y valoras las conexiones e intercambios de ideas.",
        
        "Agua": "Tienes una naturaleza emocional, intuitiva y receptiva. "
               "El elemento Agua te aporta sensibilidad, empatía y profundidad emocional. "
               "Tiendes a sentir intensamente y valoras las conexiones emocionales significativas."
    }
    
    return interpretations.get(element, f"El elemento {element} influye significativamente en tu personalidad.")


def interpret_modality(modality: str) -> str:
    """
    Interpreta una modalidad astrológica.
    
    Args:
        modality: Nombre de la modalidad (Cardinal, Fijo, Mutable)
    
    Returns:
        str: Interpretación de la modalidad
    """
    interpretations = {
        "Cardinal": "Tienes una naturaleza iniciadora, proactiva y orientada al liderazgo. "
                   "La modalidad Cardinal te aporta energía para comenzar proyectos y asumir la iniciativa. "
                   "Tiendes a ser emprendedor/a y te motiva crear impacto y establecer nuevas direcciones.",
        
        "Fijo": "Tienes una naturaleza determinada, persistente y orientada a la estabilidad. "
               "La modalidad Fija te aporta enfoque, lealtad y capacidad para mantener esfuerzos a largo plazo. "
               "Tiendes a ser constante y te motiva profundizar y consolidar lo que ya has establecido.",
        
        "Mutable": "Tienes una naturaleza adaptable, versátil y orientada al cambio. "
                  "La modalidad Mutable te aporta flexibilidad, curiosidad y capacidad para ajustarte a nuevas situaciones. "
                  "Tiendes a ser receptivo/a y te motiva integrar diversas experiencias y perspectivas."
    }
    
    return interpretations.get(modality, f"La modalidad {modality} influye significativamente en cómo enfrentas la vida.")


def get_planet_house_brief(planet: str, house: int) -> str:
    """
    Proporciona una breve descripción de un planeta en una casa.
    
    Args:
        planet: Nombre del planeta
        house: Número de casa (1-12)
    
    Returns:
        str: Breve descripción del significado
    """
    descriptions = {
        "sun": {
            1: "tu identidad se expresa a través de tu presencia y apariencia física.",
            2: "encuentras tu propósito a través de construir seguridad material y desarrollar talentos.",
            3: "tu esencia brilla a través de la comunicación y el aprendizaje diario.",
            4: "tu identidad está enraizada en tu vida hogareña y conexiones familiares.",
            5: "tu esencia se expresa naturalmente a través de la creatividad y autoexpresión.",
            6: "encuentras tu propósito en el trabajo meticuloso, servicio y bienestar.",
            7: "tu identidad se realiza a través de relaciones significativas y colaboraciones.",
            8: "encuentras tu propósito en transformaciones profundas y manejo de recursos compartidos.",
            9: "tu esencia brilla a través de la exploración mental, espiritual y física.",
            10: "tu identidad se expresa a través de tu carrera y contribuciones a la sociedad.",
            11: "encuentras tu propósito en grupos, amistades y causas humanitarias.",
            12: "tu identidad tiene una dimensión espiritual y subconsciente significativa."
        },
        "moon": {
            1: "tus emociones se expresan abiertamente y afectan tu imagen personal.",
            2: "tus necesidades emocionales están ligadas a la seguridad material y recursos.",
            3: "te nutres emocionalmente a través de la comunicación y aprendizaje.",
            4: "tus emociones están profundamente conectadas con el hogar y las raíces familiares.",
            5: "te nutres emocionalmente a través de la expresión creativa y actividades placenteras.",
            6: "tus necesidades emocionales se satisfacen a través del servicio y rutinas saludables.",
            7: "tus emociones se procesan y expresan principalmente en relaciones cercanas.",
            8: "tus emociones son intensas y te llevan a experiencias transformadoras.",
            9: "te nutres emocionalmente a través de la expansión mental y nuevas experiencias.",
            10: "tus emociones influyen en tu carrera y están conectadas con tu imagen pública.",
            11: "tus necesidades emocionales se satisfacen a través de amistades y grupos.",
            12: "tus emociones operan a nivel subconsciente y tienen cualidad espiritual."
        }
        # Se pueden añadir más planetas según sea necesario
    }
    
    # Obtener la descripción específica o crear una genérica
    if planet in descriptions and house in descriptions[planet]:
        return descriptions[planet][house]
    else:
        house_meanings = {
            1: "tu identidad y presencia personal",
            2: "tus recursos y valores",
            3: "tu comunicación y entorno cercano",
            4: "tu hogar y raíces",
            5: "tu creatividad y placeres",
            6: "tu trabajo y bienestar",
            7: "tus relaciones cercanas",
            8: "tus transformaciones y recursos compartidos",
            9: "tu expansión mental y espiritual",
            10: "tu carrera y posición social",
            11: "tus amistades y metas de vida",
            12: "tu vida interior y conexión con lo universal"
        }
        
        return f"su energía se enfoca en {house_meanings.get(house, f'la casa {house}')}"


def generate_chart_summary(chart_data: Dict[str, Any], chart_type: ChartType, depth: int = 3) -> str:
    """
    Genera un resumen general de la carta astral.
    
    Args:
        chart_data: Datos calculados de la carta
        chart_type: Tipo de carta astral
        depth: Nivel de profundidad de la interpretación
    
    Returns:
        str: Resumen general de la carta
    """
    sun_sign = chart_data.get("sun_sign", "desconocido")
    moon_sign = chart_data.get("moon_sign", "desconocido")
    rising_sign = chart_data.get("rising_sign", "desconocido")
    dominant_element = chart_data.get("dominant_element", "desconocido")
    dominant_modality = chart_data.get("dominant_modality", "desconocido")
    
    if chart_type == ChartType.NATAL:
        summary = f"""Tu carta natal muestra un Sol en {sun_sign}, Luna en {moon_sign} y Ascendente en {rising_sign}.

Con el Sol en {sun_sign}, tu esencia personal se expresa a través de las cualidades de este signo, aportándote una base de identidad y propósito vital.

Tu Luna en {moon_sign} revela cómo procesas tus emociones y necesidades instintivas, mostrando tu naturaleza interior y reacciones espontáneas.

Tu Ascendente en {rising_sign} constituye la fachada que presentas al mundo, coloreando cómo los demás te perciben inicialmente y cómo enfrentas nuevas experiencias.

El elemento dominante en tu carta es {dominant_element}, lo que indica una tendencia a procesar la realidad a través de las cualidades de este elemento.

Tu modalidad dominante es {dominant_modality}, lo que sugiere cómo tiendes a interactuar con el mundo y abordar los desafíos."""

        # Para niveles más profundos, añadir información adicional
        if depth >= 4:
            # Analizar distribución de planetas por elementos
            elements_count = {"Fuego": 0, "Tierra": 0, "Aire": 0, "Agua": 0}
            for planet, data in chart_data["planets"].items():
                sign = data["sign"]
                if sign in ["Aries", "Leo", "Sagitario"]:
                    elements_count["Fuego"] += 1
                elif sign in ["Tauro", "Virgo", "Capricornio"]:
                    elements_count["Tierra"] += 1
                elif sign in ["Géminis", "Libra", "Acuario"]:
                    elements_count["Aire"] += 1
                elif sign in ["Cáncer", "Escorpio", "Piscis"]:
                    elements_count["Agua"] += 1
            
            # Encontrar elemento con menor representación
            min_element = min(elements_count.items(), key=lambda x: x[1])
            
            summary += f"\n\nTu carta muestra una distribución de planetas que favorece el elemento {dominant_element}. "
            
            if min_element[1] == 0:
                summary += f"Careces de planetas en signos de {min_element[0]}, lo que puede indicar un área de crecimiento en tu desarrollo personal."
            
            # Añadir información sobre aspectos principales
            major_aspects = []
            for aspect in chart_data["aspects"]:
                if aspect["power"] > 7 and aspect["aspect_type"] in ["conjunción", "oposición", "trígono", "cuadratura"]:
                    major_aspects.append(aspect)
            
            if major_aspects:
                summary += "\n\nAspectos principales en tu carta:"
                for aspect in major_aspects[:3]:  # Limitar a los 3 más importantes
                    planet1 = aspect["planet1"].capitalize()
                    planet2 = aspect["planet2"].capitalize()
                    aspect_type = aspect["aspect_type"]
                    summary += f"\n- {planet1} en {aspect_type} con {planet2}"
    
    elif chart_type == ChartType.TRANSIT:
        # Aquí se añadiría la lógica para interpretar cartas de tránsitos
        summary = f"Este análisis de tránsitos muestra cómo los movimientos planetarios actuales interactúan con tu carta natal con Sol en {sun_sign}, Luna en {moon_sign} y Ascendente en {rising_sign}."
        
    elif chart_type == ChartType.SYNASTRY:
        # Aquí se añadiría la lógica para interpretar cartas de sinastría
        summary = f"Este análisis de compatibilidad muestra cómo las energías de ambas cartas interactúan entre sí. La carta principal tiene Sol en {sun_sign}, Luna en {moon_sign} y Ascendente en {rising_sign}."
    
    else:
        summary = f"Esta carta con Sol en {sun_sign}, Luna en {moon_sign} y Ascendente en {rising_sign} muestra importantes patrones energéticos para entender este momento o situación."
    
    return summary


async def interpret_prediction(transits: Dict[str, Any], prediction_type: PredictionType, 
                            prediction_period: PredictionPeriod) -> Dict[str, Any]:
    """
    Interpreta los tránsitos planetarios para generar una predicción astrológica.
    
    Args:
        transits: Datos de tránsitos planetarios
        prediction_type: Tipo de predicción
        prediction_period: Período de la predicción
    
    Returns:
        Dict: Interpretación de la predicción
    """
    try:
        logger.info(f"Interpretando predicción tipo {prediction_type} para período {prediction_period}")
        
        # Inicializar el resultado
        interpretation = {
            "summary": "",
            "transits_interpretation": [],
            "opportunities": [],
            "challenges": [],
            "focus_areas": {}
        }
        
        # Datos de la carta natal
        natal_chart = transits.get("natal_chart", {})
        sun_sign = natal_chart.get("sun_sign", "desconocido")
        moon_sign = natal_chart.get("moon_sign", "desconocido")
        rising_sign = natal_chart.get("rising_sign", "desconocido")
        
        # Períodos en español para usar en el resumen
        period_names = {
            PredictionPeriod.DAY: "día",
            PredictionPeriod.WEEK: "semana",
            PredictionPeriod.MONTH: "mes",
            PredictionPeriod.YEAR: "año",
            PredictionPeriod.CUSTOM: "período"
        }
        
        # Tipos de predicción en español para usar en el resumen
        prediction_names = {
            PredictionType.GENERAL: "general",
            PredictionType.CAREER: "profesional",
            PredictionType.LOVE: "amorosa",
            PredictionType.HEALTH: "de salud",
            PredictionType.MONEY: "financiera",
            PredictionType.PERSONAL_GROWTH: "de crecimiento personal",
            PredictionType.SPIRITUALITY: "espiritual"
        }
        
        # Generar resumen básico
        period_name = period_names.get(prediction_period, "período")
        prediction_name = prediction_names.get(prediction_type, "general")
        
        summary = f"Predicción {prediction_name} para este {period_name} basada en tus tránsitos astrológicos actuales. "
        summary += f"Con Sol natal en {sun_sign}, Luna en {moon_sign} y Ascendente en {rising_sign}, "
        summary += f"estos tránsitos planetarios activan diferentes áreas de tu carta."
        
        # Interpretar tránsitos significativos
        significant_transits = transits.get("significant_transits", [])
        
        transit_interpretations = []
        opportunities = []
        challenges = []
        
        for transit in significant_transits:
            transit_planet = transit.get("transit_planet", "")
            natal_planet = transit.get("natal_planet", "")
            aspect_type = transit.get("aspect_type", "")
            
            # Interpretar este tránsito
            interp = interpret_transit(transit_planet, natal_planet, aspect_type, prediction_type)
            
            transit_interpretations.append({
                "transit_planet": transit_planet,
                "natal_planet": natal_planet,
                "aspect_type": aspect_type,
                "interpretation": interp
            })
            
            # Clasificar como oportunidad o desafío según el aspecto
            if aspect_type in ["trígono", "sextil"] or (aspect_type == "conjunción" and transit_planet in ["jupiter", "venus"]):
                opportunities.append(f"{transit_planet.capitalize()} transitando en {aspect_type} con tu {natal_planet} natal: {get_opportunity(transit_planet, natal_planet, prediction_type)}")
            
            elif aspect_type in ["cuadratura", "oposición"] or (aspect_type == "conjunción" and transit_planet in ["saturn", "mars", "pluto"]):
                challenges.append(f"{transit_planet.capitalize()} transitando en {aspect_type} con tu {natal_planet} natal: {get_challenge(transit_planet, natal_planet, prediction_type)}")
        
        # Añadir interpretaciones específicas por área
        focus_areas = {}
        
        if prediction_type == PredictionType.CAREER:
            focus_areas["carrera"] = interpret_area_transits(significant_transits, "carrera")
        elif prediction_type == PredictionType.LOVE:
            focus_areas["amor"] = interpret_area_transits(significant_transits, "amor")
        elif prediction_type == PredictionType.HEALTH:
            focus_areas["salud"] = interpret_area_transits(significant_transits, "salud")
        elif prediction_type == PredictionType.MONEY:
            focus_areas["finanzas"] = interpret_area_transits(significant_transits, "finanzas")
        else:
            # Para predicciones generales, incluir varias áreas
            focus_areas["personal"] = interpret_area_transits(significant_transits, "personal")
            focus_areas["relaciones"] = interpret_area_transits(significant_transits, "relaciones")
            focus_areas["trabajo"] = interpret_area_transits(significant_transits, "trabajo")
        
        # Construir el resultado final
        interpretation["summary"] = summary
        interpretation["transits_interpretation"] = transit_interpretations
        interpretation["opportunities"] = opportunities
        interpretation["challenges"] = challenges
        interpretation["focus_areas"] = focus_areas
        
        logger.info(f"Interpretación de predicción completada con {len(transit_interpretations)} tránsitos analizados")
        return interpretation
        
    except Exception as e:
        logger.error(f"Error al interpretar predicción: {str(e)}")
        raise InterpretationError(message=f"Error al interpretar predicción: {str(e)}", 
                                 interpretation_type=f"{prediction_type}_{prediction_period}")


def interpret_transit(transit_planet: str, natal_planet: str, aspect_type: str, 
                    prediction_type: PredictionType) -> str:
    """
    Interpreta un tránsito específico.
    
    Args:
        transit_planet: Planeta transitando
        natal_planet: Planeta natal afectado
        aspect_type: Tipo de aspecto
        prediction_type: Tipo de predicción
    
    Returns:
        str: Interpretación del tránsito
    """
    # Esta función debería tener un amplio diccionario de interpretaciones
    # Aquí se incluye una versión simplificada para algunos ejemplos
    
    transit_meanings = {
        "jupiter": {
            "sun": {
                "conjunción": "Este tránsito trae expansión a tu identidad y vitalidad. Es un momento de crecimiento personal, optimismo y nuevas oportunidades que aumentan tu confianza y visibilidad.",
                "trígono": "Este tránsito facilita el crecimiento personal y las oportunidades que llegan con fluidez. Es un buen momento para avanzar en proyectos, realizar viajes o buscar expansión.",
                "cuadratura": "Este tránsito trae tensión entre tu deseo de expansión y tu identidad actual. Puedes enfrentar desafíos relacionados con excesos o expectativas poco realistas."
            },
            "moon": {
                "conjunción": "Este tránsito expande tu mundo emocional y aumenta tu sensibilidad. Es un buen momento para nutrir relaciones familiares y buscar comodidad emocional en nuevas experiencias.",
                "trígono": "Este tránsito facilita el bienestar emocional y la conexión con los demás. Es un momento en que te sientes emocionalmente generoso y las relaciones familiares florecen.",
                "cuadratura": "Este tránsito puede generar fluctuaciones emocionales o exageraciones sentimentales. Puedes sentirte abrumado por sensaciones o expectativas emocionales desproporcionadas."
            }
        },
        "saturn": {
            "sun": {
                "conjunción": "Este tránsito marca un período significativo de pruebas y definición de tu identidad. Puedes sentir el peso de responsabilidades adicionales que eventualmente fortalecerán tu carácter.",
                "trígono": "Este tránsito facilita la estructuración de tu vida y tus proyectos personales. Es un buen momento para establecer bases sólidas y compromisos significativos.",
                "cuadratura": "Este tránsito presenta desafíos relacionados con la autoridad, limitaciones y responsabilidades. Puedes sentir que tu expresión personal está restringida temporalmente."
            },
            "moon": {
                "conjunción": "Este tránsito somete tus emociones a un proceso de maduración y puede asociarse con sentimientos de soledad o melancolía que eventualmente llevan a mayor solidez interior.",
                "trígono": "Este tránsito te ayuda a estructurar tu mundo emocional y establecer rutinas saludables. Es un buen momento para resolver asuntos familiares con madurez.",
                "cuadratura": "Este tránsito presenta desafíos emocionales relacionados con el pasado, la familia o necesidades de seguridad. Puedes sentir una tensión entre responsabilidades y necesidades emocionales."
            }
        }
        # Aquí se añadirían más planetas y aspectos
    }
    
    # Intentar obtener interpretación específica
    if (transit_planet in transit_meanings and 
        natal_planet in transit_meanings[transit_planet] and 
        aspect_type in transit_meanings[transit_planet][natal_planet]):
        
        return transit_meanings[transit_planet][natal_planet][aspect_type]
    
    # Si no hay interpretación específica, generar una genérica
    aspect_meanings = {
        "conjunción": "unión y activación intensa",
        "sextil": "oportunidad y facilidad ligera",
        "trígono": "flujo armónico y facilidad",
        "cuadratura": "tensión y necesidad de ajuste",
        "oposición": "polarización y necesidad de equilibrio"
    }
    
    transit_planet_meanings = {
        "jupiter": "expansión, crecimiento y optimismo",
        "saturn": "estructura, responsabilidad y límites",
        "uranus": "cambio repentino, originalidad y libertad",
        "neptune": "disolución, inspiración y espiritualidad",
        "pluto": "transformación profunda, poder y regeneración",
        "mars": "acción, iniciativa y asertividad",
        "venus": "afecto, relaciones y valores",
        "mercury": "comunicación, pensamiento y aprendizaje",
        "sun": "vitalidad, expresión personal y propósito",
        "moon": "emociones, intuición y necesidades básicas"
    }
    
    natal_planet_meanings = {
        "sun": "tu identidad y propósito vital",
        "moon": "tus emociones y necesidades instintivas",
        "mercury": "tu mente y forma de comunicarte",
        "venus": "tus relaciones y valores",
        "mars": "tu energía y forma de actuar",
        "jupiter": "tu expansión y sistema de creencias",
        "saturn": "tus límites y sentido de responsabilidad",
        "uranus": "tu originalidad e independencia",
        "neptune": "tu sensibilidad e idealismo",
        "pluto": "tu poder de transformación",
        "ascendant": "tu personalidad externa y enfoque vital",
        "midheaven": "tu carrera y propósito público"
    }
    
    aspect_meaning = aspect_meanings.get(aspect_type, "interacción significativa")
    t_meaning = transit_planet_meanings.get(transit_planet, f"la energía de {transit_planet}")
    n_meaning = natal_planet_meanings.get(natal_planet, f"tu {natal_planet}")
    
    return f"Este tránsito representa una {aspect_meaning} entre {t_meaning} y {n_meaning}. Durante este período experimentarás una interacción significativa entre estas energías."


def get_opportunity(transit_planet: str, natal_planet: str, prediction_type: PredictionType) -> str:
    """
    Genera una descripción de oportunidad basada en un tránsito favorable.
    
    Args:
        transit_planet: Planeta transitando
        natal_planet: Planeta natal afectado
        prediction_type: Tipo de predicción
    
    Returns:
        str: Descripción de la oportunidad
    """
    # Esta función tendría un amplio diccionario de oportunidades según el tipo de predicción
    # Aquí se incluyen algunos ejemplos como muestra
    
    if prediction_type == PredictionType.CAREER:
        opportunities = {
            "jupiter-sun": "Oportunidad de reconocimiento profesional y expansión de tu influencia en tu campo.",
            "jupiter-midheaven": "Posibilidad de ascenso o mejora significativa en tu estatus profesional.",
            "jupiter-mercury": "Oportunidades a través de comunicación, contratos o nuevas ideas en el trabajo.",
            "saturn-midheaven": "Oportunidad para establecer bases sólidas en tu carrera y ganar credibilidad.",
            "venus-midheaven": "Posibilidad de mejorar relaciones profesionales o atraer proyectos creativos.",
            "uranus-midheaven": "Oportunidades inesperadas de cambio o innovación en tu carrera."
        }
    elif prediction_type == PredictionType.LOVE:
        opportunities = {
            "jupiter-venus": "Expansión en tu vida amorosa, posibilidad de encuentros significativos o mejora en relaciones existentes.",
            "jupiter-moon": "Mayor conexión emocional y crecimiento en intimidad con seres queridos.",
            "venus-sun": "Período favorable para el romance, atracción y expresión de afecto.",
            "venus-ascendant": "Aumento de tu atractivo personal y capacidad para atraer relaciones armoniosas.",
            "pluto-venus": "Oportunidad de transformación profunda en tus relaciones o forma de amar."
        }
    elif prediction_type == PredictionType.MONEY:
        opportunities = {
            "jupiter-venus": "Posibilidad de incremento en tus recursos financieros o bienes materiales.",
            "jupiter-saturn": "Oportunidad para solidificar inversiones o establecer estructuras financieras duraderas.",
            "venus-jupiter": "Atracción de abundancia material y oportunidades financieras favorables.",
            "sun-jupiter": "Reconocimiento que puede traducirse en mayores ingresos o recursos."
        }
    else:
        # Oportunidades generales para cualquier tipo de predicción
        opportunities = {
            "jupiter-sun": "Período de crecimiento personal, optimismo y nuevas oportunidades.",
            "jupiter-moon": "Expansión emocional y posibilidad de mejorar tu bienestar general.",
            "jupiter-ascendant": "Nuevas oportunidades para desarrollar tu identidad y expandir horizontes.",
            "saturn-sun": "Oportunidad para consolidar logros y establecer estructuras duraderas.",
            "uranus-mercury": "Inspiración repentina, ideas originales y pensamiento innovador.",
            "venus-jupiter": "Período favorable para el disfrute, abundancia y relaciones armoniosas."
        }
    
    # Crear clave para buscar en el diccionario
    key = f"{transit_planet}-{natal_planet}"
    key_reverse = f"{natal_planet}-{transit_planet}"
    
    # Buscar oportunidad específica
    if key in opportunities:
        return opportunities[key]
    elif key_reverse in opportunities:
        return opportunities[key_reverse]
    
    # Si no hay oportunidad específica, crear una genérica
    transit_descriptions = {
        "jupiter": "expansión y crecimiento",
        "venus": "armonía y conexión positiva",
        "sun": "vitalidad y reconocimiento",
        "uranus": "cambio positivo e innovación",
        "neptune": "inspiración y sensibilidad",
        "mercury": "comunicación favorable e ideas",
        "moon": "flujo emocional positivo"
    }
    
    natal_descriptions = {
        "sun": "tu identidad y propósito",
        "moon": "tus emociones y necesidades básicas",
        "mercury": "tu comunicación y procesos mentales",
        "venus": "tus relaciones y valores",
        "mars": "tu energía y capacidad de acción",
        "jupiter": "tu expansión y crecimiento",
        "saturn": "tu estructura y responsabilidad",
        "uranus": "tu originalidad e independencia",
        "neptune": "tu imaginación e intuición",
        "pluto": "tu poder de transformación",
        "ascendant": "tu proyección personal",
        "midheaven": "tu carrera y propósito público"
    }
    
    t_desc = transit_descriptions.get(transit_planet, f"la energía de {transit_planet}")
    n_desc = natal_descriptions.get(natal_planet, f"tu {natal_planet}")
    
    return f"Oportunidad para experimentar {t_desc} en relación con {n_desc}."


def get_challenge(transit_planet: str, natal_planet: str, prediction_type: PredictionType) -> str:
    """
    Genera una descripción de desafío basada en un tránsito difícil.
    
    Args:
        transit_planet: Planeta transitando
        natal_planet: Planeta natal afectado
        prediction_type: Tipo de predicción
    
    Returns:
        str: Descripción del desafío
    """
    # Esta función tendría un amplio diccionario de desafíos según el tipo de predicción
    # Aquí se incluyen algunos ejemplos como muestra
    
    if prediction_type == PredictionType.CAREER:
        challenges = {
            "saturn-sun": "Posibles obstáculos o restricciones en tu expresión profesional que requieren paciencia y disciplina.",
            "saturn-midheaven": "Pruebas en tu carrera que demandan mayor responsabilidad y perseverancia.",
            "pluto-midheaven": "Transformaciones intensas en tu carrera que pueden implicar fin de ciclos y renovación.",
            "uranus-saturn": "Tensión entre necesidad de estabilidad y cambios inesperados en tu estructura laboral.",
            "mars-mercury": "Posibles conflictos o discusiones en el entorno laboral que requieren diplomacia."
        }
    elif prediction_type == PredictionType.LOVE:
        challenges = {
            "saturn-venus": "Pruebas en relaciones que requieren madurez, compromiso y superación de miedos.",
            "pluto-venus": "Intensas transformaciones en relaciones que pueden traer a la luz dinámicas de poder.",
            "uranus-venus": "Inestabilidad o cambios repentinos en relaciones que requieren adaptabilidad.",
            "mars-venus": "Tensiones o conflictos en relaciones que pueden intensificar pasiones o desacuerdos.",
            "neptune-venus": "Confusión o desilusión en asuntos del corazón que invitan a mayor discernimiento."
        }
    elif prediction_type == PredictionType.HEALTH:
        challenges = {
            "saturn-sun": "Posible disminución de energía vital que requiere descanso y estructuración.",
            "saturn-mars": "Restricciones en tu energía física que demandan paciencia y disciplina.",
            "pluto-moon": "Intensas transformaciones emocionales que pueden afectar tu bienestar general.",
            "mars-sun": "Riesgo de desgaste por exceso de actividad o posibles inflamaciones.",
            "neptune-mars": "Confusión en la dirección de tu energía o posible debilitamiento temporario."
        }
    else:
        # Desafíos generales para cualquier tipo de predicción
        challenges = {
            "saturn-sun": "Período de pruebas y responsabilidades que requieren seriedad y determinación.",
            "saturn-moon": "Desafíos emocionales o sentimientos de soledad que invitan a mayor madurez.",
            "pluto-sun": "Transformaciones profundas en tu identidad que pueden sentirse intensas.",
            "uranus-moon": "Inestabilidad emocional o cambios repentinos que requieren adaptabilidad.",
            "mars-saturn": "Frustraciones en la acción o esfuerzos que parecen bloqueados temporalmente.",
            "neptune-mercury": "Confusión mental o malentendidos que requieren mayor claridad."
        }
    
    # Crear clave para buscar en el diccionario
    key = f"{transit_planet}-{natal_planet}"
    key_reverse = f"{natal_planet}-{transit_planet}"
    
    # Buscar desafío específico
    if key in challenges:
        return challenges[key]
    elif key_reverse in challenges:
        return challenges[key_reverse]
    
    # Si no hay desafío específico, crear uno genérico
    transit_descriptions = {
        "saturn": "restricción y necesidad de estructura",
        "pluto": "transformación profunda y crisis",
        "mars": "tensión y posibles conflictos",
        "uranus": "cambios inesperados e inestabilidad",
        "neptune": "confusión y posible desilusión"
    }
    
    natal_descriptions = {
        "sun": "tu identidad y vitalidad",
        "moon": "tus emociones y seguridad interna",
        "mercury": "tu comunicación y procesos mentales",
        "venus": "tus relaciones y sentido de valor",
        "mars": "tu energía y capacidad de acción",
        "jupiter": "tu expansión y optimismo",
        "saturn": "tu estructura y sentido de límites",
        "uranus": "tu libertad e independencia",
        "neptune": "tu sensibilidad e intuición",
        "pluto": "tu poder personal y procesos de transformación",
        "ascendant": "tu proyección personal y enfoque vital",
        "midheaven": "tu carrera y propósito social"
    }
    
    t_desc = transit_descriptions.get(transit_planet, f"la energía desafiante de {transit_planet}")
    n_desc = natal_descriptions.get(natal_planet, f"tu {natal_planet}")
    
    return f"Desafío que implica {t_desc} en relación con {n_desc}."


def interpret_area_transits(transits: List[Dict[str, Any]], area: str) -> str:
    """
    Interpreta cómo los tránsitos afectan a un área específica de la vida.
    
    Args:
        transits: Lista de tránsitos significativos
        area: Área de la vida (carrera, amor, salud, etc.)
    
    Returns:
        str: Interpretación para esa área específica
    """
    # Definir qué planetas/casas son relevantes para cada área
    area_significators = {
        "carrera": ["midheaven", "saturn", "sun", "jupiter", "10"],
        "amor": ["venus", "moon", "mars", "7", "5"],
        "salud": ["sun", "mars", "saturn", "6", "1"],
        "finanzas": ["venus", "jupiter", "saturn", "2", "8"],
        "personal": ["sun", "moon", "ascendant", "1"],
        "relaciones": ["venus", "mars", "moon", "7"],
        "trabajo": ["saturn", "mars", "mercury", "6", "10"],
        "espiritualidad": ["neptune", "jupiter", "12", "9"]
    }
    
    # Filtrar los tránsitos relevantes para esta área
    relevant_transits = []
    for transit in transits:
        transit_planet = transit.get("transit_planet", "")
        natal_planet = transit.get("natal_planet", "")
        natal_house = transit.get("natal_house", "")
        
        if (transit_planet in area_significators.get(area, []) or 
            natal_planet in area_significators.get(area, []) or 
            natal_house in area_significators.get(area, [])):
            relevant_transits.append(transit)
    
    # Si no hay tránsitos relevantes, dar una interpretación genérica
    if not relevant_transits:
        if area == "carrera":
            return "Este período no muestra tránsitos significativos directamente relacionados con tu carrera. Es un buen momento para mantener tu rumbo actual y prepararte para futuras oportunidades."
        elif area == "amor":
            return "Este período no muestra tránsitos significativos directamente relacionados con tu vida amorosa. Es un buen momento para centrarte en ti mismo y cultivar el amor propio."
        elif area == "salud":
            return "Este período no muestra tránsitos significativos directamente relacionados con tu salud. Es un buen momento para mantener rutinas saludables y prestar atención a tu bienestar general."
        elif area == "finanzas":
            return "Este período no muestra tránsitos significativos directamente relacionados con tus finanzas. Es un buen momento para revisar tu presupuesto y planificar a futuro."
        else:
            return f"Este período no muestra tránsitos significativos directamente relacionados con el área de {area}. Puedes usar este tiempo para reflexionar y planificar."
    
    # Crear interpretación basada en los tránsitos relevantes
    interpretation = f"En el área de {area}, los siguientes tránsitos son particularmente significativos:\n\n"
    
    for transit in relevant_transits[:3]:  # Limitar a los 3 más importantes
        transit_planet = transit.get("transit_planet", "").capitalize()
        natal_planet = transit.get("natal_planet", "").capitalize()
        aspect_type = transit.get("aspect_type", "")
        
        if area == "carrera":
            if aspect_type in ["trígono", "sextil"] or (aspect_type == "conjunción" and transit_planet in ["Jupiter", "Venus"]):
                interpretation += f"- {transit_planet} en {aspect_type} con tu {natal_planet} natal trae oportunidades profesionales y facilita tu progreso en este ámbito.\n"
            else:
                interpretation += f"- {transit_planet} en {aspect_type} con tu {natal_planet} natal presenta desafíos profesionales que te invitan a mayor determinación y paciencia.\n"
        elif area == "amor":
            if aspect_type in ["trígono", "sextil"] or (aspect_type == "conjunción" and transit_planet in ["Jupiter", "Venus"]):
                interpretation += f"- {transit_planet} en {aspect_type} con tu {natal_planet} natal favorece tu vida afectiva y trae armonía a tus relaciones personales.\n"
            else:
                interpretation += f"- {transit_planet} en {aspect_type} con tu {natal_planet} natal puede traer tensiones en relaciones que requieren atención y comprensión mutua.\n"
        else:
            if aspect_type in ["trígono", "sextil"] or (aspect_type == "conjunción" and transit_planet in ["Jupiter", "Venus"]):
                interpretation += f"- {transit_planet} en {aspect_type} con tu {natal_planet} natal trae una influencia positiva a esta área de tu vida.\n"
            else:
                interpretation += f"- {transit_planet} en {aspect_type} con tu {natal_planet} natal presenta situaciones que requieren ajustes en esta área de tu vida.\n"
    
    # Añadir recomendación general
    if area == "carrera":
        interpretation += "\nEste es un momento para [enfocarte en tus objetivos profesionales / reevaluar tu dirección profesional / consolidar logros] con conciencia de las energías que están influyendo en tu vida laboral."
    elif area == "amor":
        interpretation += "\nEste es un momento para [expresar tus sentimientos / fortalecer vínculos / dar espacio a nuevas conexiones] considerando las energías que están activando tu vida afectiva."
    elif area == "salud":
        interpretation += "\nEste es un momento para [prestar atención a tu bienestar / equilibrar energías / establecer hábitos saludables] en sintonía con los tránsitos que influyen en tu vitalidad."
    elif area == "finanzas":
        interpretation += "\nEste es un momento para [revisar tus recursos / planificar inversiones / ajustar tu presupuesto] de acuerdo con las energías que afectan tu situación material."
    else:
        interpretation += f"\nEste es un momento importante en el área de {area}, donde las energías planetarias te invitan a prestar especial atención a cómo te desenvuelves en este ámbito."
    
    return interpretation


async def interpret_compatibility(compatibility_calculation: Dict[str, Any], 
                               compatibility_type: CompatibilityType,
                               focus_areas: List[str] = None) -> Dict[str, Any]:
    """
    Interpreta un análisis de compatibilidad astrológica.
    
    Args:
        compatibility_calculation: Resultado del cálculo de compatibilidad
        compatibility_type: Tipo de compatibilidad
        focus_areas: Áreas específicas para enfocar la interpretación
    
    Returns:
        Dict: Interpretación completa de la compatibilidad
    """
    try:
        logger.info(f"Interpretando compatibilidad tipo {compatibility_type}")
        
        # Inicializar el resultado
        interpretation = {
            "summary": "",
            "strengths": [],
            "challenges": [],
            "dynamics": {},
            "compatibility_score": compatibility_calculation.get("compatibility_score", 0)
        }
        
        # Extraer datos básicos
        chart1 = compatibility_calculation.get("chart1", {})
        chart2 = compatibility_calculation.get("chart2", {})
        
        person1_sun = chart1.get("sun_sign", "desconocido")
        person1_moon = chart1.get("moon_sign", "desconocido")
        person1_asc = chart1.get("rising_sign", "desconocido")
        
        person2_sun = chart2.get("sun_sign", "desconocido")
        person2_moon = chart2.get("moon_sign", "desconocido")
        person2_asc = chart2.get("rising_sign", "desconocido")
        
        # Obtener aspectos entre las cartas
        synastry_aspects = compatibility_calculation.get("synastry_aspects", [])
        
        # Generar resumen básico
        summary = generate_compatibility_summary(
            compatibility_type,
            person1_sun, person1_moon, person1_asc,
            person2_sun, person2_moon, person2_asc,
            compatibility_calculation.get("compatibility_score", 0)
        )
        
        # Analizar fortalezas y desafíos
        strengths = []
        challenges = []
        
        # Usar fortalezas y desafíos precalculados si existen
        if "strengths" in compatibility_calculation and compatibility_calculation["strengths"]:
            strengths = compatibility_calculation["strengths"]
        if "challenges" in compatibility_calculation and compatibility_calculation["challenges"]:
            challenges = compatibility_calculation["challenges"]
        
        # Si no hay precalculados, generarlos desde los aspectos
        if not strengths or not challenges:
            for aspect in synastry_aspects:
                aspect_type = aspect.get("aspect_type", "")
                planet1 = aspect.get("person1_planet", aspect.get("planet1", ""))
                planet2 = aspect.get("person2_planet", aspect.get("planet2", ""))
                power = aspect.get("power", 5)
                
                if power > 7:  # Solo incluir los aspectos más significativos
                    if aspect_type in ["trígono", "sextil"] or (aspect_type == "conjunción" and aspect.get("nature") == "favorable"):
                        strength = get_compatibility_strength(planet1, planet2, aspect_type, compatibility_type)
                        if strength:
                            strengths.append(strength)
                    
                    elif aspect_type in ["cuadratura", "oposición"] or (aspect_type == "conjunción" and aspect.get("nature") == "desafiante"):
                        challenge = get_compatibility_challenge(planet1, planet2, aspect_type, compatibility_type)
                        if challenge:
                            challenges.append(challenge)
        
        # Limitar cantidad de fortalezas y desafíos
        strengths = strengths[:5]  # Máximo 5 fortalezas
        challenges = challenges[:5]  # Máximo 5 desafíos
        
        # Generar dinámicas de la relación
        dynamics = generate_compatibility_dynamics(
            compatibility_type,
            person1_sun, person1_moon, person1_asc,
            person2_sun, person2_moon, person2_asc,
            synastry_aspects
        )
        
        # Analizar áreas de enfoque específicas
        focus_interpretations = {}
        if focus_areas:
            for area in focus_areas:
                focus_interpretations[area] = interpret_compatibility_area(
                    compatibility_calculation,
                    area,
                    compatibility_type
                )
        
        # Construir el resultado final
        interpretation["summary"] = summary
        interpretation["strengths"] = strengths
        interpretation["challenges"] = challenges
        interpretation["dynamics"] = dynamics
        
        if focus_interpretations:
            interpretation["focus_areas"] = focus_interpretations
        
        logger.info(f"Interpretación de compatibilidad completada")
        return interpretation
        
    except Exception as e:
        logger.error(f"Error al interpretar compatibilidad: {str(e)}")
        raise InterpretationError(message=f"Error al interpretar compatibilidad: {str(e)}", 
                                 interpretation_type=str(compatibility_type))


def generate_compatibility_summary(compatibility_type: CompatibilityType,
                                 person1_sun: str, person1_moon: str, person1_asc: str,
                                 person2_sun: str, person2_moon: str, person2_asc: str,
                                 score: float) -> str:
    """
    Genera un resumen narrativo de la compatibilidad.
    
    Args:
        compatibility_type: Tipo de compatibilidad
        person1_sun: Signo solar de la primera persona
        person1_moon: Signo lunar de la primera persona
        person1_asc: Ascendente de la primera persona
        person2_sun: Signo solar de la segunda persona
        person2_moon: Signo lunar de la segunda persona
        person2_asc: Ascendente de la segunda persona
        score: Puntuación de compatibilidad (0-100)
    
    Returns:
        str: Resumen narrativo de la compatibilidad
    """
    # Calificar compatibilidad general
    rating = ""
    if score >= 80:
        rating = "excelente"
    elif score >= 70:
        rating = "muy buena"
    elif score >= 60:
        rating = "buena"
    elif score >= 50:
        rating = "moderada"
    elif score >= 40:
        rating = "desafiante"
    else:
        rating = "difícil"
    
    # Crear resumen específico para cada tipo de compatibilidad
    if compatibility_type == CompatibilityType.ROMANTIC:
        summary = f"""Esta compatibilidad romántica muestra una dinámica {rating} con una puntuación de {score}/100.

La interacción entre Sol en {person1_sun} y Sol en {person2_sun} sugiere cómo sus identidades y propósitos vitales se relacionan. Luna en {person1_moon} y Luna en {person2_moon} revela la compatibilidad emocional y cómo se nutren mutuamente. Sus Ascendentes en {person1_asc} y {person2_asc} indican la química inicial y la forma en que se perciben mutuamente.

Esta combinación de energías crea una relación con sus propias fortalezas y áreas de crecimiento."""
    
    elif compatibility_type == CompatibilityType.FRIENDSHIP:
        summary = f"""Esta compatibilidad de amistad muestra una dinámica {rating} con una puntuación de {score}/100.

La interacción entre Sol en {person1_sun} y Sol en {person2_sun} sugiere cómo sus personalidades se complementan y apoyan mutuamente. Luna en {person1_moon} y Luna en {person2_moon} revela la compatibilidad emocional y cómo se conectan a nivel intuitivo. Sus Ascendentes en {person1_asc} y {person2_asc} indican la dinámica social y cómo se perciben inicialmente.

Esta combinación de energías crea una amistad con características únicas y potencial para crecer juntos."""
    
    elif compatibility_type == CompatibilityType.PROFESSIONAL:
        summary = f"""Esta compatibilidad profesional muestra una dinámica {rating} con una puntuación de {score}/100.

La interacción entre Sol en {person1_sun} y Sol en {person2_sun} sugiere cómo sus propósitos profesionales y liderazgo se complementan. Luna en {person1_moon} y Luna en {person2_moon} revela la compatibilidad de sus necesidades y hábitos de trabajo. Sus Ascendentes en {person1_asc} y {person2_asc} indican cómo se presentan profesionalmente y proyectan su imagen laboral.

Esta combinación de energías crea una dinámica profesional con fortalezas específicas y áreas a considerar para optimizar su colaboración."""
    
    elif compatibility_type == CompatibilityType.FAMILY:
        summary = f"""Esta compatibilidad familiar muestra una dinámica {rating} con una puntuación de {score}/100.

La interacción entre Sol en {person1_sun} y Sol en {person2_sun} sugiere cómo sus identidades y roles familiares se relacionan. Luna en {person1_moon} y Luna en {person2_moon} revela la compatibilidad emocional y patrones familiares compartidos. Sus Ascendentes en {person1_asc} y {person2_asc} indican cómo se perciben mutuamente dentro del contexto familiar.

Esta combinación de energías crea un vínculo familiar con sus propias características y dinámicas para cultivar juntos."""
    
    else:  # Compatibilidad general
        summary = f"""Esta compatibilidad general muestra una dinámica {rating} con una puntuación de {score}/100.

La interacción entre Sol en {person1_sun} y Sol en {person2_sun} sugiere el núcleo de su dinámica relacional. Luna en {person1_moon} y Luna en {person2_moon} revela la compatibilidad emocional y cómo satisfacen mutuamente sus necesidades. Sus Ascendentes en {person1_asc} y {person2_asc} indican la química inicial y cómo se perciben el uno al otro.

Esta combinación de energías crea una relación con características únicas que pueden desarrollarse en diferentes contextos."""
    
    return summary


def get_compatibility_strength(planet1: str, planet2: str, aspect_type: str, 
                             compatibility_type: CompatibilityType) -> str:
    """
    Genera una descripción de fortaleza en la compatibilidad.
    
    Args:
        planet1: Planeta de la primera persona
        planet2: Planeta de la segunda persona
        aspect_type: Tipo de aspecto
        compatibility_type: Tipo de compatibilidad
    
    Returns:
        str: Descripción de la fortaleza
    """
    # Esta función tendría un amplio diccionario de fortalezas según el tipo de compatibilidad
    # Aquí incluimos algunas como ejemplo
    
    if compatibility_type == CompatibilityType.ROMANTIC:
        strengths = {
            "venus-venus": "Fuerte armonía en valores, gustos y expresión de afecto, creando una base cálida y placentera.",
            "venus-moon": "Conexión emocional nutricia que facilita la expresión de cariño y cuidado mutuo.",
            "sun-moon": "Complementariedad natural entre identidad y emociones, donde uno ilumina y el otro nutre.",
            "moon-moon": "Profunda sintonía emocional y capacidad para comprender intuitivamente las necesidades del otro.",
            "jupiter-venus": "Expansión del amor y disfrute compartido, generando optimismo y crecimiento en la relación.",
            "venus-mars": "Fuerte atracción y complementariedad entre principios femeninos y masculinos.",
            "sun-jupiter": "Mutuo apoyo y estímulo para el crecimiento personal, generando optimismo compartido."
        }
    elif compatibility_type == CompatibilityType.PROFESSIONAL:
        strengths = {
            "mercury-mercury": "Excelente comunicación y entendimiento mental, facilitando el trabajo en equipo.",
            "mars-jupiter": "Dinamismo y expansión de la energía compartida, impulsando proyectos ambiciosos.",
            "sun-saturn": "Estructura y propósito combinados, creando bases sólidas para logros duraderos.",
            "mercury-jupiter": "Visión expansiva combinada con comunicación efectiva, ideal para planificación.",
            "saturn-saturn": "Disciplina compartida y compromiso con objetivos a largo plazo.",
            "mars-saturn": "Energía dirigida con disciplina, generando productividad sostenida."
        }
    else:
        # Fortalezas generales para cualquier tipo de compatibilidad
        strengths = {
            "sun-moon": "Complementariedad natural entre voluntad consciente y respuestas emocionales.",
            "venus-jupiter": "Generosidad mutua y capacidad para disfrutar juntos, expandiendo lo positivo.",
            "mercury-mercury": "Excelente comunicación y entendimiento mental, facilitando el intercambio de ideas.",
            "sun-jupiter": "Estímulo mutuo para el crecimiento y apoyo a las aspiraciones de cada uno.",
            "moon-venus": "Fluidez emocional y afectiva, creando un ambiente de bienestar compartido.",
            "jupiter-jupiter": "Visión compartida de crecimiento y expansión, inspirándose mutuamente."
        }
    
    # Crear clave para buscar en el diccionario
    key = f"{planet1}-{planet2}"
    key_reverse = f"{planet2}-{planet1}"
    
    # Buscar fortaleza específica
    if key in strengths:
        return strengths[key]
    elif key_reverse in strengths:
        return strengths[key_reverse]
    
    # Si no hay fortaleza específica, crear una genérica basada en los planetas
    planet_meanings = {
        "sun": "identidad y propósito vital",
        "moon": "mundo emocional y necesidades básicas",
        "mercury": "comunicación y procesos mentales",
        "venus": "valores, afecto y sentido estético",
        "mars": "energía, iniciativa y asertividad",
        "jupiter": "expansión, optimismo y crecimiento",
        "saturn": "estructura, responsabilidad y madurez",
        "uranus": "originalidad, libertad e innovación",
        "neptune": "inspiración, idealismo y espiritualidad",
        "pluto": "transformación profunda y regeneración"
    }
    
    aspect_qualities = {
        "conjunción": "potente unión",
        "trígono": "flujo armónico",
        "sextil": "complementariedad favorable"
    }
    
    p1_meaning = planet_meanings.get(planet1, planet1)
    p2_meaning = planet_meanings.get(planet2, planet2)
    aspect_quality = aspect_qualities.get(aspect_type, "conexión positiva")
    
    return f"Hay una {aspect_quality} entre {p1_meaning} y {p2_meaning}, facilitando entendimiento y colaboración en esta área."


def get_compatibility_challenge(planet1: str, planet2: str, aspect_type: str, 
                              compatibility_type: CompatibilityType) -> str:
    """
    Genera una descripción de desafío en la compatibilidad.
    
    Args:
        planet1: Planeta de la primera persona
        planet2: Planeta de la segunda persona
        aspect_type: Tipo de aspecto
        compatibility_type: Tipo de compatibilidad
    
    Returns:
        str: Descripción del desafío
    """
    # Esta función tendría un amplio diccionario de desafíos según el tipo de compatibilidad
    # Aquí incluimos algunas como ejemplo
    
    if compatibility_type == CompatibilityType.ROMANTIC:
        challenges = {
            "saturn-venus": "Posible restricción en la expresión de afecto, requiriendo paciencia y compromiso consciente.",
            "saturn-moon": "Tensión entre necesidades emocionales y sentido de responsabilidad, pudiendo generar sensación de distancia.",
            "mars-mars": "Posible competitividad o desafíos con el manejo de la energía y asertividad compartida.",
            "pluto-sun": "Dinámicas de poder y control que requieren transformación y conciencia.",
            "uranus-venus": "Inestabilidad en el afecto o necesidad de combinar amor con libertad.",
            "saturn-saturn": "Posible rigidez o exceso de seriedad que puede enfriar la espontaneidad."
        }
    elif compatibility_type == CompatibilityType.PROFESSIONAL:
        challenges = {
            "mars-mars": "Posible competencia o conflictos en el estilo de acción y toma de iniciativa.",
            "sun-sun": "Desafíos con el ego o protagonismo, requiriendo negociación consciente de roles.",
            "saturn-jupiter": "Tensión entre expansión y contracción que puede afectar proyectos compartidos.",
            "mercury-saturn": "Diferencias en estilos de comunicación, donde uno puede percibir al otro como crítico o rígido.",
            "uranus-saturn": "Conflicto entre innovación y tradición, entre cambio y estabilidad.",
            "pluto-mercury": "Posibles luchas por el control de la información o la comunicación."
        }
    else:
        # Desafíos generales para cualquier tipo de compatibilidad
        challenges = {
            "saturn-sun": "Tensión entre expresión personal y limitaciones percibidas, requiriendo paciencia y madurez.",
            "uranus-moon": "Inestabilidad emocional o necesidad de equilibrar cercanía con independencia.",
            "pluto-venus": "Intensidad que puede manifestarse como control o celos, invitando a transformación profunda.",
            "mars-saturn": "Frustración en la iniciativa o sensación de bloqueo en la acción compartida.",
            "mars-pluto": "Posibles conflictos de poder o competencia que requieren canalización consciente.",
            "mercury-neptune": "Confusión en la comunicación o malentendidos que piden mayor claridad."
        }
    
    # Crear clave para buscar en el diccionario
    key = f"{planet1}-{planet2}"
    key_reverse = f"{planet2}-{planet1}"
    
    # Buscar desafío específico
    if key in challenges:
        return challenges[key]
    elif key_reverse in challenges:
        return challenges[key_reverse]
    
    # Si no hay desafío específico, crear uno genérico basado en los planetas
    planet_challenges = {
        "saturn": "restricciones, responsabilidades o limitaciones percibidas",
        "mars": "gestión de la energía, conflictos o asertividad",
        "pluto": "dinámicas de poder, control o transformaciones intensas",
        "uranus": "inestabilidad, independencia o cambios inesperados",
        "neptune": "confusión, idealización o desilusión",
        "mercury-saturn": "comunicación bloqueada o percibida como crítica",
        "venus-saturn": "expresión de afecto limitada o percibida como fría",
        "sun-pluto": "luchas de ego o control"
    }
    
    aspect_qualities = {
        "cuadratura": "tensión",
        "oposición": "polarización",
        "conjunción": "intensidad desafiante"
    }
    
    key_plan = f"{planet1}-{planet2}"
    if key_plan in planet_challenges:
        challenge = planet_challenges[key_plan]
    else:
        p1_challenge = planet_challenges.get(planet1, planet1)
        p2_challenge = planet_challenges.get(planet2, planet2)
        challenge = f"integración entre {p1_challenge} y {p2_challenge}"
    
    aspect_quality = aspect_qualities.get(aspect_type, "dinámica desafiante")
    
    return f"Existe una {aspect_quality} relacionada con {challenge} que invita al crecimiento a través del diálogo y la comprensión mutua."


def generate_compatibility_dynamics(compatibility_type: CompatibilityType,
                                  person1_sun: str, person1_moon: str, person1_asc: str,
                                  person2_sun: str, person2_moon: str, person2_asc: str,
                                  aspects: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Genera descripciones de dinámicas específicas en la compatibilidad.
    
    Args:
        compatibility_type: Tipo de compatibilidad
        person1_sun: Signo solar de la primera persona
        person1_moon: Signo lunar de la primera persona
        person1_asc: Ascendente de la primera persona
        person2_sun: Signo solar de la segunda persona
        person2_moon: Signo lunar de la segunda persona
        person2_asc: Ascendente de la segunda persona
        aspects: Lista de aspectos entre las cartas
    
    Returns:
        Dict[str, str]: Diccionario con dinámicas específicas de la relación
    """
    dynamics = {}
    
    # Analizar compatibilidad de elementos
    elements = {
        "Aries": "Fuego", "Leo": "Fuego", "Sagitario": "Fuego",
        "Tauro": "Tierra", "Virgo": "Tierra", "Capricornio": "Tierra",
        "Géminis": "Aire", "Libra": "Aire", "Acuario": "Aire",
        "Cáncer": "Agua", "Escorpio": "Agua", "Piscis": "Agua"
    }
    
    sun1_element = elements.get(person1_sun, "")
    sun2_element = elements.get(person2_sun, "")
    
    moon1_element = elements.get(person1_moon, "")
    moon2_element = elements.get(person2_moon, "")
    
    # Compatibilidad de elementos
    element_compatibility = {
        ("Fuego", "Fuego"): "Dinámica energética y entusiasta, con posible competencia por protagonismo.",
        ("Fuego", "Aire"): "Dinámica estimulante y creativa, donde Fuego aporta pasión y Aire alimenta las ideas.",
        ("Fuego", "Tierra"): "Dinámica de contraste entre impulso y estabilidad, que puede ser complementaria o desafiante.",
        ("Fuego", "Agua"): "Dinámica de opuestos que puede generar pasión o tensión, requiriendo comprensión mutua.",
        ("Tierra", "Tierra"): "Dinámica estable y práctica, con gran solidez pero posible falta de espontaneidad.",
        ("Tierra", "Aire"): "Dinámica entre lo concreto y lo conceptual, donde pueden aprender mucho uno del otro.",
        ("Tierra", "Agua"): "Dinámica nutricia donde Tierra contiene y Agua nutre, creando fertilidad compartida.",
        ("Aire", "Aire"): "Dinámica intelectualmente estimulante, con gran comunicación pero posible desconexión emocional.",
        ("Aire", "Agua"): "Dinámica entre intelecto y emoción, donde Aire aporta claridad y Agua profundidad.",
        ("Agua", "Agua"): "Dinámica emocionalmente profunda e intuitiva, con gran empatía pero posible sobreidentificación."
    }
    
    # Buscar descripción de compatibilidad de elementos
    sun_compatibility = element_compatibility.get((sun1_element, sun2_element))
    if not sun_compatibility:
        sun_compatibility = element_compatibility.get((sun2_element, sun1_element))
    
    if sun_compatibility:
        dynamics["element_compatibility"] = f"Compatibilidad de elementos solares ({sun1_element}-{sun2_element}): {sun_compatibility}"
    
    # Compatibilidad Sol-Luna
    sun_moon_compatibility = {}
    for sign in ZODIAC_SIGNS:
        sun_moon_compatibility[sign] = {}
    
    # Llenar algunas combinaciones como ejemplo
    sun_moon_compatibility["Aries"]["Cáncer"] = "Dinámica donde el impulso de Aries se equilibra con la sensibilidad de Cáncer, creando una combinación de acción y cuidado."
    sun_moon_compatibility["Leo"]["Libra"] = "Dinámica donde el brillo de Leo se complementa con la armonía de Libra, generando expresión creativa con equilibrio."
    
    # Buscar descripciones de compatibilidad Sol-Luna
    sun1_moon2 = sun_moon_compatibility.get(person1_sun, {}).get(person2_moon)
    if sun1_moon2:
        dynamics["sun_moon"] = f"Compatibilidad Sol-Luna (Sol en {person1_sun} y Luna en {person2_moon}): {sun1_moon2}"
    
    sun2_moon1 = sun_moon_compatibility.get(person2_sun, {}).get(person1_moon)
    if sun2_moon1:
        dynamics["moon_sun"] = f"Compatibilidad Luna-Sol (Luna en {person1_moon} y Sol en {person2_sun}): {sun2_moon1}"
    
    # Analizar dinámica de aspectos
    venus_mars_aspect = None
    sun_moon_aspect = None
    mercury_mercury_aspect = None
    
    for aspect in aspects:
        p1 = aspect.get("person1_planet", aspect.get("planet1", ""))
        p2 = aspect.get("person2_planet", aspect.get("planet2", ""))
        
        # Buscar aspectos específicos importantes
        if (p1 == "venus" and p2 == "mars") or (p1 == "mars" and p2 == "venus"):
            venus_mars_aspect = aspect
        elif (p1 == "sun" and p2 == "moon") or (p1 == "moon" and p2 == "sun"):
            sun_moon_aspect = aspect
        elif p1 == "mercury" and p2 == "mercury":
            mercury_mercury_aspect = aspect
    
    # Añadir interpretaciones de aspectos importantes
    if venus_mars_aspect:
        aspect_type = venus_mars_aspect.get("aspect_type", "")
        if aspect_type in ["conjunción", "trígono", "sextil"]:
            dynamics["attraction"] = "Fuerte química y atracción natural entre ambos, con complementariedad entre energías femeninas y masculinas."
        else:
            dynamics["attraction"] = "Atracción magnética pero con tensión, donde la química puede manifestarse como pasión intensa o desacuerdos."
    
    if sun_moon_aspect:
        aspect_type = sun_moon_aspect.get("aspect_type", "")
        if aspect_type in ["conjunción", "trígono", "sextil"]:
            dynamics["emotional_bond"] = "Fuerte conexión entre identidad y emociones, creando un vínculo de apoyo donde uno ilumina y el otro nutre."
        else:
            dynamics["emotional_bond"] = "Tensión creativa entre consciencia e intuición, que puede generar aprendizaje y crecimiento mutuos."
    
    if mercury_mercury_aspect:
        aspect_type = mercury_mercury_aspect.get("aspect_type", "")
        if aspect_type in ["conjunción", "trígono", "sextil"]:
            dynamics["communication"] = "Excelente comunicación y entendimiento mental, con facilidad para comprender las ideas del otro."
        else:
            dynamics["communication"] = "Desafíos en la comunicación que requieren escucha activa y respeto por diferentes estilos de pensamiento."
    
    # Generar dinámicas específicas según el tipo de compatibilidad
    if compatibility_type == CompatibilityType.ROMANTIC:
        dynamics["intimacy"] = generate_intimacy_dynamic(aspects, person1_venus=None, person2_mars=None)
        dynamics["growth_potential"] = generate_growth_dynamic(aspects, compatibility_type)
    elif compatibility_type == CompatibilityType.PROFESSIONAL:
        dynamics["work_style"] = generate_work_dynamic(aspects, person1_mars=None, person2_saturn=None)
        dynamics["creative_collaboration"] = generate_creative_dynamic(aspects)
    
    return dynamics


def generate_intimacy_dynamic(aspects: List[Dict[str, Any]], 
                            person1_venus: Optional[str] = None, 
                            person2_mars: Optional[str] = None) -> str:
    """
    Genera una descripción de la dinámica de intimidad en la relación.
    
    Args:
        aspects: Lista de aspectos entre las cartas
        person1_venus: Posición de Venus de la primera persona (opcional)
        person2_mars: Posición de Marte de la segunda persona (opcional)
    
    Returns:
        str: Descripción de la dinámica de intimidad
    """
    # Esta función podría ser mucho más compleja, analizando múltiples factores
    # Aquí se presenta una versión simplificada
    
    # Verificar aspectos relevantes para la intimidad
    venus_mars_aspect = None
    venus_pluto_aspect = None
    moon_mars_aspect = None
    
    for aspect in aspects:
        p1 = aspect.get("person1_planet", aspect.get("planet1", ""))
        p2 = aspect.get("person2_planet", aspect.get("planet2", ""))
        
        if (p1 == "venus" and p2 == "mars") or (p1 == "mars" and p2 == "venus"):
            venus_mars_aspect = aspect
        elif (p1 == "venus" and p2 == "pluto") or (p1 == "pluto" and p2 == "venus"):
            venus_pluto_aspect = aspect
        elif (p1 == "moon" and p2 == "mars") or (p1 == "mars" and p2 == "moon"):
            moon_mars_aspect = aspect
    
    # Generar descripción según los aspectos encontrados
    if venus_mars_aspect:
        aspect_type = venus_mars_aspect.get("aspect_type", "")
        if aspect_type in ["conjunción", "trígono", "sextil"]:
            return "La dinámica íntima entre ustedes fluye naturalmente, con buena comprensión de las necesidades mutuas y complementariedad entre dar y recibir afecto."
        else:
            return "La dinámica íntima presenta una tensión magnética que puede manifestarse como pasión intensa o desafíos en sincronizar sus diferentes formas de expresar y recibir afecto."
    elif venus_pluto_aspect:
        return "La dinámica íntima tiene una cualidad intensa y transformadora, con profunda pasión pero también posibles desafíos relacionados con control o posesividad."
    elif moon_mars_aspect:
        return "La dinámica íntima conecta necesidades emocionales con expresión física, creando un vínculo donde la vulnerabilidad y la pasión se entrelazan."
    else:
        return "La dinámica íntima entre ustedes requiere comunicación consciente para comprender las diferentes formas en que cada uno expresa y recibe afecto."


def generate_work_dynamic(aspects: List[Dict[str, Any]],
                        person1_mars: Optional[str] = None,
                        person2_saturn: Optional[str] = None) -> str:
    """
    Genera una descripción de la dinámica de trabajo en la relación.
    
    Args:
        aspects: Lista de aspectos entre las cartas
        person1_mars: Posición de Marte de la primera persona (opcional)
        person2_saturn: Posición de Saturno de la segunda persona (opcional)
    
    Returns:
        str: Descripción de la dinámica de trabajo
    """
    # Verificar aspectos relevantes para el trabajo
    mars_saturn_aspect = None
    mercury_jupiter_aspect = None
    sun_saturn_aspect = None
    
    for aspect in aspects:
        p1 = aspect.get("person1_planet", aspect.get("planet1", ""))
        p2 = aspect.get("person2_planet", aspect.get("planet2", ""))
        
        if (p1 == "mars" and p2 == "saturn") or (p1 == "saturn" and p2 == "mars"):
            mars_saturn_aspect = aspect
        elif (p1 == "mercury" and p2 == "jupiter") or (p1 == "jupiter" and p2 == "mercury"):
            mercury_jupiter_aspect = aspect
        elif (p1 == "sun" and p2 == "saturn") or (p1 == "saturn" and p2 == "sun"):
            sun_saturn_aspect = aspect
    
    # Generar descripción según los aspectos encontrados
    if mars_saturn_aspect:
        aspect_type = mars_saturn_aspect.get("aspect_type", "")
        if aspect_type in ["conjunción", "trígono", "sextil"]:
            return "Su dinámica de trabajo combina energía dirigida con estructura, creando una colaboración donde la iniciativa se canaliza constructivamente hacia metas concretas."
        else:
            return "Su dinámica de trabajo presenta tensión entre acción y restricción, donde uno puede sentir que el otro frena su impulso o es impaciente con su enfoque estructurado."
    elif mercury_jupiter_aspect:
        return "Su dinámica de trabajo integra comunicación efectiva con visión expansiva, facilitando proyectos que requieren tanto atención al detalle como perspectiva amplia."
    elif sun_saturn_aspect:
        return "Su dinámica de trabajo combina liderazgo con disciplina, donde uno aporta dirección y el otro estructura, creando bases sólidas para logros duraderos."
    else:
        return "Su dinámica de trabajo requiere definir claramente roles y responsabilidades, reconociendo sus diferentes estilos de acción y organización."


def generate_growth_dynamic(aspects: List[Dict[str, Any]],
                          compatibility_type: CompatibilityType) -> str:
    """
    Genera una descripción del potencial de crecimiento en la relación.
    
    Args:
        aspects: Lista de aspectos entre las cartas
        compatibility_type: Tipo de compatibilidad
    
    Returns:
        str: Descripción del potencial de crecimiento
    """
    # Verificar aspectos relevantes para el crecimiento
    jupiter_aspects = []
    saturn_aspects = []
    uranus_aspects = []
    
    for aspect in aspects:
        p1 = aspect.get("person1_planet", aspect.get("planet1", ""))
        p2 = aspect.get("person2_planet", aspect.get("planet2", ""))
        
        if p1 == "jupiter" or p2 == "jupiter":
            jupiter_aspects.append(aspect)
        if p1 == "saturn" or p2 == "saturn":
            saturn_aspects.append(aspect)
        if p1 == "uranus" or p2 == "uranus":
            uranus_aspects.append(aspect)
    
    # Generar descripción según los aspectos encontrados
    growth_descriptions = []
    
    if jupiter_aspects:
        favorable_jupiter = any(a.get("aspect_type") in ["conjunción", "trígono", "sextil"] for a in jupiter_aspects)
        if favorable_jupiter:
            growth_descriptions.append("tienen un gran potencial para expandirse y crecer juntos, estimulando mutuamente su optimismo y visión de futuro")
        else:
            growth_descriptions.append("pueden aprender a equilibrar diferentes visiones de crecimiento y expansión")
    
    if saturn_aspects:
        favorable_saturn = any(a.get("aspect_type") in ["conjunción", "trígono", "sextil"] for a in saturn_aspects)
        if favorable_saturn:
            growth_descriptions.append("pueden construir estructuras duraderas y aprender valiosas lecciones de responsabilidad juntos")
        else:
            growth_descriptions.append("tienen la oportunidad de superar limitaciones percibidas y desarrollar mayor madurez")
    
    if uranus_aspects:
        favorable_uranus = any(a.get("aspect_type") in ["conjunción", "trígono", "sextil"] for a in uranus_aspects)
        if favorable_uranus:
            growth_descriptions.append("pueden estimular mutuamente su originalidad y libertad, aportando frescura a la relación")
        else:
            growth_descriptions.append("pueden aprender a integrar el cambio y la estabilidad en su dinámica compartida")
    
    # Construir la descripción final
    if not growth_descriptions:
        if compatibility_type == CompatibilityType.ROMANTIC:
            return "Su potencial de crecimiento como pareja dependerá de su capacidad para comunicarse abiertamente y resolver juntos los desafíos que surjan."
        else:
            return "Su potencial de crecimiento en esta relación dependerá de su disposición para aprender uno del otro y adaptarse a los diferentes estilos y necesidades."
    
    growth_text = ", ".join(growth_descriptions)
    
    if compatibility_type == CompatibilityType.ROMANTIC:
        return f"Como pareja, {growth_text}. Este potencial de evolución compartida es un aspecto importante de su compatibilidad."
    elif compatibility_type == CompatibilityType.PROFESSIONAL:
        return f"En su colaboración profesional, {growth_text}. Este potencial de desarrollo mutuo fortalece su dinámica de trabajo."
    else:
        return f"En su relación, {growth_text}. Este potencial de desarrollo compartido enriquece su vínculo."


def generate_creative_dynamic(aspects: List[Dict[str, Any]]) -> str:
    """
    Genera una descripción de la dinámica creativa en la relación.
    
    Args:
        aspects: Lista de aspectos entre las cartas
    
    Returns:
        str: Descripción de la dinámica creativa
    """
    # Verificar aspectos relevantes para la creatividad
    sun_neptune_aspect = None
    mercury_uranus_aspect = None
    venus_jupiter_aspect = None
    
    for aspect in aspects:
        p1 = aspect.get("person1_planet", aspect.get("planet1", ""))
        p2 = aspect.get("person2_planet", aspect.get("planet2", ""))
        
        if (p1 == "sun" and p2 == "neptune") or (p1 == "neptune" and p2 == "sun"):
            sun_neptune_aspect = aspect
        elif (p1 == "mercury" and p2 == "uranus") or (p1 == "uranus" and p2 == "mercury"):
            mercury_uranus_aspect = aspect
        elif (p1 == "venus" and p2 == "jupiter") or (p1 == "jupiter" and p2 == "venus"):
            venus_jupiter_aspect = aspect
    
    # Generar descripción según los aspectos encontrados
    if sun_neptune_aspect:
        aspect_type = sun_neptune_aspect.get("aspect_type", "")
        if aspect_type in ["conjunción", "trígono", "sextil"]:
            return "Su dinámica creativa combina identidad con inspiración, donde uno ilumina la visión del otro y pueden generar juntos ideas que trascienden lo ordinario."
        else:
            return "Su dinámica creativa presenta tensión entre propósito consciente e idealismo, que puede manifestarse como inspiración desafiante o confusión de dirección."
    elif mercury_uranus_aspect:
        return "Su dinámica creativa integra pensamiento lógico con intuiciones brillantes, generando ideas innovadoras y soluciones originales en su colaboración."
    elif venus_jupiter_aspect:
        return "Su dinámica creativa combina sentido estético con visión expansiva, facilitando proyectos que requieren tanto belleza como significado amplio."
    else:
        return "Su dinámica creativa se beneficiará de combinar conscientemente sus diferentes talentos y perspectivas, respetando sus distintos procesos creativos."


def interpret_compatibility_area(compatibility_calculation: Dict[str, Any], 
                               area: str,
                               compatibility_type: CompatibilityType) -> str:
    """
    Interpreta la compatibilidad en un área específica.
    
    Args:
        compatibility_calculation: Resultado del cálculo de compatibilidad
        area: Área específica a interpretar
        compatibility_type: Tipo de compatibilidad
    
    Returns:
        str: Interpretación del área específica
    """
    # Esta función analizaría los aspectos relevantes para cada área
    # Simplificamos con interpretaciones genéricas para algunas áreas comunes
    
    chart1 = compatibility_calculation.get("chart1", {})
    chart2 = compatibility_calculation.get("chart2", {})
    aspects = compatibility_calculation.get("synastry_aspects", [])
    
    # Filtrar aspectos relevantes para el área específica
    area_planets = {
        "comunicación": ["mercury", "moon", "jupiter", "saturn"],
        "intimidad": ["venus", "mars", "pluto", "moon"],
        "valores": ["venus", "jupiter", "saturn", "sun"],
        "estabilidad": ["saturn", "moon", "sun", "jupiter"],
        "diversión": ["venus", "jupiter", "mars", "uranus"],
        "crecimiento": ["jupiter", "uranus", "saturn", "sun"],
        "trabajo": ["mars", "saturn", "mercury", "sun"],
        "hogar": ["moon", "venus", "saturn", "jupiter"]
    }
    
    # Obtener planetas relevantes para el área
    relevant_planets = area_planets.get(area.lower(), [])
    
    # Filtrar aspectos que involucren estos planetas
    relevant_aspects = []
    for aspect in aspects:
        p1 = aspect.get("person1_planet", aspect.get("planet1", ""))
        p2 = aspect.get("person2_planet", aspect.get("planet2", ""))
        
        if p1 in relevant_planets or p2 in relevant_planets:
            relevant_aspects.append(aspect)
    
    # Contar aspectos favorables y desafiantes
    favorable = 0
    challenging = 0
    
    for aspect in relevant_aspects:
        aspect_type = aspect.get("aspect_type", "")
        
        if aspect_type in ["trígono", "sextil"] or (aspect_type == "conjunción" and aspect.get("nature") == "favorable"):
            favorable += 1
        elif aspect_type in ["cuadratura", "oposición"] or (aspect_type == "conjunción" and aspect.get("nature") == "desafiante"):
            challenging += 1
    
    # Generar interpretación según el balance de aspectos
    strength_level = ""
    if favorable > challenging * 2:
        strength_level = "muy fuerte"
    elif favorable > challenging:
        strength_level = "favorable"
    elif favorable == challenging:
        strength_level = "mixta"
    elif challenging > favorable * 2:
        strength_level = "desafiante"
    else:
        strength_level = "con retos a superar"
    
    # Interpretaciones específicas por área
    interpretations = {
        "comunicación": {
            "muy fuerte": "Su comunicación fluye naturalmente, con excelente entendimiento mutuo y capacidad para expresar ideas y sentimientos. Comparten una base mental compatible que facilita el diálogo constructivo incluso en temas difíciles.",
            "favorable": "Su comunicación es generalmente buena, con facilidad para entenderse en la mayoría de las situaciones. Aunque ocasionalmente pueden tener malentendidos, tienen las herramientas para resolverlos con claridad.",
            "mixta": "Su comunicación presenta tanto facilidades como desafíos. Hay áreas donde se entienden intuitivamente y otras donde deben esforzarse por comprender las perspectivas del otro.",
            "desafiante": "Su comunicación requiere esfuerzo consciente, ya que sus estilos mentales y formas de expresión difieren significativamente. Con práctica y paciencia, pueden desarrollar un lenguaje común.",
            "con retos a superar": "Su comunicación enfrenta algunos obstáculos debido a diferentes formas de procesar información y expresar ideas. El desarrollo de escucha activa será clave para mejorar su entendimiento mutuo."
        },
        "intimidad": {
            "muy fuerte": "Su conexión íntima es profunda y natural, con gran sintonía en la expresión y recepción de afecto. La química entre ustedes facilita una intimidad que nutre a ambos.",
            "favorable": "Su intimidad fluye con relativa facilidad, permitiéndoles conectar a niveles profundos. Aunque hay áreas donde pueden tener diferentes necesidades, logran encontrar un terreno común satisfactorio.",
            "mixta": "Su intimidad presenta tanto momentos de profunda conexión como desafíos para sintonizar completamente. La comunicación abierta sobre necesidades y deseos será clave para profundizar su vínculo.",
            "desafiante": "Su intimidad requiere atención consciente debido a diferentes ritmos y formas de expresión. Con paciencia y apertura, pueden desarrollar un lenguaje íntimo que satisfaga a ambos.",
            "con retos a superar": "Su conexión íntima enfrenta algunos obstáculos relacionados con diferentes expectativas o formas de expresar vulnerabilidad. El respeto por sus diferencias será fundamental."
        },
        "valores": {
            "muy fuerte": "Comparten valores fundamentales que crean una base sólida para su relación. Sus prioridades en la vida son naturalmente compatibles, facilitando decisiones compartidas.",
            "favorable": "Sus sistemas de valores son generalmente complementarios, con suficientes puntos en común para construir acuerdos en áreas importantes. Las diferencias que existen pueden enriquecer su perspectiva.",
            "mixta": "Comparten algunos valores importantes mientras difieren en otros. Esta dinámica puede ser enriquecedora cuando hay respeto mutuo, o desafiante cuando los valores divergentes entran en conflicto.",
            "desafiante": "Sus valores fundamentales difieren en aspectos significativos, lo que requiere negociación consciente y respeto por diferentes prioridades en la vida.",
            "con retos a superar": "Tienen diferentes perspectivas sobre lo que es importante en la vida, lo que puede generar tensiones cuando deben tomar decisiones conjuntas. La comprensión de los orígenes de sus valores será importante."
        },
        "estabilidad": {
            "muy fuerte": "Su relación tiene una base excepcionalmente sólida, con gran capacidad para mantener equilibrio y continuidad incluso en tiempos difíciles. Juntos crean estructuras seguras y confiables.",
            "favorable": "Su dinámica tiende naturalmente hacia la estabilidad, con buena capacidad para construir rutinas y compromisos duraderos. Las ocasionales fluctuaciones se resuelven volviendo a un centro compartido.",
            "mixta": "Su relación combina elementos de estabilidad con períodos de cambio o incertidumbre. Necesitarán trabajar conscientemente para encontrar un equilibrio entre seguridad y adaptabilidad.",
            "desafiante": "La estabilidad en su relación requiere esfuerzo continuo, ya que pueden tener diferentes necesidades de seguridad y cambio. La comunicación clara sobre expectativas será fundamental.",
            "con retos a superar": "Pueden experimentar tensiones entre el deseo de establecer bases firmes y la tendencia a cambios inesperados. Desarrollar flexibilidad dentro de acuerdos claros les ayudará."
        },
        "diversión": {
            "muy fuerte": "Comparten un excelente sentido de diversión y placer, con facilidad para disfrutar juntos y crear momentos de alegría. Su energía lúdica se complementa naturalmente, enriqueciendo su vínculo.",
            "favorable": "Tienen buena capacidad para disfrutar juntos, encontrando actividades placenteras que satisfacen a ambos. Aunque a veces pueden tener diferentes ideas de diversión, generalmente logran encontrar terreno común.",
            "mixta": "Su concepto de diversión y placer tiene tanto puntos en común como diferencias. Esto puede enriquecer su relación cuando ambos están abiertos a nuevas experiencias, o crear distancia si no encuentran actividades compartidas.",
            "desafiante": "Sus ideas de diversión y disfrute difieren considerablemente, lo que puede requerir compromiso y negociación para encontrar actividades que ambos disfruten genuinamente.",
            "con retos a superar": "Tienen distintas formas de buscar placer y entretenimiento, lo que puede crear desconexión si no se comunican abiertamente sobre sus preferencias y buscan activamente puntos de encuentro."
        },
        "crecimiento": {
            "muy fuerte": "Su relación tiene un potencial excepcional para el crecimiento mutuo, donde ambos se inspiran naturalmente a expandirse y evolucionar. Juntos encuentran significado y ampliación de horizontes.",
            "favorable": "Su dinámica fomenta el desarrollo personal de cada uno, con buena capacidad para apoyarse mutuamente en sus caminos de crecimiento. Aunque ocasionalmente pueden tener diferentes ritmos, generalmente avanzan juntos.",
            "mixta": "El crecimiento en su relación presenta tanto oportunidades como desafíos. A veces se impulsan mutuamente y otras pueden sentir que avanzan en direcciones diferentes.",
            "desafiante": "Sus caminos de crecimiento pueden sentirse en tensión, requiriendo esfuerzo consciente para apoyarse mutuamente sin sentir que comprometen su desarrollo individual.",
            "con retos a superar": "Pueden experimentar fricción entre sus diferentes visiones de evolución personal, necesitando encontrar un equilibrio entre autonomía y crecimiento compartido."
        },
        "trabajo": {
            "muy fuerte": "Su dinámica de trabajo conjunto es excepcionalmente productiva y satisfactoria. Complementan sus habilidades naturalmente, con gran capacidad para colaborar eficientemente y lograr objetivos compartidos.",
            "favorable": "Trabajan bien juntos, combinando sus talentos de manera efectiva en la mayoría de situaciones. Aunque ocasionalmente pueden tener diferentes enfoques, generalmente encuentran métodos compatibles.",
            "mixta": "Su colaboración laboral tiene tanto fortalezas como desafíos. En algunas áreas se complementan perfectamente, mientras en otras necesitan ajustar sus diferentes estilos de trabajo.",
            "desafiante": "Trabajar juntos requiere adaptación consciente, ya que sus métodos y prioridades laborales difieren significativamente. Con compromiso mutuo, pueden desarrollar un sistema efectivo de colaboración.",
            "con retos a superar": "Sus estilos de trabajo presentan algunas incompatibilidades que pueden generar fricción. La definición clara de roles y el respeto por diferentes aproximaciones será clave."
        },
        "hogar": {
            "muy fuerte": "Comparten una visión muy compatible de lo que constituye un hogar, con facilidad para crear juntos un espacio nutriente y armonioso. Sus necesidades domésticas se complementan naturalmente.",
            "favorable": "Tienen una buena base para construir un hogar compartido, con valores domésticos generalmente alineados. Aunque pueden tener algunas preferencias diferentes, encuentran soluciones satisfactorias para ambos.",
            "mixta": "Su concepción del hogar tiene tanto puntos en común como diferencias. Esto puede enriquecer su espacio compartido cuando hay comunicación, o crear fricción cuando las expectativas no se expresan claramente.",
            "desafiante": "Sus ideas sobre el hogar y la vida doméstica difieren considerablemente, requiriendo negociación consciente y compromiso para crear un espacio que satisfaga las necesidades básicas de ambos.",
            "con retos a superar": "Pueden experimentar tensión entre sus diferentes necesidades domésticas y preferencias de convivencia. El respeto por el espacio personal dentro del hogar compartido será importante."
        }
    }
    
    # Verificar si existe interpretación específica para esta área
    if area.lower() in interpretations and strength_level in interpretations[area.lower()]:
        area_interp = interpretations[area.lower()][strength_level]
    else:
        # Generar interpretación genérica
        if strength_level == "muy fuerte":
            area_interp = f"Su compatibilidad en el área de {area} es excepcional, con aspectos astrológicos que indican una sintonía natural y fluida."
        elif strength_level == "favorable":
            area_interp = f"Su compatibilidad en el área de {area} es positiva, con aspectos que facilitan el entendimiento y la colaboración."
        elif strength_level == "mixta":
            area_interp = f"Su compatibilidad en el área de {area} presenta tanto fortalezas como desafíos, creando una dinámica de aprendizaje mutuo."
        elif strength_level == "desafiante":
            area_interp = f"Su compatibilidad en el área de {area} presenta desafíos significativos que requerirán comunicación consciente y compromiso."
        else:
            area_interp = f"Su compatibilidad en el área de {area} enfrenta algunos obstáculos que, con esfuerzo mutuo, pueden convertirse en oportunidades de crecimiento."
    
    # Añadir recomendación específica según tipo de compatibilidad
    if compatibility_type == CompatibilityType.ROMANTIC:
        if area.lower() == "comunicación":
            area_interp += "\n\nPara fortalecer su comunicación romántica, establezcan momentos regulares para conectar profundamente sin distracciones, practicando tanto la expresión honesta como la escucha empática."
        elif area.lower() == "intimidad":
            area_interp += "\n\nPara profundizar su intimidad romántica, exploren juntos nuevas formas de expresar afecto y vulnerabilidad, respetando los límites de cada uno y comunicando abiertamente sus necesidades."
        elif area.lower() == "estabilidad":
            area_interp += "\n\nPara fortalecer la estabilidad en su relación romántica, establezcan rituales compartidos y acuerdos claros que les den seguridad, mientras mantienen suficiente flexibilidad para crecer juntos."
        elif area.lower() == "diversión":
            area_interp += "\n\nPara enriquecer el elemento lúdico de su relación, dediquen tiempo regularmente a actividades que ambos disfruten y estén abiertos a experimentar nuevas formas de placer y alegría compartida."
        elif area.lower() == "crecimiento":
            area_interp += "\n\nPara potenciar su crecimiento como pareja, apóyense mutuamente en sus metas individuales mientras cultivan sueños compartidos, celebrando cada logro y aprendiendo juntos de los desafíos."
        elif area.lower() == "valores":
            area_interp += "\n\nPara alinear mejor sus valores en la relación romántica, identifiquen juntos qué es verdaderamente importante para cada uno y busquen crear una visión compartida que honre las prioridades de ambos."
        elif area.lower() == "hogar":
            area_interp += "\n\nPara crear un hogar compartido que nutra su relación, diseñen juntos un espacio que refleje las necesidades y gustos de ambos, estableciendo acuerdos claros sobre las responsabilidades domésticas."
    
    elif compatibility_type == CompatibilityType.PROFESSIONAL:
        if area.lower() == "comunicación":
            area_interp += "\n\nPara optimizar su comunicación profesional, establezcan canales claros y protocolos de intercambio de información, asegurándose de que ambos comprenden las expectativas y plazos del trabajo conjunto."
        elif area.lower() == "valores":
            area_interp += "\n\nPara alinear mejor sus valores profesionales, identifiquen explícitamente las prioridades compartidas del proyecto y establezcan acuerdos claros sobre métodos de trabajo y toma de decisiones."
        elif area.lower() == "trabajo":
            area_interp += "\n\nPara maximizar su eficiencia laboral conjunta, definan claramente roles y responsabilidades que aprovechen las fortalezas de cada uno, estableciendo sistemas para integrar sus diferentes estilos de trabajo."
        elif area.lower() == "crecimiento":
            area_interp += "\n\nPara fomentar el desarrollo profesional mutuo, compartan regularmente conocimientos y habilidades, ofreciéndose feedback constructivo y estableciendo metas compartidas de aprendizaje."
        elif area.lower() == "estabilidad":
            area_interp += "\n\nPara crear un entorno laboral estable, establezcan procesos y sistemas predecibles, mientras mantienen suficiente flexibilidad para adaptarse a nuevos desafíos y oportunidades."
    
    elif compatibility_type == CompatibilityType.FRIENDSHIP:
        if area.lower() == "comunicación":
            area_interp += "\n\nPara nutrir su comunicación amistosa, cultiven conversaciones tanto ligeras como profundas, respetando los momentos en que cada uno necesita expresarse o guardar silencio."
        elif area.lower() == "diversión":
            area_interp += "\n\nPara enriquecer el aspecto lúdico de su amistad, exploren diferentes actividades que les permitan descubrir nuevos intereses compartidos, manteniendo también espacio para sus pasatiempos individuales."
        elif area.lower() == "valores":
            area_interp += "\n\nPara honrar sus valores en la amistad, reconozcan abiertamente sus similitudes y diferencias, utilizando estas últimas como oportunidades para expandir sus perspectivas mutuas."
        elif area.lower() == "crecimiento":
            area_interp += "\n\nPara apoyar su crecimiento mutuo como amigos, celebren los logros del otro sin competitividad y ofrézcanse apoyo honesto durante los desafíos, respetando siempre el camino personal de cada uno."
    
    elif compatibility_type == CompatibilityType.FAMILY:
        if area.lower() == "comunicación":
            area_interp += "\n\nPara fortalecer su comunicación familiar, establezcan espacios seguros para expresar sentimientos y necesidades, practicando la escucha activa y el respeto por diferentes perspectivas generacionales."
        elif area.lower() == "estabilidad":
            area_interp += "\n\nPara cultivar la estabilidad familiar, mantengan tradiciones significativas mientras crean nuevas, estableciendo acuerdos claros sobre responsabilidades compartidas y respeto mutuo."
        elif area.lower() == "hogar":
            area_interp += "\n\nPara crear un ambiente hogareño nutricio, diseñen juntos espacios que honren tanto las necesidades compartidas como las individuales, estableciendo reglas claras pero flexibles de convivencia."
        elif area.lower() == "valores":
            area_interp += "\n\nPara transmitir valores familiares de forma respetuosa, compartan sus tradiciones y creencias como invitaciones, no como imposiciones, manteniendo apertura al diálogo y diferentes perspectivas."
    
    # Para cualquier tipo de compatibilidad, agregar recomendación genérica si no hay una específica
    if "\n\nPara " not in area_interp:
        area_interp += f"\n\nPara fortalecer su compatibilidad en el área de {area}, mantengan una comunicación abierta sobre sus necesidades y expectativas, celebrando sus similitudes y aprendiendo de sus diferencias."
    
    return area_interp
    