"""Connected-component analysis for routing graphs.

The largest strongly connected component (SCC) is the set of nodes from which
every other node in the set is reachable *and* which is reachable from every
other node in the set. Restricting snapping to this component guarantees that
any two snapped points always have a route between them — no more dead-ends,
isolated pedestrian nodes, or disconnected street fragments.

Uses Kosaraju's algorithm with iterative DFS (no recursion limit issues on
city-sized graphs).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Hashable, Iterable, List, Set

from .base import Graph


def _build_adjacency(graph: Graph, nodes: Iterable[Hashable]):
    """Forward and reverse adjacency restricted to nodes that have edges."""
    adj: Dict[Hashable, List[Hashable]] = defaultdict(list)
    radj: Dict[Hashable, List[Hashable]] = defaultdict(list)
    seen: Set[Hashable] = set()
    for n in nodes:
        for edge in graph.neighbors(n):
            adj[n].append(edge.to)
            radj[edge.to].append(n)
            seen.add(n)
            seen.add(edge.to)
    return adj, radj, seen


def largest_strongly_connected(graph: Graph, nodes: Iterable[Hashable]) -> Set[Hashable]:
    """Return the node set of the largest strongly connected component."""
    adj, radj, all_nodes = _build_adjacency(graph, nodes)
    if not all_nodes:
        return set()

    # Pass 1: order nodes by DFS finish time on the forward graph.
    visited: Set[Hashable] = set()
    order: List[Hashable] = []
    for start in all_nodes:
        if start in visited:
            continue
        stack = [(start, iter(adj[start]))]
        visited.add(start)
        while stack:
            node, it = stack[-1]
            pushed = False
            for nxt in it:
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append((nxt, iter(adj[nxt])))
                    pushed = True
                    break
            if not pushed:
                order.append(node)
                stack.pop()

    # Pass 2: DFS on the reverse graph in reverse finish order -> SCCs.
    visited2: Set[Hashable] = set()
    best: Set[Hashable] = set()
    for start in reversed(order):
        if start in visited2:
            continue
        comp: List[Hashable] = [start]
        visited2.add(start)
        stack = [start]
        while stack:
            u = stack.pop()
            for v in radj[u]:
                if v not in visited2:
                    visited2.add(v)
                    comp.append(v)
                    stack.append(v)
        if len(comp) > len(best):
            best = set(comp)

    return best
