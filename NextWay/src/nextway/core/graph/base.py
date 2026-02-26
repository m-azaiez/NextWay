from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Protocol, TypeVar, Hashable, runtime_checkable


NodeId = TypeVar("NodeId", bound=Hashable)


@dataclass(frozen=True, slots=True)
class Edge:
    """Directed edge u -> v with an associated traversal cost."""
    to: Hashable
    cost: float


@runtime_checkable
class Graph(Protocol[NodeId]):
    """
    Minimal graph contract for routing algorithms.

    Design rules:
    - Algorithms (A*, Dijkstra) must depend on this interface only.
    - Node IDs must be hashable (usable as dict keys).
    - neighbors(n) yields outgoing edges from n.
    """

    def neighbors(self, node: NodeId) -> Iterable[Edge]:
        """Return outgoing edges from `node`."""
        ...

    def has_node(self, node: NodeId) -> bool:
        """Fast membership check (useful for validation)."""
        ...