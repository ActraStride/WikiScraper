"""
GraphManager Exceptions

Este módulo define excepciones relacionadas con las operaciones del GraphManager.
"""
from .core import ApplicationError

class GraphManagerError(ApplicationError):
    """Clase base para errores del GraphManager."""
    pass

class InvalidTitleError(GraphManagerError):
    """Se lanza cuando un título es inválido (por ejemplo, None o vacío)."""
    pass

class NodeError(GraphManagerError):
    """Se lanza cuando ocurre un problema con las operaciones de nodos."""
    pass

class RelationshipError(GraphManagerError):
    """Se lanza cuando ocurre un problema con las operaciones de relaciones."""
    pass

class GraphCreationError(GraphManagerError):
    """Se lanza cuando ocurre un problema al crear el grafo."""
    pass

__all__ = [
    "GraphManagerError",
    "InvalidTitleError",
    "NodeError",
    "RelationshipError",
    "GraphCreationError"
]
