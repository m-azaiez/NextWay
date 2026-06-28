"""Holds the routing graph in memory, loaded once at startup.

Data source is chosen at startup:
  * if the env var NEXTWAY_OSM points to an .osm file -> load that real map
    (parsed once, then cached on disk);
  * otherwise -> fall back to the built-in demo grid.

So you can switch the API onto a real city without changing any code:
    NEXTWAY_OSM=/path/to/city.osm uvicorn nextway.api.app:app
"""
from __future__ import annotations

import os

from ..core.graph.connectivity import largest_strongly_connected
from ..core.spatial.nearest import NearestIndex
from ..io.demo import build_demo_geograph
from ..io.osm.loader import load_osm_graph


class GraphStore:
    def __init__(self, graph, coords, source: str = "demo") -> None:
        self.graph = graph
        self.coords = coords
        self.source = source
        # KD-tree if scipy is available (city-scale), else linear scan.
        # Snap only to nodes you can actually route through: the largest
        # strongly connected component. This avoids snapping onto isolated
        # pedestrian nodes or disconnected street fragments.
        routable = largest_strongly_connected(graph, coords.keys())
        self._routable = routable if routable else set(coords.keys())
        snap_coords = {n: coords[n] for n in self._routable}
        self.routable_count = len(snap_coords)
        self._ch = None  # built lazily on first CH query
        self.index = NearestIndex(snap_coords, use_kdtree=len(snap_coords) > 5000)

        lats = [lat for lat, _ in coords.values()]
        lons = [lon for _, lon in coords.values()]
        self.bbox = {
            "min_lat": min(lats), "min_lon": min(lons),
            "max_lat": max(lats), "max_lon": max(lons),
        }
        self.center = {
            "lat": (self.bbox["min_lat"] + self.bbox["max_lat"]) / 2,
            "lon": (self.bbox["min_lon"] + self.bbox["max_lon"]) / 2,
        }

    def contraction(self):
        """Build (once) and return the Contraction Hierarchies index."""
        if self._ch is None:
            import time
            from ..core.routing.ch import CH
            t0 = time.perf_counter()
            self._ch = CH(self.graph, self._routable)
            print(f"[nextway] CH preprocessing: {(time.perf_counter()-t0)*1000:.0f} ms")
        return self._ch

    @classmethod
    def from_demo(cls) -> "GraphStore":
        graph, coords = build_demo_geograph()
        return cls(graph, coords, source="demo")

    @classmethod
    def from_osm(cls, path: str) -> "GraphStore":
        graph, coords = load_osm_graph(path)
        return cls(graph, coords, source=f"osm:{path}")

    @classmethod
    def autoload(cls) -> "GraphStore":
        osm = os.environ.get("NEXTWAY_OSM")
        if not osm:
            return cls.from_demo()
        # Auto-provision: if the file is missing but a bbox is given, download it.
        if not os.path.exists(osm):
            bbox = os.environ.get("NEXTWAY_BBOX")
            if bbox:
                from ..io.osm.download import download_osm
                coords = [float(x) for x in bbox.replace(" ", "").split(",")]
                print(f"[nextway] {osm} missing - downloading bbox {coords} from Overpass...")
                download_osm(coords, osm)
                print(f"[nextway] saved {osm}")
        return cls.from_osm(osm)
