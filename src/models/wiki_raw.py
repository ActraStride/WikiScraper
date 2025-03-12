from dataclasses import dataclass

@dataclass
class WikipediaRawContent:
    """
    Modelo de datos para representar el contenido crudo de un artículo de Wikipedia.

    Atributos:
        title (str): Título del artículo de Wikipedia.
        content (str): Contenido textual completo del artículo en formato crudo.
    """
    title: str
    content: str

    def __str__(self):
        """
        Retorna el título del artículo para una representación en string legible.
        
        Returns:
            str: Título del artículo, similar al comportamiento de SearchResult.
        """
        return self.title  # Mantenemos la misma lógica de representación simple