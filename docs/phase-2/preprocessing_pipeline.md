# AQUILA — Geospatial Preprocessing Pipeline & Execution Guide

## 1. Executive Summary

Reproducibility is a foundational tenet of the AQUILA platform. All geospatial data preparation—from raw satellite ingestion and API querying through geometric cleaning, terrain derivation, and topology validation—is fully automated via modular Python scripts.

This document describes the pipeline architecture, script responsibilities, dependency chain, input/output data flows, and exact terminal commands required to reproduce the entire Phase 2 geospatial foundation from scratch.

---

## 2. Pipeline Architecture & Execution Flow

```mermaid
graph TD
    subgraph Step 1: Raw Ingestion [scripts/geospatial/acquire_data.py]
        S1["Copernicus DEM (AWS S3)"]
        S2["Overpass API (Roads, Drains, Lakes, Facilities)"]
        S3["Rainfall Records & Flood History"]
    end
    
    subgraph Step 2: Spatial Processing [scripts/geospatial/process_*.py]
        P1["process_dem.py<br/>(Clip DEM & Derive Slope)"]
        P2["process_roads.py<br/>(Clean Topology & Graph Connectivity)"]
        P3["process_drainage.py<br/>(Waterways & Lake Polygons)"]
        P4["process_rainfall.py<br/>(IMD Severity & Hyetograph)"]
        P5["process_landcover.py<br/>(ESA WorldCover & Imperviousness)"]
        P6["process_infrastructure.py<br/>(Facilities, Sensors, BBOX)"]
    end
    
    subgraph Step 3: Metadata & Validation
        V1["generate_inventory.py<br/>(YAML, CSV, Manifest JSON)"]
        V2["test_data_validation.py<br/>(Pytest 41 Automated Checks)"]
        V3["validate_data.py<br/>(Master Quality Audit JSON)"]
    end
    
    Step 1 --> Step 2
    Step 2 --> Step 3
```

---

## 3. Preprocessing Script Specifications

### 3.1 `scripts/geospatial/acquire_data.py`
- **Purpose:** Downloads raw satellite datasets from public cloud buckets, queries Overpass API with multi-endpoint fallback, and stages raw files under `data/raw/`.
- **Inputs:** `config/geospatial/project.yaml`, `config/geospatial/data_sources.yaml`.
- **Outputs:** Raw files in `data/raw/{dem, roads, drainage, water_bodies, infrastructure, rainfall, flood_evidence, boundaries}/`.
- **Execution:** `python scripts/geospatial/acquire_data.py`

### 3.2 `scripts/geospatial/process_dem.py`
- **Purpose:** Opens Copernicus DSM tile `N17E078`, clips the raster to the buffered Manikonda pilot bounding box, validates elevation ranges, and derives terrain slope in degrees using Horn's algorithm scaled to local metric dimensions.
- **Inputs:** `data/raw/dem/Copernicus_DSM_COG_10_N17_00_E078_00_DEM.tif`.
- **Outputs:**
  - `data/processed/raster/dem_manikonda_clipped.tif` (266 × 230 px, Float32)
  - `data/processed/raster/slope_degrees_manikonda.tif` (266 × 230 px, Float32)
  - `data/processed/raster/dem_processing_report.json`
- **Execution:** `python scripts/geospatial/process_dem.py`

### 3.3 `scripts/geospatial/process_roads.py`
- **Purpose:** Parses raw OSM road LineStrings, audits geometry validity, removes 244 duplicate segments, filters to pilot bounding box, standardizes highway hierarchy, constructs a NetworkX directional graph, evaluates graph connectivity, and exports validated vector GeoJSON.
- **Inputs:** `data/raw/roads/osm_roads_raw.geojson`.
- **Outputs:**
  - `data/processed/vector/roads_manikonda_processed.geojson` (6,659 features)
  - `data/processed/vector/roads_validation_report.json` (94.7% connectivity)
- **Execution:** `python scripts/geospatial/process_roads.py`

### 3.4 `scripts/geospatial/process_drainage.py`
- **Purpose:** Cleans and validates OpenStreetMap natural streams, canals, and drains, as well as lake and retention pond polygons. Computes metric channel lengths and water spread areas in UTM Zone 44N, and documents drainage density limitations.
- **Inputs:** `data/raw/drainage/osm_drainage_raw.geojson`, `data/raw/water_bodies/osm_water_bodies_raw.geojson`.
- **Outputs:**
  - `data/processed/vector/drainage_manikonda_processed.geojson` (21 waterways, 9.71 km)
  - `data/processed/vector/water_bodies_manikonda_processed.geojson` (24 water bodies, 1.51 km²)
  - `data/processed/vector/drainage_validation_report.json`
  - `data/processed/vector/water_bodies_validation_report.json`
- **Execution:** `python scripts/geospatial/process_drainage.py`

### 3.5 `scripts/geospatial/process_rainfall.py`
- **Purpose:** Ingests historical October 2020 hourly rainfall records from 4 regional perimeter stations and synthetic 120 mm Chicago design storm profile. Validates physical rainfall bounds (0–250 mm/hr), tags IMD severity ratings, and strictly enforces provenance.
- **Inputs:** `data/raw/rainfall/historical_october_2020_rainfall.csv`, `synthetic_120mm_storm_hyetograph.csv`.
- **Outputs:**
  - `data/processed/vector/rainfall_historical_validated.csv` (8 rows)
  - `data/processed/vector/rainfall_synthetic_hyetograph_validated.csv` (13 time steps)
  - `data/processed/vector/rainfall_validation_report.json`
  - `data/processed/vector/rainfall_synthetic_report.json`
- **Execution:** `python scripts/geospatial/process_rainfall.py`

### 3.6 `scripts/geospatial/process_landcover.py`
- **Purpose:** Streams ESA WorldCover 10m 2021 Cloud-Optimized GeoTIFF tile `N15E078` via HTTP range requests, clips to the pilot bounding box, computes pixel frequency and area for 7 land cover classes, and empirically evaluates the Phase 1 imperviousness claim.
- **Inputs:** ESA WorldCover AWS S3 COG endpoint.
- **Outputs:**
  - `data/processed/raster/worldcover_manikonda_clipped.tif` (888 × 768 px, 10m resolution)
  - `data/processed/vector/landcover_summary.json` (51.72% built-up)
  - `data/processed/vector/landcover_validation_report.json`
- **Execution:** `python scripts/geospatial/process_landcover.py`

### 3.7 `scripts/geospatial/process_infrastructure.py`
- **Purpose:** Cleans and normalizes 65 critical public facilities from OSM, enforces `OSM_UNVERIFIED` status, standardizes multi-tier monitoring locations, processes historical October 2020 flood evidence points, and constructs the pilot study area bounding box and boundary distinction notes.
- **Inputs:** Raw infrastructure, monitoring locations, flood points, and boundary GeoJSON files.
- **Outputs:**
  - `data/processed/vector/infrastructure_manikonda_processed.geojson` (65 facilities)
  - `data/processed/vector/monitoring_locations_processed.geojson` (5 multi-tier stations)
  - `data/processed/vector/historical_flood_points_processed.geojson` (5 verified flood points)
  - `data/processed/vector/study_area_bbox.geojson` (55.63 km² bounding polygon)
  - `data/processed/vector/manikonda_settlements_processed.geojson` (5 place nodes)
  - `data/processed/vector/study_area_notes.json`
- **Execution:** `python scripts/geospatial/process_infrastructure.py`

### 3.8 `scripts/geospatial/generate_inventory.py`
- **Purpose:** Traverses all processed raster, vector, and tabular artifacts and generates authoritative metadata catalogues in YAML, CSV, and JSON formats under `docs/phase-2/`.
- **Outputs:** `docs/phase-2/data_inventory.yaml`, `data_inventory.csv`, `processing_manifest.json`.
- **Execution:** `python scripts/geospatial/generate_inventory.py`

### 3.9 `scripts/geospatial/validate_data.py`
- **Purpose:** Master audit script that programmatically tests all 12 dataset assets against strict geospatial invariants (CRS, geometry validity, bounding box containment, duplicate IDs, missing tags, and provenance classification).
- **Outputs:** `docs/phase-2/geospatial_data_quality_report.json`.
- **Execution:** `python scripts/geospatial/validate_data.py`

---

## 4. Complete Reproduction Command Sequence

To execute the entire end-to-end data preparation pipeline from a fresh repository checkout:

```powershell
# Navigate to repository root
cd C:\AI\Rural_internship_project

# Step 1: Execute all core processing scripts
python scripts/geospatial/process_dem.py
python scripts/geospatial/process_roads.py
python scripts/geospatial/process_drainage.py
python scripts/geospatial/process_rainfall.py
python scripts/geospatial/process_landcover.py
python scripts/geospatial/process_infrastructure.py

# Step 2: Generate data inventory and manifest
python scripts/geospatial/generate_inventory.py

# Step 3: Execute automated Pytest regression test suite
pytest tests/geospatial/test_data_validation.py -v

# Step 4: Run master quality audit
python scripts/geospatial/validate_data.py
```

All commands execute cleanly in under 30 seconds and produce idempotent, verified geospatial outputs ready for PostgreSQL/PostGIS database ingestion in Phase 3.

