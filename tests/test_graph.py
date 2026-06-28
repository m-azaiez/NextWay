"""Tests for the in-memory graph layer."""
import pytest

from nextway.core.graph.adjacency import AdjacencyGraph
from nextway.core.graph.base import Edge, Graph


def test_add_node_creates_empty_adjacency():
    g = AdjacencyGraph()
    g.add_node("A")
    assert g.has_node("A")
    assert list(g.neighbors("A")) == []


def test_add_edge_creates_endpoints_and_edge():
    g = AdjacencyGraph()
    g.add_edge("A", "B", 3.0)
    assert g.has_node("A") and g.has_node("B")
    edges = list(g.neighbors("A"))
    assert edges == [Edge(to="B", cost=3.0)]


def test_edges_are_directed():
    g = AdjacencyGraph()
    g.add_edge("A", "B", 1.0)
    assert list(g.neighbors("B")) == []  # no implicit reverse edge


def test_unknown_node_has_no_neighbors():
    g = AdjacencyGraph()
    assert list(g.neighbors("ghost")) == []
    assert not g.has_node("ghost")


def test_negative_cost_is_rejected():
    g = AdjacencyGraph()
    with pytest.raises(ValueError):
        g.add_edge("A", "B", -1.0)


def test_adjacency_graph_satisfies_protocol():
    g = AdjacencyGraph()
    assert isinstance(g, Graph)
