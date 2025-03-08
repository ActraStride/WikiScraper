"""
Module Name: cli

Command-line interface (CLI) for the Wikipedia scraper.

This module provides a centralized interface to:
- Configure scraper options
- Handle errors robustly
- Enable structured logging
- Extend the command system (e.g., via integration with Click)

Example:
    >>> wiki --help
"""


import sys
import click
import logging

from pathlib import Path
from typing import Any, NoReturn, List, Optional

from src.wikiscraper import WikiScraper, LanguageNotSupportedError
from src.storage import FileSaver
from src.utils import setup_logging, LoggingSetupError
from src.service.wiki_service import WikiService  # Import WikiService if you intend to use it in CLI


# Constantes
DEFAULT_LANGUAGE: str = "es"
DEFAULT_TIMEOUT: int = 15
SUPPORTED_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]
DEFAULT_OUTPUT_DIR = "./output_files"


class CLIError(Exception):
    """Excepción base para errores específicos de la CLI."""
    pass


class WikiCLI:
    """Clase principal que encapsula la lógica de la CLI."""

    def __init__(
        self,
        language: str = DEFAULT_LANGUAGE,
        timeout: int = DEFAULT_TIMEOUT,
        log_level: str = "INFO",
        logger: logging.Logger = None  # 1. Añade el parámetro logger con valor por defecto None
    ) -> None:
        """
        Inicializa la instancia de la CLI.

        Args:
            language: Código de idioma ISO 639-1 (default: 'es')
            timeout: Timeout HTTP en segundos (default: 15)
            log_level: Nivel de logging (default: 'INFO')
            logger: Objeto logger para inyección de dependencias (default: None) # Documenta el parámetro logger

        Raises:
            CLIError: Si hay un error en la configuración inicial de la CLI.
        """
        if logger is None:  # Manejo por si no se inyecta logger (para testing muy aislado o casos excepcionales, no en uso normal)
            self._logger = logging.getLogger(__name__) # Logger por defecto si no se inyecta, PERO NO RECOMENDADO para producción
            self._logger.warning("WikiCLI inicializado SIN logger inyectado. Usando logger por defecto. ¡No es la configuración recomendada!")
        else:
            self._logger = logger # 2. Usa el logger INYECTADO

        self._configure_components(language, timeout, log_level)

    def _configure_components(
        self,
        language: str,
        timeout: int,
        log_level: str
    ) -> None:
        """Configura los componentes internos: scraper y logger, con validación de parámetros."""
        logger = self._logger  # Usa el logger INYECTADO (o por defecto si no se inyectó)
        try:
            self._validate_inputs(language, timeout, log_level)
            self.scraper = WikiScraper(language=language, timeout=timeout, logger=logger) # 3. Inyecta logger en WikiScraper
            self.file_saver = FileSaver(logger=logger) # 4. Inyecta logger en FileSaver
            self.service = WikiService(scraper=self.scraper, file_saver=self.file_saver, logger=logger) # Instantiate WikiService here!
            logger.debug("Componentes inicializados correctamente")  # Usa el logger INYECTADO
        except (LanguageNotSupportedError, ValueError) as e:
            logger.critical(f"Error de configuración: {e}", exc_info=True)  # Usa el logger INYECTADO
            raise CLIError(str(e)) from e

    def _validate_inputs(
        self,
        language: str,
        timeout: int,
        log_level: str
    ) -> None:
        """Valida los parámetros de entrada para la CLI."""
        # La lógica de validación sigue igual, si quieres añadir logging aquí, usa self._logger
        if not language.isalpha():
            raise ValueError(f"Código de idioma inválido: '{language}'. Debe ser un código ISO 639-1 de 2 letras (ej: 'es', 'en', 'fr').")

        if timeout <= 0:
            raise ValueError(f"Timeout inválido: {timeout}. Debe ser mayor a 0.")

        if log_level not in SUPPORTED_LOG_LEVELS:
            raise ValueError(f"Nivel de log inválido: '{log_level}'. Debe ser uno de: {SUPPORTED_LOG_LEVELS}")

    def execute_test_command(self) -> None:
        """
        Ejecuta un comando de prueba para verificar el funcionamiento básico de la CLI.
        """
        logger = self._logger # Usa el logger INYECTADO
        logger.info("Iniciando comando de prueba...") # Usa el logger INYECTADO
        click.secho("🕸️ ", fg="white", nl=False)
        click.secho(" 👻 ", fg="white", nl=False)
        click.secho("[ ", fg="magenta", nl=False)
        click.secho("PRUEBA SPOOKY", fg="black", bg="yellow", bold=True, nl=False)
        click.secho(" ]", fg="magenta", nl=False)
        click.secho(" ¡Algo ha ido horriblemente... bien!", fg="magenta", bold=True, nl=False)
        click.secho(" 🎃🦇", fg="white", nl=True)
        logger.debug("Comando de prueba ejecutado con éxito") # Usa el logger INYECTADO


          
    def execute_search_command(self, query: str, limit: int) -> None:
        """
        Ejecuta el comando de búsqueda utilizando WikiService.search_articles.

        Args:
            query: Término de búsqueda.
            limit: Número máximo de resultados a obtener.
        """
        logger = self._logger  # Usa el logger INYECTADO
        logger.info(f"Iniciando búsqueda en Wikipedia (a través del servicio) para: '{query}' (límite: {limit} resultados)") # Usa el logger INYECTADO

        try:
            search_results = self.service.search_articles(query=query, limit=limit) # Usa el servicio!
            if search_results: # SearchResults object is truthy if it has results
                click.secho(f"Resultados de búsqueda para '{query}':", fg="green", bold=True)
                for i, search_result in enumerate(search_results): # Iterate through SearchResults object
                    click.echo(f"{i+1}. {search_result.title}") # Access title from SearchResult object
            else:
                click.secho(f"No se encontraron resultados para '{query}'.", fg="yellow")
                logger.warning(f"No se encontraron resultados para '{query}'. Servicio no encontró resultados para '{query}'.") # Usa el logger INYECTADO, mensaje actualizado
        except Exception as e: # Captura la excepción base, puede ser WikiServiceError o sus subtipos
            logger.error(f"Error durante la búsqueda (a través del servicio) para '{query}': {e}", exc_info=True) # Usa el logger INYECTADO, mensaje actualizado
            click.secho(f"❌ Error al realizar la búsqueda: {e}", fg="red", bold=True, err=True)
            sys.exit(3) # Usa sys.exit para indicar fallo del comando dentro de la CLI

    


    def execute_get_command(self, query: str, save: bool) -> None:
        """
        Ejecuta el comando 'get' para obtener el texto de la primera página de Wikipedia
        que coincide con la búsqueda.

        Args:
            query: Término de búsqueda para la página de Wikipedia.
        """
        logger = self._logger
        logger.info(f"Iniciando comando 'get' para buscar y obtener la página de Wikipedia para: '{query}'") # Usa el logger INYECTADO

        try:
            with self.scraper as scraper_instance: # 'scraper_instance' es el mismo que self.scraper
                search_results: List[str] = scraper_instance.search_wikipedia(query=query, limit=1)
                if not search_results:
                    click.secho(f"No se encontraron páginas para la búsqueda: '{query}'.", fg="yellow")
                    logger.warning(f"No se encontraron páginas para la búsqueda: '{query}'.") # Usa el logger INYECTADO
                    return
                else:
                    page_title: str = search_results[0]
                    logger.info(f"Primer resultado de búsqueda: '{page_title}'. Obteniendo texto de la página...") # Usa el logger INYECTADO
                    page_text: str = scraper_instance.get_page_raw_text(page_title=page_title)
                    if page_text:
                        click.secho(f"Texto de la página '{page_title}':", fg="green", bold=True)
                        click.echo(page_text)
                        logger.info(f"Texto de la página '{page_title}' mostrado con éxito.") # Usa el logger INYECTADO

                        if save:
                            logger.info(f"Se proporcionó la opción de guardado'. Guardando página usando FileSaver...") # Usa el logger INYECTADO
                            try:
                                saved_path = self.file_saver.save(content=page_text, title=page_title) # Usando file_saver.save()
                                click.secho(f"Página guardada'", fg="green")
                                logger.info(f"Página '{page_title}' guardada con éxito") # Usa el logger INYECTADO
                            except Exception as save_error:
                                logger.error(f"Error al guardar la página' usando FileSaver: {save_error}", exc_info=True) # Usa el logger INYECTADO
                                click.secho(f"❌ Error al guardar la página' usando FileSaver: {save_error}", fg="red", bold=True, err=True)
                    else:
                        click.secho(f"No se pudo obtener el texto de la página '{page_title}'.", fg="yellow")
                        logger.warning(f"No se pudo obtener el texto de la página '{page_title}'.") # Usa el logger INYECTADO

        except Exception as e:
            logger.error(f"Error durante el comando 'get' para '{query}': {e}", exc_info=True) # Usa el logger INYECTADO
            click.secho(f"❌ Error al obtener la página para '{query}': {e}", fg="red", bold=True, err=True)
            sys.exit(3) # Usa sys.exit para indicar fallo del comando dentro de la CLI



    def execute_map_command(self, query: str, depth: int) -> None:
        """
        Ejecuta el comando 'map' para mapear recursivamente los links internos de una página de Wikipedia
        hasta la profundidad especificada.

        Args:
            query: Título de la página de Wikipedia a mapear.
            depth: Nivel de profundidad (niveles de recursión).
        """
        logger = self._logger
        logger.info(f"Iniciando comando 'map' para la página '{query}' con profundidad {depth}") # Usa el logger INYECTADO

        def recursive_map(page_title: str, current_depth: int, max_depth: int, visited: set) -> dict:
            if current_depth > max_depth or page_title in visited:
                return {}
            visited.add(page_title)
            logger.debug(f"Mapeando página '{page_title}' en profundidad {current_depth}") # Usa el logger INYECTADO
            try:
                links = self.scraper.get_page_links(page_title=page_title, link_type="internal")
            except Exception as e:
                logger.error(f"Error obteniendo links para la página '{page_title}': {e}", exc_info=True) # Usa el logger INYECTADO
                links = []
            subtree = {}
            for link in links:
                subtree[link] = recursive_map(link, current_depth + 1, max_depth, visited)
            return subtree

        mapping = recursive_map(query, 1, depth, set())

        def print_mapping(mapping: dict, indent: int = 0) -> None:
            for page, sublinks in mapping.items():
                click.echo("  " * indent + f"- {page}")
                print_mapping(sublinks, indent + 1)

        click.secho(f"Mapa de links para la página '{query}':", fg="green", bold=True)
        print_mapping({query: mapping})
        logger.info(f"Comando 'map' completado para la página '{query}'") # Usa el logger INYECTADO



@click.group()
@click.option(
    "--language",
    "-l",
    default=DEFAULT_LANGUAGE,
    show_default=True,
    help="Código de idioma ISO 639-1 para Wikipedia (ej: 'es', 'en', 'fr')"
)
@click.option(
    "--timeout",
    type=click.IntRange(1, 300),
    default=DEFAULT_TIMEOUT,
    show_default=True,
    help="Timeout HTTP en segundos (1-300)"
)
@click.option(
    "--verbose",
    "-v",
    default="INFO",
    show_default=True,
    type=click.Choice(SUPPORTED_LOG_LEVELS),
    help=f"Nivel de verbosidad para logging: {SUPPORTED_LOG_LEVELS}"
)
@click.pass_context
def cli(ctx: click.Context, language: str, timeout: int, verbose: str) -> None:
    """
    Punto de entrada principal para la interfaz de línea de comandos (CLI).

    Configura el entorno de logging, inicializa la CLI principal (`WikiCLI`)
    y la almacena en el contexto de click (`ctx.obj`) para ser accesible a los comandos.
    """
    try:
        # Configuración de logging centralizada
        project_root = Path(__file__).resolve().parent.parent.parent
        setup_logging(project_root=project_root, log_level=verbose.upper()) # Log level ahora configurable aquí

        # 5. Obtiene el logger DESPUÉS de configurar el logging
        logger = logging.getLogger(__name__) # Logger para el módulo cli

        # Configuración del contexto de ejecución
        ctx.obj = WikiCLI(
            language=language,
            timeout=timeout,
            log_level=verbose.upper(),
            logger=logger 
        )

        logger.debug(  # Usa el logger OBTENIDO en la función cli()
            f"CLI inicializada: language='{language}', timeout={timeout}s, log_level='{verbose}'"
        )

    except LoggingSetupError as e:
        click.secho(f"🚨 Error al configurar el logging: {e}", fg="red", bold=True, err=True)
        sys.exit(1)
    except LanguageNotSupportedError as e: # Manejo específico de LanguageNotSupportedError aquí
        click.secho(f"🌎 Idioma no soportado: {e}. Por favor, elige un idioma válido para Wikipedia.", fg="yellow", bold=True, err=True)
        sys.exit(1)
    except CLIError as e:
        click.secho(f"⚙️ Error de configuración de la CLI: {e}", fg="red", bold=True, err=True)
        sys.exit(1)
    except Exception as e:
        logging.getLogger(__name__).error("Error inesperado durante inicialización CLI", exc_info=True) # Log completo del error
        click.secho(
            f"🔥 Error inesperado en la CLI: {e}",
            fg="yellow",
            bold=True,
            err=True
        )
        sys.exit(2)



@cli.command()
@click.pass_context
def test(ctx: click.Context) -> None:
    """
    Ejecuta un comando de prueba para verificar la instalación y configuración básica de la CLI.
    """
    try:
        cli_instance: WikiCLI = ctx.obj
        cli_instance.execute_test_command()
    except Exception as e:
        logger = ctx.obj.logger  # Get the logger from ctx.obj (now DI-aligned at command level)
        logger.error("Error durante comando de prueba", exc_info=True) # Log completo del error
        click.secho(
            f"❌ Fallo en comando de prueba: {e}",
            fg="red",
            bold=True,
            err=True
        )
        sys.exit(3)

@cli.command()
@click.argument('query', type=str)
@click.option('--limit', '-l', type=click.IntRange(1, 10), default=5, show_default=True, help="Máximo número de resultados de búsqueda (1-10)")
@click.pass_context
def search(ctx: click.Context, query: str, limit: int) -> None:
    """
    Busca páginas en Wikipedia por título o contenido aproximado.
    """
    try:
        cli_instance: WikiCLI = ctx.obj
        cli_instance.execute_search_command(query, limit)
    except Exception as e:
        logger = ctx.obj.logger  # Get the logger from ctx.obj (now DI-aligned at command level)
        logger.error("Error durante comando de búsqueda", exc_info=True)
        click.secho(
            f"❌ Fallo en comando de búsqueda: {e}",
            fg="red",
            bold=True,
            err=True
        )
        sys.exit(3)


@cli.command()
@click.argument('query', type=str)
@click.option('--save', '-s',  # Cambiado a --save y -s
              is_flag=True,  # Indica que es un flag booleano (True si se usa, False si no)
              default=False,  # Ahora por defecto no guarda
              help="Guarda la salida en un archivo en lugar de mostrarla en consola.") # Help actualizado
@click.pass_context
def get(ctx: click.Context, query: str, save: bool) -> None: # output_dir reemplazado por save: bool
    """
    Realiza una acción (antes traía texto crudo, ahora acción simplificada) y
    dirige la salida a la consola o a un archivo.

    Si no se proporciona --save, la salida se muestra en la consola.
    Si se proporciona --save, la salida se guarda como archivo en un directorio predeterminado (o lógica interna).

    \b
    Ejemplos:
        wiki get <query>  # Salida en consola
        wiki get <query> --save  # Guardar en archivo (ubicación predeterminada)
        wiki get <query> -s     # Guardar en archivo (ubicación predeterminada)
    """
    logger = ctx.obj.logger  # Get the logger from ctx.obj (now DI-aligned at command level)

    try:
        cli_instance: click.Context = ctx.obj #  Asumiendo que ctx.obj contiene la instancia de WikiCLI
        # Ahora pasamos 'save' en lugar de 'output_dir'
        cli_instance.execute_get_command(query, save) #  La lógica de guardar o no estará en execute_get_command

    except Exception as e:
        logger.error("Error durante comando get", exc_info=True)
        click.secho(
            f"❌ Fallo en comando get: {e}",
            fg="red",
            bold=True,
            err=True
        )
        sys.exit(3)

@cli.command()
@click.argument('query', type=str)
@click.option(
    '--depth',
    '-d',
    type=click.IntRange(0, 10),
    default=1,
    show_default=True,
    help="Profundidad de mapeo (niveles de links a seguir)"
)
@click.pass_context
def map(ctx: click.Context, query: str, depth: int) -> None:
    """
    Mapea recursivamente los links internos de una página de Wikipedia hasta la profundidad especificada.
    """
    try:
        cli_instance: WikiCLI = ctx.obj
        cli_instance.execute_map_command(query, depth)
    except Exception as e:
        logger = ctx.obj.logger  # Get the logger from ctx.obj (now DI-aligned at command level)
        logger.error("Error durante comando map", exc_info=True)
        click.secho(
            f"❌ Fallo en comando map: {e}",
            fg="red",
            bold=True,
            err=True
        )
        sys.exit(3)



def main() -> None:
    """Función principal como punto de entrada del programa, maneja la ejecución de la CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.secho("\n🔴 Operación cancelada por el usuario.", fg="yellow")
        sys.exit(0)
    except Exception as e:
        logging.getLogger(__name__).critical("Error no controlado en main", exc_info=True) # Registrar error crítico
        click.secho(
            f"⛔ Error no controlado en la aplicación: {e}",
            fg="red",
            bold=True,
            err=True
        )
        sys.exit(4)


if __name__ == "__main__":
    main()