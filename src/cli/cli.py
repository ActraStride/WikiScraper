"""
Interfaz de línea de comandos (CLI) para el scraper de Wikipedia.

Provee:
- Configuración centralizada de opciones
- Manejo robusto de errores
- Logging estructurado
- Sistema de comandos extensible (mediante adición de más comandos click)
"""

import sys
from pathlib import Path
from typing import Any, NoReturn

import click
import logging

from src.wikiscraper import WikiScraper, LanguageNotSupportedError
from src.utils import setup_logging, LoggingSetupError

# Constantes
DEFAULT_LANGUAGE: str = "es"
DEFAULT_TIMEOUT: int = 15
SUPPORTED_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]


class CLIError(Exception):
    """Excepción base para errores específicos de la CLI."""
    pass


class WikiCLI:
    """Clase principal que encapsula la lógica de la CLI."""

    def __init__(
        self,
        language: str = DEFAULT_LANGUAGE,
        timeout: int = DEFAULT_TIMEOUT,
        log_level: str = "INFO"
    ) -> None:
        """
        Inicializa la instancia de la CLI.

        Args:
            language: Código de idioma ISO 639-1 (default: 'es')
            timeout: Timeout HTTP en segundos (default: 15)
            log_level: Nivel de logging (default: 'INFO')

        Raises:
            CLIError: Si hay un error en la configuración inicial de la CLI.
        """
        self._logger = logging.getLogger(__name__)
        self._configure_components(language, timeout, log_level)

    def _configure_components(
        self,
        language: str,
        timeout: int,
        log_level: str
    ) -> None:
        """Configura los componentes internos: scraper y logger, con validación de parámetros."""
        try:
            self._validate_inputs(language, timeout, log_level)
            self.scraper = WikiScraper(language=language, timeout=timeout)
            self._logger.debug("Componentes inicializados correctamente")
        except (LanguageNotSupportedError, ValueError) as e:
            self._logger.critical(f"Error de configuración: {e}", exc_info=True)
            raise CLIError(str(e)) from e

    def _validate_inputs(
        self,
        language: str,
        timeout: int,
        log_level: str
    ) -> None:
        """Valida los parámetros de entrada para la CLI."""
        if len(language) != 2 or not language.isalpha():
            raise ValueError(f"Código de idioma inválido: '{language}'. Debe ser un código ISO 639-1 de 2 letras (ej: 'es', 'en', 'fr').")

        if timeout <= 0:
            raise ValueError(f"Timeout inválido: {timeout}. Debe ser mayor a 0.")

        if log_level not in SUPPORTED_LOG_LEVELS:
            raise ValueError(f"Nivel de log inválido: '{log_level}'. Debe ser uno de: {SUPPORTED_LOG_LEVELS}")

    def execute_test_command(self) -> None:
        """
        Ejecuta un comando de prueba para verificar el funcionamiento básico de la CLI.
        """
        self._logger.info("Iniciando comando de prueba...")
        # click.secho("🎄", fg="green", bold=True, nl=False)   # Árbol de Navidad en verde brillante
        # click.secho(" ✨ ", fg="yellow", bold=False, nl=False) # Destellos amarillos suaves
        # click.secho("[ ", fg="white", nl=False)             # Corchete blanco
        # click.secho("PRUEBA", fg="red", bold=True, nl=False) # Texto "PRUEBA NAVIDEÑA" en rojo brillante
        # click.secho(" ]", fg="white", nl=False)             # Corchete blanco
        # click.secho(" ¿Ya es Navidad ", fg="white", nl=False) # Primera parte del mensaje en blanco
        # click.secho("🤨", fg="red", bold=True, nl=False)    # "100%" en rojo brillante
        # click.secho("?", fg="white", bold=False, nl=False)     # Exclamación en blanco suave
        # click.secho(" Sistema listo para las fiestas.", fg="white", italic=True, nl=False) # Frase final en cursiva blanca
        # click.secho(" 🎁🌟", fg="yellow", bold=True)      # Regalo y estrella dorados brillantes




        click.secho("🕸️ ", fg="white", nl=False)
        click.secho(" 👻 ", fg="white", nl=False)
        click.secho("[ ", fg="magenta", nl=False)
        click.secho("PRUEBA SPOOKY", fg="black", bg="yellow", bold=True, nl=False)
        click.secho(" ]", fg="magenta", nl=False)
        click.secho(" ¡Algo ha ido horriblemente... bien!", fg="magenta", bold=True, nl=False)
        click.secho(" 🎃🦇", fg="white", nl=True)
        self._logger.debug("Comando de prueba ejecutado con éxito")


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

        # Configuración del contexto de ejecución
        ctx.obj = WikiCLI(
            language=language,
            timeout=timeout,
            log_level=verbose.upper()
        )

        logging.getLogger(__name__).debug(
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
def prueba(ctx: click.Context) -> None:
    """
    Ejecuta un comando de prueba para verificar la instalación y configuración básica de la CLI.
    """
    try:
        cli_instance: WikiCLI = ctx.obj
        cli_instance.execute_test_command()
    except Exception as e:
        logging.getLogger(__name__).error("Error durante comando de prueba", exc_info=True) # Log completo del error
        click.secho(
            f"❌ Fallo en comando de prueba: {e}",
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