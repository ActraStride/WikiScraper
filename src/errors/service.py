"""
Wikipedia Service Exceptions

Este módulo define excepciones ocurridas en las operaciones de servicio de Wikipedia.
"""
from .core import ApplicationError

class WikiServiceError(ApplicationError):
    """Clase base para excepciones en operaciones de servicio de Wikipedia."""
    pass

class SearchServiceError(WikiServiceError):
    """Se lanza cuando falla inesperadamente una operación del servicio de búsqueda."""
    pass

class PageContentServiceError(WikiServiceError):
    """Se lanza cuando la recuperación del contenido de una página falla por errores del servicio."""
    pass

class PageMappingServiceError(WikiServiceError):
    """Se lanza cuando falla el mapeo de enlaces de la página debido a problemas de análisis."""
    pass

__all__ = [
    "WikiServiceError",
    "SearchServiceError",
    "PageContentServiceError",
    "PageMappingServiceError"
]
