"""Cost model.

Defines how a single edge's traversal cost is computed. Right now this is a
thin pass-through over ``Edge.cost``, but it is the single place to later add
distance-vs-time routing, turn penalties, road-type weighting, etc., without
touching the search algorithms.
"""
from __future__ import annotations

from typing import Callable

from ..graph.base import Edge

# A cost function maps an edge to a non-negative traversal cost.
CostFn = Callable[[Edge], float]


def default_cost(edge: Edge) -> float:
    """Use the edge's own stored cost."""
    return edge.cost
