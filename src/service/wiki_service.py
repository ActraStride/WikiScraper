"""
Module Name: wiki_service

Service layer for interacting with Wikipedia data, abstracting the core logic
from the user interface (CLI, API, etc.).

This module provides a centralized service to:
- Perform searches on Wikipedia
- Retrieve page content (raw text)
- Map internal links within Wikipedia pages
- Handle service-specific errors robustly
- Provide structured logging of service operations

Example (Simplified - Focuses on module usage):
    >>> from src.service.wiki_service import WikiService, SearchServiceError
    >>> from src.wikiscraper import WikiScraper
    >>> from src.storage import FileSaver
    >>> import logging
    >>> logger = logging.getLogger(__name__) # Or your configured logger
    >>> # Assume scraper and file_saver are already initialized and configured elsewhere
    >>> # For example (you would typically configure logger and other params):
    >>> # logger = setup_logging()
    >>> scraper = WikiScraper(language="es", timeout=10, logger=logger)
    >>> file_saver = FileSaver(output_dir="./output", logger=logger)
    >>> service = WikiService(scraper=scraper, file_saver=file_saver, logger=logger)
    >>> try:
    >>>     search_results = service.search_articles(query="Python programación")
    >>>     if search_results:
    >>>         print(f"Search results: {search_results}")
    >>>     else:
    >>>         print("No articles found for the query.")
    >>> except SearchServiceError as e:
    >>>     print(f"Search failed: {e}")
"""

import logging
from typing import List, Dict, Set

from src.wikiscraper import WikiScraper, WikiScraperError  
from src.graph import GraphManager 
from src.models import *
from pathlib import Path 

from src.errors.service import *

class WikiService:
    """Provides a centralized service to interact with Wikipedia.

    Abstracts the business logic for Wikipedia interactions, providing a clean
    interface for Wikipedia-related operations.

    This service utilizes `WikiScraper` to access Wikipedia information and
    `FileSaver` for saving operations when necessary. It is designed to decouple
    the logic of the CLI, API, or any other user interface from the core
    functionality of scraping and processing Wikipedia data.

    Attributes:
        scraper (WikiScraper): An instance of WikiScraper used for fetching
            data from Wikipedia.
        file_saver (FileSaver): An instance of FileSaver used for saving
            content to the file system.
        logger (logging.Logger): A logger instance for logging service events
            and errors.

    Methods:
        
    """

    def __init__(self, scraper: 'WikiScraper', graph_manager: 'GraphManager', logger: logging.Logger) -> None:
        """Initializes the WikiService with its dependencies.

        The WikiService depends on a `WikiScraper` for fetching data from
        Wikipedia and a `FileSaver` for persisting data to the filesystem.
        It also uses a logger for internal logging and error reporting.

        Args:
            scraper: A pre-configured and initialized instance of WikiScraper.
                     Responsible for making requests to Wikipedia and extracting data.
            file_saver: A pre-configured and initialized instance of FileSaver.
                      Responsible for saving content to the file system, if needed.
            logger: A pre-configured logger instance for the system.
                    Used for logging events, errors, and debugging within the service.
        """
        self.scraper = scraper
        self.graph_manager = graph_manager 
        self.logger = logger
        self.logger.debug("WikiService initialized successfully.")


    def search_articles(self, query: str, limit: int = 5) -> SearchResults:
        """Searches Wikipedia for articles matching the given query.

        Initiates a search on Wikipedia using the provided query string.
        It uses the `WikiScraper` to perform the search and returns a list
        of article titles that match the query, up to the specified limit.

        Args:
            query: The search term to look up on Wikipedia.
            limit: The maximum number of search results to return. Defaults to 5.

        Returns:
            SearchResults: A SearchResults object containing a list of SearchResult objects,
                           each representing a Wikipedia article title that matches the search query.
                           Returns an empty SearchResults object if no results are found.

        Raises:
            SearchServiceError: If any error occurs during the Wikipedia search operation.
                                 This exception encapsulates lower-level exceptions like
                                 `WikiScraperError` to provide a service-level error abstraction.
        """
        self.logger.info(f"Starting article search for: '{query}' (limit: {limit} results).")
        try:
            results_titles: List[str] = self.scraper.search_wikipedia(query=query, limit=limit)
            if not results_titles:
                self.logger.warning(f"No articles found for search query: '{query}'.")
                return SearchResults(results=[])  # Return empty SearchResults
            search_results_list: List[SearchResult] = [SearchResult(title=title) for title in results_titles] # Create SearchResult objects
            search_results = SearchResults(results=search_results_list) # Encapsulate in SearchResults
            self.logger.debug(f"Search for '{query}' completed, found {len(search_results)} articles.")
            return search_results
        except WikiScraperError as e:  # Catch specific scraper errors
            self.logger.error(f"Error searching articles for '{query}': {e}", exc_info=True)
            raise SearchServiceError(f"Error during article search: {e}") from e  # Re-raise as service error
        except Exception as e:  # Catch any other unexpected errors
            self.logger.critical(f"UNEXPECTED error during article search for '{query}': {e}", exc_info=True)
            raise SearchServiceError(f"Unexpected error in article search: {e}") from e
        
    
    def get_article_raw_content(self, query: str) -> WikipediaRawContent:
        """Retrieves the raw text content of the first Wikipedia article matching the query.

        Searches Wikipedia for articles matching the given query and retrieves
        the plain text content of the top result. If no articles are found or
        if the content retrieval fails, it returns an empty `WikipediaRawContent`
        object or raises a `PageContentServiceError` in case of errors.

        Args:
            query: The search term to find a Wikipedia article for.

        Returns:
            WikipediaRawContent: An object containing the title and raw text
                                 content of the article. If no article is found
                                 or content cannot be retrieved, the content
                                 attribute will be an empty string.

        Raises:
            PageContentServiceError: If an error occurs while fetching the article content.
                                     This could be due to issues with the WikiScraper
                                     or network problems.
        """
        self.logger.info(f"Fetching article content for: '{query}'")

        try:
            # First, search for the article
            search_results = self.scraper.search_wikipedia(query=query, limit=1)

            if not search_results:
                self.logger.warning(f"No articles found for search query: '{query}'")
                return WikipediaRawContent(title="", content="")

            # Get the title of the first result
            page_title = search_results[0]
            self.logger.info(f"First search result: '{page_title}'. Getting article text...")

            # Get the content of the article
            page_text = self.scraper.get_page_raw_text(page_title=page_title)

            if not page_text:
                self.logger.warning(f"Could not retrieve text for article '{page_title}'")
                return WikipediaRawContent(title=page_title, content="")

            self.logger.info(f"Successfully retrieved content for article '{page_title}'")
            return WikipediaRawContent(title=page_title, content=page_text)

        except WikiScraperError as e:
            self.logger.error(f"Error retrieving content for '{query}': {e}", exc_info=True)
            raise PageContentServiceError(f"Error retrieving article content: {e}") from e
        except Exception as e:
            self.logger.critical(f"UNEXPECTED error retrieving content for '{query}': {e}", exc_info=True)
            raise PageContentServiceError(f"Unexpected error retrieving article content: {e}") from e
        

    def map_page_links(
        self,
        root_title: str,
        max_depth: int,
        include_errors: bool = False
    ) -> PageTree:
        """
        Recursively maps the internal links of a Wikipedia page up to a specified depth.

        Args:
            root_title: Title of the root page for mapping.
            max_depth: Maximum recursion depth (must be >= 1).
            include_errors: If True, includes nodes that encountered scraping errors.

        Returns:
            PageTree: A tree structure representing the complete mapping.

        Raises:
            PageMappingServiceError: If a critical error occurs during the mapping process.
        """
        self.logger.info(f"Mapping page tree for '{root_title}' (depth: {max_depth})")
        
        if max_depth < 1:
            raise PageMappingServiceError("Depth must be at least 1")

        try:
            root_node = PageNode(title=root_title)
            visited = set()
            
            self._recursive_link_mapping(
                current_node=root_node,
                current_depth=1,
                max_depth=max_depth,
                visited=visited,
                include_errors=include_errors
            )
            
            return PageTree(root=root_node)
        
        except Exception as e:
            self.logger.error(f"Critical mapping error: {str(e)}", exc_info=True)
            raise PageMappingServiceError(f"Page mapping failed: {str(e)}") from e


    def _recursive_link_mapping(
        self,
        current_node: PageNode,
        current_depth: int,
        max_depth: int,
        visited: set,
        include_errors: bool
    ) -> None:
        """
        Internal recursive function for mapping page links.

        Args:
            current_node: The current page node being processed.
            current_depth: The current recursion depth.
            max_depth: The maximum allowed recursion depth.
            visited: A set of page titles that have already been visited.
            include_errors: Flag indicating whether to include nodes that encountered scraping errors.
        """
        if current_depth > max_depth:
            return

        if current_node.title in visited:
            self.logger.debug(f"Skipping already visited page: {current_node.title}")
            return

        visited.add(current_node.title)
        self.logger.debug(f"Processing page: {current_node.title} (depth {current_depth})")

        try:
            links = self.scraper.get_page_links(
                page_title=current_node.title,
                link_type="internal"
            )
        except WikiScraperError as e:
            self.logger.warning(f"Error retrieving links for {current_node.title}: {str(e)}")
            if include_errors:
                error_node = PageNode(title=f"[ERROR] {current_node.title}")
                current_node.add_child(error_node)
            return

        for link_title in links:
            if link_title in visited:
                continue

            child_node = PageNode(title=link_title)
            current_node.add_child(child_node)
            
            self._recursive_link_mapping(
                current_node=child_node,
                current_depth=current_depth + 1,
                max_depth=max_depth,
                visited=visited,
                include_errors=include_errors
            )

    def map_page_graph(
            self,
            root_title: str,
            max_depth: int,
            include_errors: bool = False
        ) -> WikiGraph:
        """
        Recursively maps the internal links of a Wikipedia page into a graph up to a specified depth.
        
        Args:
            root_title: Title of the root page for mapping.
            max_depth: Maximum recursion depth (must be >= 1).
            include_errors: If True, includes nodes that encountered scraping errors.
            
        Returns:
            WikiGraph: A graph structure representing the complete mapping.
            
        Raises:
            PageMappingServiceError: If a critical error occurs during the mapping process.
        """
        self.logger.info(f"Mapping page graph for '{root_title}' (depth: {max_depth})")
        
        if max_depth < 1:
            raise PageMappingServiceError("Depth must be at least 1")
            
        try:
            graph = self.graph_manager.create_graph(root_title)
            
            # Track visited nodes during exploration (for traversal control only)
            exploration_visited = set()
            
            self._recursive_graph_mapping(
                current_title=root_title,
                graph=graph,
                current_depth=1,
                max_depth=max_depth,
                exploration_visited=exploration_visited,
                include_errors=include_errors
            )
            
            return graph
            
        except Exception as e:
            self.logger.error(f"Critical mapping error: {str(e)}", exc_info=True)
            raise PageMappingServiceError(f"Page mapping failed: {str(e)}") from e
    
    def _recursive_graph_mapping(
        self,
        current_title: str,
        graph: WikiGraph,
        current_depth: int,
        max_depth: int,
        exploration_visited: set,
        include_errors: bool
    ) -> None:
        """
        Internal recursive function for mapping page links into a graph.
        
        Args:
            current_title: The title of the current page being processed.
            graph: The graph being built.
            current_depth: The current recursion depth.
            max_depth: The maximum allowed recursion depth.
            exploration_visited: A set of page titles that have already been visited during exploration.
            include_errors: Flag indicating whether to include nodes that encountered scraping errors.
        """
        if current_depth > max_depth:
            return
            
        if current_title in exploration_visited:
            self.logger.debug(f"Skipping already visited page during exploration: {current_title}")
            return
            
        exploration_visited.add(current_title)
        self.graph_manager.update_metrics(graph, current_depth)
        
        self.logger.debug(f"Processing page: {current_title} (depth {current_depth})")
        
        try:
            links = self.scraper.get_page_links(
                page_title=current_title,
                link_type="internal"
            )
            
            for link_title in links:
                # Add the link using the graph manager
                self.graph_manager.add_link(graph, current_title, link_title)
                
                # Only explore deeper if we haven't visited this page and we're not at max depth
                if link_title not in exploration_visited and current_depth < max_depth:
                    self._recursive_graph_mapping(
                        current_title=link_title,
                        graph=graph,
                        current_depth=current_depth + 1,
                        max_depth=max_depth,
                        exploration_visited=exploration_visited,
                        include_errors=include_errors
                    )
                    
        except WikiScraperError as e:
            self.logger.warning(f"Error retrieving links for {current_title}: {str(e)}")
            if include_errors:
                self.graph_manager.add_error_node(graph, current_title)