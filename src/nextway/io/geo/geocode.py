"""Address -> coordinates (geocoding) via OpenStreetMap's Nominatim.

Needs open internet (runs on the user's machine, not in the sandbox). Results
are constrained to a bounding box so an address always resolves *inside* the
loaded map area — otherwise routing would snap to the edge of the data.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import List, Optional, Sequence

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "NextWay/0.1 (learning routing project)"


def build_url(query: str, bbox: Optional[Sequence[float]] = None, limit: int = 5) -> str:
    params = {"q": query, "format": "json", "limit": str(limit)}
    if bbox:
        min_lat, min_lon, max_lat, max_lon = bbox
        # Nominatim viewbox order is: left,top,right,bottom = min_lon,max_lat,max_lon,min_lat
        params["viewbox"] = f"{min_lon},{max_lat},{max_lon},{min_lat}"
        params["bounded"] = "1"
    return NOMINATIM_URL + "?" + urllib.parse.urlencode(params)


def parse_results(raw) -> List[dict]:
    data = json.loads(raw) if isinstance(raw, (str, bytes, bytearray)) else raw
    results = []
    for item in data:
        results.append({
            "display_name": item.get("display_name", ""),
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
        })
    return results


def geocode(query: str, bbox: Optional[Sequence[float]] = None, limit: int = 5) -> List[dict]:
    url = build_url(query, bbox, limit)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return parse_results(resp.read())
