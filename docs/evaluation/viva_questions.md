# AQUILA — 60 Comprehensive Viva Questions and Model Answers

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Area:** Manikonda Pilot Area, Hyderabad, Telangana, India  
**Target Audience:** Academic Project Viva Examiners, Technical Evaluators, and Defending Students  
**Document Location:** `docs/evaluation/viva_questions.md`  

---

## Category 1: Basic Project Questions (10 Questions)

### Q1. What is AQUILA, and what core problem does it solve?
**Answer:** AQUILA is an academic geospatial decision-support prototype engineered to integrate multi-source spatial data, empirical flood risk scoring, incident lifecycle tracking, emergency resource dispatch, and scenario simulation for urban flood management. It solves the critical operational challenge of information fragmentation during flash floods in rapidly urbanizing Indian peripheral catchments like Manikonda, Western Hyderabad.

### Q2. Is AQUILA an official public flood forecasting and warning system?
**Answer:** No. AQUILA is an academic decision-support prototype. It does not replace statutory municipal and meteorological agencies such as GHMC, HYDRAA, IMD, or NDRF. It is designed to assist municipal control-room operators with transparent spatial analytics, not to issue legal civilian evacuation directives.

### Q3. Why did you choose Manikonda in Hyderabad as the pilot study area?
**Answer:** Manikonda represents an ideal real-world urban flash flood laboratory: it underwent hyper-rapid urbanization over 15 years, expanding built-up cover to over 51% across the envelope. It exhibits steep topographic relief (638m Khajaguda ridge down to 492m Neknampur Lake), has natural drainage channels encroached by high-rise developments, and suffered severe, well-documented inundation during the October 2020 Hyderabad floods.

### Q4. What are the two operational modes supported by AQUILA?
**Answer:** AQUILA supports:
1. *Real-World / Field Mode:* Uses verified spatial datasets (roads, nalas, lakes, DEM terrain) and historical rainfall/flood evidence for baseline spatial risk analysis.
2. *Simulation Mode:* Uses controlled synthetic rainfall hyetographs (e.g., scenario `MANI-HEAVY-001`), synthetic emergency fleet resources, and deterministic incident injection for operator training and system testing without contaminating real operational records.

### Q5. What is the difference between the municipal boundary, the catchment, and the analysis envelope?
**Answer:**
- *Municipal Boundary (~15.5 km²):* The administrative and political jurisdiction of Manikonda Municipality.
- *Hydrological Catchment (~22.4 km²):* The natural topographic surface drainage basin bounded by ridgelines, naturally draining into Neknampur Lake.
- *Analysis Envelope (55.63 km²):* A rectangular geospatial modeling bounding box (`[17.3605°N, 78.3455°E]` to `[17.4245°N, 78.4195°E]`) established with a 500m buffer to guarantee hydrological continuity from upstream ridges down to receiving water bodies.

### Q6. Why didn't you use Machine Learning or Deep Learning for flood prediction?
**Answer:** Deep learning models require thousands of historical, ground-truthed sensor observations (e.g., historical flood depth grids, IoT water level timeseries) that simply do not exist for Manikonda. Furthermore, ML models operate as "black boxes," making it impossible for municipal engineers to trace why a specific street was flagged. AQUILA uses a transparent, explainable 5-factor multi-criteria evaluation with mathematically defensible weights.
*Follow-up:* Could ML be added later? *Answer:* Yes, once IoT water-level sensor networks provide sufficient continuous training data, ML can serve as a secondary predictive component.

### Q7. What technology stack powers AQUILA, and why was it chosen?
**Answer:** The platform is built on Python 3.13, FastAPI for the REST API service tier, SQLAlchemy 2.0 with SQLite for relational persistence, Streamlit with Folium for interactive geospatial dashboards, GeoPandas/Shapely/Rasterio for GIS operations, and Pytest for automated testing. This stack was selected because it is 100% open-source, runs cross-platform without complex server dependencies, and executes sub-second analytics.

### Q8. What is the current verification status of the project?
**Answer:** The project has completed Phase 1 (Research & Specification), Phase 2 (Geospatial Acquisition & Preprocessing), Phase 3 (Emergency MVP Implementation), and a comprehensive Final Audit. It possesses **57 automated Pytest tests passing with a 100% pass rate** in 2.39 seconds.

### Q9. What are the key end-to-end user workflows demonstrated by AQUILA?
**Answer:** The complete workflow includes:
1. Viewing multi-layer GIS assets on an interactive Folium map.
2. Dynamically computing the 5-factor geographic risk score.
3. Advancing the `MANI-HEAVY-001` heavy rainfall scenario to peak downpour (70 mm/hr).
4. Observing automated injection of flash-flood incident `INC-SIM-001`.
5. Running capability-matched, proximity-based emergency resource recommendation (`RES-PUMP-01`).
6. Dispatching the resource and transitioning incident status from `REPORTED` to `ASSIGNED` to `RESOLVED`.
7. Reviewing the append-only operational audit log.
8. Executing a safe scenario reset that purges simulated data while preserving historical records.

### Q10. What are the primary ethical considerations when deploying flood software?
**Answer:** Ethical considerations include: never presenting synthetic data as real-world observations, explicitly tagging unverified open data (`OSM_UNVERIFIED`), preventing operator confusion through visible demo badges (`[DEMO SYNTHETIC]`), and clearly disclaiming statutory forecasting authority to avoid causing public panic or interfering with official emergency communications.

---

## Category 2: Geospatial & GIS Questions (10 Questions)

### Q11. Why does AQUILA employ a dual Coordinate Reference System (CRS) architecture?
**Answer:** AQUILA uses `EPSG:4326` (WGS 84 geographic coordinates in decimal degrees) for storage, GeoJSON interoperability, and web mapping. However, for planar spatial operations—such as buffer creation, distance calculations, slope derivation, and area measurements—it dynamically transforms data into `EPSG:32644` (UTM Zone 44N, in metres). This avoids severe spatial distortion, because at Hyderabad's latitude (~17.4°N), 1° longitude (~106.1 km) does not equal 1° latitude (~110.7 km).

### Q12. What Digital Elevation Model (DEM) is used, and what are its specifications?
**Answer:** We use the Copernicus DEM GLO-30 DSM (Tile `Copernicus_DSM_COG_10_N17_00_E078_00_DEM.tif`), which provides 1 arc-second (~30.9-meter) horizontal resolution and ~2m vertical accuracy referenced to the EGM2008 geoid. It was clipped to a 266 × 230 pixel grid covering Manikonda with elevations spanning 492.7m to 638.7m and zero NoData pixels.

### Q13. What is the fundamental difference between a DEM, a DTM, and a DSM?
**Answer:** A Digital Elevation Model (DEM) is a generic term. A Digital Terrain Model (DTM) represents the bare ground surface with all trees and man-made structures removed. A Digital Surface Model (DSM)—which Copernicus GLO-30 is—captures the top reflective surface, including tree canopies, building roofs, and overpasses.
*Follow-up:* How does a DSM affect urban flood modeling? *Answer:* Rooftop heights in dense apartment blocks can artificially inflate surface elevation, causing a DSM to act as if buildings are impassable solid terrain blocks rather than channels.

### Q14. Can a 30-meter DEM resolve urban roadside curbs and drainage gutters?
**Answer:** No. Urban stormwater flow is heavily governed by micro-topography: 15cm road curbs, compound walls, and basement ramps. A 30m grid cell covers $900\text{ m}^2$, averaging out street gutters and roadside drains. Resolving curbs requires sub-meter LiDAR or high-density drone photogrammetry.

### Q15. How were OpenStreetMap road networks cleaned and validated?
**Answer:** Raw OSM Overpass exports were filtered by highway classification (keeping arterial, secondary, tertiary, residential, and link roads while discarding pedestrian tracks). Features were clipped to the study bounding box, duplicate OSM IDs were removed, and topological geometries were validated via Shapely. The network comprises 6,659 cleaned segments.

### Q16. What is the difference between open nalas and subsurface stormwater drains in Manikonda?
**Answer:** Open nalas are wide, natural, or concrete-lined surface canals that drain water bodies into the Musi river basin; these are mapped in OpenStreetMap and satellite imagery. Subsurface stormwater drains are underground buried concrete pipes and culverts. In Manikonda, municipal underground pipe cadastre data is not publicly available in GIS format, which is an openly documented system limitation.

### Q17. How many water bodies and waterways are mapped in the Manikonda study envelope?
**Answer:** In the 55.63 km² pilot envelope, AQUILA maps **21 open waterway channels** totaling 9.71 km in length and **24 surface water bodies** (lakes, cheruvus, and retention ponds) covering 1.51 km², including major lakes like Neknampur Lake (Pedda Cheruvu) and Chinna Cheruvu.

### Q18. What land cover dataset is used, and what is the built-up share in Manikonda?
**Answer:** We used the ESA WorldCover 2021 dataset at 10-meter spatial resolution. Across the 55.63 km² analysis envelope, the built-up impervious urban share is **51.72%**. This refined the preliminary Phase 1 estimate of >75%, because the larger envelope includes open agricultural patches, rocky granite outcrops, and water bodies.

### Q19. How did you identify historical flood evidence points?
**Answer:** Five ground-truth flood points were compiled from verified post-event municipal reports and geo-referenced news reports from the catastrophic October 2020 Hyderabad floods (recording inundation depths between 0.45m and 0.70m in locations such as Alkapur Township and Neknampur Lake spillway).

### Q20. Why can't satellite Synthetic Aperture Radar (SAR) like Sentinel-1 be easily used for urban flash flood detection in Manikonda?
**Answer:** In dense urban environments, SAR radar beams suffer from "radar shadow" and "double-bounce scattering" caused by high-rise apartment towers and narrow street canyons. Floodwater inside narrow street corridors cannot reflect the radar signal cleanly back to the satellite, rendering spaceborne SAR ineffective for localized urban street flooding.

---

## Category 3: Data Engineering & Preprocessing Questions (10 Questions)

### Q21. What is data provenance, and what taxonomy does AQUILA enforce?
**Answer:** Data provenance records the origin, derivation history, and custody of data. AQUILA enforces a strict 5-tier taxonomy:
1. `OBSERVED`: Direct physical sensor measurements (Official IMD AWS stations).
2. `HISTORICAL`: Verified archival event records (October 2020 flood points).
3. `DERIVED_ANALYTICAL`: Geoprocessed analytical layers (Slope raster derived from DEM).
4. `MANUALLY_SEEDED`: Baseline municipal infrastructure centroids.
5. `SIMULATED`: Synthetic demonstration models, scenarios, and test resources.

### Q22. How are raw data files converted into processed GeoJSON and GeoTIFF formats?
**Answer:** Python automated preprocessing scripts in `scripts/geospatial/` execute an idempotent pipeline:
- `process_dem.py` uses Rasterio to clip raw DEM GeoTIFFs and derive slope grids.
- `process_roads.py` filters raw OSM GeoJSON, cleans attributes, and builds NetworkX topology.
- `process_drainage.py` cleans water bodies and line channels using Shapely.
- `process_rainfall.py` normalizes historical station CSVs and validates synthetic hyetographs.
All outputs are written to `data/processed/`.

### Q23. What happens if a raw GeoJSON feature contains a self-intersecting or invalid geometry?
**Answer:** The preprocessing pipeline uses Shapely's `is_valid` property to inspect every feature. Degenerate geometries (e.g., LineStrings with fewer than 2 coordinates, self-intersecting polygon rings) are either repaired using `shapely.validation.make_valid()` or logged and rejected. All 8 processed vector GeoJSONs pass 100% validity checks in Pytest.

### Q24. How is metadata tracked across the data pipeline?
**Answer:** Metadata is tracked in three synchronized machine-readable formats in `docs/phase-2/`:
1. `data_inventory.yaml`: Hierarchical source authority, licensing, and processing parameters.
2. `data_inventory.csv`: Tabular catalog for spreadsheet audits.
3. `processing_manifest.json`: Execution timestamps, file sizes, bounding boxes, and SHA-256 hashes.

### Q25. Why are there no Automated Weather Stations (AWS) inside core Manikonda?
**Answer:** Historically, Manikonda was an unincorporated panchayat. Official IMD and TSDPS weather stations were established in older, established administrative centers: Gachibowli (4.8 km NW), Rajendranagar (8.2 km S), Shaikpet (5.5 km NE), and Begumpet (13.5 km NE). Manikonda relies on these perimeter stations as spatial proxies.

### Q26. What is the Chicago Design Storm, and how was the synthetic hyetograph constructed?
**Answer:** The Chicago Design Storm is an analytical method that creates an asymmetric triangular rainfall hyetograph based on Intensity-Duration-Frequency (IDF) parameters. AQUILA constructed a 120 mm / 3-hour storm peaking at 70 mm/hr at $T=45\text{ min}$ ($r=0.375$). It approximates a 1-in-25 to 1-in-50 year convective storm analog of the October 2020 event.

### Q27. What is the verification status of the 65 critical infrastructure facilities mapped in the system?
**Answer:** All 65 critical facilities (substations, clinics, emergency centers, schools) are tagged `OSM_UNVERIFIED` and `UNKNOWN_UNVERIFIED`. Because they were extracted from OpenStreetMap and have not undergone on-site physical municipal audits, we explicitly refrain from claiming operational field verification.

### Q28. How does the pipeline ensure idempotency?
**Answer:** All preprocessing scripts are designed to be idempotent: re-running them multiple times with the same raw inputs produces identical output files, identical geometries, and identical checksums without accumulating duplicate database records or file bloat.

### Q29. How does AQUILA handle raster NoData values?
**Answer:** In `process_dem.py`, the Copernicus DEM tile was inspected and confirmed to contain zero NoData pixels within the study bounding box. When deriving slope, boundary edge artifacts are assigned a standard nodata value (`-9999.0`), and floating-point NaNs are masked before statistics are computed.

### Q30. Why is database seeding necessary for the MVP?
**Answer:** Emergency fleet assets (dewatering pumps, rescue squads) cannot be fetched from live government GPS APIs due to security restrictions. The seed script [`app/db/seed.py`](file:///C:/AI/Rural_internship_project/app/db/seed.py) populates the SQLite database with 6 plausible demonstration resources tagged `[DEMO SYNTHETIC]` to enable immediate end-to-end testing of the dispatch workflow.

---

## Category 4: Risk Modelling & Mathematical Questions (10 Questions)

### Q31. State the exact mathematical formula for the AQUILA Geographic Risk Index.
**Answer:**
$$R = \frac{\sum_{i=1}^n w_i \cdot S_i}{\sum_{i=1}^n w_i} \times 100$$
Under full layer availability, with default weights summing to 1.00:
$$R = 0.40 \cdot S_P + 0.20 \cdot S_T + 0.20 \cdot S_D + 0.10 \cdot S_L + 0.10 \cdot S_H$$
Where $S_P$ is Precipitation Hazard, $S_T$ is Terrain Vulnerability, $S_D$ is Drainage Proximity, $S_L$ is Land Cover Imperviousness, and $S_H$ is Historical Flood Recurrence.

### Q32. How is continuous rainfall intensity (mm/hr) converted into a 0–100 score?
**Answer:** It uses a 4-tier piecewise linear function based on IMD classification breakpoints:
- $0\text{ mm/hr} \implies 0$
- $0 < \text{rate} < 15.6\text{ mm/hr}$ (Moderate): Scaled linearly from $0$ to $40$.
- $15.6 \le \text{rate} < 64.5\text{ mm/hr}$ (Heavy): Scaled linearly from $40$ to $75$.
- $64.5 \le \text{rate} < 100.0\text{ mm/hr}$ (Very Heavy): Scaled linearly from $75$ to $100$.
- $\ge 100.0\text{ mm/hr}$ (Cloudburst): Clamped at $100.0$.

### Q33. How does the terrain component combine elevation and slope?
**Answer:** The terrain score $S_T$ is a weighted combination of $60\%$ elevation basin risk and $40\%$ slope stagnation risk:
$$S_T = 0.60 \cdot S_{\text{elev}} + 0.40 \cdot S_{\text{slope}}$$
Low valley elevations ($\le 495\text{m}$) score 100, while ridges ($\ge 600\text{m}$) score 10. Flat slopes ($\le 1.5^\circ$) score 100, while steep slopes ($\ge 15^\circ$) score 15.

### Q34. How does the system handle missing geospatial layers during risk calculation?
**Answer:** The risk engine applies **Dynamic Weight Renormalization**. If a component is null (e.g., terrain data unavailable), it is excluded from active weights. The score is computed as $\sum_{\text{active}} w_i S_i / \sum_{\text{active}} w_i$. This ensures the remaining factors scale proportionally to sum to 1.0, preventing the risk score from falsely dropping to zero.

### Q35. What are the risk category classification thresholds implemented in the code?
**Answer:** In [`app/services/risk_engine.py`](file:///C:/AI/Rural_internship_project/app/services/risk_engine.py):
- **$0.0 \le R < 40.0$:** `LOW`
- **$40.0 \le R < 70.0$:** `MODERATE`
- **$70.0 \le R \le 100.0$:** `HIGH`

### Q36. Can the AQUILA Risk Score predict the physical flood depth in meters?
**Answer:** No. The risk score is a dimensionless relative vulnerability index ($0 - 100$), indicating which locations are most susceptible to waterlogging. It does not calculate physical flood water depth ($h$) or flood volume in cubic meters. Predicting water depth requires solving 2D Shallow Water hydrodynamic differential equations.

### Q37. What is Inverse Distance Weighting (IDW), and what is its mathematical formula?
**Answer:** IDW is a spatial interpolation technique where unmonitored locations are estimated by a distance-weighted average of observed points:
$$Z(\mathbf{x}) = \frac{\sum_{i=1}^N \frac{Z_i}{d_i^p}}{\sum_{i=1}^N \frac{1}{d_i^p}}$$
Where $Z_i$ is the rainfall at station $i$, $d_i$ is the distance to the target coordinate, and $p$ is the power parameter (typically $p=2$, inverse square).

### Q38. How is slope calculated from the DEM in Python?
**Answer:** In `scripts/geospatial/process_dem.py`, slope is computed using NumPy's central finite difference gradient:
```python
dy, dx = np.gradient(data, res_m, res_m)
slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
slope_deg = np.degrees(slope_rad)
```
Where `res_m` is the grid cell spacing in metres (~30.9m).

### Q39. What is the Great-Circle Haversine distance formula?
**Answer:**
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d = 2 R_{\text{earth}} \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$
Where $R_{\text{earth}} = 6371.0\text{ km}$, and coordinates are converted to radians. It calculates the shortest spherical surface distance between two latitude/longitude points.

### Q40. Why does Haversine distance differ from actual road driving distance?
**Answer:** Haversine measures straight-line distance through the air ("as the crow flies"). It ignores road network geometry, winding street layouts (tortuosity factor of 1.3 to 1.6 in Manikonda), physical barriers (compound walls, railway lines), and flooded impassable road segments.

---

## Category 5: Backend, API & Database Questions (10 Questions)

### Q41. Why did you choose FastAPI over Flask or Django?
**Answer:** FastAPI offers native asynchronous concurrency (`async/await`), automatic OpenAPI/Swagger documentation generation (`/docs`), high execution speed comparable to NodeJS and Go, and integrated data validation using Pydantic V2. For a geospatial REST service requiring rapid sub-second query evaluation, FastAPI is technically superior to Flask and far lighter than Django.

### Q42. Why did you choose SQLite over PostgreSQL / PostGIS for the MVP?
**Answer:** For an academic evaluation prototype with a strict two-day MVP delivery timeline, SQLite requires zero installation, zero server daemon management, and zero credential configuration. The entire database is stored in a single file (`aquila_mvp.db`), allowing any evaluator to clone the repo and run it instantly. PostGIS is an enhancement for enterprise production.

### Q43. How does the Incident Lifecycle state machine work?
**Answer:** The lifecycle is managed in `app/api/main.py`:
$$\text{REPORTED} \longrightarrow \text{ASSIGNED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{RESOLVED}$$
The API rejects invalid state skips (e.g., trying to jump from `REPORTED` directly to `RESOLVED`) with an HTTP 400 Bad Request error. Marking an incident `RESOLVED` automatically releases all linked resources back to `AVAILABLE`.

### Q44. How does the system prevent duplicate emergency resource assignments?
**Answer:** In [`app/services/resource_service.py`](file:///C:/AI/Rural_internship_project/app/services/resource_service.py), before dispatching a resource, the system checks whether its status is already `ASSIGNED` to another active incident. If an operator attempts to double-book a resource, the service raises a `ValueError`, which FastAPI returns as an HTTP 400 error stating that the resource is already deployed.

### Q45. How does the resource recommendation engine match capabilities?
**Answer:** The service maintains a capability mapping dictionary:
- `WATERLOGGING` $\implies$ `["PUMPING", "ROAD_CLEARING"]`
- `CELLAR_FLOODING` $\implies$ `["PUMPING"]`
- `DRAIN_OVERFLOW` $\implies$ `["DEBRIS_CLEARING", "PUMPING"]`
- `STRUCTURAL_HAZARD` $\implies$ `["WATER_RESCUE", "MEDICAL_EVAC"]`
It filters available resources matching the incident's required capability, then sorts the matching candidates by Haversine proximity.

### Q46. How are database timestamps managed, and how did you resolve Python 3.13 deprecation warnings?
**Answer:** In Python 3.13, `datetime.utcnow()` is deprecated. We created a centralized helper `utc_now()` in `app/db/database.py` that returns `datetime.now(timezone.utc).replace(tzinfo=None)`. This provides clean, timezone-naive UTC timestamps across all database models and eliminated all 56 deprecation warnings.

### Q47. What is stored in the `AuditHistory` table?
**Answer:** The `AuditHistory` table implements an append-only operational log recording: `id`, `entity_type` (`INCIDENT`, `ASSIGNMENT`, `SCENARIO`), `entity_id`, `action` (`CREATED`, `STATUS_UPDATED`, `RECOMMENDED`, `ASSIGNED`, `SCENARIO_STARTED`, `SCENARIO_RESET`), `details` (human-readable string), and `timestamp` (UTC).

### Q48. Is the AQUILA audit log cryptographically immutable?
**Answer:** No. It is an append-only relational audit table stored in SQLite. It does not use cryptographic hashing (like blockchain) or write-once-read-many (WORM) hardware storage. However, the application layer provides no endpoints to edit or delete audit records, preserving an audit trail for administrative review.

### Q49. How does the scenario engine maintain simulation isolation?
**Answer:** All simulated incidents receive `source_type="SIMULATED"` and the code prefix `INC-SIM-*`. Simulated rainfall receives `source_type="SIMULATED"`. When `reset_scenario()` is executed, it runs a scoped SQL query deleting only records where `source_type == "SIMULATED"`, leaving operator-created and historical records completely intact.

### Q50. How does the Streamlit dashboard communicate with the backend?
**Answer:** In the integrated MVP architecture, the Streamlit dashboard imports the database session factory (`SessionLocal`) and modular service layer functions directly (`compute_geographic_risk`, `recommend_resource_for_incident`, `scenario_manager`). It can also query the running FastAPI REST endpoints over HTTP.

---

## Category 6: Testing & Validation Questions (5 Questions)

### Q51. How many automated tests exist, and how are they organized?
**Answer:** There are **57 automated Pytest tests** divided into two suites:
1. `tests/geospatial/test_data_validation.py` (41 tests): Validates vector CRS (EPSG:4326), geometry validity, bounding box coordinates, raster elevation/slope ranges, road graph connectivity ($\ge 90\%$), provenance tags, and rainfall physical bounds.
2. `tests/mvp/test_backend.py` (16 tests): Validates API health, database seeding, risk engine scoring, dynamic weight renormalization, incident lifecycle, duplicate assignment prevention, scenario determinism, and audit history.

### Q52. What is the execution speed of your automated test suite?
**Answer:** The complete test suite of 57 tests executes in **2.39 seconds** on a standard developer workstation, demonstrating the efficiency of vectorization and lightweight SQLite architecture.

### Q53. How do you validate a system when real-time ground-truth flood sensor feeds are unavailable?
**Answer:** We validate through:
1. *Boundary and Regression Testing:* Ensuring mathematical outputs remain clamped within physically valid bounds ($R \in [0, 100]$, elevation $492 - 639\text{m}$, slope $0 - 90^\circ$).
2. *Historical Ground-Truth Benchmarking:* Verifying that known October 2020 waterlogging points receive high risk scores under heavy rainfall conditions.
3. *Deterministic Scenario Invariant Checks:* Running scenario `MANI-HEAVY-001` multiple times to verify that identical rainfall steps produce identical incident injections and risk escalations.

### Q54. What did the road connectivity test prove, and what was the numerical result?
**Answer:** Test `test_road_network_connectivity` constructs a directed NetworkX graph of the 6,659 road segments and computes weakly connected components. The result was **94.7% connectivity** in the largest connected component, easily exceeding the Phase 1 NFR-004 threshold of $\ge 90\%$.

### Q55. How do you test for duplicate resource assignment prevention?
**Answer:** In `tests/mvp/test_backend.py`, test `test_duplicate_resource_assignment_prevention` creates two separate incidents (`INC-A` and `INC-B`). It assigns resource `RES-1` to `INC-A`, and then attempts to assign `RES-1` to `INC-B`. The test asserts that the service raises a `ValueError` (HTTP 400), confirming that mutual exclusion is strictly enforced.

---

## Category 7: Limitations, Ethics & Future Scope Questions (5 Questions)

### Q56. Why didn't you implement the EPA Storm Water Management Model (SWMM)?
**Answer:** SWMM is a 1D/2D hydrodynamic engine that solves the dynamic Saint-Venant equations for pipe networks and surface channels. It requires continuous pipe diameters, slope invert levels, manhole surface elevations, and headloss friction coefficients. Because the Greater Hyderabad Municipal Corporation does not publish public GIS cadastres of underground pipes in Manikonda, building an uncalibrated SWMM model would give a false illusion of hydraulic accuracy.

### Q57. What are the primary technical limitations of AQUILA today?
**Answer:**
1. *Empirical Index vs. Hydrodynamics:* Computes relative vulnerability (0–100), not physical flood water depth ($h(x, y, t)$).
2. *Underground Cadastre Gap:* Cannot model clogged subsurface pipe conduits.
3. *30m DEM Resolution:* Averages out urban curbs and roadside drainage ditches.
4. *Haversine Metric:* Straight-line proximity does not account for flooded road closures.
5. *Synthetic Fleet:* Emergency assets are modeled demonstration units, not live GHMC telemetry.

### Q58. How could the platform be upgraded from Haversine distance to dynamic flood routing?
**Answer:** In Phase 4/5, the existing NetworkX road graph can be coupled with dynamic edge impedance weights. If an incident or high risk score occurs on an edge, that edge's traversal weight is set to infinity (closed road). The system then runs Dijkstra or A* shortest-path algorithms to route emergency vehicles strictly along dry, unflooded roads.

### Q59. What IoT hardware would be required to transition AQUILA into a live monitoring system?
**Answer:** It would require deploying:
1. Solar-powered IoT ultrasonic or radar water level sensors mounted on culverts and bridges across the 21 open nalas and Neknampur Lake.
2. Low-cost optical or tipping-bucket rain gauges installed at municipal ward offices.
3. LoRaWAN or 4G-LTE telemetry nodes transmitting sensor readings via MQTT/REST to the FastAPI backend every 5 minutes.

### Q60. If you had 6 more months on this project, what would be your top engineering priority?
**Answer:** My top priority would be acquiring high-resolution (<1m) drone photogrammetric or LiDAR elevation data for the low-lying Alkapur and Puppalguda corridors, surveying critical culvert cross-sections, and coupling our FastAPI backend with a GPU-accelerated 2D shallow-water hydrodynamic solver to compute real-time waterline contours and flood travel times.

