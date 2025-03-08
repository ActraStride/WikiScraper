"""
Module Name: wiki_service

Service layer for interacting with Wikipedia data, abstracting the core logic
from the user interface (CLI, API, etc.).

This module provides a centralized service to:
- Perform searches on Wikipedia
- Retrieve page content (raw text)
- Map internal links within Wikipedia pages
- Handle service-specific errors robustly
- Provide structured logging of service operations

Example (Simplified - Focuses on module usage):
    >>> from src.service.wiki_service import WikiService, SearchServiceError
    >>> from src.wikiscraper import WikiScraper
    >>> from src.storage import FileSaver
    >>> import logging
    >>> logger = logging.getLogger(__name__) # Or your configured logger
    >>> # Assume scraper and file_saver are already initialized and configured elsewhere
    >>> # For example (you would typically configure logger and other params):
    >>> # logger = setup_logging()
    >>> scraper = WikiScraper(language="es", timeout=10, logger=logger)
    >>> file_saver = FileSaver(output_dir="./output", logger=logger)
    >>> service = WikiService(scraper=scraper, file_saver=file_saver, logger=logger)
    >>> try:
    >>>     search_results = service.search_articles(query="Python programación")
    >>>     if search_results:
    >>>         print(f"Search results: {search_results}")
    >>>     else:
    >>>         print("No articles found for the query.")
    >>> except SearchServiceError as e:
    >>>     print(f"Search failed: {e}")
"""

import logging
from typing import List, Dict, Set

from src.wikiscraper import WikiScraper, WikiScraperError  # Importa todos los errores relevantes de WikiScraper
from src.storage import FileSaver # Importa también los errores de FileSaver si se van a usar directamente en el Service
from src.service.models import SearchResult, SearchResults
from pathlib import Path # Import pathlib for cleaner path handling in example


class WikiServiceError(Exception):
    """Excepción base para errores generales del servicio WikiService."""
    pass


class SearchServiceError(WikiServiceError):
    """Excepción para errores específicos durante la operación de búsqueda en el servicio."""
    pass


class PageContentServiceError(WikiServiceError):
    """Excepción para errores al obtener contenido de una página."""
    pass

class PageMappingServiceError(WikiServiceError):
    """Excepción para errores durante el mapeo de enlaces de páginas."""
    pass

class WikiService:
    """
    Servicio centralizado para interactuar con Wikipedia, abstrayendo la lógica de negocio
    y proporcionando una interfaz limpia para operaciones relacionadas con Wikipedia.

    Este servicio utiliza `WikiScraper` para acceder a la información de Wikipedia
    y `FileSaver` para las operaciones de guardado si son necesarias.  Está diseñado
    para desacoplar la lógica de la CLI, API, o cualquier otra interfaz de usuario
    de la funcionalidad central de scraping y procesamiento de datos de Wikipedia.
    """

    def __init__(self, scraper: WikiScraper, file_saver: FileSaver, logger: logging.Logger) -> None:
        """
        Inicializa el servicio WikiService con sus dependencias.

        Args:
            scraper (WikiScraper): Instancia de WikiScraper previamente configurada e inicializada.
                                   Responsable de realizar las peticiones y extraer datos de Wikipedia.
            file_saver (FileSaver): Instancia de FileSaver previamente configurada e inicializada.
                                    Responsable de guardar contenido en el sistema de archivos, si es necesario.
            logger (logging.Logger):  Instancia de logger ya configurada para el sistema.
                                     Se utiliza para registrar eventos, errores y depuración dentro del servicio.
        """
        self.scraper = scraper
        self.file_saver = file_saver  # Guarda el FileSaver si el servicio lo necesita para alguna operación
        self.logger = logger
        self.logger.debug("Servicio WikiService inicializado correctamente.")


    def search_articles(self, query: str, limit: int = 5) -> SearchResults:
        """
        Busca artículos en Wikipedia que coincidan con el término de búsqueda dado.

        Args:
            query (str): Término de búsqueda para buscar en Wikipedia.
            limit (int, optional): Número máximo de resultados a retornar. Por defecto es 5.

        Returns:
            List[str]: Una lista de títulos de artículos de Wikipedia que coinciden con la búsqueda.
                       Retorna una lista vacía si no se encuentran resultados.

        Raises:
            SearchServiceError: Si ocurre cualquier error durante la búsqueda en Wikipedia.
                               Encapsula excepciones de nivel inferior como `WikiScraperError`.
        """
        self.logger.info(f"Iniciando búsqueda de artículos para: '{query}' (límite: {limit} resultados).")
        try:
            results_titles: List[str] = self.scraper.search_wikipedia(query=query, limit=limit)
            if not results_titles:
                self.logger.warning(f"No se encontraron artículos para la búsqueda: '{query}'.")
                return SearchResults(results=[])  # Retorna SearchResults vacío
            search_results_list: List[SearchResult] = [SearchResult(title=title) for title in results_titles] # Crea objetos SearchResult
            search_results = SearchResults(results=search_results_list) # Encapsula en SearchResults
            self.logger.debug(f"Búsqueda para '{query}' completada, se encontraron {len(search_results)} artículos.")
            return search_results
        except WikiScraperError as e:  # Captura errores específicos del scraper
            self.logger.error(f"Error al buscar artículos para '{query}': {e}", exc_info=True)
            raise SearchServiceError(f"Error durante la búsqueda de artículos: {e}") from e  # Relanza con excepción de servicio
        except Exception as e:  # Captura cualquier otro error inesperado
            self.logger.critical(f"Error INESPERADO durante la búsqueda de artículos para '{query}': {e}", exc_info=True)
            raise SearchServiceError(f"Error inesperado en la búsqueda de artículos: {e}") from e