"""
Wikipedia Scraping Exceptions

Este módulo define excepciones ocurridas durante operaciones de scraping en Wikipedia.
"""
from .core import ApplicationError

class WikiScraperError(ApplicationError):
    """Clase base para excepciones durante el scraping de Wikipedia."""
    pass

class InvalidPageTitleError(WikiScraperError):
    """Se lanza cuando se proporciona un título de página inválido o vacío."""
    pass

class ParsingError(WikiScraperError):
    """Se lanza cuando falla el análisis del contenido HTML debido a una estructura malformada."""
    pass

class LanguageNotSupportedError(WikiScraperError):
    """Se lanza cuando se intenta usar un código de idioma no soportado."""
    pass

class NonHTMLContentError(WikiScraperError):
    """Se lanza cuando el contenido recibido no está en formato HTML."""
    pass

class SearchError(WikiScraperError):
    """Clase base para excepciones ocurridas durante búsquedas en Wikipedia."""
    pass

class NoSearchResultsError(SearchError):
    """Se lanza cuando una consulta de búsqueda no arroja resultados válidos."""
    pass

__all__ = [
    "WikiScraperError",
    "InvalidPageTitleError",
    "ParsingError",
    "LanguageNotSupportedError",
    "NonHTMLContentError",
    "SearchError",
    "NoSearchResultsError"
]
