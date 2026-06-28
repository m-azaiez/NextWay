"""Shared result type and path reconstruction for the routing algorithms."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Hashable, List, Optional


@dataclass(frozen=True, slots=True)
class RouteResult:
    """A computed route: the ordered list of nodes and its total cost."""
    path: List[Hashable]
    cost: float


def reconstruct_path(
    came_from: Dict[Hashable, Hashable],
    start: Hashable,
    goal: Hashable,
) -> List[Hashable]:
    """Walk predecessor links from goal back to start, returned start->goal."""
    path: List[Hashable] = [goal]
    node = goal
    while node != start:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path
