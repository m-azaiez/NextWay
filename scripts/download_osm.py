#!/usr/bin/env python3
"""Download a real OSM extract for a bounding box, via the Overpass API.

Run this ON YOUR OWN MACHINE (it needs open internet). It saves a .osm file
you can then feed to NextWay:

    python scripts/download_osm.py --bbox 48.853 2.349 48.860 2.360 -o data/paris.osm
    NEXTWAY_OSM=data/paris.osm uvicorn nextway.api.app:app --reload

--bbox is: min_lat min_lon max_lat max_lon  (south west north east)

Tip: find a bbox by drawing a box on https://overpass-turbo.eu (Export) or by
zooming on https://www.openstreetmap.org and reading the URL.
Keep the box SMALL at first (a few streets) — big cities are large downloads.
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def build_query(min_lat, min_lon, max_lat, max_lon, drive_only=True):
    # Overpass uses (south, west, north, east).
    bbox = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    if drive_only:
        highway = (
            '["highway"]'
            '["highway"!~"footway|pedestrian|steps|path|cycleway|bridleway|construction|proposed"]'
        )
    else:
        highway = '["highway"]'
    return f"[out:xml][timeout:60];(way{highway}({bbox}););(._;>;);out body;"


def main(argv=None):
    p = argparse.ArgumentParser(description="Download an OSM extract via Overpass.")
    p.add_argument("--bbox", nargs=4, type=float, required=True,
                   metavar=("MIN_LAT", "MIN_LON", "MAX_LAT", "MAX_LON"))
    p.add_argument("-o", "--out", required=True, help="output .osm file path")
    p.add_argument("--all", action="store_true",
                   help="include footways/cycleways (default: drivable roads only)")
    args = p.parse_args(argv)

    query = build_query(*args.bbox, drive_only=not args.all)
    data = urllib.parse.urlencode({"data": query}).encode()

    print("Querying Overpass... (this can take a few seconds)")
    req = urllib.request.Request(OVERPASS_URL, data=data,
                                 headers={"User-Agent": "NextWay/0.1"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read()

    with open(args.out, "wb") as fh:
        fh.write(body)
    print(f"Saved {len(body):,} bytes to {args.out}")
    print(f"Now run:  NEXTWAY_OSM={args.out} uvicorn nextway.api.app:app --reload")


if __name__ == "__main__":
    sys.exit(main())
