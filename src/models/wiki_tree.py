from dataclasses import dataclass, field
from typing import Dict, Optional, Set

@dataclass
class PageNode:
    """Represents a node in a Wikipedia page connection tree structure.
    
    Attributes:
        title: Canonical title of the Wikipedia page
        children: Child nodes representing linked pages (title → node mapping)
        is_error: Flag indicating if page retrieval failed for this node
        visited: Tracking set for cycle prevention in graph traversal
    """
    title: str
    children: Dict[str, 'PageNode'] = field(default_factory=dict)
    is_error: bool = field(default=False)
    visited: Set[str] = field(default_factory=set, init=False)

    def add_child(self, node: 'PageNode') -> None:
        """Adds a child node to the current node's connections.
        
        Args:
            node: PageNode to add as a child connection
        """
        self.children[node.title] = node

@dataclass
class PageTree:
    """Represents a hierarchical tree structure of Wikipedia page connections.
    
    Tracks traversal metrics and tree properties during mapping operations.
    
    Attributes:
        root: Entry point node of the tree structure
        total_nodes: Cumulative count of nodes in the tree
        error_count: Total nodes that encountered retrieval errors
        max_depth_reached: Maximum depth level explored in the hierarchy
    """
    root: Optional[PageNode] = None
    total_nodes: int = 0
    error_count: int = 0
    max_depth_reached: int = 0

    def update_metrics(self, depth: int) -> None:
        """Updates tree statistics after node insertion.
        
        Args:
            depth: Current depth level of the added node
        """
        self.max_depth_reached = max(self.max_depth_reached, depth)
        self.total_nodes += 1