# AQUILA — Geospatial Data Source Inventory

## 1. Inventory Summary

This document presents a comprehensive audit of all geospatial, terrain, hydrologic, and meteorologic datasets ingested, processed, and validated during Phase 2 of the AQUILA platform.

Every dataset is assigned a permanent identifier, spatial metadata, licensing rights, processing status, and strict provenance classification:
- `OBSERVED`: Primary satellite or physical sensor observations.
- `HISTORICAL`: Official post-disaster field reports and historical event data.
- `MANUALLY_SEEDED`: Manually configured reference entities and study envelopes.
- `SIMULATED`: Synthetic scenarios and design storm profiles.
- `MODEL_ESTIMATE`: Computationally derived terrain indices and spatial grids.

---

## 2. Dataset Audit Table

| Dataset ID | Dataset Name | Category | Provider | Format | Resolution | CRS | Provenance | Verification Status | Output Artifact |
|---|---|---|---|---|---|---|---|---|---|
| `SRC-DEM-COP30` | Copernicus DEM GLO-30 | Elevation / Terrain | European Space Agency (ESA) | COG GeoTIFF | 30m (1 arc-sec) | EPSG:4326 | `OBSERVED` | VERIFIED_SATELLITE_OBSERVATION | `data/processed/raster/dem_manikonda_clipped.tif` |
| `SRC-DEM-SLOPE` | Terrain Slope Grid | Elevation / Terrain | AQUILA Geoprocessing | GeoTIFF | 30m | EPSG:4326 | `MODEL_ESTIMATE` | COMPUTED_FROM_DEM | `data/processed/raster/slope_degrees_manikonda.tif` |
| `SRC-ESA-WORLDCOVER` | ESA WorldCover 10m 2021 v200 | Land Use / Land Cover | European Space Agency (ESA) | COG GeoTIFF | 10m | EPSG:4326 | `OBSERVED` | VERIFIED_SATELLITE_OBSERVATION | `data/processed/raster/worldcover_manikonda_clipped.tif` |
| `SRC-OSM-ROADS` | OSM Highway Topologies | Transportation | OpenStreetMap Contributors | GeoJSON | Vector Lines | EPSG:4326 | `OBSERVED` | COMMUNITY_VERIFIED_94.7%_CONNECTIVITY | `data/processed/vector/roads_manikonda_processed.geojson` |
| `SRC-OSM-DRAINAGE` | OSM Waterways & Drains | Drainage Network | OpenStreetMap Contributors | GeoJSON | Vector Lines | EPSG:4326 | `OBSERVED` | DOCUMENTED_PARTIAL_COVERAGE | `data/processed/vector/drainage_manikonda_processed.geojson` |
| `SRC-OSM-WATERBODIES` | OSM Natural Water Bodies | Hydrology | OSM / HMDA Survey | GeoJSON | Vector Polygons | EPSG:4326 | `OBSERVED` | VERIFIED_SURFACE_WATERBODIES | `data/processed/vector/water_bodies_manikonda_processed.geojson` |
| `SRC-OSM-INFRA` | Critical Infrastructure Facilities | Facilities | OpenStreetMap Contributors | GeoJSON | Vector Points | EPSG:4326 | `OBSERVED` | OSM_UNVERIFIED | `data/processed/vector/infrastructure_manikonda_processed.geojson` |
| `SRC-TGDPS-RAIN-HIST` | Historical Rainfall (Oct 2020) | Meteorology | TGDPS / IMD | CSV | Hourly Records | EPSG:4326 | `HISTORICAL` | OFFICIAL_HISTORICAL_STATION_RECORDS | `data/processed/vector/rainfall_historical_validated.csv` |
| `SRC-SCN-RAIN-SIM` | Synthetic 120mm Hyetograph | Simulation | AQUILA Simulation Engine | CSV | 15-min Steps | N/A | `SIMULATED` | SYNTHETIC_TEST_PROFILE | `data/processed/vector/rainfall_synthetic_hyetograph_validated.csv` |
| `SRC-NRSC-FLOOD-2020` | Historical Flood Inundation Evidence | Historical Inundation | NRSC Bhuvan / GHMC Field Logs | GeoJSON | Point Records | EPSG:4326 | `HISTORICAL` | VERIFIED_HISTORICAL | `data/processed/vector/historical_flood_points_processed.geojson` |
| `SRC-MONITOR-LOCS` | Multi-Tier Monitoring Stations | Sensor Infrastructure | Multi-Agency Synthesis | GeoJSON | Vector Points | EPSG:4326 | `MANUALLY_SEEDED` / `OBSERVED` / `SIMULATED` | MULTI_TIER_PROVENANCE_TAGGED | `data/processed/vector/monitoring_locations_processed.geojson` |
| `SRC-BOUND-BBOX` | Study Area Analysis Envelope | Boundaries | AQUILA Project Configuration | GeoJSON | Vector Polygon | EPSG:4326 | `MANUALLY_SEEDED` | DEFINED_PROJECT_BOUNDING_BOX | `data/processed/vector/study_area_bbox.geojson` |

---

## 3. Detailed Dataset Audits

### 3.1 `SRC-DEM-COP30`: Copernicus Digital Elevation Model GLO-30
- **Provider:** European Space Agency (ESA) & Airbus Defence and Space.
- **Source URL:** `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N17_00_E078_00_DEM/Copernicus_DSM_COG_10_N17_00_E078_00_DEM.tif`
- **Acquisition / Observation Window:** 2011–2015 (TanDEM-X radar constellation mission).
- **Download Date:** 2026-11-03.
- **License:** Open Data (ODC-BY / Copernicus Open Access).
- **Format & CRS:** Cloud-Optimized GeoTIFF (COG), EPSG:4326 (WGS 84), Vertical Datum: EGM2008.
- **Coverage & Extent:** Tile N17E078 (17°N to 18°N, 78°E to 79°E). Clipped envelope: 78.3455°E to 78.4195°E, 17.3605°N to 17.4245°N.
- **Grid Statistics:** Width: 266 px, Height: 230 px; Min: 492.7 m, Max: 638.7 m, Mean: 538.8 m.
- **Limitations:** Digital Surface Model (DSM) captures top-of-canopy and building heights; cannot resolve sub-metre urban curbs, road crowns, or below-grade culvert openings.

### 3.2 `SRC-ESA-WORLDCOVER`: ESA WorldCover 10m 2021 (v200)
- **Provider:** European Space Agency (ESA) WorldCover Consortium.
- **Source URL:** `https://esa-worldcover.s3.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N15E078_Map.tif`
- **Acquisition Year:** 2021 (annual composite based on Sentinel-1 SAR and Sentinel-2 optical data).
- **Download Date:** 2026-11-03.
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Format & CRS:** Cloud-Optimized GeoTIFF, EPSG:4326.
- **Clipped Grid Size:** 888 px width × 768 px height (~10 m ground sampling distance).
- **Class Breakdown:**
  - Built-up (Class 50): 51.72% (28.77 km²)
  - Tree cover / Vegetation / Agriculture (Classes 10, 20, 30, 40): 44.26% (24.62 km²)
  - Bare land / Rock outcrop (Class 60): 3.58% (1.99 km²)
  - Water bodies (Class 80): 0.44% (0.24 km²)
- **Limitations:** 10m pixel size cannot separate narrow vegetated road medians from asphalt; single 2021 epoch precedes 2022–2025 construction expansion in Puppalaguda.

### 3.3 `SRC-OSM-ROADS`: OpenStreetMap Manikonda Highway Network
- **Provider:** OpenStreetMap Contributors.
- **Extraction Protocol:** Overpass API (`https://overpass-api.de/api/interpreter`).
- **Download Date:** 2026-11-03.
- **License:** Open Database License (ODbL) 1.0.
- **Format & CRS:** GeoJSON FeatureCollection, EPSG:4326.
- **Summary:** 6,659 processed line segments representing 23,802 graph vertices and 48,391 directed edges.
- **Network Connectivity:** 94.7% of nodes reside in the largest weakly-connected component (exceeds NFR-004 target of ≥90.0%).
- **Road Hierarchy:** Residential (5,245), Service (651), Tertiary (229), Secondary (122), Motorway (61), Primary (46), Living Street (208), Links (75).
- **Limitations:** Over 90% of residential street segments lack width (`width`) or surface condition tags; bridge/tunnel features are sparsely tagged (56 bridges, 0 tunnels identified).

### 3.4 `SRC-OSM-DRAINAGE`: OpenStreetMap Waterways & Channels
- **Provider:** OpenStreetMap Contributors.
- **Extraction Protocol:** Overpass API waterway filter (`waterway~"drain|ditch|stream|canal"`).
- **Download Date:** 2026-11-03.
- **Format & CRS:** GeoJSON FeatureCollection, EPSG:4326.
- **Summary:** 21 LineString features totaling 9.71 km across the 55.63 km² study area.
- **Limitations:** **CRITICAL URBAN DATA GAP.** Mapped drainage density is only 0.17 km/km². Underground concrete box drains, roadside stormwater gutters, and residential storm sewers are virtually unmapped in public OSM datasets.

### 3.5 `SRC-OSM-WATERBODIES`: OpenStreetMap Lakes and Cheruvus
- **Provider:** OpenStreetMap Contributors & HMDA Lakes Registry reference.
- **Extraction Protocol:** Overpass API natural/water filter (`natural="water"`, `water="lake|pond|reservoir"`).
- **Download Date:** 2026-11-03.
- **Format & CRS:** GeoJSON FeatureCollection, EPSG:4326.
- **Summary:** 24 Polygon features covering approximately 1.51 km² (Neknampur Lake, Puppalaguda Cheruvu, Khajaguda Pedda Cheruvu, Lanco Hills Lake).
- **Limitations:** Static boundary representation; does not reflect seasonal drying, siltation, or weed encroachment.

### 3.6 `SRC-OSM-INFRA`: Critical Facilities Inventory
- **Provider:** OpenStreetMap Contributors.
- **Download Date:** 2026-11-03.
- **Format & CRS:** GeoJSON FeatureCollection, EPSG:4326.
- **Summary:** 65 point facilities:
  - Schools / Educational institutions: 28
  - Hospitals: 17
  - Medical Clinics: 13
  - Pharmacies: 6
  - Fire Stations: 1
- **Limitations:** Field operational status during severe weather is unverified (`OSM_UNVERIFIED`). Backup power generators, cellar elevations, and ICU capacities are not recorded in OSM.

### 3.7 `SRC-TGDPS-RAIN-HIST`: Historical Rainfall Records (October 2020)
- **Provider:** Telangana Development Planning Society (TGDPS) / IMD.
- **Observation Period:** October 13–14, 2020.
- **Download Date:** 2026-11-03.
- **Format & CRS:** CSV, EPSG:4326.
- **Summary:** 8 validated hourly and daily records across 4 perimeter AWS stations:
  - TGDPS Gachibowli AWS (Station ID: `TGDPS_AWS_GCB01`, ~3.8 km from centroid, 24-hr rainfall: 163.5 mm).
  - TGDPS Serilingampally AWS (Station ID: `TGDPS_AWS_SRP02`, ~13.5 km northwest, 24-hr rainfall: 205.0 mm).
  - IMD Begumpet Observatory (Station ID: `IMD_OBS_BGP01`, ~13.1 km northeast, 24-hr rainfall: 192.1 mm).
  - TGDPS Rajendranagar AWS (Station ID: `TGDPS_AWS_RJN03`, ~8.2 km south, 24-hr rainfall: 142.5 mm).
- **Limitations:** No physical station is located inside Manikonda municipality. Spatial interpolation (IDW / Kriging) is mandatory to estimate local catchment precipitation.

### 3.8 `SRC-SCN-RAIN-SIM`: Synthetic 120 mm Design Storm Hyetograph
- **Provider:** AQUILA Simulation Engine.
- **Specification:** Chicago Design Storm distribution (120 mm total depth, 180 min duration, peak 70 mm/hr at t = 75 min).
- **Format & CRS:** CSV, Temporal Profile.
- **Provenance:** Strictly tagged as `SIMULATED`.
- **Limitations:** Illustrative stress-test scenario; not an official IMD-certified local IDF curve.

### 3.9 `SRC-NRSC-FLOOD-2020`: Historical Flood Evidence Points
- **Provider:** National Remote Sensing Centre (NRSC) Bhuvan Disaster Management Support & Cyberabad Traffic Police advisories.
- **Event Date:** October 14, 2020.
- **Format & CRS:** GeoJSON FeatureCollection, EPSG:4326.
- **Summary:** 5 ground-truth verified inundation points with observed water depths (0.45 m to 0.70 m), including Neknampur Culvert, Puppalaguda Main Road depression, and ORR Service Road underpass.
- **Limitations:** Discrete field points; satellite optical imagery was obscured by thick cloud cover, and SAR coherence was degraded in urban building shadows.

### 3.10 `SRC-MONITOR-LOCS`: Multi-Tier Monitoring Locations
- **Provider:** AQUILA Sensor Registry.
- **Format & CRS:** GeoJSON FeatureCollection, EPSG:4326.
- **Summary:** 5 monitoring stations categorized across three distinct tiers:
  - Tier 1: Real-world official AWS stations (2 stations, `OBSERVED`).
  - Tier 2: Proposed pilot ultrasonic culvert level sensors (2 stations, `MANUALLY_SEEDED`).
  - Tier 3: Synthetic demonstration telemetry node (1 station, `SIMULATED`).
- **Limitations:** Proposed and simulated sensors have no active physical hardware deployed.

---

## 4. Machine-Readable Cross-References

Machine-readable representations of this inventory are generated directly by `scripts/geospatial/generate_inventory.py` and maintained at:
- [data_inventory.yaml](file:///c:/AI/Rural_internship_project/docs/phase-2/data_inventory.yaml)
- [data_inventory.csv](file:///c:/AI/Rural_internship_project/docs/phase-2/data_inventory.csv)
- [processing_manifest.json](file:///c:/AI/Rural_internship_project/docs/phase-2/processing_manifest.json)

