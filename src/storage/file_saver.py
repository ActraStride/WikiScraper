# src/storage/file_saver.py

"""
Módulo profesional para almacenamiento seguro de contenido scrapeado con manejo de errores,
control de encoding y gestión automática de directorios.
"""

import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Final
from urllib.parse import quote

# Constantes
DEFAULT_OUTPUT_DIR: Final[str] = "data"
VALID_ENCODINGS: Final[tuple] = ('utf-8', 'latin-1', 'iso-8859-1')
MAX_FILENAME_LENGTH: Final[int] = 255
SAFE_FILENAME_PATTERN: Final[str] = r"[^A-Za-z0-9_\-\.]"

logger = logging.getLogger(__name__)

class StorageError(Exception):
    """Excepción base para errores de almacenamiento."""
    pass

class DirectoryCreationError(StorageError):
    """Error durante la creación de directorios."""
    pass

class FileWriteError(StorageError):
    """Error durante la escritura del archivo."""
    pass

class InvalidFilenameError(StorageError):
    """Nombre de archivo inválido o inseguro."""
    pass

class FileSaver:
    """
    Clase para almacenamiento seguro de contenido textual con gestión automática de directorios
    y generación de nombres de archivo.
    
    Atributos:
        output_dir (Path): Directorio base de almacenamiento
        encoding (str): Codificación de archivos (default: 'utf-8')
        timestamp_format (str): Formato para timestamps en nombres de archivo
        
    Métodos:
        save(content: str, title: Optional[str] = None) -> Path
        generate_filename(title: Optional[str] = None) -> str
        sanitize_filename(filename: str) -> str
    """
    
    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        encoding: str = 'utf-8',
        timestamp_format: str = "%Y%m%d_%H%M%S"
    ) -> None:
        """
        Inicializa el FileSaver con configuración personalizable.
        
        Args:
            output_dir: Directorio base para almacenamiento
            encoding: Codificación de texto para los archivos
            timestamp_format: Formato strftime para nombres de archivo
            
        Raises:
            DirectoryCreationError: Si no se puede crear el directorio
            ValueError: Si la codificación no es soportada
        """
        self.output_dir = Path(output_dir)
        self.timestamp_format = timestamp_format
        
        if encoding.lower() not in VALID_ENCODINGS:
            raise ValueError(f"Codificación no soportada: {encoding}. Usar: {', '.join(VALID_ENCODINGS)}")
        self.encoding = encoding.lower()
        
        self._setup_storage()
        
    def _setup_storage(self) -> None:
        """Crea el directorio de salida con verificación de permisos."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de almacenamiento listo: {self.output_dir}")
        except PermissionError as e:
            logger.critical(f"Permisos denegados para: {self.output_dir}")
            raise DirectoryCreationError(f"Error de permisos: {e}") from e
        except OSError as e:
            logger.critical(f"Error creando directorio: {e}")
            raise DirectoryCreationError(f"Error de sistema: {e}") from e
            
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitiza nombres de archivo removiendo caracteres peligrosos y limitando longitud.
        
        Args:
            filename: Nombre de archivo original
            
        Returns:
            str: Nombre sanitizado y seguro
            
        Raises:
            InvalidFilenameError: Si el nombre resultante está vacío
        """
        # Remover caracteres inseguros
        clean_name = re.sub(SAFE_FILENAME_PATTERN, "_", filename)
        
        # Limitar longitud y remover espacios
        clean_name = clean_name.strip().replace(" ", "_")[:MAX_FILENAME_LENGTH]
        
        if not clean_name:
            raise InvalidFilenameError("Nombre de archivo no válido después de sanitización")
            
        return clean_name
    
    def generate_filename(self, title: Optional[str] = None) -> str:
        """
        Genera un nombre de archivo único basado en título y timestamp.
        
        Args:
            title: Título opcional para incluir en el nombre
            
        Returns:
            str: Nombre de archivo válido
        """
        timestamp = datetime.now().strftime(self.timestamp_format)
        
        if title:
            try:
                safe_title = self.sanitize_filename(quote(title))
                return f"{timestamp}_{safe_title}.txt"
            except InvalidFilenameError:
                logger.warning("Título no válido, usando nombre generado")
                
        return f"{timestamp}_wikipedia_content.txt"
    
    def save(self, content: str, title: Optional[str] = None) -> Path:
        """
        Almacena el contenido en un archivo de texto con encoding adecuado.
        
        Args:
            content: Contenido textual a guardar
            title: Título opcional para el nombre de archivo
            
        Returns:
            Path: Ruta completa del archivo guardado
            
        Raises:
            FileWriteError: Si falla la escritura del archivo
        """
        filename = self.generate_filename(title)
        file_path = self.output_dir / filename
        
        try:
            with open(file_path, "w", encoding=self.encoding, errors="replace") as f:
                f.write(content)
                
            logger.info(f"Archivo guardado exitosamente: {file_path}")
            self._post_save_validation(file_path, content)
            return file_path
            
        except IOError as e:
            logger.error(f"Error escribiendo archivo: {e}", exc_info=True)
            raise FileWriteError(f"Error de E/S: {e}") from e
        except UnicodeEncodeError as e:
            logger.error(f"Error de encoding: {e}", exc_info=True)
            raise FileWriteError(f"Problema de codificación: {e}") from e
            
    def _post_save_validation(self, file_path: Path, original_content: str) -> None:
        """Verificación de integridad del archivo guardado."""
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                saved_content = f.read()
                
            if saved_content != original_content:
                logger.warning("Discrepancia en contenido guardado. Posible corrupción de datos.")
                
        except IOError as e:
            logger.error(f"Error validando archivo: {e}")

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass  # Puede implementarse limpieza de recursos si es necesario

    def __repr__(self) -> str:
        return (f"FileSaver(output_dir={self.output_dir}, "
                f"encoding={self.encoding}, "
                f"timestamp_format={self.timestamp_format})")