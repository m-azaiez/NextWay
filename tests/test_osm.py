"""Tests for the OSM parser and the caching loader, on a real-structured fixture."""
import shutil
from pathlib import Path

import pytest

from nextway.core.routing import a_star, dijkstra
from nextway.io.osm.loader import _cache_path, load_osm_graph
from nextway.io.osm.parser import parse_osm

FIXTURE = Path(__file__).parent / "fixtures" / "mini_city.osm"


def test_parse_reads_all_nodes():
    graph, coords = parse_osm(str(FIXTURE))
    # 10 <node> elements in the fixture
    assert len(coords) == 10
    assert coords[1] == (48.8540, 2.3490)


def test_footway_is_excluded_in_drive_mode():
    graph, coords = parse_osm(str(FIXTURE), drive_only=True)
    # node 10 is only reachable via a footway -> no drivable edges touch it
    assert list(graph.neighbors(10)) == []
    assert all(e.to != 10 for e in graph.neighbors(5))


def test_footway_included_when_not_drive_only():
    graph, _ = parse_osm(str(FIXTURE), drive_only=False)
    assert any(e.to == 10 for e in graph.neighbors(5))


def test_oneway_is_directional():
    graph, _ = parse_osm(str(FIXTURE))
    # way 106 is one-way 2 -> 5 -> 8
    assert any(e.to == 5 for e in graph.neighbors(2))      # forward allowed
    assert all(e.to != 2 for e in graph.neighbors(5))      # reverse blocked
    assert any(e.to == 8 for e in graph.neighbors(5))


def test_astar_equals_dijkstra_on_osm():
    graph, coords = parse_osm(str(FIXTURE))
    from nextway.core.routing.heuristic import haversine_heuristic
    for start, goal in [(1, 9), (8, 2), (7, 3)]:
        d = dijkstra.shortest_path(graph, start, goal)
        h = haversine_heuristic(coords, goal)
        a = a_star.shortest_path(graph, start, goal, heuristic=h)
        if d is None:
            assert a is None
        else:
            assert a.cost == pytest.approx(d.cost)


def test_loader_creates_and_reuses_cache(tmp_path):
    # copy fixture into a writable tmp dir so the cache lands there
    osm = tmp_path / "mini.osm"
    shutil.copy(FIXTURE, osm)
    cache = _cache_path(osm)
    assert not cache.exists()

    g1, c1 = load_osm_graph(str(osm))
    assert cache.exists()                    # cache written on first load

    g2, c2 = load_osm_graph(str(osm))        # second load hits the cache
    assert c2 == c1
    assert list(g2.neighbors(2)) == list(g1.neighbors(2))
