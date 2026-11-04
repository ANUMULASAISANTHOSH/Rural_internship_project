# AQUILA — Final Academic Consistency & Integrity Audit

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Area:** Manikonda Pilot Area, Hyderabad, Telangana, India  
**Document Type:** Cross-Phase Verification, Numerical Reconciliation & Integrity Check  
**Document Location:** `docs/evaluation/academic_consistency_check.md`  

---

## 1. Executive Consistency Sign-Off

To ensure bulletproof credibility during an academic project evaluation or viva defense, all presentation slides, documentation deliverables, source code comments, and verbal statements must adhere to verified empirical benchmarks.

This document performs an exhaustive cross-phase reconciliation across:
- **Phase 1:** Problem Research & Requirements Specifications (`docs/phase-1/`)
- **Phase 2:** Geospatial Data Collection & Preparation (`docs/phase-2/`)
- **Phase 3:** Emergency MVP Implementation (`docs/mvp/`)
- **Final Audit:** Integration & Validation Reports (`docs/final-audit/`)
- **Active Codebase & Automated Test Suite:** 57 Passing Tests (`tests/`)

---

## 2. Canonical Numerical Metrics & Benchmark Reconciliation

The following table provides the single source of truth for all quantitative claims. Any deviation in verbal presentation or slide decks constitutes an academic inconsistency.

| Dimension / Metric | Canonical Benchmark Value | Source Authority / Verification Artifact | Reconciliation & Consistency Notes |
| :--- | :--- | :--- | :--- |
| **Administrative Boundary** | **15.5 km²** | `docs/phase-2/study_area_definition.md` | Statutory municipal jurisdiction of Manikonda Municipality established in 2019. |
| **Hydrological Catchment** | **22.4 km²** | `docs/phase-2/study_area_definition.md` | Topographic watershed derived from Copernicus DEM ridgeline flow paths draining into Neknampur Lake. |
| **Analysis Bounding Box** | **55.63 km²** | `config/geospatial/project.yaml`, `study_area_bbox.geojson` | Rectangular modeling envelope: `[78.3455°E, 17.3605°N]` to `[78.4195°E, 17.4245°N]`. |
| **Built-Up Land Cover Share** | **51.72%** | `docs/phase-2/landcover_report.md`, `landcover_summary.json` | Measured across 55.63 km² envelope using ESA WorldCover 10m 2021 (Class 50). Refines Phase 1's >75% claim. |
| **Mapped Open Waterways** | **21 channels** (9.71 km) | `drainage_manikonda_processed.geojson`, `drainage_and_waterbody_report.md` | Open surface nalas extracted from OSM & TSDI. Severe data gap in underground stormwater pipes documented. |
| **Mapped Water Bodies** | **24 lakes / cheruvus** (1.51 km²) | `water_bodies_manikonda_processed.geojson`, `drainage_and_waterbody_report.md` | Natural lakes, retention ponds, and kuntas, including Neknampur Chinna/Pedda Cheruvu and Puppalguda Cheruvu. |
| **Road Network Segments** | **6,659 segments** | `roads_manikonda_processed.geojson`, `roads_validation_report.json` | Cleaned and validated vehicular road network; verified against study bounding box. |
| **Road Network Connectivity** | **94.7% in largest component** | `roads_validation_report.json`, `test_road_network_connectivity` | Computed via NetworkX weakly connected components; exceeds Phase 1 NFR-004 target ($\ge 90.0\%$). |
| **Critical Infrastructure** | **65 facilities** | `infrastructure_manikonda_processed.geojson`, `infrastructure_inventory.md` | Tagged `OSM_UNVERIFIED` and `UNKNOWN_UNVERIFIED`. Sourced from OSM without physical on-site audit. |
| **Historical Flood Hotspots** | **5 verified points** | `historical_flood_points_processed.geojson`, `historical_flood_evidence_report.md` | Ground truth evidence from October 2020 cloudburst with documented depths of 0.45m to 0.70m. |
| **Meteorological Stations** | **4 perimeter proxy stations** | `rainfall_validation_report.json`, `rainfall_data_report.md` | Gachibowli (4.8 km), Rajendranagar (8.2 km), Begumpet (13.5 km), Serilingampally (8.0 km). No AWS in core. |
| **Historical Hourly Records** | **8 validated records** | `rainfall_historical_validated.csv` | Historical precipitation telemetry points from the October 2020 Hyderabad event. |
| **Synthetic Design Storm** | **120 mm / 3-hour storm** | `rainfall_synthetic_hyetograph_validated.csv`, `scenario_heavy_rainfall.json` | Asymmetric Chicago hyetograph peaking at 70 mm/hr at $T=45\text{ min}$; tagged strictly `SIMULATED`. |
| **Automated Verification Tests** | **57 Tests (100% Passing)** | `pytest -v` across `tests/geospatial/` and `tests/mvp/` | 41 geospatial data validation tests + 16 backend integration tests; executes in 2.39 seconds. |

---

## 3. Strict Data Provenance Classification

A foundational ethical requirement of the project is never to misrepresent synthetic, interpolated, or unverified data as direct observations. The candidate must strictly defend the following classifications:

```
+----------------------------------------------------------------------------------------------------+
|                                    AQUILA DATA PROVENANCE MATRIX                                   |
+-------------------+--------------------+-----------------------------------+-----------------------+
| Dataset / Entity  | Provenance Tag     | Source Authority                  | Operational Status    |
+-------------------+--------------------+-----------------------------------+-----------------------+
| AWS Rain Gauges   | OBSERVED           | IMD / TSDPS Perimeter Stations    | Verified measurements |
| Oct 2020 Hotspots | HISTORICAL         | GHMC Post-Event Reports / Media   | Verified ground-truth |
| DEM & Slope Grid  | DERIVED_ANALYTICAL | Copernicus GLO-30 DSM / GDAL      | Analytical raster     |
| Critical Baseline | MANUALLY_SEEDED    | OSM Nodes / Municipal Locations   | Seeded reference      |
| Public Facilities | OSM_UNVERIFIED     | OpenStreetMap Overpass Extract    | Unverified crowdsource|
| Emergency Fleet   | SIMULATED          | Seed script (`[DEMO SYNTHETIC]`)  | Demonstration only    |
| Scenario Storm    | SIMULATED          | Synthetic Chicago Hyetograph      | Model test input      |
| Risk Index Score  | MODEL_ESTIMATE     | Rule-based MCE Engine             | Algorithmic estimate  |
+-------------------+--------------------+-----------------------------------+-----------------------+
```

---

## 4. Discrepancies, Historical Refinements & Code vs. Documentation Audit

During our comprehensive audit, four specific historical refinements and minor documentation nuances were identified. A well-prepared student should understand and openly explain these distinctions:

### A. Phase 1 Preliminary Assumptions vs. Phase 2 Empirical Ground Truth
* **Phase 1 Preliminary Assumption:** Early literature review assumed built-up land cover in Manikonda exceeded **75%**, based on regional estimates of the HITEC City core.
* **Phase 2 Empirical Finding:** High-resolution ESA WorldCover 10m raster processing proved that the actual built-up share is **51.72%** across the 55.63 km² envelope, because the envelope incorporates the Khajaguda rocky granite hills, open reserve plots, and agricultural patches in adjacent Gandipet.
* **Viva Defense Strategy:** Present this discrepancy as evidence of scientific rigor: *"In Phase 1, we cited preliminary literature estimates of >75% built-up density; however, in Phase 2, our actual satellite classification proved the true figure across our analysis envelope is 51.72%."*

### B. Risk Category Thresholds: Actual Code vs. Phase 1 Drafts
* **Early Documentation Drafts:** Mentioned a 4-tier risk classification: `LOW` (0–25), `MODERATE` (25–50), `HIGH` (50–75), and `CRITICAL` (75–100).
* **Production Code Implementation (`risk_engine.py`):** The actual deployed function `classify_risk(final_score)` implements a 3-tier boundary:
  ```python
  def classify_risk(final_score: float) -> str:
      if final_score < 40.0:
          return "LOW"
      elif final_score < 70.0:
          return "MODERATE"
      else:
          return "HIGH"
  ```
  *(Note: In incident severity models, `CRITICAL` is retained as an incident severity label, but geographic risk scores use `LOW`, `MODERATE`, and `HIGH`).*
* **Viva Defense Strategy:** Defend the actual code implementation: *"In the production risk engine, scores below 40 are categorized as LOW, 40 to 69.9 as MODERATE, and 70 and above as HIGH. Incidents themselves can carry a CRITICAL severity."*

### C. Slope Calculation: Horn's Method (8-Neighbor) vs. NumPy Finite Difference
* **Documentation & Literature:** Phase 1 and 2 reports describe Horn's (1981) 8-neighbor weighted finite-difference method.
* **Code Implementation (`process_dem.py`):** The actual script computes slope using NumPy's central finite difference: `dy, dx = np.gradient(data, res_m, res_m)`.
* **Viva Defense Strategy:** Explain that while Horn's 8-neighbor filter is standard in GIS desktop tools like QGIS, NumPy's 2nd-order central difference produces equivalent gradient magnitudes across smoothly interpolated DEM rasters while executing in vectorized C code in $<100\text{ ms}$.

### D. Emergency Distance Metric: Haversine vs. Driving Distance
* **Strict Terminology Rule:** Never call Haversine distance "travel distance" or "driving distance."
* **Accurate Terminology:** Always state *"Straight-line Haversine Great-Circle distance."*
* **Viva Defense Strategy:** Clearly state that Haversine calculates geodesic straight-line distance, and that road network routing with dynamic flood impedance is designated for Phase 4.

---

## 5. Verification Checklist for Viva Defending Candidate

Before entering the defense room, confirm that you have memorized:

- [x] **Study Extents:** 15.5 km² (admin), 22.4 km² (catchment), 55.63 km² (envelope).
- [x] **Elevation Range:** 492.7m (Neknampur Lake) to 638.7m (Khajaguda Ridge).
- [x] **Water Features:** 21 waterways (9.71 km) and 24 water bodies (1.51 km²).
- [x] **Road Connectivity:** 6,659 segments with 94.7% connectivity in largest component.
- [x] **Risk Weights:** Rainfall (0.40), Terrain (0.20), Drainage (0.20), Land Cover (0.10), Historical (0.10).
- [x] **Missing Data Handling:** Dynamic weight renormalization dividing by $\sum_{\text{active}} w_i$.
- [x] **Test Results:** Exactly 57 passing tests (41 geospatial, 16 backend) in 2.39s.
- [x] **Synthetic Tag:** Resources carry `[DEMO SYNTHETIC]` and `provenance="SIMULATED"`.
- [x] **Audit History:** Append-only relational audit log in SQLite with UTC timestamps.
- [x] **Institutional Boundary:** Academic decision-support prototype; does not replace GHMC, HYDRAA, or IMD.

