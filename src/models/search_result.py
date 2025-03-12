from dataclasses import dataclass
from typing import List

@dataclass
class SearchResult:
    """
    Data model representing a Wikipedia search result.

    Attributes:
        title (str): The title of the Wikipedia article matching the search query.
    """
    title: str

    def __str__(self):
        """
        Returns the article title as a human-readable string representation.

        Simplifies printing and logging by directly showing the article title.

        Returns:
            str: The title of the search result article.
        """
        return self.title

@dataclass
class SearchResults:
    """
    Data model representing a collection of Wikipedia search results.

    Encapsulates a list of `SearchResult` objects and provides methods for
    result management and inspection, including emptiness checks, iteration,
    length retrieval, and indexed access.

    Attributes:
        results (List[SearchResult]): List of `SearchResult` objects,
                                      each representing a found Wikipedia article.
    """
    results: List[SearchResult]

    def __bool__(self):
        """
        Enables boolean evaluation of `SearchResults`.

        The object evaluates to `True` if it contains at least one result,
        and `False` if the results list is empty. Useful for quick result presence checks.

        Returns:
            bool: `True` if results exist, `False` otherwise.
        """
        return bool(self.results)

    def __iter__(self):
        """
        Enables direct iteration over contained search results.

        Makes `SearchResults` iterable, allowing use in `for` loops
        and other iterable contexts.

        Yields:
            SearchResult: Individual search result objects from the results list.
        """
        return iter(self.results)

    def __len__(self):
        """
        Returns the number of search results in the collection.

        Allows usage of standard `len()` function to retrieve result count.

        Returns:
            int: Number of search results contained.
        """
        return len(self.results)

    def __getitem__(self, index):
        """
        Provides indexed access to individual search results.

        Implements list-like index access (0-based) to retrieve specific results.
        Raises `IndexError` for out-of-range indices.

        Args:
            index (int): Positional index of the desired result (0-based).

        Returns:
            SearchResult: The search result at the specified index position.
        """
        return self.results[index]

    def __str__(self):
        """
        Returns a human-readable string representation of the search results.

        Format includes total result count and list of article titles,
        useful for debugging and logging purposes.

        Returns:
            str: Formatted string showing result count and titles.
        """
        return f"SearchResults(count={len(self)}, titles={[str(res) for res in self.results]})"