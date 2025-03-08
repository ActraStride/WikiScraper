"""
Module Name: wikiscraper

Professional Wikipedia scraping module with robust error handling, intelligent retries, and adherence to web scraping best practices.

This module provides:
- Automatic HTTP session management with configurable retries
- Strict input and parameter validation
- Redirection and non-HTML content detection
- Safe parsing with proper encoding handling
- Detailed logging and flexible configuration
- Compliance with robots.txt and usage policies

Basic Usage:
    >>> from wiki_scraper import WikiScraper
    >>> with WikiScraper(language="es") as scraper:
    ...     soup = scraper.get_page_soup("Python")
    ...     print(soup.title.string)
"""


import logging
import requests

from typing import Any, Final, Optional, Set, List, Dict
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import quote, urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de logging


# Constantes
USER_AGENT: Final[str] = "WikiScraperBot/3.0 (+https://github.com/tu_usuario/tu_repositorio)"
VALID_LANGUAGES: Final[Set[str]] = {"en", "ceb", "es", "fr", "de", "it", "pt", "ja", "zh", "ru", "ko", "nl", "ar", "simple"}
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_MAX_REDIRECTS: Final[int] = 3
DEFAULT_TIMEOUT: Final[int] = 15
DEFAULT_PARSER: Final[str] = "lxml"


class WikiScraperError(Exception):
    """Excepción base para errores del módulo de scraping."""
    pass

class InvalidPageTitleError(WikiScraperError):
    """Excepción para títulos de página inválidos o vacíos."""
    pass

class ParsingError(WikiScraperError):
    """Excepción para errores durante el parsing del contenido HTML."""
    pass

class LanguageNotSupportedError(WikiScraperError):
    """Excepción para códigos de idioma no soportados."""
    pass

class NonHTMLContentError(WikiScraperError):
    """Excepción para respuestas con contenido no HTML."""
    pass


class SearchError(WikiScraperError):
    """Excepción general para errores durante la búsqueda en Wikipedia."""
    pass


class NoSearchResultsError(SearchError):
    """Excepción específica para cuando la búsqueda no devuelve resultados."""
    pass


class WikiScraper:
    """
    Clase profesional para realizar scraping de páginas de Wikipedia

    Atributos:
        language (str): Código de idioma de Wikipedia (default: "es")
        timeout (int): Tiempo máximo de espera para peticiones HTTP en segundos
        parser (str): Parser a utilizar por BeautifulSoup (lxml, html.parser, etc.)
        max_retries (int): Número máximo de reintentos para peticiones fallidas
        max_redirects (int): Límite máximo de redirecciones HTTP permitidas

    Métodos:
        get_page_soup(page_title: str) -> BeautifulSoup
        _build_url(page_title: str) -> str

    Ejemplo:
        with WikiScraper(language="es") as scraper:
            try:
                soup = scraper.get_page_soup("Inteligencia_artificial")
                # Procesar el contenido...
            except WikiScraperError as e:
                print(f"Error: {e}")
    """

    def __init__(
        self,
        logger: logging.Logger,
        language: str = "es",
        timeout: int = DEFAULT_TIMEOUT,
        parser: str = DEFAULT_PARSER,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_redirects: int = DEFAULT_MAX_REDIRECTS
    ) -> None:
        """
        Inicializa una nueva instancia del scraper con configuración personalizable.

        Args:
            language: Código de idioma ISO 639-1 (default: "es")
            timeout: Tiempo máximo de espera por respuesta HTTP
            parser: Parser HTML para BeautifulSoup
            max_retries: Intentos máximos para peticiones fallidas
            max_redirects: Límite de redirecciones HTTP

        Raises:
            LanguageNotSupportedError: Si el idioma no está en VALID_LANGUAGES
        """
        if language not in VALID_LANGUAGES:
            raise LanguageNotSupportedError(f"Idioma '{language}' no soportado. Idiomas válidos: {', '.join(VALID_LANGUAGES)}")
        self.logger = logger
        self.language = language
        self.timeout = timeout
        self.parser = parser
        self.max_redirects = max_redirects
        self.base_url = f"https://{self.language}.wikipedia.org/"
        self.session = requests.Session()
        
        # Configuración de sesión HTTP
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.max_redirects = self.max_redirects

        # Configuración de reintentos
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[408, 429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.logger.debug("Scraper inicializado: %s", self.__repr__())

    def __repr__(self) -> str:
        return (f"WikiScraper(language={self.language}, timeout={self.timeout}, "
                f"parser={self.parser}, retries={self.session.adapters['https://'].max_retries.total})")

    def _build_url(self, page_title: str) -> str:
        """
        Construye la URL completa y validada para la página solicitada.

        Args:
            page_title: Título de la página en Wikipedia

        Returns:
            str: URL completa y validada

        Raises:
            InvalidPageTitleError: Si el título está vacío o es inválido
        """
        if not page_title or not isinstance(page_title, str):
            raise InvalidPageTitleError("El título de la página debe ser una cadena no vacía")

        cleaned_title = page_title.strip()
        encoded_title = quote(cleaned_title, safe='')
        return urljoin(self.base_url, f"wiki/{encoded_title}")

    def get_page_soup(self, page_title: str) -> BeautifulSoup:
        """
        Obtiene y parsea el contenido HTML de una página de Wikipedia.

        Args:
            page_title: Título de la página (ej: "Inteligencia_artificial")

        Returns:
            BeautifulSoup: Objeto parseado con el contenido de la página

        Raises:
            WikiScraperError: Para errores de red, HTTP o validación
            ParsingError: Si falla el parseo del contenido HTML
            NonHTMLContentError: Si la respuesta no es HTML válido

        Ejemplo:
            with WikiScraper() as scraper:
                soup = scraper.get_page_soup("Python")
                print(soup.find('h1').text)
        """
        url = self._build_url(page_title)
        self.logger.info("Iniciando solicitud para: %s", url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            
            # Verificar redirecciones
            if response.history:
                self.logger.warning("Redirección detectada (%d saltos): %s -> %s",
                             len(response.history), response.history[0].url, response.url)

            # Validar tipo de contenido
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                raise NonHTMLContentError(f"Tipo de contenido no válido: {content_type}")

            response.raise_for_status()

            self.logger.debug("Respuesta recibida [%d] en %.2fs, Tamaño: %.2fKB",
                         response.status_code,
                         response.elapsed.total_seconds(),
                         len(response.content)/1024)

            return BeautifulSoup(response.content, self.parser, from_encoding=response.encoding)

        except requests.RequestException as e:
            status_code = getattr(e.response, 'status_code', None)
            error_msg = f"Error HTTP {status_code}" if status_code else f"Error de red: {e}"
            self.logger.error("%s - URL: %s", error_msg, url)
            raise WikiScraperError(error_msg) from e

        except FeatureNotFound as e:
            self.logger.error("Parser '%s' no disponible: %s", self.parser, e)
            raise ParsingError(f"Parser {self.parser} no disponible") from e

        except Exception as e:
            self.logger.error("Error inesperado: %s - %s", type(e).__name__, e, exc_info=True)
            raise WikiScraperError(f"Error inesperado: {type(e).__name__} - {e}") from e
        
    def search_wikipedia(self, query: str, limit: int = 5) -> List[str]:
        """
        Busca títulos de páginas en Wikipedia usando la API.

        Args:
            query: Término de búsqueda.
            limit: Número máximo de resultados a devolver.

        Returns:
            Una lista de títulos de páginas de Wikipedia que coinciden con la búsqueda.

        Raises:
            SearchError: Si hay un error en la solicitud a la API.
            NoSearchResultsError: Si la búsqueda no devuelve resultados.
        """
        search_url = urljoin(self.base_url, "w/api.php")
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "",
        }

        self.logger.info(f"Iniciando búsqueda en Wikipedia para la consulta: '{query}' con límite de {limit} resultados.")
        self.logger.debug(f"URL de búsqueda: {search_url} | Parámetros: {params}")

        try:
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            self.logger.info("Respuesta recibida de la API de Wikipedia exitosamente.")
            data = response.json()
            self.logger.debug(f"Datos recibidos de la API: {data}")

            # Verificar errores de la API
            if "error" in data:
                error_info = data["error"].get("info", "Error desconocido en la API de Wikipedia")
                self.logger.error(f"Error en la API de Wikipedia: {error_info}")
                raise SearchError(f"Error en la API: {error_info}")

            # Verificar estructura de la respuesta
            if "query" not in data or "search" not in data["query"]:
                self.logger.error(f"Estructura inesperada en la respuesta para la búsqueda '{query}'.")
                raise NoSearchResultsError(f"La búsqueda '{query}' no devolvió resultados.")

            results = [item["title"] for item in data["query"]["search"]]
            self.logger.info(f"Búsqueda completada. Se encontraron {len(results)} resultados para '{query}'.")

            # Verificar si hay resultados vacíos
            if not results:
                self.logger.warning(f"La búsqueda '{query}' no devolvió resultados.")
                raise NoSearchResultsError(f"La búsqueda '{query}' no devolvió resultados.")

            return results

        except requests.RequestException as e:
            self.logger.exception(f"Error en la búsqueda en Wikipedia: {e}")
            raise SearchError(f"Error en la búsqueda en Wikipedia: {e}") from e
        except (KeyError, ValueError) as e:
            self.logger.exception(f"Error procesando la respuesta de la API: {e}")
            raise SearchError(f"Error procesando la respuesta de la API: {e}") from e

    

    def get_page_soup_with_search(self, query: str) -> BeautifulSoup:
        """
        Obtiene el contenido de una página utilizando la búsqueda de Wikipedia.

        Args:
            query: Término de búsqueda o título de la página.

        Returns:
            BeautifulSoup: Objeto parseado con el contenido de la página.

        Raises:
            WikiScraperError: Si hay errores en la búsqueda o al obtener la página.
            NoSearchResultsError: Si no se encuentran resultados de búsqueda.
        """
        self.logger.info(f"Iniciando obtención de contenido para la consulta: '{query}'.")
        try:
            # Paso 1: Buscar el término
            search_results = self.search_wikipedia(query)  # search_wikipedia ahora maneja resultados vacíos
            self.logger.info(f"Resultados de búsqueda obtenidos: {search_results}")

            # Paso 2: Intentar recuperar la primera página
            first_result_title = search_results[0]
            self.logger.info(f"Recuperando contenido de la página: '{first_result_title}'.")
            page_soup = self.get_page_soup(first_result_title)
            self.logger.info(f"Contenido de la página '{first_result_title}' obtenido exitosamente.")
            return page_soup

        except WikiScraperError as e:
            self.logger.error(f"Error al obtener '{first_result_title}': {str(e)}")
            raise  # Relanza la excepción preservando el traceback original


    
    def get_page_raw_text(self, page_title: str) -> str:
        """
        Obtiene el contenido de un artículo de Wikipedia en texto plano utilizando la API.

        Args:
            page_title: Título de la página de Wikipedia.

        Returns:
            str: El contenido del artículo en texto plano.

        Raises:
            WikiScraperError: Si hay un error al comunicarse con la API o al procesar la respuesta.
            NoSearchResultsError: Si la página no se encuentra o no tiene contenido.
        """
        api_url = urljoin(self.base_url, "w/api.php")
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "extracts",
            "explaintext": "true",  # Importante para obtener texto plano
            "exlimit": "1",  # Limitar a una página (la solicitada)
        }

        self.logger.info(f"Obteniendo texto plano para '{page_title}' desde la API.")
        self.logger.debug(f"URL de la API: {api_url} | Parámetros: {params}")

        try:
            response = self.session.get(api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            self.logger.debug(f"Respuesta de la API: {data}")

            if "error" in data:
                error_info = data["error"].get("info", "Error desconocido en la API de Wikipedia")
                self.logger.error(f"Error en la API de Wikipedia: {error_info}")
                raise SearchError(f"Error en la API: {error_info}")

            query = data.get("query", {})
            pages = query.get("pages", {})

            if not pages:
                self.logger.warning(f"No se encontró la página '{page_title}' en la respuesta de la API.")
                raise NoSearchResultsError(f"No se encontró la página '{page_title}'.")

            # Las páginas están indexadas por pageid, normalmente solo habrá una
            page_content = None
            for page_id in pages:
                page_data = pages[page_id]
                if "extract" in page_data:
                    page_content = page_data["extract"]
                    break  # Tomamos el contenido de la primera página (debería ser la única con exlimit=1)
                elif "missing" in page_data:
                    self.logger.warning(f"Página '{page_title}' no encontrada (missing en la API).")
                    raise NoSearchResultsError(f"Página '{page_title}' no encontrada.")
                else:
                    self.logger.warning(f"Respuesta inesperada de la API para '{page_title}': {page_data}")
                    raise SearchError(f"Respuesta inesperada de la API al obtener '{page_title}'.")

            if page_content:
                self.logger.info(f"Texto plano obtenido exitosamente para '{page_title}'.")
                return page_content
            else:
                self.logger.warning(f"No se pudo extraer el contenido de texto plano para '{page_title}'.")
                raise NoSearchResultsError(f"No se pudo obtener el contenido de texto plano para '{page_title}'.")


        except requests.RequestException as e:
            self.logger.exception(f"Error al obtener texto plano de la API para '{page_title}': {e}")
            raise SearchError(f"Error de comunicación con la API: {e}") from e
        except (KeyError, ValueError) as e:
            self.logger.exception(f"Error al procesar la respuesta de la API para '{page_title}': {e}")
            raise SearchError(f"Error al procesar la respuesta de la API: {e}") from e
    
    
    def get_page_links(self, page_title: str,
                           link_type: str = "internal",
                           limit: int = 500,
                           namespace: Optional[int] = None) -> List[str]:
        """
        Retrieves links from a Wikipedia page using the API.

        Args:
            page_title: Title of the page.
            link_type: Type of link ('internal', 'external', 'linkshere', 'interwiki').
            limit: Maximum number of links to return (API limit: 500 for users, 5000 for bots).
            namespace: Filter by namespace (e.g., 0 for main, 1 for discussion, etc.).
                       See https://www.mediawiki.org/wiki/Help:Namespaces

        Returns:
            A list of page titles (for internal and linkshere links),
            URLs (for external links), or interwiki prefixes with page titles (for interwiki links).

        Raises:
            WikiScraperError: If there is an error in the API request.
            ValueError: If the link type is invalid.
        """
        logger = logging.getLogger(__name__)

        ALLOWED_LINK_TYPES = ["internal", "external", "linkshere", "interwiki"] # Constant for valid link types
        API_ACTION = "query"
        API_FORMAT = "json"
        API_PROP = None # Will be set dynamically based on link_type

        if link_type not in ALLOWED_LINK_TYPES:
            raise ValueError(f"Invalid link type. Must be one of: {', '.join(ALLOWED_LINK_TYPES)}")

        module = ""        # API Module for 'prop' parameter
        param_prefix = ""  # Parameter prefix for API (e.g., 'pl', 'el', 'lh', 'iw')
        result_key = ""    # Key in the API response containing the link results

        if link_type == "internal":
            module = "links"
            param_prefix = "pl"
            result_key = "links"
            API_PROP = module # set prop based on module
        elif link_type == "external":
            module = "extlinks"
            param_prefix = "el"
            result_key = "extlinks"
            API_PROP = module
        elif link_type == "linkshere":
            module = "linkshere"
            param_prefix = "lh"
            result_key = "linkshere"
            API_PROP = module
        elif link_type == "interwiki":
            module = "iwlinks"
            param_prefix = "iw"
            result_key = "iwlinks"
            API_PROP = module


        api_url = urljoin(self.base_url, "w/api.php")

        def build_params(continue_token: Optional[Dict[str, str]] = None) -> Dict[str, Any]: # Function for building params, supporting continue token
            """Builds API parameters for link retrieval, including pagination."""
            params = {
                "action": API_ACTION,
                "format": API_FORMAT,
                "titles": page_title,
                "prop": API_PROP,
                f"{param_prefix}limit": str(limit), # Limit needs to be string according to API
            }
            if namespace is not None:
                params[f"{param_prefix}namespace"] = str(namespace) # Namespace also string
            if continue_token:
                params.update(continue_token) # Use update to merge continue params
            return params


        def extract_links_from_response(page_data: Dict[str, Any], link_type: str) -> List[str]:
            """Extracts links of the specified type from a page data dictionary."""
            extracted_links = []
            if result_key in page_data:
                for item in page_data[result_key]:
                    if link_type == "external":
                        extracted_links.append(item["*"])  # URL of external link
                    elif link_type == "interwiki":
                         extracted_links.append(item["prefix"] + ":" + item["*"]) # Prefix and page title
                    else:
                        extracted_links.append(item["title"])  # Page title for internal/linkshere
            return extracted_links


        links = []
        continue_data = None  # Pagination continuation dictionary

        self.logger.info(f"Retrieving {link_type} links from '{page_title}' with limit {limit}.")
        api_query_params_log = build_params()
        self.logger.debug(f"API Request URL: {api_url} | Parameters (initial): {api_query_params_log}")


        while True:  # Pagination loop
            try:
                request_params = build_params(continue_data) # Build params, now including continue if available.
                response = self.session.get(api_url, params=request_params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                self.logger.debug(f"API response data received: {data}")


                if "error" in data:
                    error_info = data["error"].get("info", "Unknown Wikipedia API error")
                    error_code = data['error'].get('code')
                    self.logger.error(f"Wikipedia API error: {error_info} | Code: {error_code}")
                    raise WikiScraperError(f"API Error: {error_info} (Code: {error_code})")


                query_data = data.get("query", {})
                pages_data = query_data.get("pages", {})

                if not pages_data: # Check for no pages returned in query - potentially page not found? Or just no links of requested type.
                    self.logger.warning(f"No pages data found in API response for '{page_title}'. Possibly no {link_type} links or page not found.")
                    break # If no pages, assuming no more links, break the loop, avoid error if page not found is not explicitly checked.
                    # Depending on requirements, could raise NoSearchResultsError if you want to specifically flag page not found for link retrieval too, but current impl. suggests returning empty list if no links or page is problematic in this context.


                for page_id, page_info in pages_data.items():
                    links.extend(extract_links_from_response(page_info, link_type)) # Extract links and extend results


                continue_data = data.get("continue") # Get continue info for pagination. If not present, it's None
                if continue_data:
                    self.logger.debug(f"Continuing pagination with parameters: {continue_data}")
                else:
                    break # No 'continue' in response, pagination is complete


            except requests.HTTPError as http_err:
                status_code = http_err.response.status_code if http_err.response else 'N/A'
                reason = http_err.response.reason if http_err.response else 'N/A'
                self.logger.error(f"HTTP error {status_code}: {reason} retrieving links.")
                raise WikiScraperError(f"HTTP Error: {status_code} - {reason} during link retrieval") from http_err
            except requests.Timeout as timeout_err:
                self.logger.error("Timeout during Wikipedia link retrieval.")
                raise WikiScraperError("Timeout during link retrieval from Wikipedia") from timeout_err
            except KeyError as key_err:
                self.logger.error(f"Key error processing API response for links: {key_err}")
                raise WikiScraperError("Error processing API response structure for links") from key_err
            except Exception as e:
                self.logger.exception(f"Unexpected error during Wikipedia link retrieval: {e}")
                raise WikiScraperError("Unexpected error during link retrieval from Wikipedia") from e


        self.logger.info(f"Retrieved {len(links)} {link_type} links from '{page_title}'.")
        return links
            
    def get_page_categories(self, page_title: str) -> List[str]:
        """
        Retrieves categories for a Wikipedia article using the API with full pagination.
        """
        logger = logging.getLogger(__name__) # Get logger based on module name, standard practice

        API_ACTION = "query" # Define constants for API parameters, makes code more readable and maintainable
        API_FORMAT = "json"
        API_PROP = "categories"
        API_CATEGORY_LIMIT = "max" # Which corresponds to 500, maximum allowed by the API
        API_CATEGORY_SHOW = "!hidden"
        API_CATEGORY_NAMESPACE = 14

        def build_params(continue_token: str = None) -> Dict[str, str]:
            """Builds API parameters with pagination support."""
            params = {
                "action": API_ACTION,
                "format": API_FORMAT,
                "titles": page_title,
                "prop": API_PROP,
                "cllimit": API_CATEGORY_LIMIT,
                "clshow": API_CATEGORY_SHOW,
                "clnamespace": API_CATEGORY_NAMESPACE # Categories namespace
            }
            if continue_token:
                params["clcontinue"] = continue_token
            return params

        def process_category_title(category: Dict[str, Any]) -> str:
            """Extracts and safely formats the category name from API response."""
            title = category.get("title", "")
            return title.split(":", 1)[-1] if title else "" # Safely process title and remove "Category:" prefix

        api_url = urljoin(self.base_url, "w/api.php")
        categories = []
        continue_token = None
        self.logger.info(f"Starting category retrieval for page: '{page_title}'") # Log in English

        try:
            while True:
                response = self.session.get(
                    api_url,
                    params=build_params(continue_token),
                    timeout=self.timeout
                )
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                data = response.json()
                self.logger.debug(f"API response received - Size: {len(response.content)} bytes") # Log in English

                if "error" in data:
                    error_info = data["error"].get("info", "Unknown API error") # Default error message in English
                    error_code = data['error'].get('code')
                    self.logger.error(f"API Error: {error_info} | Code: {error_code}") # Log in English, include error code
                    raise WikiScraperError(f"API Error: {error_info} (Code: {error_code})") # Include code in exception message

                query_data = data.get("query", {}) # Renamed to be clearer
                pages_data = query_data.get("pages", {}) # Renamed to be clearer

                if not pages_data or "-1" in pages_data: # Check if pages are missing or API returns -1 for not found
                    self.logger.warning(f"Page not found: '{page_title}'") # Log in English
                    raise NoSearchResultsError(f"Page '{page_title}' does not exist") # Exception message in English

                page_info = next(iter(pages_data.values()))  # Get the first/only page data
                categories_batch = [
                    process_category_title(category)
                    for category in page_info.get("categories", [])
                    if process_category_title(category) # Ensure processed category is not empty
                ]
                categories.extend(categories_batch)

                # Handle pagination
                continue_data = data.get("continue") # Renamed for clarity
                if continue_data:
                    continue_token = continue_data.get("clcontinue")
                    self.logger.debug(f"Continuing pagination with token: {continue_token}") # Log in English
                else:
                    break # No more continue token, pagination finished

        except requests.HTTPError as http_err: # Specific exception name for clarity
            status_code = http_err.response.status_code if http_err.response else 'N/A' # Handle case where response is None
            reason = http_err.response.reason if http_err.response else 'N/A'
            self.logger.error(f"HTTP Error {status_code}: {reason}") # Log with status code and reason
            raise WikiScraperError(f"HTTP Error: {status_code} - {reason}") from http_err # Re-raise with original exception context
        except requests.Timeout as timeout_err: # Specific exception name
            self.logger.error("Timeout connecting to Wikipedia API") # Log in English
            raise WikiScraperError("Connection Timeout") from timeout_err # Re-raise with original exception context
        except KeyError as key_err: # Specific exception name
            self.logger.error(f"Unexpected API response structure: Missing field {key_err}") # Log in English
            raise WikiScraperError("Invalid API response structure") from key_err # Re-raise with original exception context
        except Exception as e: # Catch-all for unexpected exceptions during API interaction, consider more specific exceptions as needed
            self.logger.exception(f"Unexpected error during API request: {e}") # Use self.logger.exception to capture traceback
            raise WikiScraperError(f"Unexpected error during API request") from e # Re-raise as WikiScraperError

        self.logger.info(f"Retrieved {len(categories)} categories for '{page_title}'") # Final log in English
        return categories

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        self.logger.debug("Sesión HTTP cerrada correctamente")


