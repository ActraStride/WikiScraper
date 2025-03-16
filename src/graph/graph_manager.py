from typing import Dict

from src.models import *
from src.errors.graph import *

class GraphManager:
    """Manages the creation and manipulation of WikiGraph objects.
    
    Handles all operations that modify the graph structure, separating
    the concerns of graph operations from the data structure itself.
    """
    
    def __init__(self, logger=None):
        """Initialize the GraphManager.
        
        Args:
            logger: Optional logger instance for tracking operations
        """
        self.logger = logger
    
    def create_graph(self, root_title: str) -> WikiGraph:
        """Creates a new graph with the given root title.
        
        Args:
            root_title: Title of the root page
            
        Returns:
            WikiGraph: A new graph with the root node added
            
        Raises:
            GraphCreationError: If the graph cannot be created
            InvalidTitleError: If the root title is invalid
        """
        if not root_title or not isinstance(root_title, str):
            if self.logger:
                self.logger.error(f"Invalid root title: {root_title}")
            raise InvalidTitleError(f"Invalid root title: {root_title}")
            
        try:
            graph = WikiGraph()
            graph.root_title = root_title
            self.add_node(graph, root_title)
            return graph
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create graph with root '{root_title}': {str(e)}")
            raise GraphCreationError(f"Failed to create graph with root '{root_title}': {str(e)}") from e
    
    def add_node(self, graph: WikiGraph, title: str, is_error: bool = False, 
                 metadata: Dict = None) -> WikiNode:
        """Adds a node to the graph if it doesn't exist or returns the existing one.
        
        Args:
            graph: The graph to modify
            title: Title of the Wikipedia page
            is_error: Flag indicating if page retrieval failed
            metadata: Optional additional information about the node
            
        Returns:
            WikiNode: The new or existing node
            
        Raises:
            InvalidTitleError: If the title is invalid
            NodeError: If there's an issue adding the node
        """
        if not title or not isinstance(title, str):
            if self.logger:
                self.logger.error(f"Invalid node title: {title}")
            raise InvalidTitleError(f"Invalid node title: {title}")
            
        try:
            if title in graph.nodes:
                return graph.nodes[title]
            
            node = WikiNode(
                title=title,
                is_error=is_error,
                metadata=metadata or {}
            )
            
            graph.nodes[title] = node
            graph.total_nodes += 1
            
            if is_error:
                graph.error_count += 1
                
            return node
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to add node '{title}': {str(e)}")
            raise NodeError(f"Failed to add node '{title}': {str(e)}") from e
    
    def add_relationship(self, graph: WikiGraph, source_title: str, target_title: str, 
                         rel_type: str = "LINKS_TO", metadata: Dict = None) -> WikiEdge:
        """Creates a relationship (edge) between two nodes.
        
        Args:
            graph: The graph to modify
            source_title: Title of the source node
            target_title: Title of the target node
            rel_type: Type of relationship
            metadata: Optional additional information about the relationship
            
        Returns:
            WikiEdge: The newly created edge
            
        Raises:
            InvalidTitleError: If either title is invalid
            NodeError: If either node doesn't exist in the graph
            RelationshipError: If there's an issue adding the relationship
        """
        if not source_title or not isinstance(source_title, str):
            if self.logger:
                self.logger.error(f"Invalid source title: {source_title}")
            raise InvalidTitleError(f"Invalid source title: {source_title}")
            
        if not target_title or not isinstance(target_title, str):
            if self.logger:
                self.logger.error(f"Invalid target title: {target_title}")
            raise InvalidTitleError(f"Invalid target title: {target_title}")
            
        try:
            # Ensure both nodes exist
            if source_title not in graph.nodes:
                if self.logger:
                    self.logger.error(f"Source node '{source_title}' not found in graph")
                raise NodeError(f"Source node '{source_title}' not found in graph")
                
            if target_title not in graph.nodes:
                if self.logger:
                    self.logger.error(f"Target node '{target_title}' not found in graph")
                raise NodeError(f"Target node '{target_title}' not found in graph")
            
            edge = WikiEdge(
                source=source_title,
                target=target_title,
                rel_type=rel_type,
                metadata=metadata or {}
            )
            
            graph.edges.append(edge)
            return edge
        except NodeError:
            # Re-raise NodeError as is
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to add relationship from '{source_title}' to '{target_title}': {str(e)}")
            raise RelationshipError(f"Failed to add relationship from '{source_title}' to '{target_title}': {str(e)}") from e
    
    def add_link(self, graph: WikiGraph, source_title: str, target_title: str) -> None:
        """Adds a link relationship between source and target pages.
        
        Args:
            graph: The graph to modify
            source_title: Title of the source page
            target_title: Title of the target page
            
        Raises:
            InvalidTitleError: If either title is invalid
            NodeError: If the source node doesn't exist
            RelationshipError: If there's an issue adding the relationship
        """
        try:
            # Add target node if it doesn't exist
            self.add_node(graph, target_title)
            # Create a LINKS_TO relationship
            self.add_relationship(graph, source_title, target_title, "LINKS_TO")
        except (InvalidTitleError, NodeError, RelationshipError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to add link from '{source_title}' to '{target_title}': {str(e)}")
            raise RelationshipError(f"Failed to add link from '{source_title}' to '{target_title}': {str(e)}") from e
    
    def add_error_node(self, graph: WikiGraph, source_title: str) -> None:
        """Adds an error node connected to the source page.
        
        Args:
            graph: The graph to modify
            source_title: Title of the source page
            
        Raises:
            InvalidTitleError: If the source title is invalid
            NodeError: If the source node doesn't exist
            RelationshipError: If there's an issue adding the relationship
        """
        try:
            error_title = f"[ERROR] {source_title}"
            self.add_node(graph, error_title, is_error=True)
            self.add_relationship(graph, source_title, error_title, "ERROR")
        except (InvalidTitleError, NodeError, RelationshipError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to add error node for '{source_title}': {str(e)}")
            raise NodeError(f"Failed to add error node for '{source_title}': {str(e)}") from e
    
    def update_metrics(self, graph: WikiGraph, depth: int) -> None:
        """Updates graph statistics after exploration.
        
        Args:
            graph: The graph to update
            depth: Current depth level of exploration
        """
        try:
            graph.max_depth_explored = max(graph.max_depth_explored, depth)
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to update graph metrics: {str(e)}")
            # Non-critical operation, so just log and continue