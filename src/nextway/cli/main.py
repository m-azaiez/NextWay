"""Command-line interface for NextWay.

Examples:
    nextway --demo --start A --goal D
    nextway --demo --algo dijkstra --start A --goal D
    nextway --osm map.osm --start <node_id> --goal <node_id>
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional, Tuple

from ..core.graph.adjacency import AdjacencyGraph
from ..core.routing import a_star, dijkstra
from ..core.routing.heuristic import haversine_heuristic, zero_heuristic


def build_demo_graph() -> AdjacencyGraph:
    """A tiny weighted graph for trying the engine without map data."""
    g = AdjacencyGraph()
    edges = [
        ("A", "B", 1.0),
        ("B", "D", 1.0),
        ("A", "C", 4.0),
        ("C", "D", 1.0),
        ("B", "C", 5.0),
        ("D", "E", 2.0),
    ]
    for u, v, c in edges:
        g.add_edge(u, v, c)
    return g


def _parse_args(argv) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="nextway", description="Pathfinding engine.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--demo", action="store_true", help="use the built-in demo graph")
    src.add_argument("--osm", metavar="FILE", help="path to a .osm XML extract")
    p.add_argument("--start", required=True, help="start node id")
    p.add_argument("--goal", required=True, help="goal node id")
    p.add_argument(
        "--algo",
        choices=["dijkstra", "astar"],
        default="astar",
        help="search algorithm (default: astar)",
    )
    return p.parse_args(argv)


def _load(args) -> Tuple[AdjacencyGraph, Optional[dict]]:
    """Return (graph, coords). coords is None when unavailable."""
    if args.demo:
        return build_demo_graph(), None
    from ..io.osm.parser import parse_osm

    graph, coords = parse_osm(args.osm)
    return graph, coords


def main(argv=None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    graph, coords = _load(args)

    # Node ids from OSM are ints; demo ids are strings. Coerce when needed.
    start, goal = args.start, args.goal
    if coords is not None:
        try:
            start, goal = int(start), int(goal)
        except ValueError:
            pass

    if not graph.has_node(start):
        print(f"error: start node {start!r} not in graph", file=sys.stderr)
        return 2

    if args.algo == "dijkstra":
        result = dijkstra.shortest_path(graph, start, goal)
    else:
        if coords is not None and goal in coords:
            h = haversine_heuristic(coords, goal)
        else:
            h = zero_heuristic
        result = a_star.shortest_path(graph, start, goal, heuristic=h)

    if result is None:
        print(f"No route from {start} to {goal}.")
        return 1

    print(f"Route ({args.algo}):  " + " -> ".join(str(n) for n in result.path))
    print(f"Total cost: {result.cost:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
