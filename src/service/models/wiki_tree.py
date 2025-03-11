# # src/service/models.py
# from dataclasses import dataclass, field
# from typing import Dict, Optional, Set

# @dataclass
# class PageNode:
#     """Nodo que representa una página Wikipedia y sus enlaces"""
#     title: str
#     children: Dict[str, 'PageNode'] = field(default_factory=dict)
#     is_error: bool = field(default=False)
#     visited: Set[str] = field(default_factory=set, init=False)

#     def add_child(self, node: 'PageNode') -> None:
#         self.children[node.title] = node

# @dataclass
# class PageTree:
#     """Estructura de árbol para el mapeo de páginas"""
#     root: Optional[PageNode] = None
#     total_nodes: int = 0
#     error_count: int = 0
#     max_depth_reached: int = 0

#     def update_metrics(self, depth: int) -> None:
#         self.max_depth_reached = max(self.max_depth_reached, depth)
#         self.total_nodes += 1