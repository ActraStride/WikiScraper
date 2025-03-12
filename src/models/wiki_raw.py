from dataclasses import dataclass

@dataclass
class WikipediaRawContent:
    """
    Data model representing the raw content of a Wikipedia article.

    Encapsulates unprocessed article content typically obtained directly from
    Wikipedia's API before any parsing or transformation.

    Attributes:
        title (str): Canonical title of the Wikipedia article
        content (str): Raw textual content of the article (unprocessed markup format)
    """
    title: str
    content: str

    def __str__(self) -> str:
        """
        Provides a human-readable string representation of the article.

        Maintains consistent string representation with other Wikipedia models
        by returning only the article title for simplicity and readability.

        Returns:
            Article title as string identifier
        """
        return self.title