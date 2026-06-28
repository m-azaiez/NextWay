"""Request/response schemas for the API (validated by Pydantic)."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class Point(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class RouteRequest(BaseModel):
    start: Point
    goal: Point
    algo: Literal["astar", "dijkstra", "ch"] = "astar"


class NearestResponse(BaseModel):
    node: int
    lat: float
    lon: float
    distance_m: float


class RouteResponse(BaseModel):
    algo: str
    nodes: List[int]
    path: List[List[float]]  # ordered [[lat, lon], ...], ready for Leaflet
    distance_m: float
    snapped_start: List[float]
    snapped_goal: List[float]


class GeocodeResult(BaseModel):
    display_name: str
    lat: float
    lon: float
