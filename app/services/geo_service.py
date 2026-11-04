"""
AQUILA MVP - Geospatial Layer Service
Loads and serves Phase 2 processed vector GeoJSON layers.
"""

import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VEC_DIR = os.path.join(BASE_DIR, "data", "processed", "vector")

LAYER_FILES = {
    "study_area_bbox": "study_area_bbox.geojson",
    "roads": "roads_manikonda_processed.geojson",
    "water_bodies": "water_bodies_manikonda_processed.geojson",
    "drainage": "drainage_manikonda_processed.geojson",
    "infrastructure": "infrastructure_manikonda_processed.geojson",
    "historical_flood_points": "historical_flood_points_processed.geojson",
    "monitoring_locations": "monitoring_locations_processed.geojson",
    "settlements": "manikonda_settlements_processed.geojson"
}

_LAYER_CACHE = {}

def get_layer(layer_name: str) -> dict:
    if layer_name in _LAYER_CACHE:
        return _LAYER_CACHE[layer_name]

    fname = LAYER_FILES.get(layer_name)
    if not fname:
        raise ValueError(f"Unknown layer: {layer_name}")

    fpath = os.path.join(VEC_DIR, fname)
    if not os.path.exists(fpath):
        raise FileNotFoundError(f"Layer file not found: {fpath}")

    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    _LAYER_CACHE[layer_name] = data
    return data

def get_layer_summary() -> dict:
    summary = {}
    for name, fname in LAYER_FILES.items():
        fpath = os.path.join(VEC_DIR, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    d = json.load(f)
                summary[name] = {
                    "available": True,
                    "features_count": len(d.get("features", [])),
                    "file": fname
                }
            except Exception as e:
                summary[name] = {"available": False, "error": str(e)}
        else:
            summary[name] = {"available": False, "error": "File missing"}
    return summary

