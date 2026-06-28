"""Geographic distance helpers."""
from __future__ import annotations

import math

EARTH_RADIUS_M = 6_371_008.8  # mean Earth radius in metres (IUGG)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two (lat, lon) points, in metres.

    Inputs are decimal degrees. This is the standard heuristic distance for
    map routing and is always <= the true road distance, which keeps it
    admissible as an A* heuristic.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))
