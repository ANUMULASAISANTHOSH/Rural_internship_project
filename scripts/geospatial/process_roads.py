"""
AQUILA Phase 2 - Road Network Processing Pipeline
Module: process_roads.py
Description:
    Validates, cleans, and processes the OSM road network for Manikonda.
    Outputs a validated GeoJSON and NetworkX graph for eventual routing use.
    Records geometry validity, connectivity, and attribute completeness.
"""

import os, json, sys
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_ROADS = os.path.join(BASE_DIR, "data", "raw", "roads", "osm_roads_raw.geojson")
OUT_VECTOR = os.path.join(BASE_DIR, "data", "processed", "vector")
OUT_NETWORK = os.path.join(BASE_DIR, "data", "processed", "network")
os.makedirs(OUT_VECTOR, exist_ok=True)
os.makedirs(OUT_NETWORK, exist_ok=True)

# Study area BBOX (WGS84)
WEST, SOUTH, EAST, NORTH = 78.3455, 17.3605, 78.4195, 17.4245

KEEP_HIGHWAY_TYPES = {
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "residential", "service", "unclassified", "living_street",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"
}

KEEP_ATTRIBUTES = [
    "osm_id", "highway", "name", "surface", "lanes", "maxspeed",
    "oneway", "bridge", "tunnel", "access", "width"
]


def validate_geojson_geometry(feat):
    """Returns (is_valid, reason) for a GeoJSON feature."""
    geom = feat.get("geometry")
    if geom is None:
        return False, "null_geometry"
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if not coords:
        return False, "empty_coordinates"
    if gtype == "LineString":
        if len(coords) < 2:
            return False, "degenerate_linestring_less_than_2_points"
    return True, "ok"


def bbox_filter(feat, west, south, east, north):
    """Returns True if any coordinate in the feature is within the BBOX."""
    coords = feat.get("geometry", {}).get("coordinates", [])
    if not coords:
        return False

    def check_point(pt):
        if not isinstance(pt, list) or len(pt) < 2:
            return False
        # A point is [lon, lat], but coordinates may be nested lists
        if isinstance(pt[0], (int, float)):
            lon, lat = float(pt[0]), float(pt[1])
            return west <= lon <= east and south <= lat <= north
        return False

    for pt in coords:
        if isinstance(pt, list) and len(pt) >= 2:
            if isinstance(pt[0], (int, float)):
                # Flat coordinate pair
                if check_point(pt):
                    return True
            else:
                # Nested (e.g. Polygon ring)
                for inner_pt in pt:
                    if check_point(inner_pt):
                        return True
    return False


def process_roads():
    try:
        import geopandas as gpd
        import networkx as nx
        from shapely.geometry import shape, LineString
        from pyproj import Transformer
    except ImportError as e:
        print(f"[ROADS] Missing library: {e}"); sys.exit(1)

    print("[ROADS] Loading raw OSM roads...")
    with open(RAW_ROADS, encoding="utf-8") as f:
        raw = json.load(f)

    features = raw.get("features", [])
    print(f"[ROADS] Raw features: {len(features)}")

    # Filter by highway type and BBOX
    valid_feats = []
    stats = {
        "total_raw": len(features),
        "invalid_geometry": 0,
        "outside_bbox": 0,
        "wrong_highway_type": 0,
        "duplicate_osm_ids": 0,
        "missing_highway": 0,
        "missing_name": 0,
        "has_bridge": 0,
        "has_tunnel": 0,
    }

    seen_ids = set()
    for feat in features:
        props = feat.get("properties", {})
        osm_id = props.get("osm_id")
        hw = props.get("highway", "")

        # Geometry validity
        is_valid, reason = validate_geojson_geometry(feat)
        if not is_valid:
            stats["invalid_geometry"] += 1
            continue

        # Highway type filter
        if hw not in KEEP_HIGHWAY_TYPES:
            stats["wrong_highway_type"] += 1
            continue

        # BBOX filter
        if not bbox_filter(feat, WEST, SOUTH, EAST, NORTH):
            stats["outside_bbox"] += 1
            continue

        # Duplicate check
        if osm_id in seen_ids:
            stats["duplicate_osm_ids"] += 1
            continue
        seen_ids.add(osm_id)

        # Attribute completeness
        if not hw:
            stats["missing_highway"] += 1
        if not props.get("name"):
            stats["missing_name"] += 1
        if props.get("bridge") in ("yes", "1"):
            stats["has_bridge"] += 1
        if props.get("tunnel") in ("yes", "1"):
            stats["has_tunnel"] += 1

        # Keep only relevant attributes
        clean_props = {k: props.get(k) for k in KEEP_ATTRIBUTES}
        clean_props["provenance"] = "OBSERVED"
        clean_props["source"] = "OpenStreetMap"

        valid_feats.append({
            "type": "Feature",
            "id": feat.get("id"),
            "geometry": feat.get("geometry"),
            "properties": clean_props
        })

    stats["accepted_features"] = len(valid_feats)

    # Save processed GeoJSON
    out_path = os.path.join(OUT_VECTOR, "roads_manikonda_processed.geojson")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": valid_feats}, f)
    print(f"[ROADS] Processed GeoJSON: {out_path}  ({len(valid_feats)} features)")

    # --- Build minimal NetworkX graph for connectivity analysis ---
    G = nx.DiGraph()
    node_coords = {}
    node_idx = 0

    def get_node_id(lon, lat):
        nonlocal node_idx
        key = (round(lon, 6), round(lat, 6))
        if key not in node_coords:
            node_coords[key] = node_idx
            G.add_node(node_idx, lon=lon, lat=lat)
            node_idx += 1
        return node_coords[key]

    for feat in valid_feats:
        geom = feat["geometry"]
        if geom["type"] != "LineString":
            continue
        coords = geom["coordinates"]
        props = feat["properties"]
        for i in range(len(coords) - 1):
            u_lon, u_lat = coords[i][0], coords[i][1]
            v_lon, v_lat = coords[i+1][0], coords[i+1][1]
            u = get_node_id(u_lon, u_lat)
            v = get_node_id(v_lon, v_lat)
            dx = (v_lon - u_lon) * 111320 * 0.94  # approx metres
            dy = (v_lat - u_lat) * 111320
            length_m = (dx**2 + dy**2)**0.5
            G.add_edge(u, v, length_m=length_m, highway=props.get("highway"),
                       osm_id=props.get("osm_id"))
            if props.get("oneway") != "yes":
                G.add_edge(v, u, length_m=length_m, highway=props.get("highway"),
                           osm_id=props.get("osm_id"))

    # Connectivity analysis
    components = list(nx.weakly_connected_components(G))
    largest_cc = max(components, key=len) if components else set()
    connectivity_pct = round(100 * len(largest_cc) / max(G.number_of_nodes(), 1), 1)

    stats["graph_nodes"]           = G.number_of_nodes()
    stats["graph_edges"]           = G.number_of_edges()
    stats["connected_components"]  = len(components)
    stats["largest_cc_nodes"]      = len(largest_cc)
    stats["largest_cc_pct"]        = connectivity_pct
    stats["connectivity_target_pct"] = 90.0
    stats["connectivity_meets_target"] = connectivity_pct >= 90.0

    # Highway type breakdown
    hw_counts = {}
    for feat in valid_feats:
        hw = feat["properties"].get("highway", "unknown")
        hw_counts[hw] = hw_counts.get(hw, 0) + 1
    stats["highway_type_breakdown"] = hw_counts

    # Save validation report
    report_path = os.path.join(OUT_VECTOR, "roads_validation_report.json")
    with open(report_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"[ROADS] Validation report: {report_path}")
    print(f"[ROADS] Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"[ROADS] Connectivity: {connectivity_pct}% in largest component "
          f"({'PASS' if connectivity_pct >= 90 else 'FAIL - below 90% target'})")
    print(f"[ROADS] Highway types: {hw_counts}")
    print("[ROADS] Road processing complete.")
    return stats


def main():
    print("=" * 60)
    print("AQUILA PHASE 2: ROAD NETWORK PROCESSING")
    print("=" * 60)
    if not os.path.exists(RAW_ROADS):
        print(f"[ROADS] ERROR: Raw roads file not found: {RAW_ROADS}")
        sys.exit(1)
    process_roads()
    print("=" * 60)


if __name__ == "__main__":
    main()
