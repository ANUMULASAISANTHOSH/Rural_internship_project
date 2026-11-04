# AQUILA — Technical Project Explanation & Architectural Guide

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Area:** Manikonda Pilot Area, Hyderabad, Telangana, India  
**Document Type:** Comprehensive Technical Viva & Academic Defense Reference  
**Document Location:** `docs/evaluation/technical_explanation.md`  

---

## Guide Structure & Format

This document provides in-depth, defensible explanations for the 17 core technical, mathematical, geospatial, and architectural concepts governing AQUILA.

For each concept, five standard dimensions are documented:
1. **Concept:** Technical definition and theoretical principles.
2. **Why It Was Selected:** Engineering justification and trade-off analysis.
3. **How It Is Implemented in AQUILA:** Code-level architecture, module references, and data flow.
4. **Practical Example:** Concrete, realistic scenario from the Manikonda pilot area.
5. **Limitations:** Honest disclosures of technical boundaries, assumptions, and edge cases.

---

## 1. Why AQUILA Was Developed

* **Concept:** Urban flood decision support. Flash flooding in rapidly expanding Indian metropolitan peripheral zones is driven by the breakdown of traditional stormwater retention networks, uncoordinated surface runoff, and fragmented emergency communications.
* **Why It Was Selected:** Existing municipal systems operate reactively via paper hotspot lists, manual phone calls, and city-scale forecasts that cannot resolve neighborhood flash ponding. AQUILA was conceived to demonstrate a unified, transparent platform connecting geospatial datasets, empirical risk scoring, incident reporting, and proximity-based dispatch.
* **How It Is Implemented in AQUILA:** Built as a multi-tier Python platform combining a FastAPI REST service ([`app/api/main.py`](file:///C:/AI/Rural_internship_project/app/api/main.py)), an empirical 5-factor risk engine ([`app/services/risk_engine.py`](file:///C:/AI/Rural_internship_project/app/services/risk_engine.py)), an interactive Folium/Streamlit command center ([`app/dashboard/main.py`](file:///C:/AI/Rural_internship_project/app/dashboard/main.py)), and an SQLite database ([`app/db/models.py`](file:///C:/AI/Rural_internship_project/app/db/models.py)).
* **Practical Example:** During an intense evening monsoon storm, an operator opens AQUILA, observes rainfall spiking across Manikonda, sees the composite risk score rise to 74 (High), receives an incident report on Secretariat Main Road, and dispatches a nearby mobile dewatering pump within 60 seconds.
* **Limitations:** AQUILA is an academic prototype designed to prove software architecture and integration feasibility; it does not possess direct hardware links to municipal sirens or GHMC emergency telephony consoles.

---

## 2. Why Manikonda Was Selected as the Pilot Study Area

* **Concept:** Hyper-growth peri-urban watershed. Manikonda represents the quintessential challenges of western Hyderabad: granite ridgelines, rapid transition from rural panchayat to dense multi-story apartments, fragmented natural drainage, and recurring flash floods.
* **Why It Was Selected:**
  1. *Topographic Diversity:* Relief spans from 638m on Khajaguda granite ridge down to 492m at Neknampur Lake.
  2. *Severe Urbanization Pressure:* Built-up area expanded dramatically within 15 years, eliminating natural infiltration cascades.
  3. *Historical Ground Truth:* Suffered well-documented inundation during the catastrophic October 2020 Hyderabad floods (e.g., Alkapur Township, Puppalguda).
  4. *Data Accessibility:* Rich OpenStreetMap coverage, Copernicus DEM availability, and open perimeter weather station records.
* **How It Is Implemented in AQUILA:** Codified as a 55.63 km² rectangular analysis bounding box (`[17.3605°N, 78.3455°E]` to `[17.4245°N, 78.4195°E]`) enclosing both the 15.5 km² municipal polygon and the 22.4 km² natural hydrological catchment.
* **Practical Example:** Runoff generating on the steep slopes of Khajaguda Hills flows south into Manikonda's low-lying valleys. The platform captures this cross-boundary runoff instead of artificially truncating it at the municipal boundary.
* **Limitations:** The area lacks an internal municipal Automated Weather Station (AWS), requiring reliance on perimeter proxy stations (Gachibowli, Rajendranagar).

---

## 3. Why Copernicus DEM GLO-30 Was Used

* **Concept:** Digital Surface Model (DSM) providing elevation data at 1 arc-second (~30-meter) horizontal resolution acquired by the TanDEM-X radar mission.
* **Why It Was Selected:**
  1. *Public Accessibility & Global Consistency:* Freely available without commercial licensing barriers.
  2. *Superior Vertical Accuracy:* Demonstrates ~2m vertical RMSE, outperforming legacy SRTM 30m and ASTER GDEM over the Deccan Plateau.
  3. *Zero Missing Pixels:* Tile `Copernicus_DSM_COG_10_N17_00_E078_00_DEM.tif` contains complete, continuous data across Manikonda with zero NoData holes.
* **How It Is Implemented in AQUILA:** Processed in [`scripts/geospatial/process_dem.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_dem.py) via Rasterio. Clipped to the 55.63 km² bounding box into a 266 × 230 pixel grid (`dem_manikonda_clipped.tif`) with elevations ranging from 492.7m to 638.7m (EGM2008 vertical datum).
* **Practical Example:** The risk engine queries the DEM at latitude 17.3912, longitude 78.3845, extracting an elevation of 518.2m. Because this elevation lies in the bottom 25% of the catchment's relief, it receives an elevated terrain vulnerability score.
* **Limitations:** A 30m DSM averages surface elevations over a $900\text{ m}^2$ footprint and reflects tree canopies and building rooftops rather than bare earth. It cannot resolve sub-meter road curbs, gutters, or building plinths.

---

## 4. How Slope Was Calculated Using Horn's Method & Implementation Details

* **Concept:** Topographic slope represents the rate of maximum change in elevation from each grid cell to its neighbors, measured in degrees ($0^\circ - 90^\circ$).
* **Why It Was Selected:** Flat terrain ($<1.5^\circ$) impedes gravitational sheet runoff, causing water ponding. Steep terrain ($>15^\circ$) sheds water rapidly.
* **How It Is Implemented in AQUILA:**
  - *Theoretical Foundation:* In GIS literature and Phase 1 specifications, Horn's (1981) method is standard, using an 8-neighbor weighted finite-difference scheme to smooth surface roughness:
    $$\frac{\partial z}{\partial x} = \frac{(c + 2f + i) - (a + 2d + g)}{8 \cdot \Delta x}, \quad \frac{\partial z}{\partial y} = \frac{(g + 2h + i) - (a + 2b + c)}{8 \cdot \Delta y}$$
  - *Actual Python Implementation:* In [`scripts/geospatial/process_dem.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_dem.py), slope is computed via NumPy's 2nd-order central finite difference gradient:
    ```python
    res_m = src.res[0] * 111320  # ~30.9 metres
    dy, dx = np.gradient(data, res_m, res_m)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    ```
    This produces `slope_degrees_manikonda.tif` ranging from $0.0^\circ$ to $36.85^\circ$ (mean $4.18^\circ$).
* **Practical Example:** In Alkapur Township valley, the computed slope is $1.2^\circ$, producing a terrain slope score of $100/100$ (maximum stagnation risk). On the Khajaguda hills, slope exceeds $18^\circ$, yielding a minimum score of $15/100$.
* **Limitations:** Slope calculated across 30m cells smooths localized road cambers and drainage ditch gradients, underestimating localized runoff velocity.

---

## 5. How OpenStreetMap (OSM) Data Was Collected and Processed

* **Concept:** Community-driven global geospatial vector database providing road networks, waterways, water bodies, and public infrastructure.
* **Why It Was Selected:** Authoritative municipal GIS cadastres (GHMC / HMDA shapefiles) are restricted and unavailable publicly. OSM provides the only open, geometrically detailed street network for Manikonda.
* **How It Is Implemented in AQUILA:**
  1. Extracted raw OSM data via Overpass API queries covering the study bounding box.
  2. Executed cleaning scripts ([`scripts/geospatial/process_roads.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_roads.py), [`scripts/geospatial/process_drainage.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_drainage.py)).
  3. Filtered non-vehicular paths, retained 6,659 road segments, cleaned invalid geometries with Shapely, and converted topological coordinates into a directed NetworkX graph.
* **Practical Example:** When an incident occurs on Manikonda Road, the system renders the OSM arterial segment in cyan on the Folium map and confirms topological adjacency to nearby response depots.
* **Limitations:** OSM data is contributed voluntarily and lacks official ground verification. Subsurface stormwater drains are almost entirely absent in OSM, and 65 mapped critical facilities carry the `OSM_UNVERIFIED` provenance tag.

---

## 6. How ESA WorldCover Classifications Were Used

* **Concept:** Global land cover / land use (LULC) dataset produced by the European Space Agency at 10-meter spatial resolution from Sentinel-1 and Sentinel-2 imagery.
* **Why It Was Selected:** Surface infiltration is dictated by land cover. High-density urban built-up areas generate 4 to 5 times more surface runoff than vegetated parklands or croplands.
* **How It Is Implemented in AQUILA:**
  - Clipped to the study bounding box (`worldcover_manikonda_clipped.tif`, 888 × 768 pixels).
  - Built-up fraction measured at **51.72%** across the 55.63 km² envelope (refining Phase 1's preliminary estimate of >75%).
  - In [`app/services/risk_engine.py`](file:///C:/AI/Rural_internship_project/app/services/risk_engine.py), ESA class IDs map directly to runoff hazard scores:
    - Class 50 (Built-up): Score = $90$
    - Class 80 (Permanent Water Body buffer): Score = $95$
    - Class 60 (Bare rock / soil): Score = $65$
    - Class 40 (Cropland): Score = $35$
    - Class 30 (Grassland): Score = $30$
    - Class 10/20 (Tree cover / Shrubland): Score = $15$
* **Practical Example:** A query at Puppalguda commercial center maps to Class 50 (Built-up), assigning an impervious score of 90.0, which scales the composite flood risk upward.
* **Limitations:** The 2021 ESA dataset is static. Rapid construction in Manikonda between 2021 and 2026 means several former agricultural plots (Class 40) are now paved residential sites.

---

## 7. Why Rainfall Interpolation Uses Inverse Distance Weighting (IDW)

* **Concept:** Spatial interpolation technique based on Tobler's First Law of Geography: points closer to an observation station exert greater influence than points further away.
  $$Z(\mathbf{x}) = \frac{\sum_{i=1}^N \frac{Z_i}{d_i^p}}{\sum_{i=1}^N \frac{1}{d_i^p}}$$
* **Why It Was Selected:** Manikonda has no internal AWS. Rainfall must be estimated from 4 surrounding perimeter proxy stations (Gachibowli, Serilingampally, Begumpet, Rajendranagar). IDW provides an exact, deterministic, and computationally lightweight interpolator ($p=2$).
* **How It Is Implemented in AQUILA:** Formulated in Phase 2 spatial pipelines to interpolate point telemetry onto grid cells. In the MVP runtime, if station feeds are enabled, IDW computes the weighted average rainfall intensity across the Manikonda study centroid.
* **Practical Example:** If Gachibowli AWS (4.8 km NW) records 60 mm/hr and Rajendranagar AWS (8.2 km S) records 20 mm/hr, IDW assigns higher weight to Gachibowli ($w \propto 1/4.8^2 \approx 0.043$ vs $w \propto 1/8.2^2 \approx 0.015$), yielding an interpolated rate of ~49.7 mm/hr at Manikonda.
* **Limitations:** IDW cannot extrapolate outside the range of measured values (bullseye effect) and cannot simulate localized convective cloudburst cells smaller than the inter-station distance (~5–10 km).

---

## 8. What the Chicago Hyetograph Represents

* **Concept:** A synthetic, asymmetric design storm hyetograph developed by Keifer and Chu (1957) that preserves rainfall intensity-duration-frequency (IDF) curves while concentrating peak intensity at an asymmetric time fraction ($r \in [0.3, 0.5]$).
* **Why It Was Selected:** Evaluating flood response systems requires testing against extreme, stress-inducing storm events. The Chicago method produces a continuous, realistic rainfall profile with an abrupt convective burst rather than an artificial block rainfall.
* **How It Is Implemented in AQUILA:**
  - Prepared in [`data/processed/vector/rainfall_synthetic_hyetograph_validated.csv`](file:///C:/AI/Rural_internship_project/data/processed/vector/rainfall_synthetic_hyetograph_validated.csv) as a 120 mm / 3-hour storm peaking at 70 mm/hr at $T=45\text{ min}$ ($r=0.375$).
  - Fed into the runtime scenario engine (`MANI-HEAVY-001`) across 4 operational demo timesteps (12.5 $\to$ 35.0 $\to$ 70.0 $\to$ 18.0 mm/hr).
* **Practical Example:** At Step 3 ($T=45\text{ min}$), the rainfall rate reaches peak intensity (70 mm/hr). This tests whether the system dynamically escalates risk and triggers automated simulated incident injection.
* **Limitations:** The hyetograph is a calibrated illustrative design storm, not an official statutory IDF curve published by IMD or GHMC. It is classified strictly as `SIMULATED`.

---

## 9. How the Five-Factor Risk Index Works

* **Concept:** Multi-Criteria Evaluation (MCE) combining meteorological hazard and physical terrain vulnerability into a single dimensionless index $R \in [0, 100]$.
* **Why It Was Selected:** Complex 2D hydrodynamic solvers take hours to compute. Urban emergency managers need sub-second, transparent, and explainable risk scores to triage priority corridors.
* **How It Is Implemented in AQUILA:**
  Implemented in [`app/services/risk_engine.py`](file:///C:/AI/Rural_internship_project/app/services/risk_engine.py):
  $$R = \frac{0.40P + 0.20T + 0.20D + 0.10L + 0.10H}{\sum w_i} \times 100$$
  - $P$: Rainfall score (normalized 0–100 via IMD thresholds).
  - $T$: Terrain score (60% low elevation + 40% flat slope).
  - $D$: Drainage proximity score (distance decay to mapped nalas).
  - $L$: Land cover imperviousness score (ESA WorldCover).
  - $H$: Historical flood proximity score (proximity to October 2020 points).
  Categorized as `LOW` ($<40$), `MODERATE` ($40 - 69.9$), or `HIGH` ($\ge 70$).
* **Practical Example:** An operator evaluates Secretariat Road during 65 mm/hr rain: $P=75.3$, $T=82.0$, $D=75.0$, $L=90.0$, $H=75.0$. The formula yields $R = 78.0$ (`HIGH`), prompting immediate asset pre-positioning.
* **Limitations:** The index reflects relative spatial vulnerability, not physical flood depth in meters or inundation extent polygons.

---

## 10. Why Dynamic Weight Renormalization Is Necessary

* **Concept:** Mathematical adaptation of multi-criteria weights when one or more input layers are missing or null, ensuring the denominator always equals the sum of active weights.
  $$R = \frac{\sum_{i \in \text{Active}} w_i \cdot S_i}{\sum_{i \in \text{Active}} w_i}$$
* **Why It Was Selected:** In real-world GIS operations, spatial layers occasionally fail: a GPS query may lie outside a raster tile, or a cloud shadow may corrupt satellite land cover. Without renormalization, missing layers are treated as zero, artificially deflating the risk score.
* **How It Is Implemented in AQUILA:** In [`app/services/risk_engine.py`](file:///C:/AI/Rural_internship_project/app/services/risk_engine.py), if `distance_to_waterway_m is None`, the drainage component is appended to `missing_components` and excluded from `active_weights`. The score is divided by $\sum_{\text{active}} w_i$ rather than 1.0.
* **Practical Example:** If the drainage layer is unavailable ($w_D = 0.20$), total active weight becomes $0.80$. The remaining weights effectively scale by $1 / 0.80 = 1.25$ ($w_P$ becomes $0.50$, $w_T$ becomes $0.25$, etc.), preserving the calibrated 0–100 scale.
* **Limitations:** Renormalization assumes the missing layer's hazard distribution aligns with the remaining factors; if an unmapped nala is nearby, the risk may still be slightly underestimated.

---

## 11. How Incident Lifecycle Management Works

* **Concept:** Finite State Machine (FSM) enforcing valid operational state transitions for urban emergency reports to ensure data integrity and workflow compliance.
* **Why It Was Selected:** Unstructured ticketing systems allow operators to accidentally skip verification or leave resources stranded. A formal FSM guarantees systematic triage.
* **How It Is Implemented in AQUILA:**
  - Implemented in [`app/api/main.py`](file:///C:/AI/Rural_internship_project/app/api/main.py) and verified by automated tests:
    $$\text{REPORTED} \longrightarrow \text{ASSIGNED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{RESOLVED}$$
  - Status updates pass through `PATCH /api/incidents/{id}/status`.
  - When status transitions to `RESOLVED`, the system automatically marks linked assignments as `COMPLETED` and reverts attached emergency resources to `AVAILABLE`.
  - Every transition generates an immutable record in `AuditHistory`.
* **Practical Example:** An operator receives incident `INC-SIM-001`. They cannot mark it `RESOLVED` directly without first assigning a resource (`ASSIGNED`) and confirming field work has begun (`IN_PROGRESS`).
* **Limitations:** Does not currently support branching states like `ESCALATED` or `CANCELLED_FALSE_ALARM`.

---

## 12. How Resource Compatibility and Haversine Distance Are Used

* **Concept:** Multi-attribute emergency dispatch pairing operational capability matching with spherical geodesy to identify the closest suitable response asset.
* **Why It Was Selected:** Sending an inflatable boat to pump water out of a flooded basement is ineffective. The system must filter by equipment capability before ranking by geographic proximity.
* **How It Is Implemented in AQUILA:**
  - In [`app/services/resource_service.py`](file:///C:/AI/Rural_internship_project/app/services/resource_service.py):
    1. Capability filter maps incident type (e.g., `WATERLOGGING` $\to$ `["PUMPING", "ROAD_CLEARING"]`).
    2. Available units are scored via the Great-Circle Haversine formula ($R = 6371\text{ km}$):
       $$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos \phi_1 \cos \phi_2 \sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
    3. Prevents duplicate deployment: If a resource is already `ASSIGNED`, assignment raises an HTTP 400 error.
* **Practical Example:** For a flash flood at Alkapur Township, the system queries available assets, ignores rescue boats, identifies dewatering pump `RES-PUMP-01` at Manikonda Ward Depot (0.74 km away), and displays it as the top recommendation.
* **Limitations:** Haversine computes straight-line distance ("as the crow flies"). It does not evaluate road network travel times, traffic congestion, or flooded street closures.

---

## 13. How the Scenario Engine Changes System State

* **Concept:** A discrete event simulation controller that deterministically modifies rainfall observations, recalculates spatial risk, and triggers synthetic incidents along a pre-defined timeline.
* **Why It Was Selected:** Evaluators and emergency trainees cannot wait for real monsoon storms to test workflows. A deterministic scenario allows repeatable demonstration and stress-testing.
* **How It Is Implemented in AQUILA:**
  - Managed by `ScenarioManager` in [`app/services/scenario_service.py`](file:///C:/AI/Rural_internship_project/app/services/scenario_service.py).
  - Executing `advance_step()` writes a `RainfallObservation` tagged `SIMULATED`, recomputes risk, and at Step 3 ($70\text{ mm/hr}$), automatically injects incident `INC-SIM-001` into the SQLite database.
  - Resetting the scenario triggers a targeted SQL deletion: deletes only records where `source_type == "SIMULATED"`, restores assigned resources, and leaves historical field data untouched.
* **Practical Example:** Advancing to Step 3 raises rainfall to 70 mm/hr. The map immediately displays `INC-SIM-001` with a red marker. Once the evaluation is finished, clicking Reset wipes `INC-SIM-001` from the database in 15ms.
* **Limitations:** Scenarios follow a fixed, pre-scripted hyetograph rather than dynamic agent-based stochastic behavior.

---

## 14. How Database Transactions and Audit Logging Work

* **Concept:** Relational ACID transactions coupled with an append-only operational audit trail to record every administrative and automated system action.
* **Why It Was Selected:** Municipal disaster operations require accountability. Post-disaster reviews must determine who dispatched a resource, what the rainfall was, and exactly when status transitions occurred.
* **How It Is Implemented in AQUILA:**
  - Built using SQLAlchemy 2.0 and SQLite in [`app/db/database.py`](file:///C:/AI/Rural_internship_project/app/db/database.py).
  - Standardized on `utc_now()` returning timezone-naive UTC datetimes to prevent Python 3.13 deprecation warnings.
  - The `AuditHistory` table records: `entity_type`, `entity_id`, `action`, `details`, and `timestamp`.
* **Practical Example:** When an operator approves dispatch for `RES-PUMP-01`, an audit record is created: `"Operator approved deployment of RES-PUMP-01 to incident INC-SIM-001 at 2026-11-03T17:15:22"`.
* **Limitations:** It is an append-only application log stored in SQLite; it does not utilize a cryptographically immutable blockchain ledger or write-once cloud storage.

---

## 15. Why SQLite and FastAPI Were Selected

* **Concept:** Modern, lightweight Python technology stack prioritizing zero-dependency local portability, high-performance async concurrency, and strict schema validation.
* **Why It Was Selected:**
  - *FastAPI:* Provides async execution, automatic OpenAPI Swagger documentation, and Pydantic V2 schema validation with sub-millisecond route latency.
  - *SQLite:* Serverless, zero-configuration relational database stored as a single file (`aquila_mvp.db`). Perfect for a self-contained academic MVP evaluated on standalone laptops without requiring PostgreSQL/PostGIS server installation.
* **How It Is Implemented in AQUILA:**
  - FastAPI runs in [`app/api/main.py`](file:///C:/AI/Rural_internship_project/app/api/main.py).
  - SQLite is managed via SQLAlchemy ORM with foreign key cascades and thread-safe session factories.
* **Practical Example:** An evaluator can clone the repository and run `pytest` or `uvicorn` immediately without installing database servers or configuring Docker containers.
* **Limitations:** SQLite locks the entire database file during write transactions, limiting scalability beyond ~50 concurrent write requests per second.

---

## 16. Why SWMM or a 2D Hydrodynamic Model Was Not Implemented

* **Concept:** Physics-based numerical modeling solving 2D Shallow Water Equations (Saint-Venant equations) or 1D Saint-Venant pipe flow (EPA-SWMM).
* **Why It Was Not Implemented in the MVP:**
  1. *Computational Overhead:* Solving 2D fluid momentum across a 55.63 km² grid requires minutes to hours of GPU/CPU cluster computation, making real-time slider interactivity impossible.
  2. *Data Paucity:* 2D hydrodynamic solvers require continuous micro-topography (sub-meter bare-earth LiDAR), detailed culvert geometry, pipe friction coefficients (Manning's $n$), and underground pipe cadastres—none of which are publicly accessible for Manikonda.
  3. *Scope & Time Constraints:* Building a calibrated SWMM model requires months of hydraulic survey; the two-day MVP focused on software architecture and decision support.
* **How It Is Handled in AQUILA:** Substituted with the 5-factor rule-based risk engine, which computes relative vulnerability in $<4\text{ ms}$.
* **Practical Example:** While SWMM computes whether water depth on Puppalguda Road is 0.48m or 0.52m after 40 minutes, AQUILA immediately flags Puppalguda Road as `HIGH` risk ($R=76/100$) the moment rainfall hits 60 mm/hr.
* **Limitations:** AQUILA cannot predict dynamic flood wave propagation, backwater inundation velocity, or exact waterline contours.

---

## 17. Why AQUILA Is a Decision-Support Prototype Rather than an Operational Warning System

* **Concept:** Distinction between an academic decision-support prototype (demonstrating algorithmic integration and workflow feasibility) and a statutory operational warning system (legally authorized to issue evacuation orders).
* **Why This Distinction Is Strictly Maintained:**
  - False alerts in public warning systems cause panic, economic disruption, and loss of life.
  - Statutory warning authority belongs exclusively to government bodies: GHMC, HYDRAA, IMD, and NDMA.
  - AQUILA operates on open, unverified datasets (OSM) and synthetic demonstration resources.
* **How It Is Implemented in AQUILA:**
  - Explicit warning banners on the dashboard.
  - Synthetic resources tagged `[DEMO SYNTHETIC]` with `provenance="SIMULATED"`.
  - Comprehensive disclosures in [`docs/final-audit/technical_limitations.md`](file:///C:/AI/Rural_internship_project/docs/final-audit/technical_limitations.md).
* **Practical Example:** In an academic viva, when asked if the platform can be deployed tomorrow to evacuate Manikonda residents, the candidate defends: *"No. AQUILA is an academic decision-support prototype. It demonstrates the technical workflow for municipal operators but lacks ground-calibrated hydraulic sensors and statutory authorization."*
* **Limitations:** Must not be connected to public sirens or civilian emergency SMS gateways in its current MVP state.

