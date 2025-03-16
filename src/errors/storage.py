"""
Storage Operation Exceptions

Este módulo define excepciones relacionadas con operaciones de almacenamiento.
"""
from .core import ApplicationError

class StorageError(ApplicationError):
    """Clase base para excepciones relacionadas con el almacenamiento."""
    pass

class DirectoryCreationError(StorageError):
    """Se lanza cuando no se puede crear un directorio por problemas del sistema de archivos."""
    pass

class FileWriteError(StorageError):
    """Se lanza cuando falla la escritura de un archivo debido a errores de I/O o permisos."""
    pass

class InvalidFilenameError(StorageError):
    """Se lanza cuando un nombre de archivo contiene caracteres inválidos o representa un riesgo de seguridad."""
    pass

__all__ = [
    "StorageError",
    "DirectoryCreationError",
    "FileWriteError",
    "InvalidFilenameError"
]
