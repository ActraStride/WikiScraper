# src/cli/cli.py

"""
Módulo CLI para interactuar con WikiScraper y realizar operaciones sobre Wikipedia.

Este módulo proporciona una interfaz de línea de comandos (CLI) para interactuar
con la clase WikiScraper, permitiendo a los usuarios realizar diversas 
operaciones relacionadas con la extracción de información de Wikipedia, 
como buscar artículos, obtener resúmenes, y más.  La CLI se construye usando
el paquete `click`.

"""

import click
from src.wikiscraper import WikiScraper  # Importa la clase principal
import logging

# Configuración del logger
logger = logging.getLogger(__name__)

@click.group()
def wiki():
    """
    Grupo de comandos principal para la aplicación WikiScraper.

    Este grupo actúa como el punto de entrada principal para la CLI.
    Todos los comandos definidos dentro de este grupo se invocarán
    usando `wiki <comando>`.
    
    Ejemplo:
        wiki prueba 
    """
    pass

@wiki.command()
def prueba():
    """
    Comando de prueba para verificar la instalación y configuración de la CLI.

    Este comando simplemente imprime un mensaje de prueba en la consola.
    Es útil para asegurar que la CLI esté funcionando correctamente.
    
    Ejemplo:
        wiki prueba
    """
    click.echo('¿Ya es navidad? 🎄🎇🎄')

if __name__ == '__main__':
    wiki()  # Punto de entrada principal al ejecutar el script.