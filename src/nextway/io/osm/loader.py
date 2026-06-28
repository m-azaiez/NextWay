"""Load an OSM graph with on-disk caching.

Parsing a city-sized .osm file is slow, so we parse it once and pickle the
resulting (graph, coords). On later loads we reuse the pickle if it is newer
than the source file. This is what keeps API startup fast.
"""
from __future__ import annotations

import pickle
import time
from pathlib import Path
from typing import Tuple

from ...core.graph.adjacency import AdjacencyGraph
from .parser import Coords, parse_osm


def _cache_path(osm_path: Path) -> Path:
    return osm_path.with_suffix(osm_path.suffix + ".cache.pkl")


def load_osm_graph(
    path: str,
    use_cache: bool = True,
    drive_only: bool = True,
) -> Tuple[AdjacencyGraph, Coords]:
    """Return (graph, coords) for an .osm file, using a pickle cache.

    The cache is rebuilt automatically if the .osm file is newer than it.
    """
    osm_path = Path(path)
    if not osm_path.exists():
        raise FileNotFoundError(f"OSM file not found: {osm_path}")

    cache = _cache_path(osm_path)
    if use_cache and cache.exists() and cache.stat().st_mtime >= osm_path.stat().st_mtime:
        with cache.open("rb") as fh:
            return pickle.load(fh)

    graph, coords = parse_osm(str(osm_path), drive_only=drive_only)

    if use_cache:
        with cache.open("wb") as fh:
            pickle.dump((graph, coords), fh)

    return graph, coords
