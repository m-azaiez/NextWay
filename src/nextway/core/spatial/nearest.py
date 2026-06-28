"""Snap an arbitrary (lat, lon) to the nearest node in the graph.

A user clicks anywhere on the map; that point is almost never exactly a graph
node. This index answers "which node is closest?".

Default backend is a linear scan with true haversine distance — O(n) per query,
perfectly fine for the demo grid and small extracts. For city-scale graphs,
construct with ``use_kdtree=True`` to use scipy's cKDTree (O(log n) per query)
if scipy is installed; it queries in lat/lon Euclidean space (a good enough
approximation for *nearest* node), and the reported distance is still recomputed
with haversine.
"""
from __future__ import annotations

from typing import Dict, Hashable, List, Tuple

from ..geometry.distance import haversine

Coords = Dict[Hashable, Tuple[float, float]]


class NearestIndex:
    def __init__(self, coords: Coords, use_kdtree: bool = False) -> None:
        if not coords:
            raise ValueError("cannot build a nearest index over an empty graph")
        self._coords = coords
        self._ids: List[Hashable] = list(coords.keys())
        self._kdtree = None
        if use_kdtree:
            self._try_build_kdtree()

    def _try_build_kdtree(self) -> None:
        try:
            import numpy as np
            from scipy.spatial import cKDTree
        except ImportError:
            self._kdtree = None
            return
        pts = np.array([self._coords[i] for i in self._ids])
        self._kdtree = cKDTree(pts)

    def nearest(self, lat: float, lon: float) -> Tuple[Hashable, float]:
        """Return (node_id, distance_in_metres) of the closest node."""
        if self._kdtree is not None:
            _, idx = self._kdtree.query([lat, lon])
            node = self._ids[int(idx)]
        else:
            node = min(
                self._ids,
                key=lambda n: haversine(lat, lon, *self._coords[n]),
            )
        nlat, nlon = self._coords[node]
        return node, haversine(lat, lon, nlat, nlon)
