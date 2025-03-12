from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class WikipediaSection:
    """
    Modelo de datos para representar una sección de un artículo de Wikipedia.
    
    Atributos:
        title (str): El título de la sección.
        content (str): El contenido textual de la sección.
        level (int): El nivel de jerarquía de la sección (1 para secciones principales, 2+ para subsecciones).
        subsections (List['WikipediaSection']): Lista de subsecciones contenidas en esta sección.
    """
    title: str
    content: str
    level: int
    subsections: List['WikipediaSection'] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
    
    def __str__(self):
        """
        Retorna una representación en string legible de la sección.
        
        Returns:
            str: El título de la sección.
        """
        return self.title

@dataclass
class WikipediaArticle:
    """
    Modelo de datos para representar un artículo completo de Wikipedia.
    
    Encapsula toda la información relevante de un artículo de Wikipedia,
    incluyendo su título, contenido, secciones, enlaces, referencias,
    y metadatos como la fecha de última edición.
    
    Atributos:
        title (str): El título del artículo.
        page_id (int): El identificador único del artículo en Wikipedia.
        summary (str): Un resumen breve del contenido del artículo.
        content (str): El contenido completo del artículo en texto plano.
        url (str): La URL del artículo en Wikipedia.
        last_edited (datetime): Fecha y hora de la última edición del artículo.
        sections (List[WikipediaSection]): Lista de secciones del artículo.
        categories (List[str]): Lista de categorías a las que pertenece el artículo.
        links (List[str]): Lista de enlaces internos a otros artículos de Wikipedia.
        external_links (List[str]): Lista de enlaces externos referenciados en el artículo.
        images (List[str]): Lista de URLs de imágenes incluidas en el artículo.
        references (List[str]): Lista de referencias bibliográficas del artículo.
        infobox (Dict[str, str]): Información estructurada del artículo (datos de la caja de información).
        languages (Dict[str, str]): Diccionario de enlaces a versiones del artículo en otros idiomas.
    """
    title: str
    page_id: int
    summary: str
    content: str
    url: str
    last_edited: datetime
    sections: List[WikipediaSection]
    categories: List[str]
    links: List[str]
    external_links: List[str]
    images: List[str]
    references: List[str]
    infobox: Dict[str, str]
    languages: Dict[str, str]
    
    def __str__(self):
        """
        Retorna una representación en string legible del artículo.
        
        Returns:
            str: Una cadena que muestra el título del artículo y su URL.
        """
        return f"WikipediaArticle(title={self.title}, url={self.url})"
    
    def get_section(self, section_title: str) -> Optional[WikipediaSection]:
        """
        Busca y devuelve una sección específica del artículo por su título.
        
        La búsqueda se realiza de forma recursiva en todas las secciones y subsecciones.
        
        Args:
            section_title (str): El título de la sección a buscar.
            
        Returns:
            Optional[WikipediaSection]: La sección encontrada o None si no existe.
        """
        def search_in_sections(sections, title):
            for section in sections:
                if section.title.lower() == title.lower():
                    return section
                
                if section.subsections:
                    result = search_in_sections(section.subsections, title)
                    if result:
                        return result
            return None
        
        return search_in_sections(self.sections, section_title)
    
    def has_category(self, category: str) -> bool:
        """
        Verifica si el artículo pertenece a una categoría específica.
        
        Args:
            category (str): El nombre de la categoría a verificar.
            
        Returns:
            bool: True si el artículo pertenece a la categoría, False en caso contrario.
        """
        return any(cat.lower() == category.lower() for cat in self.categories)
    
    def count_references(self) -> int:
        """
        Cuenta el número total de referencias bibliográficas en el artículo.
        
        Returns:
            int: El número de referencias bibliográficas.
        """
        return len(self.references)
    
    def get_main_sections(self) -> List[WikipediaSection]:
        """
        Devuelve las secciones principales del artículo (nivel 1).
        
        Returns:
            List[WikipediaSection]: Lista de secciones principales.
        """
        return [section for section in self.sections if section.level == 1]
    
    def get_translation_url(self, language_code: str) -> Optional[str]:
        """
        Obtiene la URL del artículo en otro idioma.
        
        Args:
            language_code (str): El código del idioma (por ejemplo, 'en', 'fr', 'de').
            
        Returns:
            Optional[str]: La URL del artículo en el idioma especificado,
                          o None si no existe traducción para ese idioma.
        """
        return self.languages.get(language_code)