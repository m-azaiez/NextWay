"""Download a real OSM extract from the Overpass API (needs open internet).

Used both by the CLI helper script and, automatically, by the API when the
configured .osm file is missing but a bounding box is provided.
"""
from __future__ import annotations

import urllib.parse
import urllib.request
from pathlib import Path
from typing import Sequence

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_EXCLUDE = "footway|pedestrian|steps|path|cycleway|bridleway|construction|proposed"


def build_query(min_lat, min_lon, max_lat, max_lon, drive_only: bool = True) -> str:
    bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"  # Overpass: S,W,N,E
    highway = '["highway"]' + (f'["highway"!~"{_EXCLUDE}"]' if drive_only else "")
    return f"[out:xml][timeout:180];(way{highway}({bbox}););(._;>;);out body;"


def download_osm(bbox: Sequence[float], out_path: str, drive_only: bool = True) -> Path:
    """Fetch the extract for ``bbox`` (min_lat,min_lon,max_lat,max_lon) -> file."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    query = build_query(*bbox, drive_only=drive_only)
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        OVERPASS_URL, data=data, headers={"User-Agent": "NextWay/0.1"}
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = resp.read()
    if b"<osm" not in body[:2000]:
        raise RuntimeError("Overpass did not return OSM data (server busy? bbox too big?)")
    out.write_bytes(body)
    return out
