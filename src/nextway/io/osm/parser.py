"""Parse an OpenStreetMap XML extract (.osm) into a routing graph.

This is intentionally dependency-free (standard-library ``xml.etree``) and
aimed at small extracts for development. For large .pbf files, swap in a
library like ``pyrosm`` or ``osmnx`` behind the same return signature.

What it does:
  * reads every <node> to get its (lat, lon)
  * reads every routable <way> (those tagged with `highway=...`)
  * turns each consecutive pair of nodes in a way into graph edges, with cost
    = great-circle distance in metres
  * respects `oneway=yes/-1`; otherwise adds edges in both directions

Returns ``(graph, coords)`` where ``coords`` maps node id -> (lat, lon), ready
to feed the haversine A* heuristic.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Dict, Tuple

from ...core.geometry.distance import haversine
from ...core.graph.adjacency import AdjacencyGraph

Coords = Dict[int, Tuple[float, float]]

# Highway types we don't want to route over by default.
_EXCLUDED_HIGHWAYS = {
    "footway", "pedestrian", "steps", "path", "cycleway",
    "bridleway", "construction", "proposed",
}


def _way_tags(way: ET.Element) -> Dict[str, str]:
    return {t.get("k"): t.get("v") for t in way.findall("tag")}


def parse_osm(path: str, drive_only: bool = True) -> Tuple[AdjacencyGraph, Coords]:
    """Build a graph from an .osm XML file at ``path``.

    ``drive_only`` skips footways/cycleways and similar non-drivable ways.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    coords: Coords = {}
    for node in root.findall("node"):
        nid = int(node.get("id"))
        coords[nid] = (float(node.get("lat")), float(node.get("lon")))

    graph = AdjacencyGraph()

    for way in root.findall("way"):
        tags = _way_tags(way)
        highway = tags.get("highway")
        if highway is None:
            continue
        if drive_only and highway in _EXCLUDED_HIGHWAYS:
            continue

        refs = [int(nd.get("ref")) for nd in way.findall("nd")]
        # keep only nodes we actually have coordinates for
        refs = [r for r in refs if r in coords]

        oneway = tags.get("oneway", "no")
        forward = oneway not in ("-1", "reverse")
        backward = oneway in ("no", "false", "0") or oneway == "-1"

        for a, b in zip(refs, refs[1:]):
            dist = haversine(*coords[a], *coords[b])
            if forward:
                graph.add_edge(a, b, dist)
            if backward:
                graph.add_edge(b, a, dist)

    return graph, coords
