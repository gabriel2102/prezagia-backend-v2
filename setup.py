"""
Script para configurar el entorno de desarrollo de Prezagia en Windows
"""

import os
import shutil
import subprocess
import sys

def check_docker_installed():
    """Verifica si Docker está instalado"""
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE)
        subprocess.run(["docker-compose", "--version"], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def create_directories():
    """Crea los directorios necesarios"""
    os.makedirs("data/skyfield", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("✓ Directorios creados correctamente")

def setup_env_file():
    """Configura el archivo .env"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✓ Archivo .env creado a partir de .env.example")
            print("  Por favor, edita el archivo .env con tus configuraciones")
        else:
            print("✗ No se encontró el archivo .env.example")
    else:
        print("✓ El archivo .env ya existe")

def setup_docker():
    """Configura y levanta los contenedores Docker"""
    if not check_docker_installed():
        print("✗ ERROR: Docker y/o Docker Compose no están instalados")
        print("  Por favor, instala Docker Desktop antes de continuar")
        return False
    
    print("✓ Docker y Docker Compose están instalados")
    
    try:
        print("Construyendo y levantando contenedores Docker...")
        subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error al levantar Docker: {e}")
        return False

def main():
    """Función principal"""
    print("=== Configuración del entorno de desarrollo de Prezagia ===\n")
    
    create_directories()
    setup_env_file()
    
    if setup_docker():
        print("\n=================================================")
        print("✓ Entorno Docker configurado correctamente")
        print("  La API está disponible en: http://localhost:8000")
        print("  Documentación de la API: http://localhost:8000/docs")
        print("=================================================")
    else:
        print("\n✗ No se pudo configurar completamente el entorno Docker")
        print("  Revisa los errores anteriores e intenta de nuevo")

if __name__ == "__main__":
    main()