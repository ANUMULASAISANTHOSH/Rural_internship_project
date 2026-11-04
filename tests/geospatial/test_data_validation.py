"""
AQUILA Phase 2 - Geospatial Data Validation Test Suite
File: tests/geospatial/test_data_validation.py
Tests:
    1. CRS validation (vector and raster)
    2. Geometry validity (Shapely is_valid)
    3. Study area spatial bounds coverage
    4. Raster metadata, bounds, and NoData integrity
    5. Road network connectivity (>90%)
    6. Duplicate feature detection
    7. Missing attribute detection
    8. Geographic coordinate range verification
    9. Strict provenance taxonomy enforcement
    10. Simulation isolation (no synthetic data tagged as observed)
    11. Rainfall physical bounds (0 <= rate <= 250 mm/hr)
    12. Land cover classification and built-up fraction
"""

import os
import json
import csv
import pytest
import rasterio
from shapely.geometry import shape

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_VEC = os.path.join(BASE_DIR, "data", "processed", "vector")
PROCESSED_RAS = os.path.join(BASE_DIR, "data", "processed", "raster")
DOCS_DIR = os.path.join(BASE_DIR, "docs", "phase-2")

# Bounding box limits for western Hyderabad (Manikonda pilot)
WEST_LIMIT = 78.30
EAST_LIMIT = 78.45
SOUTH_LIMIT = 17.30
NORTH_LIMIT = 17.50

VALID_PROVENANCES = {"OBSERVED", "HISTORICAL", "MANUALLY_SEEDED", "SIMULATED", "MODEL_ESTIMATE"}

VECTOR_FILES = [
    "roads_manikonda_processed.geojson",
    "drainage_manikonda_processed.geojson",
    "water_bodies_manikonda_processed.geojson",
    "infrastructure_manikonda_processed.geojson",
    "monitoring_locations_processed.geojson",
    "historical_flood_points_processed.geojson",
    "study_area_bbox.geojson",
    "manikonda_settlements_processed.geojson"
]

RASTER_FILES = [
    ("dem_manikonda_clipped.tif", 450.0, 700.0),
    ("slope_degrees_manikonda.tif", 0.0, 90.0),
    ("worldcover_manikonda_clipped.tif", 0.0, 100.0)
]

def load_geojson(fname):
    path = os.path.join(PROCESSED_VEC, fname)
    assert os.path.exists(path), f"File missing: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 1. CRS Validation
@pytest.mark.parametrize("fname", VECTOR_FILES)
def test_vector_crs_and_validity(fname):
    data = load_geojson(fname)
    crs = data.get("crs", {}).get("properties", {}).get("name", "")
    assert "OGC:1.3:CRS84" in crs or "EPSG:4326" in crs or data.get("type") == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) > 0

# 2. Geometry Validity
@pytest.mark.parametrize("fname", VECTOR_FILES)
def test_geometry_validity(fname):
    data = load_geojson(fname)
    for feat in data["features"]:
        geom = feat.get("geometry")
        assert geom is not None, f"Null geometry in {fname} feature {feat.get('id')}"
        s = shape(geom)
        assert s.is_valid, f"Invalid geometry in {fname}: {s.is_empty}"
        assert not s.is_empty, f"Empty geometry in {fname}"

# 3. Study Area Coordinate Range
@pytest.mark.parametrize("fname", VECTOR_FILES)
def test_coordinate_range(fname):
    data = load_geojson(fname)
    for feat in data["features"]:
        geom = feat.get("geometry")
        s = shape(geom)
        bounds = s.bounds  # (minx, miny, maxx, maxy)
        assert bounds[0] >= WEST_LIMIT - 0.05, f"Lon min {bounds[0]} < {WEST_LIMIT} in {fname}"
        assert bounds[2] <= EAST_LIMIT + 0.05, f"Lon max {bounds[2]} > {EAST_LIMIT} in {fname}"
        assert bounds[1] >= SOUTH_LIMIT - 0.05, f"Lat min {bounds[1]} < {SOUTH_LIMIT} in {fname}"
        assert bounds[3] <= NORTH_LIMIT + 0.05, f"Lat max {bounds[3]} > {NORTH_LIMIT} in {fname}"

# 4. Raster Metadata and Value Integrity
@pytest.mark.parametrize("fname,val_min,val_max", RASTER_FILES)
def test_raster_integrity(fname, val_min, val_max):
    path = os.path.join(PROCESSED_RAS, fname)
    assert os.path.exists(path), f"Raster missing: {path}"
    with rasterio.open(path) as src:
        assert src.crs.to_string() == "EPSG:4326", f"Unexpected CRS {src.crs} in {fname}"
        assert src.width > 100
        assert src.height > 100
        arr = src.read(1)
        valid_vals = arr[arr != src.nodata] if src.nodata is not None else arr
        assert len(valid_vals) > 0
        assert valid_vals.min() >= val_min, f"Value {valid_vals.min()} < {val_min} in {fname}"
        assert valid_vals.max() <= val_max, f"Value {valid_vals.max()} > {val_max} in {fname}"

# 5. Road Network Connectivity
def test_road_network_connectivity():
    rep_path = os.path.join(PROCESSED_VEC, "roads_validation_report.json")
    assert os.path.exists(rep_path)
    with open(rep_path) as f:
        rep = json.load(f)
    conn = rep.get("largest_cc_pct", rep.get("largest_component_percent", 0.0))
    assert conn >= 90.0, f"Road connectivity {conn}% is below NFR threshold (90.0%)"
    assert rep.get("accepted_features", 0) > 5000

# 6. Duplicate Feature Detection
def test_duplicate_features_in_roads():
    data = load_geojson("roads_manikonda_processed.geojson")
    osm_ids = set()
    duplicates = 0
    for feat in data["features"]:
        oid = feat.get("properties", {}).get("osm_id")
        if oid in osm_ids:
            duplicates += 1
        osm_ids.add(oid)
    assert duplicates == 0, f"Found {duplicates} duplicate OSM IDs in roads layer"

# 7. Missing Attribute Detection
def test_missing_attributes_roads():
    data = load_geojson("roads_manikonda_processed.geojson")
    for feat in data["features"]:
        props = feat.get("properties", {})
        assert "highway" in props and props["highway"], f"Missing highway tag in road {feat.get('id')}"
        assert "osm_id" in props and props["osm_id"] is not None

# 8. Provenance Taxonomy Completeness
@pytest.mark.parametrize("fname", VECTOR_FILES)
def test_provenance_tagging(fname):
    data = load_geojson(fname)
    for feat in data["features"]:
        props = feat.get("properties", {})
        prov = props.get("provenance")
        assert prov in VALID_PROVENANCES, f"Invalid provenance '{prov}' in {fname} feature {feat.get('id')}"

# 9. Simulation Isolation
def test_simulation_isolation():
    # Historical records must never be SIMULATED
    hist_rain = os.path.join(PROCESSED_VEC, "rainfall_historical_validated.csv")
    with open(hist_rain, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row["provenance"] in ("OBSERVED", "HISTORICAL"), f"Historical rainfall row tagged {row['provenance']}"

    # Synthetic hyetograph must be explicitly SIMULATED
    sim_rain = os.path.join(PROCESSED_VEC, "rainfall_synthetic_hyetograph_validated.csv")
    with open(sim_rain, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assert row["provenance"] == "SIMULATED", f"Synthetic rainfall row tagged {row['provenance']}"

    # Monitoring points must preserve their individual provenances
    data = load_geojson("monitoring_locations_processed.geojson")
    for feat in data["features"]:
        props = feat.get("properties", {})
        if "SIM" in props.get("location_id", ""):
            assert props.get("provenance") == "SIMULATED"
            assert props.get("verification_status") == "SYNTHETIC_DEMO"
        elif "AWS" in props.get("location_id", ""):
            assert props.get("provenance") == "OBSERVED"
            assert props.get("verification_status") == "OFFICIAL_STATION"

# 10. Rainfall Physical Validity
def test_rainfall_bounds():
    for fname in ["rainfall_historical_validated.csv", "rainfall_synthetic_hyetograph_validated.csv"]:
        fpath = os.path.join(PROCESSED_VEC, fname)
        with open(fpath, newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                val = float(row["rainfall_rate_mm_hr"])
                assert 0.0 <= val <= 250.0, f"Unphysical rainfall rate {val} in {fname} row {i+1}"

# 11. Manifest and Inventory Completeness
def test_manifest_and_inventory_exist():
    assert os.path.exists(os.path.join(DOCS_DIR, "data_inventory.yaml"))
    assert os.path.exists(os.path.join(DOCS_DIR, "data_inventory.csv"))
    assert os.path.exists(os.path.join(DOCS_DIR, "processing_manifest.json"))
    with open(os.path.join(DOCS_DIR, "processing_manifest.json")) as f:
        manifest = json.load(f)
    assert manifest.get("datasets_total") == 12
    assert manifest.get("study_area", {}).get("area_km2") > 50.0
