"""Tests for largest-strongly-connected-component snapping."""
from pathlib import Path

from nextway.core.graph.adjacency import AdjacencyGraph
from nextway.core.graph.connectivity import largest_strongly_connected
from nextway.io.osm.parser import parse_osm

FIXTURE = Path(__file__).parent / "fixtures" / "mini_city.osm"


def test_isolated_node_excluded():
    """A node reachable only via an (excluded) footway is not routable."""
    graph, coords = parse_osm(str(FIXTURE), drive_only=True)
    scc = largest_strongly_connected(graph, coords.keys())
    assert 10 not in scc          # footway-only node dropped
    assert {1, 2, 3, 4, 5, 6, 7, 8, 9} <= scc


def test_largest_component_is_picked():
    """Two disconnected clusters -> only the bigger one is returned."""
    g = AdjacencyGraph()
    # cluster A (3 nodes, strongly connected)
    g.add_edge("a1", "a2", 1.0); g.add_edge("a2", "a1", 1.0)
    g.add_edge("a2", "a3", 1.0); g.add_edge("a3", "a2", 1.0)
    # cluster B (2 nodes), disconnected from A
    g.add_edge("b1", "b2", 1.0); g.add_edge("b2", "b1", 1.0)
    scc = largest_strongly_connected(g, ["a1", "a2", "a3", "b1", "b2"])
    assert scc == {"a1", "a2", "a3"}


def test_one_way_dead_end_excluded():
    """A node you can drive into but never out of is not strongly connected."""
    g = AdjacencyGraph()
    g.add_edge("x", "y", 1.0); g.add_edge("y", "x", 1.0)  # 2-way core
    g.add_edge("x", "trap", 1.0)                          # one-way into trap
    scc = largest_strongly_connected(g, ["x", "y", "trap"])
    assert scc == {"x", "y"}
    assert "trap" not in scc
