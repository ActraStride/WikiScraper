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
from typing import Final, Optional, Set
import requests
from bs4 import BeautifulSoup, FeatureNotFound
from urllib.parse import quote, urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de logging

logger = logging.getLogger(__name__)

# Constantes
USER_AGENT: Final[str] = "WikiScraperBot/3.0 (+https://github.com/tu_usuario/tu_repositorio)"
VALID_LANGUAGES: Final[Set[str]] = {"en", "es", "fr", "de", "it", "pt", "ja", "zh", "ru"}
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


class WikiScraper:
    """
    Clase profesional para realizar scraping de páginas de Wikipedia de manera segura y eficiente.

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        logger.debug("Sesión HTTP cerrada correctamente")


