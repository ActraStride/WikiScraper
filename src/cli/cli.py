import click
import logging
import sys
from pathlib import Path
from src.wikiscraper import WikiScraper, LanguageNotSupportedError
from src.utils import setup_logging, LoggingSetupError

class WikiCLI:
    def __init__(self, language: str = "es", timeout: int = 15, verbose: str = "INFO") -> None:
        self.language = language
        self.timeout = timeout
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"WikiCLI inicializada con: Idioma={self.language}, Timeout={self.timeout}, Verbose={self.verbose}")
        try:
            self.scraper = WikiScraper(language=self.language, timeout=self.timeout)
            self.logger.debug("WikiScraper inicializado correctamente.")
        except LanguageNotSupportedError as e:
            click.secho(f"Error: {e}", fg='red', err=True)
            sys.exit(1)
    
    def prueba(self) -> None:
        self.logger.info("Ejecutando comando de prueba...")
        click.echo("¿Ya es navidad? 🎄🎇🎄")

# Definición del grupo de comandos a nivel de módulo
@click.group()
@click.option('--language', '-l', default='es', show_default=True, help='Código de idioma de Wikipedia.')
@click.option('--timeout', default=15, show_default=True, type=int, help='Tiempo máximo de espera para peticiones HTTP (segundos).')
@click.option('--verbose', '-v', default='INFO', show_default=True,
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), help="Nivel de logging.")
@click.pass_context
def cli(ctx: click.Context, language: str, timeout: int, verbose: str) -> None:
    # Configuramos el logging (ajusta la ruta según tu estructura de proyecto)
    LOG_DIR = Path(__file__).resolve().parent.parent.parent
    setup_logging(project_root=LOG_DIR)
    # Creamos la instancia de WikiCLI y la guardamos en el contexto
    ctx.obj = WikiCLI(language=language, timeout=timeout, verbose=verbose)

# Registro del subcomando "prueba"
@cli.command()
@click.pass_context
def prueba(ctx: click.Context) -> None:
    """Comando de prueba para verificar la instalación y configuración."""
    cli_instance: WikiCLI = ctx.obj
    cli_instance.prueba()

# La función main que será el punto de entrada de la CLI
def main() -> None:
    cli()

if __name__ == '__main__':
    main()