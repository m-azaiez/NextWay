"""Tests for the routing algorithms (Dijkstra and A*)."""
import random

import pytest

from nextway.core.graph.adjacency import AdjacencyGraph
from nextway.core.routing import a_star, dijkstra
from nextway.core.routing.heuristic import haversine_heuristic, zero_heuristic


def _hand_graph():
    """A small graph with a known optimal A->D path.

        A --1--> B --1--> D        (total 2)
        A --4--> C --1--> D        (total 5)
        B --5--> C

    Cheapest A->D is A,B,D with cost 2.
    """
    g = AdjacencyGraph()
    g.add_edge("A", "B", 1.0)
    g.add_edge("B", "D", 1.0)
    g.add_edge("A", "C", 4.0)
    g.add_edge("C", "D", 1.0)
    g.add_edge("B", "C", 5.0)
    return g


def test_dijkstra_known_answer():
    res = dijkstra.shortest_path(_hand_graph(), "A", "D")
    assert res is not None
    assert res.path == ["A", "B", "D"]
    assert res.cost == 2.0


def test_astar_known_answer_matches_dijkstra():
    res = a_star.shortest_path(_hand_graph(), "A", "D")
    assert res is not None
    assert res.path == ["A", "B", "D"]
    assert res.cost == 2.0


def test_unreachable_returns_none():
    g = AdjacencyGraph()
    g.add_edge("A", "B", 1.0)
    g.add_node("Z")
    assert dijkstra.shortest_path(g, "A", "Z") is None
    assert a_star.shortest_path(g, "A", "Z") is None


def test_missing_start_raises():
    g = _hand_graph()
    with pytest.raises(ValueError):
        dijkstra.shortest_path(g, "missing", "D")
    with pytest.raises(ValueError):
        a_star.shortest_path(g, "missing", "D")


def test_start_equals_goal():
    g = _hand_graph()
    res = dijkstra.shortest_path(g, "A", "A")
    assert res is not None
    assert res.path == ["A"]
    assert res.cost == 0.0


def _random_graph(n=40, p=0.15, seed=0):
    rnd = random.Random(seed)
    g = AdjacencyGraph()
    for i in range(n):
        g.add_node(i)
    for u in range(n):
        for v in range(n):
            if u != v and rnd.random() < p:
                g.add_edge(u, v, rnd.uniform(1.0, 10.0))
    return g


@pytest.mark.parametrize("seed", range(20))
def test_astar_matches_dijkstra_random(seed):
    """Correctness oracle: A* (zero heuristic) must equal Dijkstra's cost."""
    g = _random_graph(seed=seed)
    for start, goal in [(0, 39), (5, 20), (10, 0)]:
        d = dijkstra.shortest_path(g, start, goal)
        a = a_star.shortest_path(g, start, goal, heuristic=zero_heuristic)
        if d is None:
            assert a is None
        else:
            assert a is not None
            assert a.cost == pytest.approx(d.cost)


def test_admissible_heuristic_still_optimal():
    """A* with a real geographic heuristic returns the optimal cost.

    Coordinates roughly along a line; edge costs are the straight-line
    distances, so the haversine heuristic is admissible.
    """
    from nextway.core.geometry.distance import haversine

    coords = {
        "P": (48.8566, 2.3522),   # Paris
        "Q": (49.2583, 4.0317),   # Reims-ish
        "R": (48.5734, 7.7521),   # Strasbourg
    }
    g = AdjacencyGraph()
    g.add_edge("P", "Q", haversine(*coords["P"], *coords["Q"]))
    g.add_edge("Q", "R", haversine(*coords["Q"], *coords["R"]))
    g.add_edge("P", "R", haversine(*coords["P"], *coords["R"]))

    h = haversine_heuristic(coords, "R")
    d = dijkstra.shortest_path(g, "P", "R")
    a = a_star.shortest_path(g, "P", "R", heuristic=h)
    assert a.cost == pytest.approx(d.cost)
