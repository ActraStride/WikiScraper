from src.utils import setup_logging
from src.wikiscraper import WikiScraper
from pathlib import Path




# Ejemplo de uso rápido
if __name__ == "__main__":
# Definir el directorio para los logs
    LOG_DIR = Path(__file__).resolve().parent # Dos niveles hacia arriba

    setup_logging(project_root=LOG_DIR)
    with WikiScraper() as scraper:
        try:
            internal_links = scraper.get_page_links("minecraft", link_type="linkshere")
            print(f"Enlaces internos: {internal_links[:10]}")  # Imprimir los primeros 10
        except Exception as e:
            print(f"Error al obtener la página: {e}")