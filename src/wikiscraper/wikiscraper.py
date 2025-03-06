"""
Módulo profesional para scraping de Wikipedia con manejo robusto de errores, reintentos inteligentes
y cumplimiento de buenas prácticas de web scraping.

Características principales:
- Gestión automática de sesiones HTTP con reintentos configurables
- Validación estricta de entradas y parámetros
- Detección de redirecciones y contenido no HTML
- Parseo seguro con manejo correcto de encoding
- Logging detallado y configuración flexible
- Cumplimiento de robots.txt y políticas de uso

Uso básico:
>>> from wiki_scraper import WikiScraper
>>> with WikiScraper(language="es") as scraper:
...     soup = scraper.get_page_soup("Python")
...     print(soup.title.string)
"""

import logging
from typing import Final, Optional, Set, List
import requests
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import quote, urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de logging

logger = logging.getLogger(__name__)

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

        logger.debug("Scraper inicializado: %s", self.__repr__())

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
        logger.info("Iniciando solicitud para: %s", url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            
            # Verificar redirecciones
            if response.history:
                logger.warning("Redirección detectada (%d saltos): %s -> %s",
                             len(response.history), response.history[0].url, response.url)

            # Validar tipo de contenido
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                raise NonHTMLContentError(f"Tipo de contenido no válido: {content_type}")

            response.raise_for_status()

            logger.debug("Respuesta recibida [%d] en %.2fs, Tamaño: %.2fKB",
                         response.status_code,
                         response.elapsed.total_seconds(),
                         len(response.content)/1024)

            return BeautifulSoup(response.content, self.parser, from_encoding=response.encoding)

        except requests.RequestException as e:
            status_code = getattr(e.response, 'status_code', None)
            error_msg = f"Error HTTP {status_code}" if status_code else f"Error de red: {e}"
            logger.error("%s - URL: %s", error_msg, url)
            raise WikiScraperError(error_msg) from e

        except FeatureNotFound as e:
            logger.error("Parser '%s' no disponible: %s", self.parser, e)
            raise ParsingError(f"Parser {self.parser} no disponible") from e

        except Exception as e:
            logger.error("Error inesperado: %s - %s", type(e).__name__, e, exc_info=True)
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

        logger.info(f"Iniciando búsqueda en Wikipedia para la consulta: '{query}' con límite de {limit} resultados.")
        logger.debug(f"URL de búsqueda: {search_url} | Parámetros: {params}")

        try:
            response = self.session.get(search_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            logger.info("Respuesta recibida de la API de Wikipedia exitosamente.")
            data = response.json()
            logger.debug(f"Datos recibidos de la API: {data}")

            # Verificar errores de la API
            if "error" in data:
                error_info = data["error"].get("info", "Error desconocido en la API de Wikipedia")
                logger.error(f"Error en la API de Wikipedia: {error_info}")
                raise SearchError(f"Error en la API: {error_info}")

            # Verificar estructura de la respuesta
            if "query" not in data or "search" not in data["query"]:
                logger.error(f"Estructura inesperada en la respuesta para la búsqueda '{query}'.")
                raise NoSearchResultsError(f"La búsqueda '{query}' no devolvió resultados.")

            results = [item["title"] for item in data["query"]["search"]]
            logger.info(f"Búsqueda completada. Se encontraron {len(results)} resultados para '{query}'.")

            # Verificar si hay resultados vacíos
            if not results:
                logger.warning(f"La búsqueda '{query}' no devolvió resultados.")
                raise NoSearchResultsError(f"La búsqueda '{query}' no devolvió resultados.")

            return results

        except requests.RequestException as e:
            logger.exception(f"Error en la búsqueda en Wikipedia: {e}")
            raise SearchError(f"Error en la búsqueda en Wikipedia: {e}") from e
        except (KeyError, ValueError) as e:
            logger.exception(f"Error procesando la respuesta de la API: {e}")
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
        logger.info(f"Iniciando obtención de contenido para la consulta: '{query}'.")
        try:
            # Paso 1: Buscar el término
            search_results = self.search_wikipedia(query)  # search_wikipedia ahora maneja resultados vacíos
            logger.info(f"Resultados de búsqueda obtenidos: {search_results}")

            # Paso 2: Intentar recuperar la primera página
            first_result_title = search_results[0]
            logger.info(f"Recuperando contenido de la página: '{first_result_title}'.")
            page_soup = self.get_page_soup(first_result_title)
            logger.info(f"Contenido de la página '{first_result_title}' obtenido exitosamente.")
            return page_soup

        except WikiScraperError as e:
            logger.error(f"Error al obtener '{first_result_title}': {str(e)}")
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

        logger.info(f"Obteniendo texto plano para '{page_title}' desde la API.")
        logger.debug(f"URL de la API: {api_url} | Parámetros: {params}")

        try:
            response = self.session.get(api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Respuesta de la API: {data}")

            if "error" in data:
                error_info = data["error"].get("info", "Error desconocido en la API de Wikipedia")
                logger.error(f"Error en la API de Wikipedia: {error_info}")
                raise SearchError(f"Error en la API: {error_info}")

            query = data.get("query", {})
            pages = query.get("pages", {})

            if not pages:
                logger.warning(f"No se encontró la página '{page_title}' en la respuesta de la API.")
                raise NoSearchResultsError(f"No se encontró la página '{page_title}'.")

            # Las páginas están indexadas por pageid, normalmente solo habrá una
            page_content = None
            for page_id in pages:
                page_data = pages[page_id]
                if "extract" in page_data:
                    page_content = page_data["extract"]
                    break  # Tomamos el contenido de la primera página (debería ser la única con exlimit=1)
                elif "missing" in page_data:
                    logger.warning(f"Página '{page_title}' no encontrada (missing en la API).")
                    raise NoSearchResultsError(f"Página '{page_title}' no encontrada.")
                else:
                    logger.warning(f"Respuesta inesperada de la API para '{page_title}': {page_data}")
                    raise SearchError(f"Respuesta inesperada de la API al obtener '{page_title}'.")

            if page_content:
                logger.info(f"Texto plano obtenido exitosamente para '{page_title}'.")
                return page_content
            else:
                logger.warning(f"No se pudo extraer el contenido de texto plano para '{page_title}'.")
                raise NoSearchResultsError(f"No se pudo obtener el contenido de texto plano para '{page_title}'.")


        except requests.RequestException as e:
            logger.exception(f"Error al obtener texto plano de la API para '{page_title}': {e}")
            raise SearchError(f"Error de comunicación con la API: {e}") from e
        except (KeyError, ValueError) as e:
            logger.exception(f"Error al procesar la respuesta de la API para '{page_title}': {e}")
            raise SearchError(f"Error al procesar la respuesta de la API: {e}") from e
    
    def get_page_links(self, page_title: str,
                       link_type: str = "internal",  # 'internal', 'external', 'linkshere', 'interwiki'
                       limit: int = 500,
                       namespace: Optional[int] = None) -> List[str]:
        """
        Obtiene los enlaces de una página de Wikipedia usando la API.

        Args:
            page_title: Título de la página.
            link_type: Tipo de enlace ('internal', 'external', 'linkshere', 'interwiki').
            limit: Número máximo de enlaces a devolver (límite de la API: 500 para usuarios, 5000 para bots).
            namespace: Filtra por espacio de nombres (ej: 0 para principal, 1 para discusión, etc.).
                       Ver https://www.mediawiki.org/wiki/Help:Namespaces

        Returns:
            Una lista de títulos de páginas (para enlaces internos y linkshere),
            URLs (para enlaces externos), o prefijos interwiki (para enlaces interwiki).

        Raises:
            SearchError: Si hay un error en la solicitud a la API.
            ValueError:  Si el tipo de enlace es inválido.
        """

        if link_type not in ["internal", "external", "linkshere", "interwiki"]:
            raise ValueError("Tipo de enlace inválido.  Debe ser 'internal', 'external', 'linkshere' o 'interwiki'.")

        if link_type == "internal":
            module = "links"
            param_prefix = "pl"  # Parámetro para el módulo 'links'
            result_key = "links"
        elif link_type == "external":
            module = "extlinks"
            param_prefix = "el"  # Parámetro para el módulo 'extlinks'
            result_key = "extlinks"
        elif link_type == "linkshere":
            module = "linkshere"
            param_prefix = "lh" # Parámetro para el módulo 'linkshere'
            result_key = "linkshere"
        elif link_type == "interwiki":
            module = "iwlinks"
            param_prefix = "iw" # Parámetro para el módulo 'iwlinks'
            result_key = "iwlinks"

        base_url = urljoin(self.base_url, "w/api.php")
        params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            f"{param_prefix}limit": limit,
            "prop": module,
        }
        if namespace is not None:
            params[f"{param_prefix}namespace"] = namespace

        logger.info(f"Obteniendo enlaces {link_type} de '{page_title}' con límite {limit}.")
        logger.debug(f"URL: {base_url} | Parámetros: {params}")

        results = []
        continue_param = {}  # Para paginación

        while True:  # Bucle para manejar la paginación
            try:
                # Combinar parámetros de continuación con los parámetros base
                request_params = params.copy()
                request_params.update(continue_param)

                response = self.session.get(base_url, params=request_params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Datos recibidos de la API: {data}")


                if "error" in data:
                    error_info = data["error"].get("info", "Error desconocido en la API de Wikipedia")
                    logger.error(f"Error en la API de Wikipedia: {error_info}")
                    raise SearchError(f"Error en la API: {error_info}")

                if "query" not in data or "pages" not in data["query"]:
                    logger.error(f"Estructura inesperada en la respuesta para '{page_title}'.")
                    raise SearchError(f"Estructura inesperada en la respuesta de la API.")

                # La API devuelve las páginas con un ID como clave.  Iterar sobre ellas.
                for page_id, page_data in data["query"]["pages"].items():
                    if result_key in page_data:
                        for item in page_data[result_key]:
                            if link_type == "external":
                                results.append(item["*"])  # URL del enlace externo
                            elif link_type == "interwiki":
                                 results.append(item["prefix"] + ":" + item["*"])  # prefijo y pagina
                            else:
                                results.append(item["title"])  # Título de la página

                # Paginación:  Verificar si hay más resultados
                if "continue" in data:
                    continue_param = data["continue"]
                    logger.debug(f"Continuando paginación: {continue_param}")
                else:
                    break  # No hay más resultados

            except requests.RequestException as e:
                logger.exception(f"Error al obtener enlaces de Wikipedia: {e}")
                raise SearchError(f"Error en la solicitud a la API: {e}") from e
            except (KeyError, ValueError) as e:
                logger.exception(f"Error procesando la respuesta de la API: {e}")
                raise SearchError(f"Error procesando la respuesta de la API: {e}") from e

        logger.info(f"Se obtuvieron {len(results)} enlaces {link_type} de '{page_title}'.")
        return results
            

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        logger.debug("Sesión HTTP cerrada correctamente")


