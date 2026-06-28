"""Tests for the REST API, using FastAPI's in-process TestClient."""
from fastapi.testclient import TestClient

from nextway.api.app import app

client = TestClient(app)

# Opposite corners of the demo grid.
SW = {"lat": 48.8566, "lon": 2.3522}
NE = {"lat": 48.8566 + 5 * 0.004, "lon": 2.3522 + 5 * 0.004}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["nodes"] > 0


def test_nearest_snaps_to_a_node():
    r = client.get("/nearest", params={"lat": SW["lat"] + 0.001, "lon": SW["lon"]})
    assert r.status_code == 200
    body = r.json()
    assert "node" in body
    assert body["distance_m"] >= 0


def test_route_valid():
    r = client.post("/route", json={"start": SW, "goal": NE})
    assert r.status_code == 200
    body = r.json()
    assert len(body["path"]) >= 2
    assert body["distance_m"] > 0
    assert all(len(p) == 2 for p in body["path"])  # each point is [lat, lon]


def test_route_astar_equals_dijkstra():
    base = {"start": SW, "goal": NE}
    a = client.post("/route", json={**base, "algo": "astar"}).json()
    d = client.post("/route", json={**base, "algo": "dijkstra"}).json()
    assert abs(a["distance_m"] - d["distance_m"]) < 1e-6


def test_invalid_coords_rejected():
    r = client.get("/nearest", params={"lat": 200, "lon": 2.0})
    assert r.status_code == 422  # Pydantic validation rejects out-of-range lat


def test_route_ch_matches_dijkstra():
    base = {"start": SW, "goal": NE}
    ch = client.post("/route", json={**base, "algo": "ch"}).json()
    dj = client.post("/route", json={**base, "algo": "dijkstra"}).json()
    assert abs(ch["distance_m"] - dj["distance_m"]) < 1e-6
