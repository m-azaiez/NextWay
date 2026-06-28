"""A* heuristics.

A heuristic estimates the remaining cost from a node to the goal. To keep A*
correct (optimal), the heuristic must be *admissible*: it must never
overestimate the true remaining cost.
"""
from __future__ import annotations

from typing import Callable, Dict, Hashable, Tuple

from ..geometry.distance import haversine

# A heuristic maps a node to an estimated remaining cost to the goal.
Heuristic = Callable[[Hashable], float]


def zero_heuristic(_node: Hashable) -> float:
    """Always 0. Makes A* behave exactly like Dijkstra (the safe baseline)."""
    return 0.0


def haversine_heuristic(
    coords: Dict[Hashable, Tuple[float, float]],
    goal: Hashable,
) -> Heuristic:
    """Straight-line-distance heuristic for geographic graphs.

    ``coords`` maps each node id to a (lat, lon) pair. Admissible as long as
    edge costs are real-world distances in metres.
    """
    glat, glon = coords[goal]

    def h(node: Hashable) -> float:
        lat, lon = coords[node]
        return haversine(lat, lon, glat, glon)

    return h
