# AQUILA — System Audit & Technical Verification Report

## 1. Executive Summary

This report delivers a rigorous technical audit of the **AQUILA Emergency MVP** platform implemented for the **Manikonda pilot area (Hyderabad, Telangana)**.

As Senior QA Engineer and Technical Project Auditor, this audit examined the source codebase, relational database schemas, REST API endpoints, Streamlit dashboard, geospatial layers, and automated test harnesses to verify stability, data provenance, security boundaries, and operational fidelity.

**Key Audit Findings:**
- **Architecture Integrity:** Clean, modular separation between data access (`app/db/`), service logic (`app/services/`), REST interface (`app/api/`), and UI presentation (`app/dashboard/`).
- **Operational Status:** Fully operational locally with zero external network or commercial API dependencies.
- **Automated Regression Suite:** **57 passed tests** across geospatial data validation (41 tests) and MVP backend/integration suites (16 tests).
- **Provenance Integrity:** Strict 5-tier taxonomy (`OBSERVED`, `HISTORICAL`, `MANUALLY_SEEDED`, `SIMULATED`, `MODEL_ESTIMATE`) enforced across all records. Fictional resources are explicitly prefixed with `[DEMO SYNTHETIC]`.

---

## 2. Actual vs. Documented Architecture

| Architectural Component | Documented Specification | Actual Inspected Implementation | Audit Status |
|---|---|---|---|
| **Python Runtime** | Python 3.10+ | Python 3.13.2 (64-bit, Windows) | **VERIFIED** |
| **Backend REST API** | FastAPI (ASGI) | FastAPI 0.161.1 on Uvicorn 0.49.0 | **VERIFIED** |
| **Data Validation** | Pydantic V2 | Pydantic 2.13.4 with `ConfigDict` and coordinate bounds validation | **VERIFIED** |
| **Database & ORM** | SQLite / SQLAlchemy | SQLite (`aquila_mvp.db`) with SQLAlchemy 2.1.6; 6 relational tables | **VERIFIED** |
| **Dashboard Interface** | Streamlit + Folium | Streamlit 1.58.0 + Folium 0.20.0 + Streamlit-Folium 0.27.4 | **VERIFIED** |
| **Dynamic Visualizations** | Plotly | Plotly 6.8.0 (Risk gauge + hyetograph chart) | **VERIFIED** |
| **Geospatial Processing** | GeoPandas, Shapely, Rasterio | GeoPandas 1.2.0, Shapely 2.2.0, Rasterio 1.5.2 | **VERIFIED** |
| **Network Analysis** | NetworkX | NetworkX 3.5 (Road graph connectivity 94.7%) | **VERIFIED** |
| **Test Harness** | Pytest | Pytest 9.1.1 (57 tests passing in 2.42s) | **VERIFIED** |

---

## 3. Module-by-Module Functional Audit

### 3.1 Database & Persistence Layer (`app/db/`)
- **Tables Verified:** `incidents`, `resources`, `rainfall_observations`, `risk_assessments`, `incident_assignments`, `audit_history`.
- **Timestamp Standardization:** Standardized on timezone-naive UTC helper `utc_now()` in `database.py`, eliminating 56 Python 3.13 deprecation warnings.
- **Fleet Seeding:** 6 synthetic emergency resources seeded with explicit `[DEMO SYNTHETIC]` naming prefixes and `provenance="SIMULATED"` metadata.

### 3.2 Geospatial Layer Service (`app/services/geo_service.py`)
- **Layers Verified on Disk:**
  - `study_area_bbox.geojson` (55.63 km² bounding polygon)
  - `roads_manikonda_processed.geojson` (6,659 lines, 94.7% connectivity)
  - `water_bodies_manikonda_processed.geojson` (24 polygons, 1.51 km²)
  - `drainage_manikonda_processed.geojson` (21 channels, 9.71 km)
  - `infrastructure_manikonda_processed.geojson` (65 facilities, `OSM_UNVERIFIED`)
  - `monitoring_locations_processed.geojson` (5 multi-tier stations)
  - `historical_flood_points_processed.geojson` (5 verified October 2020 points)
  - `dem_manikonda_clipped.tif` (266×230 px, 492.7m to 638.7m elevation relief)
  - `slope_degrees_manikonda.tif` (266×230 px, 0.0° to 36.85° slope)
  - `worldcover_manikonda_clipped.tif` (888×768 px, 10m LULC, 51.72% built-up)
- **Caching Mechanism:** Implemented in-memory caching to avoid repeated file system I/O.

### 3.3 Rule-Based Risk Engine (`app/services/risk_engine.py`)
- **Formula:**
  $$R = \frac{\sum w_i S_i}{\sum w_i} \quad \text{Default:} \quad 0.40P + 0.20T + 0.20D + 0.10L + 0.10H$$
- **Missing Data Handling:** Verified. If a layer is omitted or passed as `None`, the engine excludes that component and renormalizes remaining weights, logging the missing component explicitly without silently assuming zero risk.
- **Physical Bounds Clamping:** Negative rainfall, negative elevation, or negative distances are clamped to physical lower limits.
- **Classification:** Strictly categorizes scores into `LOW` (0–39), `MODERATE` (40–69), and `HIGH` (70–100).

### 3.4 Resource Recommendation & Dispatch Service (`app/services/resource_service.py`)
- **Distance Calculation:** Haversine great-circle distance verified against spatial benchmark coordinates.
- **Capability Matching:** Verified capability filtering (`WATERLOGGING` $\to$ `PUMPING`, `ROAD_SEVERANCE` $\to$ `ROAD_CLEARING`, etc.).
- **Duplicate Assignment Prevention:** Verified. Assigning a resource that is already deployed to another active incident raises a 400 Bad Request error.
- **Automatic Fleet Release:** Setting an incident to `RESOLVED` automatically releases assigned resources back to `AVAILABLE`.

### 3.5 Heavy Rainfall Scenario Simulator (`app/services/scenario_service.py`)
- **Scenario ID:** `MANI-HEAVY-001` (*Heavy Rainfall — Manikonda*).
- **Execution:** Successfully steps through 13 time steps (180 minutes) based on `rainfall_synthetic_hyetograph_validated.csv`.
- **Deterministic Incident Injection:** Injects `INC-SIM-001` at Step 3 ($T=45$ min, 70 mm/hr) and `INC-SIM-002` at Step 5 ($T=75$ min).
- **Clean Reset Isolation:** Verified. Deletes only records where `source_type == "SIMULATED"`, leaving user-reported (`REPORTED`) and historical records untouched.

---

## 4. Data Provenance & Labelling Audit

| Data Entity | Previous Ambiguity | Audit Finding & Correction Applied | Verified Label |
|---|---|---|---|
| **Emergency Fleet** | Named "GHMC Dewatering Pump" | Conflated with official municipal assets; now prefixed with `[DEMO SYNTHETIC]`. | `SIMULATED` |
| **OSM Facilities** | Mapped hospital points | Ground operational readiness unverified; tagged with warning badge. | `OSM_UNVERIFIED` |
| **Rainfall Telemetry** | Displayed as live | No AWS inside Manikonda; perimeter AWS stations labeled as proxies. | `HISTORICAL` / `PROXY_STATION` |
| **Design Storm** | Scenario rainfall | Synthetic profile isolated from real-world telemetry; tagged `SIMULATED`. | `SIMULATED` |
| **Risk Scoring** | Implied flood probability | Renamed to "Geographic Risk Index (Rule-Based Vulnerability)". | `MODEL_ESTIMATE` |
| **Audit History** | Described as "immutable" | Standard append-only SQLite table; accurately documented as operational log. | `OPERATIONAL_LOG` |

---

## 5. Security & Reliability Review

1. **SQL Injection Vulnerabilities:** **NONE DETECTED.** All database interactions utilize SQLAlchemy ORM parameterized queries (`db.query().filter()`). Zero raw SQL concatenation exists.
2. **Input Validation:** Input parameters for incident creation are validated using Pydantic V2 (`latitude` in $[17.20, 17.60]$, `longitude` in $[78.20, 78.60]$, title length 3–255 chars). Out-of-bounds coordinates return HTTP 422 Unprocessable Entity.
3. **Invalid Status Transitions:** Validated against set `{"REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"}`; invalid strings return HTTP 400 Bad Request.
4. **Hardcoded Secrets:** Zero hardcoded API keys or credentials. SQLite uses local file path.
5. **Cross-Origin Resource Sharing (CORS):** Middleware configured on FastAPI application to allow local frontend access.

---

## 6. Discrepancies & Defect Corrections Applied

During this final audit, the following technical defects were identified and resolved:
1. **Missing Resource Provenance Column:** SQLite database did not have `resources.provenance`. Database schema was migrated and reseeded with `provenance="SIMULATED"`.
2. **Missing Road Layer in Dashboard Checkboxes:** Dashboard checkboxes lacked an arterial roads toggle. Added `show_roads` checkbox rendering filtered arterial highway vectors (`primary`, `secondary`, `tertiary`, `motorway`, `trunk`).
3. **Duplicate Assignment Conflict:** `assign_resource_to_incident` previously allowed double-deploying an already assigned resource. Added conflict validation raising `ValueError` if a resource is deployed elsewhere.
4. **Python 3.13 Deprecation Warnings:** Replaced deprecated `datetime.utcnow()` with custom timezone-clean `utc_now()` across models and services.
5. **Pydantic V2 Schema Modernization:** Replaced deprecated `example` keyword and `class Config:` with `json_schema_extra` and `model_config = ConfigDict(from_attributes=True)`.
6. **Risk Engine Missing Component Handling:** Added dynamic reweighting and clamping for missing/null input parameters.

