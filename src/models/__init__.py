from .search_result import SearchResult, SearchResults
from .wiki_raw import WikipediaRawContent
from .wiki_tree import PageNode, PageTree
from .wiki_graph import WikiNode, WikiEdge, WikiGraph


# Exporta las funciones y clases que quieres que estén disponibles al importar 
__all__ = ["SearchResult", "SearchResults", "WikipediaRawContent", "PageNode", "PageTree", "WikiNode", "WikiEdge", "WikiGraph"]
