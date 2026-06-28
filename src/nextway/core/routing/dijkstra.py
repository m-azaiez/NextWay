"""Dijkstra's shortest-path algorithm.

This is the correctness baseline for the engine: given non-negative edge
costs, it always returns an optimal path. A* is validated against it.
"""
from __future__ import annotations

import heapq
import itertools
import math
from typing import Dict, Hashable, Optional

from ..graph.base import Graph
from .cost import CostFn, default_cost
from .result import RouteResult, reconstruct_path


def shortest_path(
    graph: Graph,
    start: Hashable,
    goal: Hashable,
    cost_fn: CostFn = default_cost,
) -> Optional[RouteResult]:
    """Return the cheapest route from ``start`` to ``goal``.

    Returns ``None`` if the goal is unreachable. Raises ``ValueError`` if
    ``start`` is not in the graph.
    """
    if not graph.has_node(start):
        raise ValueError(f"start node {start!r} is not in the graph")

    best: Dict[Hashable, float] = {start: 0.0}
    came_from: Dict[Hashable, Hashable] = {}
    visited: set = set()
    counter = itertools.count()  # tie-breaker so heap never compares node ids
    frontier = [(0.0, next(counter), start)]

    while frontier:
        dist, _, node = heapq.heappop(frontier)
        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            return RouteResult(reconstruct_path(came_from, start, goal), dist)

        for edge in graph.neighbors(node):
            new_dist = dist + cost_fn(edge)
            if new_dist < best.get(edge.to, math.inf):
                best[edge.to] = new_dist
                came_from[edge.to] = node
                heapq.heappush(frontier, (new_dist, next(counter), edge.to))

    return None
