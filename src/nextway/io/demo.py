"""A small geographic demo graph (a street grid) with real lat/lon coords.

Used so the API can be built and tested before wiring in real OSM data.
Nodes are laid out on a regular grid near central Paris; adjacent grid
points are connected in both directions, with cost = haversine distance.
"""
from __future__ import annotations

from typing import Dict, Tuple

from ..core.geometry.distance import haversine
from ..core.graph.adjacency import AdjacencyGraph

Coords = Dict[int, Tuple[float, float]]


def build_demo_geograph(
    rows: int = 6,
    cols: int = 6,
    lat0: float = 48.8566,
    lon0: float = 2.3522,
    step: float = 0.004,
) -> Tuple[AdjacencyGraph, Coords]:
    coords: Coords = {}
    grid: Dict[Tuple[int, int], int] = {}
    for r in range(rows):
        for c in range(cols):
            nid = r * cols + c
            coords[nid] = (lat0 + r * step, lon0 + c * step)
            grid[(r, c)] = nid

    g = AdjacencyGraph()
    for nid in coords:
        g.add_node(nid)

    def connect(a: int, b: int) -> None:
        d = haversine(*coords[a], *coords[b])
        g.add_edge(a, b, d)
        g.add_edge(b, a, d)

    for r in range(rows):
        for c in range(cols):
            a = grid[(r, c)]
            if c + 1 < cols:
                connect(a, grid[(r, c + 1)])
            if r + 1 < rows:
                connect(a, grid[(r + 1, c)])

    return g, coords
