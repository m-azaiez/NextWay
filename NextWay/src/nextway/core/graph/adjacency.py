# src/nextway/core/graph/adjacency.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Hashable, Iterable, List

from .base import Edge, Graph


@dataclass(slots=True)
class AdjacencyGraph(Graph[Hashable]):
    """
    Simple in-memory directed weighted graph.

    Storage:
      adjacency[u] = [Edge(to=v, cost=c), ...]
    """

    _adjacency: Dict[Hashable, List[Edge]] = field(default_factory=dict)

    def add_node(self, node: Hashable) -> None:
        """Ensure `node` exists in the graph (even if it has no outgoing edges)."""
        self._adjacency.setdefault(node, [])

    def add_edge(self, u: Hashable, v: Hashable, cost: float) -> None:
        """Add a directed edge u -> v with given cost."""
        if cost < 0:
            raise ValueError("Edge cost must be non-negative for Dijkstra/A*.")
        self.add_node(u)
        self.add_node(v)
        self._adjacency[u].append(Edge(to=v, cost=float(cost)))

    def neighbors(self, node: Hashable) -> Iterable[Edge]:
        return self._adjacency.get(node, [])

    def has_node(self, node: Hashable) -> bool:
        return node in self._adjacency