from src.models import *

class GraphManager:
    """Manages the creation and manipulation of WikiGraph objects."""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def create_graph(self, root_title: str) -> WikiGraph:
        """Creates a new graph with the given root title."""
        graph = WikiGraph()
        graph.root_title = root_title
        graph.add_or_get_node(root_title)
        return graph
        
    def add_link(self, graph: WikiGraph, source_title: str, target_title: str) -> None:
        """Adds a link relationship between source and target pages."""
        # Add target node if it doesn't exist
        graph.add_or_get_node(target_title)
        
        # Create a LINKS_TO relationship
        graph.add_relationship(source_title, target_title, "LINKS_TO")
    
    def add_error_node(self, graph: WikiGraph, source_title: str) -> None:
        """Adds an error node connected to the source page."""
        error_title = f"[ERROR] {source_title}"
        graph.add_or_get_node(error_title, is_error=True)
        graph.add_relationship(source_title, error_title, "ERROR")


class WikiService:
    def __init__(self, scraper, logger=None):
        self.scraper = scraper
        self.logger = logger
        self.graph_manager = GraphManager(logger)
    
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
            # Create a new graph with the root node
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
        graph.update_metrics(current_depth)
        
        self.logger.debug(f"Processing page: {current_title} (depth {current_depth})")
        
        try:
            links = self.scraper.get_page_links(
                page_title=current_title,
                link_type="internal"
            )
            
            for link_title in links:
                # Add the link to the graph
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


