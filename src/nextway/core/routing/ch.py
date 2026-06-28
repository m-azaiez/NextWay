"""Contraction Hierarchies (CH): preprocess once, query in milliseconds.

How it works
------------
Preprocessing contracts nodes one at a time, from least to most "important".
Contracting a node v means removing it and, for every pair of neighbours
(u, w) whose shortest path went through v, inserting a *shortcut* edge u->w of
the same length — but only if no other path (a "witness") is already as short.
Each node gets a rank = the order in which it was contracted.

Querying runs a bidirectional Dijkstra on the augmented graph (original edges +
shortcuts) that only ever moves to *higher-ranked* nodes. Every shortest path in
a CH has an "up then down" shape, so the two upward searches meet at the highest
node on the path. Shortcuts are then unpacked back into the real road segments.

CH returns the exact same distances as plain Dijkstra — that's the test oracle.
"""
from __future__ import annotations

import heapq
import itertools
import math
from typing import Dict, Hashable, Iterable, List, Optional, Tuple

from ..graph.base import Graph
from .result import RouteResult

INF = math.inf
EPS = 1e-9

# An edge value is (weight, middle): middle is None for an original edge, or the
# contracted node a shortcut bypasses (used to unpack the shortcut later).
EdgeVal = Tuple[float, Optional[Hashable]]


class CH:
    def __init__(self, graph: Graph, nodes: Iterable[Hashable]) -> None:
        self.nodes: List[Hashable] = list(dict.fromkeys(nodes))
        self._node_set = set(self.nodes)
        # Working graph: pruned as nodes get contracted (used for witness search).
        self.out: Dict[Hashable, Dict[Hashable, EdgeVal]] = {}
        self.inc: Dict[Hashable, Dict[Hashable, EdgeVal]] = {}
        # Permanent CH graph: original edges + every shortcut, never pruned.
        self.ch_out: Dict[Hashable, Dict[Hashable, EdgeVal]] = {}
        for n in self.nodes:
            self.out[n] = {}
            self.inc[n] = {}
            self.ch_out[n] = {}

        for u in self.nodes:
            for e in graph.neighbors(u):
                self._ensure(e.to)
                self._add(self.out, self.inc, u, e.to, e.cost, None)
                self._add_ch(u, e.to, e.cost, None)

        self.rank: Dict[Hashable, int] = {}
        self.contracted: set = set()
        self._unpack_cache: Dict[Tuple[Hashable, Hashable], List[Hashable]] = {}

        self._preprocess()
        self._build_search_graphs()

    # ---- graph helpers -------------------------------------------------
    def _ensure(self, n: Hashable) -> None:
        if n not in self.out:
            self.out[n] = {}
            self.inc[n] = {}
            self.ch_out[n] = {}
            self.nodes.append(n)
            self._node_set.add(n)

    @staticmethod
    def _add(out, inc, u, v, w, mid) -> None:
        cur = out[u].get(v)
        if cur is None or w < cur[0] - EPS:
            out[u][v] = (w, mid)
            inc[v][u] = (w, mid)

    def _add_ch(self, u, v, w, mid) -> None:
        cur = self.ch_out[u].get(v)
        if cur is None or w < cur[0] - EPS:
            self.ch_out[u][v] = (w, mid)

    def _remove_node(self, v: Hashable) -> None:
        for u in list(self.inc[v]):
            self.out[u].pop(v, None)
        for w in list(self.out[v]):
            self.inc[w].pop(v, None)
        self.out[v] = {}
        self.inc[v] = {}

    # ---- witness search ------------------------------------------------
    def _witness(self, source, avoid, limit, targets, max_settle=500):
        """Shortest distances source->target over the working graph, never
        passing through `avoid`, exploring only up to `limit`. Conservative:
        if it stops early it simply finds fewer witnesses (=> more shortcuts),
        which stays correct."""
        remaining = set(targets)
        dist = {source: 0.0}
        pq = [(0.0, source)]
        found: Dict[Hashable, float] = {}
        settled = 0
        while pq and remaining and settled < max_settle:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, INF) + EPS:
                continue
            if d > limit + EPS:
                break
            settled += 1
            if u in remaining:
                found[u] = d
                remaining.discard(u)
            for v, (w, _mid) in self.out[u].items():
                if v == avoid:
                    continue
                nd = d + w
                if nd < dist.get(v, INF) - EPS and nd <= limit + EPS:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return found

    def _shortcuts_for(self, v):
        ins = list(self.inc[v].items())   # (u, (w_uv, mid))
        outs = list(self.out[v].items())  # (w, (w_vw, mid))
        result = []
        if not ins or not outs:
            return result
        max_out = max(w for _, (w, _m) in outs)
        for u, (wuv, _m1) in ins:
            limit = wuv + max_out
            targets = {w for w, _ in outs if w != u}
            if not targets:
                continue
            witness = self._witness(u, avoid=v, limit=limit, targets=targets)
            for w, (wvw, _m2) in outs:
                if w == u:
                    continue
                p = wuv + wvw
                if witness.get(w, INF) > p + EPS:
                    result.append((u, w, p))
        return result

    def _priority(self, v) -> float:
        shortcuts = len(self._shortcuts_for(v))
        degree = len(self.inc[v]) + len(self.out[v])
        return float(shortcuts - degree)

    # ---- preprocessing -------------------------------------------------
    def _contract(self, v) -> None:
        for u, w, p in self._shortcuts_for(v):
            self._add(self.out, self.inc, u, w, p, v)
            self._add_ch(u, w, p, v)
        self._remove_node(v)

    def _preprocess(self) -> None:
        counter = itertools.count()
        pq = [(self._priority(v), next(counter), v) for v in self.nodes]
        heapq.heapify(pq)
        r = 0
        while pq:
            _pri, _c, v = heapq.heappop(pq)
            if v in self.contracted:
                continue
            new_pri = self._priority(v)
            if pq and new_pri > pq[0][0] + EPS:   # lazy update: no longer minimal
                heapq.heappush(pq, (new_pri, next(counter), v))
                continue
            self._contract(v)
            self.contracted.add(v)
            self.rank[v] = r
            r += 1

    def _build_search_graphs(self) -> None:
        self.fwd: Dict[Hashable, List[Tuple[Hashable, float]]] = {n: [] for n in self.nodes}
        self.bwd: Dict[Hashable, List[Tuple[Hashable, float]]] = {n: [] for n in self.nodes}
        for u in self.nodes:
            ru = self.rank[u]
            for v, (w, _mid) in self.ch_out[u].items():
                if self.rank[v] > ru:
                    self.fwd[u].append((v, w))
                else:
                    self.bwd[v].append((u, w))  # reverse edge, upward from v

    # ---- query ---------------------------------------------------------
    @staticmethod
    def _dijkstra_up(source, adj):
        dist = {source: 0.0}
        pred: Dict[Hashable, Hashable] = {}
        pq = [(0.0, source)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, INF) + EPS:
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist.get(v, INF) - EPS:
                    dist[v] = nd
                    pred[v] = u
                    heapq.heappush(pq, (nd, v))
        return dist, pred

    def shortest_path(self, source, target) -> Optional[RouteResult]:
        if source not in self._node_set:
            raise ValueError(f"start node {source!r} is not in the graph")
        if target not in self._node_set:
            return None

        dist_f, pred_f = self._dijkstra_up(source, self.fwd)
        dist_b, pred_b = self._dijkstra_up(target, self.bwd)

        best = INF
        meet = None
        for x in dist_f.keys() & dist_b.keys():
            d = dist_f[x] + dist_b[x]
            if d < best - EPS:
                best = d
                meet = x
        if meet is None:
            return None

        # forward edges s..meet (directed a->b)
        edges: List[Tuple[Hashable, Hashable]] = []
        fchain = [meet]
        node = meet
        while node != source:
            node = pred_f[node]
            fchain.append(node)
        fchain.reverse()
        for a, b in zip(fchain, fchain[1:]):
            edges.append((a, b))
        # backward edges meet..t (directed node->pred_b[node])
        node = meet
        while node != target:
            nxt = pred_b[node]
            edges.append((node, nxt))
            node = nxt

        path = self._stitch(edges, source)
        return RouteResult(path=path, cost=best)

    def _stitch(self, edges, source) -> List[Hashable]:
        if not edges:
            return [source]
        out: List[Hashable] = []
        for a, b in edges:
            seg = self._unpack(a, b)
            if out and out[-1] == seg[0]:
                out.extend(seg[1:])
            else:
                out.extend(seg)
        return out

    def _unpack(self, a, b) -> List[Hashable]:
        key = (a, b)
        cached = self._unpack_cache.get(key)
        if cached is not None:
            return cached
        _w, mid = self.ch_out[a][b]
        if mid is None:
            seg = [a, b]
        else:
            left = self._unpack(a, mid)
            right = self._unpack(mid, b)
            seg = left[:-1] + right
        self._unpack_cache[key] = seg
        return seg
