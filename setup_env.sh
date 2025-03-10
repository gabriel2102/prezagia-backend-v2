#!/bin/bash

# Script para configurar el entorno de desarrollo de Prezagia

# Crear directorios necesarios
mkdir -p data/skyfield logs

# Verificar si existe el archivo .env
if [ ! -f .env ]; then
    echo "Creando archivo .env a partir de .env.example..."
    cp .env.example .env
    echo "Por favor, edita el archivo .env con tus configuraciones"
else
    echo "El archivo .env ya existe"
fi

# Comprobar si Docker está instalado
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "Docker y Docker Compose están instalados"
    
    # Construir y levantar contenedores
    echo "Construyendo y levantando contenedores Docker..."
    docker-compose up -d --build
    
    echo "===================================================="
    echo "Entorno Docker configurado correctamente"
    echo "La API está disponible en: http://localhost:8000"
    echo "Documentación de la API: http://localhost:8000/docs"
    echo "===================================================="
else
    echo "ERROR: Docker y/o Docker Compose no están instalados"
    echo "Por favor, instala Docker antes de continuar"
    exit 1
fi