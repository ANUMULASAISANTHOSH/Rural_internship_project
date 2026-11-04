"""
AQUILA MVP - Rule-Based Geographic Risk Engine
Implements the 5-factor transparent risk formula:
    R = 0.40P + 0.20T + 0.20D + 0.10L + 0.10H
Where:
    P = Rainfall Score (0-100)
    T = Terrain Vulnerability Score (0-100)
    D = Drainage Proximity Score (0-100)
    L = Land Cover Imperviousness Score (0-100)
    H = Historical Flood Proximity Score (0-100)
Categories:
    0-39:   LOW
    40-69:  MODERATE
    70-100: HIGH
"""

import math
from typing import Dict, Any, Optional

DEFAULT_WEIGHTS = {
    "rainfall": 0.40,
    "terrain": 0.20,
    "drainage": 0.20,
    "landcover": 0.10,
    "historical": 0.10
}

def calculate_rainfall_score(rate_mm_hr: float) -> float:
    """
    Normalizes rainfall intensity (mm/hr) to a 0-100 vulnerability score
    based on IMD meteorological thresholds:
        0 mm/hr     -> 0
        15.6 mm/hr  -> 40  (Heavy threshold)
        64.5 mm/hr  -> 75  (Very Heavy threshold)
        100+ mm/hr  -> 100 (Cloudburst scale)
    """
    if rate_mm_hr <= 0:
        return 0.0
    elif rate_mm_hr < 15.6:
        return (rate_mm_hr / 15.6) * 40.0
    elif rate_mm_hr < 64.5:
        return 40.0 + ((rate_mm_hr - 15.6) / (64.5 - 15.6)) * 35.0
    elif rate_mm_hr < 100.0:
        return 75.0 + ((rate_mm_hr - 64.5) / (100.0 - 64.5)) * 25.0
    else:
        return 100.0

def calculate_terrain_score(elevation_m: float, slope_degrees: float) -> float:
    """
    Evaluates terrain vulnerability based on local elevation and slope:
    - Low-elevation valley basins (< 515m) have high accumulation risk.
    - Flat slopes (< 2.0 deg) cannot clear sheet runoff quickly.
    """
    # Elevation factor (492m to 638m range in Manikonda)
    # 492m -> 100 score, 600m+ -> 10 score
    if elevation_m <= 495.0:
        elev_score = 100.0
    elif elevation_m >= 600.0:
        elev_score = 10.0
    else:
        elev_score = 100.0 - ((elevation_m - 495.0) / (600.0 - 495.0)) * 90.0

    # Slope factor
    # Flat (< 2 deg) -> 100 score, Steep (> 15 deg) -> 15 score
    if slope_degrees <= 1.5:
        slope_score = 100.0
    elif slope_degrees >= 15.0:
        slope_score = 15.0
    else:
        slope_score = 100.0 - ((slope_degrees - 1.5) / (15.0 - 1.5)) * 85.0

    # Combine: 60% elevation, 40% slope
    return round(0.60 * elev_score + 0.40 * slope_score, 2)

def calculate_drainage_score(distance_to_waterway_m: float) -> float:
    """
    Proximity to mapped natural water bodies and primary drainage nalas:
    Backwater overflow risk decreases with distance.
    """
    if distance_to_waterway_m <= 50.0:
        return 95.0
    elif distance_to_waterway_m <= 150.0:
        return 75.0
    elif distance_to_waterway_m <= 300.0:
        return 45.0
    elif distance_to_waterway_m <= 600.0:
        return 25.0
    else:
        return 10.0

def calculate_landcover_score(class_id: int) -> float:
    """
    ESA WorldCover class runoff score:
    50 (Built-up)   -> 90
    60 (Bare rock)  -> 65
    40 (Cropland)   -> 35
    30 (Grassland)  -> 30
    10/20 (Forest)  -> 15
    80 (Water)      -> 95
    """
    scores = {
        50: 90.0,
        60: 65.0,
        40: 35.0,
        30: 30.0,
        20: 20.0,
        10: 15.0,
        80: 95.0
    }
    return scores.get(class_id, 50.0)

def calculate_historical_score(distance_to_flood_point_m: float) -> float:
    """
    Proximity to verified historical October 2020 inundation evidence.
    """
    if distance_to_flood_point_m <= 150.0:
        return 100.0
    elif distance_to_flood_point_m <= 300.0:
        return 75.0
    elif distance_to_flood_point_m <= 600.0:
        return 45.0
    elif distance_to_flood_point_m <= 1000.0:
        return 20.0
    else:
        return 5.0

def classify_risk(final_score: float) -> str:
    if final_score < 40.0:
        return "LOW"
    elif final_score < 70.0:
        return "MODERATE"
    else:
        return "HIGH"

def compute_geographic_risk(
    rainfall_rate_mm_hr: Optional[float] = 25.0,
    elevation_m: Optional[float] = 525.0,
    slope_degrees: Optional[float] = 2.5,
    distance_to_waterway_m: Optional[float] = 120.0,
    landcover_class: Optional[int] = 50,
    distance_to_flood_point_m: Optional[float] = 250.0,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculates composite geographic risk index with configurable weights.
    Handles missing layers explicitly by renormalizing remaining weights.
    Clamps negative or extreme inputs to physical bounds.
    """
    weights = custom_weights or DEFAULT_WEIGHTS.copy()
    active_weights = {}
    component_scores = {}
    missing_components = []

    # 1. Rainfall Component (P)
    if rainfall_rate_mm_hr is not None:
        clamped_rain = max(0.0, float(rainfall_rate_mm_hr))
        component_scores["rainfall_score"] = calculate_rainfall_score(clamped_rain)
        active_weights["rainfall"] = max(0.0, weights.get("rainfall", 0.40))
    else:
        missing_components.append("rainfall")

    # 2. Terrain Component (T)
    if elevation_m is not None and slope_degrees is not None:
        clamped_elev = max(400.0, min(1000.0, float(elevation_m)))
        clamped_slope = max(0.0, min(90.0, float(slope_degrees)))
        component_scores["terrain_score"] = calculate_terrain_score(clamped_elev, clamped_slope)
        active_weights["terrain"] = max(0.0, weights.get("terrain", 0.20))
    else:
        missing_components.append("terrain")

    # 3. Drainage Proximity (D)
    if distance_to_waterway_m is not None:
        clamped_drain = max(0.0, float(distance_to_waterway_m))
        component_scores["drainage_score"] = calculate_drainage_score(clamped_drain)
        active_weights["drainage"] = max(0.0, weights.get("drainage", 0.20))
    else:
        missing_components.append("drainage")

    # 4. Land Cover (L)
    if landcover_class is not None:
        component_scores["landcover_score"] = calculate_landcover_score(int(landcover_class))
        active_weights["landcover"] = max(0.0, weights.get("landcover", 0.10))
    else:
        missing_components.append("landcover")

    # 5. Historical Flood Proximity (H)
    if distance_to_flood_point_m is not None:
        clamped_flood = max(0.0, float(distance_to_flood_point_m))
        component_scores["historical_score"] = calculate_historical_score(clamped_flood)
        active_weights["historical"] = max(0.0, weights.get("historical", 0.10))
    else:
        missing_components.append("historical")

    total_weight = sum(active_weights.values())
    if total_weight <= 0:
        total_weight = 1.0

    raw_score = sum(
        active_weights[k] * component_scores[f"{k}_score"]
        for k in active_weights
    ) / total_weight

    final_score = round(min(100.0, max(0.0, raw_score)), 1)
    category = classify_risk(final_score)

    return {
        "final_risk_score": final_score,
        "risk_category": category,
        "formula": "R = sum(w_i * S_i) / sum(w_i) [Default: 0.40P + 0.20T + 0.20D + 0.10L + 0.10H]",
        "label": "Geographic Risk Index (Rule-Based Vulnerability)",
        "provenance": "MODEL_ESTIMATE",
        "component_breakdown": {k: round(v, 1) for k, v in component_scores.items()},
        "weights_applied": active_weights,
        "missing_components": missing_components,
        "input_parameters": {
            "rainfall_rate_mm_hr": rainfall_rate_mm_hr,
            "elevation_m": elevation_m,
            "slope_degrees": slope_degrees,
            "distance_to_waterway_m": distance_to_waterway_m,
            "landcover_class": landcover_class,
            "distance_to_flood_point_m": distance_to_flood_point_m
        }
    }

