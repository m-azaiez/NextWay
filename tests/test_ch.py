"""Contraction Hierarchies validated against Dijkstra (the correctness oracle)."""
import random
from pathlib import Path

import pytest

from nextway.core.graph.adjacency import AdjacencyGraph
from nextway.core.routing import dijkstra
from nextway.core.routing.ch import CH
from nextway.io.osm.parser import parse_osm

FIXTURE = Path(__file__).parent / "fixtures" / "mini_city.osm"


def _min_cost_lookup(graph, nodes):
    """(u,v) -> cheapest original edge cost, to validate unpacked paths."""
    table = {}
    for u in nodes:
        for e in graph.neighbors(u):
            k = (u, e.to)
            if k not in table or e.cost < table[k]:
                table[k] = e.cost
    return table


def _assert_valid_path(result, cost_table, expected_cost):
    """Every consecutive pair is a real edge, and the costs sum to the total."""
    total = 0.0
    for a, b in zip(result.path, result.path[1:]):
        assert (a, b) in cost_table, f"edge {a}->{b} is not a real road segment"
        total += cost_table[(a, b)]
    assert total == pytest.approx(expected_cost)


def _random_graph(n=60, p=0.12, seed=0):
    rnd = random.Random(seed)
    g = AdjacencyGraph()
    for i in range(n):
        g.add_node(i)
    for u in range(n):
        for v in range(n):
            if u != v and rnd.random() < p:
                g.add_edge(u, v, rnd.uniform(1.0, 10.0))
    return g


@pytest.mark.parametrize("seed", range(12))
def test_ch_distances_match_dijkstra(seed):
    g = _random_graph(seed=seed)
    nodes = list(range(60))
    ch = CH(g, nodes)
    table = _min_cost_lookup(g, nodes)
    for start, goal in [(0, 59), (5, 30), (10, 0), (3, 40), (59, 1)]:
        d = dijkstra.shortest_path(g, start, goal)
        c = ch.shortest_path(start, goal)
        if d is None:
            assert c is None
        else:
            assert c is not None
            assert c.cost == pytest.approx(d.cost)          # same distance as oracle
            _assert_valid_path(c, table, c.cost)            # real, consistent path
            assert c.path[0] == start and c.path[-1] == goal


def test_ch_on_osm_fixture():
    graph, coords = parse_osm(str(FIXTURE))
    ch = CH(graph, coords.keys())
    table = _min_cost_lookup(graph, coords.keys())
    for start, goal in [(1, 9), (8, 2), (7, 3), (1, 8)]:
        d = dijkstra.shortest_path(graph, start, goal)
        c = ch.shortest_path(start, goal)
        assert (c is None) == (d is None)
        if d is not None:
            assert c.cost == pytest.approx(d.cost)
            _assert_valid_path(c, table, c.cost)


def test_ch_start_equals_goal():
    g = _random_graph(seed=1)
    ch = CH(g, list(range(60)))
    r = ch.shortest_path(7, 7)
    assert r is not None and r.path == [7] and r.cost == 0.0


def test_ch_unreachable():
    g = AdjacencyGraph()
    g.add_edge("a", "b", 1.0)
    g.add_node("island")
    ch = CH(g, ["a", "b", "island"])
    assert ch.shortest_path("a", "island") is None


def test_ch_missing_start_raises():
    g = _random_graph(seed=2)
    ch = CH(g, list(range(60)))
    with pytest.raises(ValueError):
        ch.shortest_path(999, 1)
