# AQUILA — Emergency MVP Implementation Plan (Two-Day Scope)

## 1. Repository Inspection & Environment Baseline

### 1.1 Environment Findings
- **Python Version:** 3.13.2 (Windows 64-bit)
- **Key Installed Libraries:**
  - Backend: `fastapi` (0.161.1), `uvicorn` (0.49.0), `pydantic` (2.13.4), `sqlalchemy` (2.1.6)
  - UI / Dashboard: `streamlit` (1.58.0), `folium` (0.20.0), `streamlit-folium` (0.27.4), `plotly` (6.8.0)
  - Geospatial: `geopandas` (1.2.0), `shapely` (2.2.0), `rasterio` (1.5.2), `networkx` (3.5)
  - Testing: `pytest` (9.1.1), `requests` (2.32.5)
- **Database Architecture Decision:**
  - Local PostgreSQL/PostGIS is not currently running as an active Windows service.
  - In strict alignment with Section 3 and Section 5 instructions (*"If PostGIS setup would consume significant implementation time, use SQLite for operational records and load the existing GeoJSON layers directly for spatial visualization and analysis. Do not block the entire MVP because of database installation problems"*), AQUILA MVP will use **SQLite (`aquila_mvp.db`) via SQLAlchemy** for all transactional records (Incidents, Resources, Risk Assessments, Incident Assignments, Audit History, Rainfall Observations).
  - Spatial layers will be loaded directly from Phase 2 GeoJSON and raster assets, using Shapely and GeoPandas for spatial operations, and Haversine metric distance for rapid resource allocation.

### 1.2 Verified Phase 2 Datasets
- Vector assets:
  - `data/processed/vector/study_area_bbox.geojson`
  - `data/processed/vector/roads_manikonda_processed.geojson` (6,659 lines)
  - `data/processed/vector/water_bodies_manikonda_processed.geojson` (24 polygons)
  - `data/processed/vector/drainage_manikonda_processed.geojson` (21 channels)
  - `data/processed/vector/infrastructure_manikonda_processed.geojson` (65 facilities)
  - `data/processed/vector/historical_flood_points_processed.geojson` (5 verified flood points)
  - `data/processed/vector/monitoring_locations_processed.geojson` (5 multi-tier stations)
- Tabular records:
  - `data/processed/vector/rainfall_historical_validated.csv`
  - `data/processed/vector/rainfall_synthetic_hyetograph_validated.csv` (13 time steps)
- Raster assets:
  - `data/processed/raster/dem_manikonda_clipped.tif`
  - `data/processed/raster/slope_degrees_manikonda.tif`
  - `data/processed/raster/worldcover_manikonda_clipped.tif`

---

## 2. MVP Architecture

```text
+--------------------------------------------------------------------------+
|                     STREAMLIT DASHBOARD (app/dashboard)                  |
|  - Interactive Map (Folium): Layers, Incidents, Resources, Floods        |
|  - Real-Time Risk Panel: Gauge, Component Breakdown, Provenance Tags     |
|  - Incident Command: Create, View, Status Update, Assign Resource        |
|  - Scenario Simulator: Step-through MANI-HEAVY-001, Reset Scenario       |
+--------------------------------------------------------------------------+
                                     │ (HTTP / Local Python Client)
                                     ▼
+--------------------------------------------------------------------------+
|                        FASTAPI BACKEND (app/api)                         |
|  - Endpoints: /health, /api/summary, /api/layers, /api/risk              |
|  - Incidents: /api/incidents (CRUD), /api/resources                      |
|  - Dispatch: /recommend-resource, /assign-resource                       |
|  - Scenario: /api/scenarios/start, /reset, /status                       |
+--------------------------------------------------------------------------+
                  │                                        │
                  ▼                                        ▼
+-----------------------------------+    +---------------------------------+
|      SQLITE DATABASE (SQLAlchemy) |    |   GEOSPATIAL ENGINE (GeoPandas) |
|  - Incidents                      |    |   - Load Phase 2 GeoJSON        |
|  - Resources (Seed data)          |    |   - Rule-based Risk Engine      |
|  - Incident Assignments           |    |   - Haversine Distance Calc     |
|  - Rainfall Observations          |    |   - Scenario Timeline Engine    |
|  - Risk Assessments & Audit Log   |    +---------------------------------+
+-----------------------------------+
```

---

## 3. Two-Day Implementation Work Breakdown

### Day 1: Backend, Database & Core Engines
1. **Database Models & Session Setup (`app/db/`):**
   - Define SQLAlchemy models: `Incident`, `Resource`, `RainfallObservation`, `RiskAssessment`, `IncidentAssignment`, `AuditHistory`.
   - SQLite initialization and database seeder (`seed_data.py`) with realistic synthetic emergency resources (NDRF teams, GHMC dewatering squads, ambulances, rescue boats).
2. **Rule-Based Geographic Risk Engine (`app/services/risk_engine.py`):**
   - Formula: $R = 0.40P + 0.20T + 0.20D + 0.10L + 0.10H$ (normalized 0–100).
   - Component scorers for Rainfall ($P$), Terrain ($T$), Drainage proximity ($D$), Land Cover ($L$), and Historical Flood evidence ($H$).
   - Configurable weights and explicit provenance labeling.
3. **Resource Recommendation Service (`app/services/resource_service.py`):**
   - Haversine distance calculation and capability filtering.
   - Separate `RECOMMENDED` and `ASSIGNED` states with audit logging.
4. **Scenario Simulator Engine (`app/services/scenario_service.py`):**
   - Scenario `MANI-HEAVY-001` using `rainfall_synthetic_hyetograph_validated.csv`.
   - Step advancement, deterministic simulated incident injection, and scenario-isolated cleanup.
5. **FastAPI Application (`app/api/main.py`):**
   - Implement all required endpoints with Pydantic validation schemas.
6. **Backend Automated Tests (`tests/mvp/test_backend.py`):**
   - Pytest suite testing health, risk calculation, incidents, resources, scenario, and audit trail.

### Day 2: Streamlit Dashboard, Interactive Map & Integration
1. **Interactive Map Component (`app/dashboard/map_view.py`):**
   - Folium map with LayerControl: Study Area BBOX, Roads, Water Bodies, Drainage, Facilities, Monitoring Stations, Historical Inundation, and Incidents.
2. **Streamlit Command Centre (`app/dashboard/main.py`):**
   - Overview metrics, incident management panel, resource dispatch panel, risk breakdown gauge, scenario simulation controls, and audit history viewer.
3. **End-to-End Verification & Demonstration Walkthrough:**
   - Verify complete 13-step demonstration workflow.
4. **Documentation Delivery:**
   - Produce all documentation deliverables in `docs/mvp/`.

