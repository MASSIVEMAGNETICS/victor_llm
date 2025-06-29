# File: bandocodex/meta.py

"""
Meta-algebra, graph operations, and function composition tools
for the BandoCosmicCodex.
"""

from typing import Callable, Any, TypeVar, Iterable, Hashable, Set, Dict, List, Optional

T = TypeVar('T')

def compose(*functions: Callable[..., Any]) -> Callable[..., Any]:
    """
    Composes a sequence of functions.
    The functions are applied from right to left.
    For example, compose(f, g, h)(x) is equivalent to f(g(h(x))).

    Args:
        *functions: A sequence of functions to compose.

    Returns:
        A new function that is the composition of the input functions.
    """
    if not functions:
        raise ValueError("Composition requires at least one function.")

    def composed_function(x: Any) -> Any:
        result = x
        for func in reversed(functions):
            result = func(result)
        return result
    return composed_function


class Graph:
    """
    A simple directed graph implementation.
    Allows adding edges and performing Depth First Search (DFS).
    """

    def __init__(self):
        """Initializes an empty graph."""
        self.edges: Dict[Hashable, List[Hashable]] = {}

    def add_edge(self, u: Hashable, v: Hashable) -> None:
        """
        Adds a directed edge from node u to node v.

        Args:
            u: The source node.
            v: The destination node.
        """
        self.edges.setdefault(u, []).append(v)

    def dfs(self, start_node: Hashable, visited: Optional[Set[Hashable]] = None) -> Set[Hashable]:
        """
        Performs a Depth First Search (DFS) starting from a given node.

        Args:
            start_node: The node from which to start the DFS.
            visited: An optional set of already visited nodes.
                     Typically used for internal recursive calls.

        Returns:
            A set of all nodes visited during the DFS traversal.
        """
        if visited is None:
            visited = set()

        visited.add(start_node)
        for neighbor in self.edges.get(start_node, []):
            if neighbor not in visited:
                self.dfs(neighbor, visited)
        return visited

    def get_nodes(self) -> Set[Hashable]:
        """Returns a set of all nodes in the graph."""
        nodes = set(self.edges.keys())
        for destinations in self.edges.values():
            nodes.update(destinations)
        return nodes
