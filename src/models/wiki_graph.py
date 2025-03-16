from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class WikiNode:
    """Represents a node in a Wikipedia page connection graph structure.
    
    Attributes:
        title: Canonical title of the Wikipedia page
        is_error: Flag indicating if page retrieval failed for this node
        metadata: Optional additional information about the node
    """
    title: str
    is_error: bool = field(default=False)
    metadata: Dict = field(default_factory=dict)


@dataclass
class WikiEdge:
    """Represents a directional connection between Wikipedia pages.
    
    Attributes:
        source: Title of the source page
        target: Title of the target page
        rel_type: Type of relationship (default: "LINKS_TO")
        metadata: Optional additional information about the relationship
    """
    source: str
    target: str
    rel_type: str = "LINKS_TO"
    metadata: Dict = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source, self.target, self.rel_type))

    
@dataclass
class WikiGraph:
    """Represents a graph structure of Wikipedia page connections.
    
    Pure data structure containing nodes and edges with basic access methods.
    
    Attributes:
        nodes: Repository of all nodes in the graph (title → node mapping)
        edges: List of all edges in the graph
        root_title: Entry point title of the graph exploration
        total_nodes: Cumulative count of nodes in the graph
        error_count: Total nodes that encountered retrieval errors
        max_depth_explored: Maximum depth level explored during mapping
    """
    nodes: Dict[str, WikiNode] = field(default_factory=dict)
    edges: List[WikiEdge] = field(default_factory=list)
    root_title: Optional[str] = None
    total_nodes: int = 0
    error_count: int = 0
    max_depth_explored: int = 0
    
    def get_node(self, title: str) -> Optional[WikiNode]:
        """Retrieves a node by its title.
        
        Args:
            title: Title of the node to retrieve
            
        Returns:
            Optional[WikiNode]: The node if found, None otherwise
        """
        return self.nodes.get(title)
    
    def get_outgoing_edges(self, source_title: str) -> List[WikiEdge]:
        """Retrieves all outgoing edges from a node.
        
        Args:
            source_title: Title of the source node
            
        Returns:
            List[WikiEdge]: List of outgoing edges
        """
        return [edge for edge in self.edges if edge.source == source_title]
    
    def get_incoming_edges(self, target_title: str) -> List[WikiEdge]:
        """Retrieves all incoming edges to a node.
        
        Args:
            target_title: Title of the target node
            
        Returns:
            List[WikiEdge]: List of incoming edges
        """
        return [edge for edge in self.edges if edge.target == target_title]
    
    def get_connected_nodes(self, title: str) -> Set[str]:
        """Retrieves all nodes directly connected to the specified node.
        
        Args:
            title: Title of the node
            
        Returns:
            Set[str]: Set of titles of connected nodes
        """
        outgoing = {edge.target for edge in self.get_outgoing_edges(title)}
        incoming = {edge.source for edge in self.get_incoming_edges(title)}
        return outgoing.union(incoming)