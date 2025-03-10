# app/utils/log_utils.py
import os
import re
import shutil
import gzip
from datetime import datetime, timedelta
import logging
from pathlib import Path
from collections import Counter, defaultdict

from app.core.config import settings


def archive_old_logs(days_to_keep=30):
    """
    Archiva (comprime) los archivos de log más antiguos que el número de días especificado.
    
    Args:
        days_to_keep (int): Número de días para mantener los logs sin comprimir
    """
    log_dir = Path(settings.LOGS_DIR)
    if not log_dir.exists():
        return
    
    # Calcular la fecha límite
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # Patrón para archivos de log: prezagia_YYYY-MM-DD.log
    log_pattern = re.compile(r'prezagia_(\d{4}-\d{2}-\d{2})\.log')
    
    # Buscar todos los archivos de log
    for log_file in log_dir.glob('prezagia_*.log'):
        match = log_pattern.match(log_file.name)
        if not match:
            continue
        
        # Extraer la fecha del nombre del archivo
        log_date_str = match.group(1)
        try:
            log_date = datetime.strptime(log_date_str, '%Y-%m-%d')
            
            # Si el archivo es más antiguo que la fecha límite, comprimirlo
            if log_date < cutoff_date:
                compressed_file = log_file.with_suffix('.log.gz')
                
                # Si ya existe un archivo comprimido, omitirlo
                if compressed_file.exists():
                    continue
                
                # Comprimir el archivo
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Si la compresión fue exitosa, eliminar el original
                if compressed_file.exists():
                    os.remove(log_file)
                    logging.info(f"Archivo de log comprimido: {log_file.name} -> {compressed_file.name}")
        
        except ValueError:
            # Si hay un error al parsear la fecha, ignorar el archivo
            continue


def delete_old_archives(days_to_keep=180):
    """
    Elimina archivos de log comprimidos más antiguos que el número de días especificado.
    
    Args:
        days_to_keep (int): Número de días para mantener los logs comprimidos
    """
    log_dir = Path(settings.LOGS_DIR)
    if not log_dir.exists():
        return
    
    # Calcular la fecha límite
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # Patrón para archivos de log comprimidos: prezagia_YYYY-MM-DD.log.gz
    log_pattern = re.compile(r'prezagia_(\d{4}-\d{2}-\d{2})\.log\.gz')
    
    # Buscar todos los archivos de log comprimidos
    for log_file in log_dir.glob('prezagia_*.log.gz'):
        match = log_pattern.match(log_file.name)
        if not match:
            continue
        
        # Extraer la fecha del nombre del archivo
        log_date_str = match.group(1)
        try:
            log_date = datetime.strptime(log_date_str, '%Y-%m-%d')
            
            # Si el archivo es más antiguo que la fecha límite, eliminarlo
            if log_date < cutoff_date:
                os.remove(log_file)
                logging.info(f"Archivo de log antiguo eliminado: {log_file.name}")
        
        except ValueError:
            # Si hay un error al parsear la fecha, ignorar el archivo
            continue


def analyze_logs(log_file=None, days=7):
    """
    Analiza los logs para obtener estadísticas de uso y errores.
    
    Args:
        log_file (str, opcional): Archivo específico a analizar. Si es None, analiza todos los archivos de los últimos 'days' días.
        days (int): Número de días hacia atrás para analizar (si log_file es None)
    
    Returns:
        dict: Estadísticas de los logs
    """
    stats = {
        'total_requests': 0,
        'errors': 0,
        'warnings': 0,
        'endpoint_counts': Counter(),
        'status_codes': Counter(),
        'error_messages': Counter(),
        'slow_requests': [],  # Solicitudes que tomaron más de 1 segundo
        'requests_by_day': defaultdict(int),
        'average_response_time': 0,
    }
    
    log_dir = Path(settings.LOGS_DIR)
    if not log_dir.exists():
        return stats
    
    # Patrón para solicitudes HTTP
    request_pattern = re.compile(r'Solicitud .+ completada: (\w+) (.+) - Estado: (\d+) - Tiempo: (\d+\.\d+)s')
    
    # Patrón para errores
    error_pattern = re.compile(r'ERROR - \[.+\] - (.+)')
    
    # Patrón para warnings
    warning_pattern = re.compile(r'WARNING - \[.+\] - (.+)')
    
    # Patrones de fecha en el log
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2}')
    
    # Lista de archivos a analizar
    log_files = []
    
    if log_file:
        # Analizar un archivo específico
        file_path = log_dir / log_file
        if file_path.exists():
            log_files.append(file_path)
    else:
        # Analizar archivos de los últimos 'days' días
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Archivos no comprimidos
        for log_file in log_dir.glob('prezagia_*.log'):
            try:
                date_str = log_file.name.split('_')[1].split('.')[0]
                log_date = datetime.strptime(date_str, '%Y-%m-%d')
                if log_date >= cutoff_date:
                    log_files.append(log_file)
            except (ValueError, IndexError):
                continue
    
    if not log_files:
        return stats
    
    total_response_time = 0
    response_count = 0
    
    # Analizar cada archivo
    for log_file in log_files:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Extraer fecha de la línea para estadísticas diarias
                date_match = date_pattern.search(line)
                if date_match:
                    day = date_match.group(1)
                
                # Analizar solicitudes HTTP completadas
                req_match = request_pattern.search(line)
                if req_match:
                    method, endpoint, status, response_time = req_match.groups()
                    stats['total_requests'] += 1
                    stats['endpoint_counts'][f"{method} {endpoint}"] += 1
                    stats['status_codes'][status] += 1
                    stats['requests_by_day'][day] += 1
                    
                    # Convertir tiempo de respuesta a float
                    try:
                        response_time_float = float(response_time)
                        total_response_time += response_time_float
                        response_count += 1
                        
                        # Registrar solicitudes lentas (> 1 segundo)
                        if response_time_float > 1.0:
                            stats['slow_requests'].append({
                                'method': method,
                                'endpoint': endpoint,
                                'status': status,
                                'time': response_time_float,
                                'date': day
                            })
                    except ValueError:
                        pass
                
                # Analizar errores
                error_match = error_pattern.search(line)
                if error_match:
                    stats['errors'] += 1
                    error_msg = error_match.group(1)
                    # Truncar mensajes muy largos para las estadísticas
                    if len(error_msg) > 100:
                        error_msg = error_msg[:100] + "..."
                    stats['error_messages'][error_msg] += 1
                
                # Analizar advertencias
                warning_match = warning_pattern.search(line)
                if warning_match:
                    stats['warnings'] += 1
    
    # Calcular tiempo de respuesta promedio
    if response_count > 0:
        stats['average_response_time'] = round(total_response_time / response_count, 4)
    
    # Ordenar solicitudes lentas por tiempo (descendente)
    stats['slow_requests'].sort(key=lambda x: x['time'], reverse=True)
    
    # Limitar a las 10 solicitudes más lentas
    stats['slow_requests'] = stats['slow_requests'][:10]
    
    return stats


def cleanup_logs():
    """
    Limpia y organiza los archivos de log.
    - Archiva logs antiguos
    - Elimina archivos muy antiguos
    """
    # Archivar logs más antiguos que 30 días
    archive_old_logs(days_to_keep=30)
    
    # Eliminar archivos comprimidos más antiguos que 180 días (6 meses)