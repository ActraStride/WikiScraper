from .wikiscraper import WikiScraper
from .wikiscraper import WikiScraperError
from .wikiscraper import LanguageNotSupportedError


# Exporta las funciones y clases que quieres que estén disponibles al importar utils
__all__ = ["WikiScraper", "WikiScraperError", "LanguageNotSupportedError"]
