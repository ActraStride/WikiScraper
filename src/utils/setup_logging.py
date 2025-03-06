# app/utils/setup_logging.py

"""
Módulo de configuración avanzada de logging para aplicaciones Python.

Provee:
- Configuración centralizada de logging
- Rotación de archivos de log
- Configuración segura de directorios
- Manejo robusto de errores
- Formato consistente con zona horaria UTC
"""
import logging.config
import time
import sys
from pathlib import Path
from typing import Final
from logging.handlers import RotatingFileHandler

# Constantes inmutables (type hinted)
LOG_DIR_NAME: Final[str] = "logs"
LOG_FILE_NAME: Final[str] = "application.log"
LOG_FORMAT: Final[str] = (
    "%(asctime)s.%(msecs)03d [%(levelname)-8s] "
    "%(name)s:%(funcName)s:%(lineno)d - %(message)s"
)
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S%z"
LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: Final[int] = 5
LOG_ENCODING: Final[str] = "utf-8"

class LoggingSetupError(Exception):
    """Excepción personalizada para errores de configuración de logging."""
    pass

def get_log_dir(project_root: Path = None) -> Path:
    """
    Determina y crea el directorio de logs de manera segura.
    
    Args:
        project_root: Ruta raíz opcional del proyecto
        
    Returns:
        Path: Ruta absoluta al directorio de logs
        
    Raises:
        LoggingSetupError: Si no se puede crear el directorio
    """
    try:
        if project_root is None:
            # Asume que este archivo está en proyecto_root/app/utils
            project_root = Path(__file__).resolve().parent.parent.parent
            
        log_dir = project_root / LOG_DIR_NAME
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    except (PermissionError, FileExistsError, OSError) as e:
        raise LoggingSetupError(
            f"No se pudo crear el directorio de logs: {e}"
        ) from e

def get_logging_config(log_file_path: Path, log_level: str) -> dict:
    """
    Genera configuración de logging dinámica con type hints y validación.
    
    Args:
        log_file_path: Ruta completa al archivo de log
        log_level: Nivel de descripción en el log
        
    Returns:
        dict: Configuración de logging compatible con dictConfig
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": LOG_FORMAT,
                "datefmt": LOG_DATE_FORMAT,
                "validate": True,
            }
        },
        "handlers": {
            "rotating_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": str(log_file_path),
                "encoding": LOG_ENCODING,
                "maxBytes": LOG_MAX_BYTES,
                "backupCount": LOG_BACKUP_COUNT,
                "delay": True,  # Retrasa la apertura del archivo hasta el primer uso
            },
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            # Logger raíz configura todos los módulos
            "": {
                "handlers": ["rotating_file"],
                "level": log_level,
                "propagate": False,
            },
            # Configuración específica para dependencias ruidosas
            "urllib3": {
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

def setup_logging(log_level: str, project_root: Path = None) -> None:
    """
    Configura el sistema de logging de la aplicación.
    
    Args:
        project_root: Ruta al directorio raíz del proyecto (default: None)
        log_level: Nivel de descripción en el log
    
    Raises:
        LoggingSetupError: Si la configuración falla
    """
    try:
        # Obtener directorio de logs
        log_dir = get_log_dir(project_root)
        log_file = log_dir / LOG_FILE_NAME
        
        # Configurar logging
        config = get_logging_config(log_file, log_level)
        logging.config.dictConfig(config)
        
        # Configurar UTC para tiempos de registro
        logging.Formatter.converter = time.localtime  # Si quieres la hora local

        
        # Registrar éxito
        logger = logging.getLogger(__name__)
        logger.info(
            "Logging configurado correctamente. Archivo: %s", log_file
        )
        
    except Exception as e:
        raise LoggingSetupError(
            f"Error configurando el sistema de logging: {e}"
        ) from e

# Uso recomendado:
# if __name__ == "__main__":
#     setup_logging()