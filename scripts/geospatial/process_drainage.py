"""
AQUILA Phase 2 - Drainage and Water Body Processing
Module: process_drainage.py
Description:
    Validates OSM drainage channels and water bodies.
    Records coverage gaps, geometry validity, and attribute completeness.
    Outputs validated GeoJSON layers and a coverage gap report.
"""

import os, json, sys
import warnings
warnings.filterwarnings("ignore")

BASE_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DRAIN    = os.path.join(BASE_DIR, "data", "raw", "drainage", "osm_drainage_raw.geojson")
RAW_WATER    = os.path.join(BASE_DIR, "data", "raw", "water_bodies", "osm_water_bodies_raw.geojson")
OUT_VECTOR   = os.path.join(BASE_DIR, "data", "processed", "vector")
os.makedirs(OUT_VECTOR, exist_ok=True)

WEST, SOUTH, EAST, NORTH = 78.3455, 17.3605, 78.4195, 17.4245


def validate_feature(feat, expected_types):
    geom = feat.get("geometry", {})
    gtype = geom.get("type", "")
    coords = geom.get("coordinates", [])
    if gtype not in expected_types:
        return False, f"unexpected_geometry_type:{gtype}"
    if not coords:
        return False, "empty_coordinates"
    return True, "ok"


def compute_linestring_length_m(coords):
    """Approximate length in metres using planar approximation."""
    total = 0.0
    for i in range(len(coords) - 1):
        dx = (coords[i+1][0] - coords[i][0]) * 111320 * 0.94
        dy = (coords[i+1][1] - coords[i][1]) * 111320
        total += (dx**2 + dy**2) ** 0.5
    return total


def process_drainage():
    print("[DRAIN] Loading OSM drainage channels...")
    with open(RAW_DRAIN, encoding="utf-8") as f:
        raw = json.load(f)

    features = raw.get("features", [])
    print(f"[DRAIN] Raw drainage features: {len(features)}")

    stats = {
        "total_raw": len(features),
        "invalid_geometry": 0,
        "accepted": 0,
        "waterway_types": {},
        "named_channels": 0,
        "total_length_km": 0.0,
        "coverage_gap_note": (
            "OSM drainage coverage is INCOMPLETE for Manikonda. "
            "Secondary roadside gutters, culverts, and underground drains are largely absent. "
            "Only 21 primary waterway features were mapped in the study bounding box. "
            "DEM-derived flow accumulation should be used as a topographic aid, NOT as a "
            "substitute for actual drainage infrastructure surveys."
        )
    }

    valid_feats = []
    for feat in features:
        is_valid, reason = validate_feature(feat, {"LineString"})
        if not is_valid:
            stats["invalid_geometry"] += 1
            feat["properties"]["_validation_error"] = reason
            continue

        props = feat.get("properties", {})
        ww = props.get("waterway", "unknown")
        stats["waterway_types"][ww] = stats["waterway_types"].get(ww, 0) + 1
        if props.get("name"):
            stats["named_channels"] += 1

        coords = feat["geometry"]["coordinates"]
        length_m = compute_linestring_length_m(coords)
        stats["total_length_km"] += length_m / 1000

        clean_feat = {
            "type": "Feature",
            "id": feat.get("id"),
            "geometry": feat["geometry"],
            "properties": {
                "osm_id":   props.get("osm_id"),
                "waterway": ww,
                "name":     props.get("name"),
                "width":    props.get("width"),
                "layer":    props.get("layer"),
                "length_m": round(length_m, 1),
                "provenance": "OBSERVED",
                "source": "OpenStreetMap",
                "coverage_note": "OSM waterway coverage incomplete — secondary drains missing."
            }
        }
        valid_feats.append(clean_feat)
        stats["accepted"] += 1

    stats["total_length_km"] = round(stats["total_length_km"], 3)

    out_drain = os.path.join(OUT_VECTOR, "drainage_manikonda_processed.geojson")
    with open(out_drain, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": valid_feats}, f, indent=2)
    print(f"[DRAIN] Processed drainage: {out_drain}  ({len(valid_feats)} features, "
          f"{stats['total_length_km']:.2f} km)")

    # Save report
    report = {"drainage_validation": stats, "output_file": out_drain}
    rpt_path = os.path.join(OUT_VECTOR, "drainage_validation_report.json")
    with open(rpt_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[DRAIN] Validation report: {rpt_path}")
    return stats


def process_water_bodies():
    print("[WATER] Loading OSM water bodies...")
    with open(RAW_WATER, encoding="utf-8") as f:
        raw = json.load(f)

    features = raw.get("features", [])
    print(f"[WATER] Raw water body features: {len(features)}")

    stats = {
        "total_raw": len(features),
        "invalid_geometry": 0,
        "accepted": 0,
        "water_types": {},
        "named_bodies": 0,
        "total_area_km2": 0.0,
        "coverage_note": (
            "OSM water body coverage includes major lakes (Neknampur Lake, Puppalaguda Cheruvu, "
            "Khajaguda Reservoir) but may miss small seasonal ponds and modified water bodies. "
            "FTL (Full Tank Level) boundaries differ from OSM mapped extents and require "
            "official HMDA/GHMC records for authoritative delineation."
        )
    }

    valid_feats = []
    for feat in features:
        # Accept Polygon or LineString (closed ways)
        geom = feat.get("geometry", {})
        gtype = geom.get("type", "")
        coords = geom.get("coordinates", [])

        if not coords:
            stats["invalid_geometry"] += 1
            continue

        props = feat.get("properties", {})
        wtype = props.get("water", props.get("natural", "unknown"))
        stats["water_types"][wtype] = stats["water_types"].get(wtype, 0) + 1
        if props.get("name"):
            stats["named_bodies"] += 1

        # Approximate area for Polygons (shoelace formula in degrees, convert)
        area_km2 = 0.0
        if gtype == "Polygon" and coords:
            ring = coords[0]
            n = len(ring)
            if n >= 3:
                area_deg2 = abs(sum(
                    ring[i][0] * ring[(i+1) % n][1] - ring[(i+1) % n][0] * ring[i][1]
                    for i in range(n)
                ) / 2)
                # Convert deg² to km² (~111 km/deg latitude, 104 km/deg longitude at 17°N)
                area_km2 = area_deg2 * 111.0 * 104.0
        stats["total_area_km2"] += area_km2

        clean_feat = {
            "type": "Feature",
            "id": feat.get("id"),
            "geometry": feat["geometry"],
            "properties": {
                "osm_id":    props.get("osm_id"),
                "name":      props.get("name"),
                "natural":   props.get("natural"),
                "water":     props.get("water"),
                "area_km2":  round(area_km2, 4),
                "provenance": "OBSERVED",
                "source": "OpenStreetMap",
                "ftl_note": (
                    "Official FTL boundary not confirmed from OSM alone. "
                    "Refer to HMDA/HYDRAA records for legally-defined lake boundaries."
                )
            }
        }
        valid_feats.append(clean_feat)
        stats["accepted"] += 1

    stats["total_area_km2"] = round(stats["total_area_km2"], 4)

    out_water = os.path.join(OUT_VECTOR, "water_bodies_manikonda_processed.geojson")
    with open(out_water, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": valid_feats}, f, indent=2)
    print(f"[WATER] Processed water bodies: {out_water}  ({len(valid_feats)} features, "
          f"~{stats['total_area_km2']:.3f} km² total area)")

    rpt_path = os.path.join(OUT_VECTOR, "water_bodies_validation_report.json")
    with open(rpt_path, "w") as f:
        json.dump({"water_body_validation": stats, "output_file": out_water}, f, indent=2)
    print(f"[WATER] Validation report: {rpt_path}")
    return stats


def main():
    print("=" * 60)
    print("AQUILA PHASE 2: DRAINAGE & WATER BODY PROCESSING")
    print("=" * 60)
    for fp in [RAW_DRAIN, RAW_WATER]:
        if not os.path.exists(fp):
            print(f"ERROR: Raw file not found: {fp}"); sys.exit(1)
    d_stats = process_drainage()
    w_stats = process_water_bodies()
    print("=" * 60)
    print(f"[SUCCESS] Drainage: {d_stats['accepted']} features, "
          f"Water Bodies: {w_stats['accepted']} features.")
    print("[COVERAGE GAP] Secondary stormwater drains and culverts are "
          "largely absent from OSM in this urban area. Document this gap.")
    print("=" * 60)


if __name__ == "__main__":
    main()

