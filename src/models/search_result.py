from dataclasses import dataclass
from typing import List

@dataclass
class SearchResult:
    """
    Modelo de datos para representar un resultado de búsqueda de Wikipedia.

    Atributos:
        title (str): El título del artículo de Wikipedia que es un resultado de búsqueda.
    """
    title: str

    def __str__(self):
        """
        Retorna el título del artículo para una representación en string legible.

        Esto facilita la impresión del objeto `SearchResult` en ejemplos y logs,
        mostrando directamente el título del artículo.

        Returns:
            str: El título del artículo de búsqueda.
        """
        return self.title # Para facilitar la impresión en ejemplos y logs

@dataclass
class SearchResults:
    """
    Modelo de datos para representar una lista de resultados de búsqueda de Wikipedia.

    Encapsula una lista de objetos `SearchResult` y proporciona métodos para
    facilitar el manejo y la inspección de la lista de resultados, como
    verificar si la lista está vacía, iterar sobre los resultados,
    obtener la cantidad de resultados y acceder a resultados individuales por índice.

    Atributos:
        results (List[SearchResult]): Una lista de objetos `SearchResult`,
                                     cada uno representando un artículo encontrado en la búsqueda.
    """
    results: List[SearchResult]

    def __bool__(self):
        """
        Permite evaluar `SearchResults` como booleano.

        Un objeto `SearchResults` se considera `True` si contiene al menos un resultado,
        y `False` si la lista de resultados está vacía. Esto es útil para verificar
        rápidamente si una búsqueda devolvió algún resultado.

        Returns:
            bool: `True` si hay resultados en la lista, `False` en caso contrario.
        """
        return bool(self.results)

    def __iter__(self):
        """
        Permite iterar directamente sobre los resultados contenidos en `SearchResults`.

        Esto hace que un objeto `SearchResults` sea iterable, permitiendo usarlo
        en bucles `for` y otras construcciones que requieren iterables,
        iterando sobre los objetos `SearchResult` individuales.

        Yields:
            SearchResult: Cada objeto `SearchResult` en la lista de resultados.
        """
        return iter(self.results)

    def __len__(self):
        """
        Devuelve el número de resultados de búsqueda contenidos en `SearchResults`.

        Esto permite obtener la cantidad de artículos encontrados en la búsqueda
        simplemente usando la función `len()` en un objeto `SearchResults`.

        Returns:
            int: El número de resultados de búsqueda en la lista.
        """
        return len(self.results)

    def __getitem__(self, index):
        """
        Permite acceder a un resultado específico por su índice.

        Funciona como el acceso por índice en una lista estándar de Python,
        permitiendo obtener un objeto `SearchResult` específico de la lista
        utilizando su posición (índice).

        Args:
            index (int): El índice del resultado a obtener (basado en 0).

        Returns:
            SearchResult: El objeto `SearchResult` en la posición del índice especificado.
                          Levanta `IndexError` si el índice está fuera de rango.
        """
        return self.results[index]

    def __str__(self):
        """
        Retorna una representación en string legible del objeto `SearchResults`.

        Esta representación incluye el número total de resultados y una lista de los
        títulos de los artículos encontrados, facilitando la lectura en logs,
        mensajes de depuración y ejemplos.

        Returns:
            str: Una cadena formateada que representa el objeto `SearchResults`,
                 incluyendo el conteo de resultados y una lista de títulos.
        """
        return f"SearchResults(count={len(self)}, titles={[str(res) for res in self.results]})"