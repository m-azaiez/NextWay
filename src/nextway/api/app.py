"""NextWay REST API (FastAPI).

Run locally:
    uvicorn nextway.api.app:app --reload
Then open http://127.0.0.1:8000/docs for interactive docs.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from ..core.routing import a_star, dijkstra
from ..core.routing.heuristic import haversine_heuristic
from .graph_store import GraphStore
from .models import GeocodeResult, NearestResponse, RouteRequest, RouteResponse

# Loaded once, reused by every request.
store = GraphStore.autoload()

app = FastAPI(
    title="NextWay API",
    version="0.1.0",
    description="Pathfinding API over a road graph (Dijkstra / A*).",
)

# Allow a browser frontend (served from a different origin) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "nodes": len(store.coords),
        "routable_nodes": store.routable_count,
        "source": store.source,
        "center": store.center,
        "bbox": store.bbox,
    }


@app.get("/nearest", response_model=NearestResponse)
def nearest(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    node, dist = store.index.nearest(lat, lon)
    nlat, nlon = store.coords[node]
    return NearestResponse(node=node, lat=nlat, lon=nlon, distance_m=dist)


@app.post("/route", response_model=RouteResponse)
def route(req: RouteRequest):
    # Snap both clicked points onto actual graph nodes.
    start_node, _ = store.index.nearest(req.start.lat, req.start.lon)
    goal_node, _ = store.index.nearest(req.goal.lat, req.goal.lon)

    if req.algo == "dijkstra":
        result = dijkstra.shortest_path(store.graph, start_node, goal_node)
    elif req.algo == "ch":
        result = store.contraction().shortest_path(start_node, goal_node)
    else:
        h = haversine_heuristic(store.coords, goal_node)
        result = a_star.shortest_path(store.graph, start_node, goal_node, heuristic=h)

    if result is None:
        raise HTTPException(status_code=404, detail="No route between the given points.")

    path = [[store.coords[n][0], store.coords[n][1]] for n in result.path]
    return RouteResponse(
        algo=req.algo,
        nodes=list(result.path),
        path=path,
        distance_m=result.cost,
        snapped_start=path[0],
        snapped_goal=path[-1],
    )


@app.get("/geocode", response_model=list[GeocodeResult])
def geocode_endpoint(q: str = Query(..., min_length=2, description="Adresse ou lieu")):
    """Resolve an address to coordinates, restricted to the loaded map area."""
    from ..io.geo.geocode import geocode
    bbox = (
        store.bbox["min_lat"], store.bbox["min_lon"],
        store.bbox["max_lat"], store.bbox["max_lon"],
    )
    try:
        results = geocode(q, bbox=bbox)
    except Exception as exc:  # network / Nominatim issue
        raise HTTPException(status_code=502, detail=f"Geocoding failed: {exc}")
    if not results:
        raise HTTPException(status_code=404, detail="Adresse introuvable dans la zone chargée.")
    return results

# --- Serve the web frontend from the API itself (one server, one URL) ---
# Declared AFTER the API routes so /health, /route, /nearest, /docs win.
import pathlib as _pathlib  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

_WEB_DIR = _pathlib.Path(__file__).resolve().parents[3] / "web"
if _WEB_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
