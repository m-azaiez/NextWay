"""Tests for geocoding (URL building, parsing) and the /geocode endpoint."""
import nextway.io.geo.geocode as geo
from fastapi.testclient import TestClient
from nextway.api.app import app

client = TestClient(app)


def test_build_url_constrains_to_bbox():
    url = geo.build_url("rue de rivoli", bbox=(48.81, 2.22, 48.90, 2.47))
    assert "bounded=1" in url
    assert "viewbox=" in url
    # viewbox order = min_lon,max_lat,max_lon,min_lat
    assert "2.22" in url and "48.9" in url


def test_parse_results():
    raw = '[{"display_name":"Rue de Rivoli, Paris","lat":"48.8584","lon":"2.3470"}]'
    out = geo.parse_results(raw)
    assert out == [{"display_name": "Rue de Rivoli, Paris", "lat": 48.8584, "lon": 2.3470}]


def test_geocode_endpoint(monkeypatch):
    # avoid the network: fake the geocoder
    def fake_geocode(q, bbox=None, limit=5):
        return [{"display_name": f"{q} (fake)", "lat": 48.86, "lon": 2.35}]
    monkeypatch.setattr(geo, "geocode", fake_geocode)

    r = client.get("/geocode", params={"q": "tour eiffel"})
    assert r.status_code == 200
    body = r.json()
    assert body[0]["lat"] == 48.86
    assert "fake" in body[0]["display_name"]


def test_geocode_not_found(monkeypatch):
    monkeypatch.setattr(geo, "geocode", lambda q, bbox=None, limit=5: [])
    r = client.get("/geocode", params={"q": "zzzzz"})
    assert r.status_code == 404
