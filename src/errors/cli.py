"""
Command-line Interface Exceptions

Este módulo define excepciones relacionadas con operaciones de la interfaz de línea de comandos.
"""
from .core import ApplicationError

class CLIError(ApplicationError):
    """Clase base para excepciones en operaciones de la CLI."""
    pass

__all__ = ["CLIError"]
