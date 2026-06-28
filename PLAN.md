# NextWay — Build Plan & Progress

_Last updated: 2026-06-26_

From "graph layer only" to a working, tested pathfinding engine that runs on real map data.

---

## Status summary

- **Phase 0 — Packaging:** ✅ done
- **Phase 1 — Core routing engine:** ✅ done
- **Phase 2 — Tests + correctness oracle:** ✅ done (32 tests passing)
- **Phase 3 — CLI:** ✅ done
- **Phase 4 — OSM parser:** ✅ done (dependency-free, small extracts)
- **Phase 5 — Optimization & app layer:** ⬜ not started

---

## Phase 0 — Packaging ✅
- [x] `pyproject.toml` (src-layout, package `nextway`, `requires-python >=3.10`, console script `nextway`, pytest config).
- [x] `requirements.txt` (runtime: none; dev: pytest).
- [x] `pip install -e .` works; `import nextway` works.

## Phase 1 — Core routing engine ✅
- [x] `routing/cost.py` — pluggable cost model (`default_cost`, hook for distance/time later).
- [x] `routing/result.py` — `RouteResult` + `reconstruct_path` (shared helper).
- [x] `routing/dijkstra.py` — `shortest_path(graph, start, goal)` with heap; tie-breaker counter so node ids are never compared.
- [x] `geometry/distance.py` — `haversine()` in metres.
- [x] `routing/heuristic.py` — `zero_heuristic` + admissible `haversine_heuristic`.
- [x] `routing/a_star.py` — A* (defaults to zero heuristic = Dijkstra).

## Phase 2 — Tests ✅
- [x] `test_graph.py` — add node/edge, directedness, negative-cost rejection, protocol check.
- [x] `test_astar.py` — hand-computed graph, unreachable, missing-start, start==goal.
- [x] **Correctness oracle:** A* (zero heuristic) == Dijkstra over 20 random graphs.
- [x] Admissible-heuristic A* still optimal on geographic data.

## Phase 3 — CLI ✅
- [x] `cli/main.py` — argparse: `--demo`/`--osm`, `--start`, `--goal`, `--algo {dijkstra,astar}`.
- [x] Console script wired: `nextway --demo --start A --goal D`.

## Phase 4 — OSM parser ✅
- [x] `io/osm/parser.py` — parse `.osm` XML → `AdjacencyGraph` + coords, edge cost = haversine distance, respects `oneway`, skips footways/cycleways. Returns `(graph, coords)` ready for the A* heuristic.
- [ ] _Next:_ test against a real city extract; for large `.pbf`, swap in `pyrosm`/`osmnx` behind the same signature.

## Phase 5 — Optimization & app layer ⬜
- [ ] Profiling.
- [ ] Speedups (bidirectional search, contraction hierarchies).
- [ ] REST API.
- [ ] Web visualization.

---

## Open decision (still relevant)

`Edge` currently stores only `cost`. For "shortest vs fastest" routing you'll want **`distance`** and **`speed`/`time`** stored separately. Deferred for now — the cost model in `cost.py` is the single place to wire it in when needed.
