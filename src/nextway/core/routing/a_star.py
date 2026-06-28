"""A* shortest-path algorithm.

A* is Dijkstra guided by a heuristic estimate of the remaining cost. With an
admissible heuristic it returns the same optimal cost as Dijkstra, but usually
explores far fewer nodes.
"""
from __future__ import annotations

import heapq
import itertools
import math
from typing import Dict, Hashable, Optional

from ..graph.base import Graph
from .cost import CostFn, default_cost
from .heuristic import Heuristic, zero_heuristic
from .result import RouteResult, reconstruct_path


def shortest_path(
    graph: Graph,
    start: Hashable,
    goal: Hashable,
    heuristic: Heuristic = zero_heuristic,
    cost_fn: CostFn = default_cost,
) -> Optional[RouteResult]:
    """Return the cheapest route from ``start`` to ``goal`` using A*.

    With the default ``zero_heuristic`` this is exactly Dijkstra. Returns
    ``None`` if the goal is unreachable. Raises ``ValueError`` if ``start`` is
    not in the graph.
    """
    if not graph.has_node(start):
        raise ValueError(f"start node {start!r} is not in the graph")

    g_score: Dict[Hashable, float] = {start: 0.0}
    came_from: Dict[Hashable, Hashable] = {}
    closed: set = set()
    counter = itertools.count()
    frontier = [(heuristic(start), next(counter), start)]

    while frontier:
        _, _, node = heapq.heappop(frontier)
        if node in closed:
            continue
        closed.add(node)

        if node == goal:
            return RouteResult(
                reconstruct_path(came_from, start, goal), g_score[node]
            )

        for edge in graph.neighbors(node):
            tentative = g_score[node] + cost_fn(edge)
            if tentative < g_score.get(edge.to, math.inf):
                g_score[edge.to] = tentative
                came_from[edge.to] = node
                f = tentative + heuristic(edge.to)
                heapq.heappush(frontier, (f, next(counter), edge.to))

    return None
