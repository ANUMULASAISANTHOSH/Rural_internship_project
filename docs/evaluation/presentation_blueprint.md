# AQUILA — Academic Presentation Blueprint & Slide Deck Specification

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Pilot Study Area:** Manikonda, Hyderabad, Telangana, India  
**Target Audience:** Academic Project Evaluation Committee, External Examiners, and Department Defense Panel  
**Estimated Total Presentation Time:** 15 Minutes (1 Minute per Slide on Average)  
**Document Location:** `docs/evaluation/presentation_blueprint.md`  

---

## Slide 1: Title and Project Introduction

* **Slide Title:** AQUILA: Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform
* **Key Content:**
  - **Academic Project Defense:** Capstone Project / Engineering Dissertation
  - **Focus Area:** Geospatial Decision Support for Urban Flood Management
  - **Case-Study Region:** Manikonda Pilot Catchment, Western Hyderabad, Telangana
  - **Core Integration:** Geospatial Data Layers + Empirical Risk Scoring + Incident Management + Proximity Dispatch + Synthetic Scenario Simulation
  - **Status:** Functional Academic MVP (57 Automated Verification Tests Passing)
* **Recommended Visual / Diagram:**
  - High-resolution system logo alongside a split view: left showing the Western Hyderabad regional elevation map, right showing the AQUILA Streamlit Command Dashboard with active layers.
* **Important Technical Talking Points:**
  - "Good morning, respected members of the evaluation committee. Today, I present AQUILA, an open-source, reproducible decision-support prototype engineered to address the growing crisis of urban flash flooding in rapidly urbanizing Indian suburban catchments."
  - "Using Manikonda in Hyderabad as our case study, AQUILA demonstrates how multi-criteria geospatial intelligence can bridge the gap between meteorological warnings and localized emergency response."
* **Suggested Speaking Duration:** 45 seconds

---

## Slide 2: Problem Statement and Motivation

* **Slide Title:** The Urban Flash Flood Crisis in Rapidly Expanding Cities
* **Key Content:**
  - **Suburban Urbanization Velocity:** Manikonda transformed from a semi-rural panchayat to a high-density urban township within 15 years.
  - **Impervious Surface Expansion:** Impervious surface cover reached 51.72% across the 55.63 km² analysis envelope, eliminating historical infiltration cascades.
  - **Hydrological Fragmentation:** Encroached and narrowed open nalas (channels) struggle with intense convective downpours (>50–70 mm/hr).
  - **The Response Bottleneck:** Lack of hyper-local spatial context leaves municipal response teams operating reactively without real-time terrain or proximity awareness.
* **Recommended Visual / Diagram:**
  - Comparison graphic: Historical 2000s chain of lakes (*cheruvus*) vs. modern satellite imagery showing dense built-up residential towers over historical drainage channels.
* **Important Technical Talking Points:**
  - "Hyderabad's Deccan plateau topography naturally relies on interconnected cascading lakes. When urban development severed these channels in Manikonda, roadways like Puppalguda Main Road became de facto flood corridors."
  - "During cloudburst events, floodwaters pond to depths of 0.45m to 0.70m within 20 minutes. Municipal operators receive flood reports via uncoordinated phone calls without elevation or drainage context."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 3: Existing System Limitations

* **Slide Title:** Gaps in Current Municipal Disaster Response
* **Key Content:**
  - **Coarse Meteorological Spatial Scale:** IMD weather forecasts operate at district/city scale ($0.25^\circ \approx 25\text{ km}$ grid), failing to resolve neighborhood flash-floods.
  - **Siloed Agency Operations:** GHMC emergency control rooms, HYDRAA asset protection, and traffic police operate on separate, non-integrated tracking channels.
  - **Static Hotspot Registers:** Municipal disaster management relies on paper registers of past waterlogging spots without dynamic rainfall-to-terrain risk calculation.
  - **Absence of Coordinated Dispatch Logic:** Emergency pumps and quick-response teams are assigned ad-hoc without automated geodetic proximity matching or duplicate assignment guards.
* **Recommended Visual / Diagram:**
  - Flow diagram contrasting the current fragmented response (Citizen Call $\to$ Control Room Log $\to$ Radio Broadcast $\to$ Manual Dispatch) against AQUILA's unified spatial decision loop.
* **Important Technical Talking Points:**
  - "Existing disaster control rooms rely heavily on static paper registers of past waterlogging spots. They lack automated spatial overlays linking rainfall rates to local slope and drainage distance."
  - "Furthermore, dispatchers have no automated system to prevent duplicate tasking—a single pump can inadvertently be assigned to two distant colonies simultaneously."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 4: Proposed AQUILA Solution

* **Slide Title:** AQUILA — Unified Geospatial Decision Support
* **Key Content:**
  - **Multi-Layer Geospatial Foundation:** Integrates Copernicus 30m DEM, OSM road network, open water bodies, drainage channels, and critical infrastructure in EPSG:4326.
  - **Transparent 5-Factor Risk Engine:** Computes a 0–100 geographic vulnerability index using empirical multi-criteria evaluation with dynamic missing-data renormalization.
  - **Incident Lifecycle Management:** Tracks reports through a formal finite state machine (`REPORTED` $\to$ `ASSIGNED` $\to$ `IN_PROGRESS` $\to$ `RESOLVED`).
  - **Proximity Emergency Dispatch:** Automated capability matching and Haversine distance ranking with strict mutual exclusion.
  - **Deterministic Scenario Simulation:** Controlled testing via design storm hyetographs without polluting historical operational records.
* **Recommended Visual / Diagram:**
  - High-level system architecture flowchart connecting the Data Tier, Service Tier (FastAPI), Presentation Tier (Streamlit), and Database (SQLite).
* **Important Technical Talking Points:**
  - "AQUILA is not an opaque AI black-box, nor is it an unverified claim of an operational public alert system. It is a decision-support prototype built to give emergency operators transparent, defensible, and reproducible situational awareness."
  - "Every algorithm in AQUILA—from slope evaluation to distance ranking—is mathematically verifiable and runs with sub-second execution speed."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 5: Pilot Study Area — Manikonda, Hyderabad

* **Slide Title:** Spatial Delineation: Administrative vs. Catchment vs. Analysis Envelope
* **Key Content:**
  - **Crucial Distinction Defined in Phase 2:**
    1. *Manikonda Municipal Boundary:* ~15.5 km² statutory administrative jurisdiction.
    2. *Manikonda-Neknampur Catchment:* ~22.4 km² natural hydrological watershed bounded by Khajaguda granite ridge (638m) down to Neknampur Lake (512m).
    3. *AQUILA Analysis Bounding Box:* **55.63 km²** rectangular modeling envelope (`[17.3605°N, 78.3455°E]` to `[17.4245°N, 78.4195°E]`).
  - **Dual CRS Architecture:**
    - Storage / Visualization: `EPSG:4326` (WGS 84).
    - Planar Computations: `EPSG:32644` (UTM Zone 44N) to eliminate degree-to-meter distortion.
* **Recommended Visual / Diagram:**
  - Nested polygon map showing the rectangular 55.63 km² bounding box enclosing the 22.4 km² natural catchment, which in turn encloses the 15.5 km² municipal polygon.
* **Important Technical Talking Points:**
  - "One of our most important geospatial findings is that administrative boundaries never match watershed boundaries. If we restricted our analysis to the 15.5 km² municipal polygon, we would ignore upstream runoff pouring down from the Khajaguda hills."
  - "Therefore, we established a 55.63 km² rectangular analysis envelope ensuring hydrological continuity, and we compute planar distances in UTM Zone 44N."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 6: Dataset Sources & Data Provenance

* **Slide Title:** Multi-Source Data Inventory & Provenance Governance
* **Key Content:**
  - **Rigorous 5-Tier Provenance Taxonomy:**
    1. `OBSERVED`: Ground measurements (Official IMD AWS stations).
    2. `HISTORICAL`: Archival municipal records (October 2020 flood points).
    3. `DERIVED_ANALYTICAL`: Geoprocessed rasters (Slope grid derived from DEM).
    4. `MANUALLY_SEEDED`: Baseline municipal infrastructure centroids.
    5. `SIMULATED`: Synthetic demonstration resources and scenario storms.
  - **Inventory Summary:**
    - 6,659 OSM road segments (94.7% connectivity in largest component).
    - 21 mapped open waterways (9.71 km) & 24 water bodies (1.51 km²).
    - 65 critical facilities tagged `OSM_UNVERIFIED`.
    - 5 verified historical inundation ground truth points.
    - 4 perimeter AWS proxy stations (Gachibowli, Serilingampally, Begumpet, Rajendranagar).
* **Recommended Visual / Diagram:**
  - Data Provenance matrix table with color-coded badges mapping each dataset to its source and license (ODbL, Copernicus Open Access, CC-BY).
* **Important Technical Talking Points:**
  - "In safety-critical systems, mixing simulated data with real-world observations is dangerous. AQUILA enforces strict metadata tagging across all database models and GIS files."
  - "We openly document that critical facilities are sourced from OpenStreetMap and classified `OSM_UNVERIFIED`, and all emergency response fleet units are tagged `[DEMO SYNTHETIC]`."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 7: Geospatial Preprocessing & Architecture

* **Slide Title:** Automated Geospatial Ingestion & Cleansing Pipeline
* **Key Content:**
  - **Terrain Processing (`process_dem.py`):**
    - Sourced Copernicus GLO-30 DSM (Tile `N17E078`).
    - Clipped to 55.63 km² envelope (266 × 230 pixels, zero NaNs, elevation 492.7m to 638.7m).
    - Derived continuous slope degrees raster ($0.0^\circ$ to $36.85^\circ$).
  - **Road Network Topology (`process_roads.py`):**
    - Extracted and filtered OSM highway hierarchies.
    - Constructed directed NetworkX graph `G(V, E)` with node rounding to 6 decimal places.
    - Verified 94.7% connectivity in largest weakly connected component (exceeding 90% target).
  - **Hydrology & Water Bodies (`process_drainage.py`):**
    - Extracted natural waterways and water body polygons; topologically validated with Shapely.
* **Recommended Visual / Diagram:**
  - Preprocessing pipeline diagram showing raw tiles and GeoJSON feeds flowing into Python cleaning scripts, outputting validated rasters and GeoJSONs in `data/processed/`.
* **Important Technical Talking Points:**
  - "Our preprocessing pipeline is completely reproducible. It automatically validates geometries, removes self-intersections using Shapely, and builds a directed graph to verify road connectivity."
  - "41 automated geospatial tests run against these processed layers to confirm coordinate bounds and topological validity."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 8: Multi-Factor Risk Assessment Methodology

* **Slide Title:** The Five-Factor Rule-Based Geographic Risk Engine
* **Key Content:**
  - **Mathematical Formulation:**
    $$R = \frac{\sum_{i=1}^n w_i \cdot S_i}{\sum_{i=1}^n w_i} \times 100 \in [0, 100]$$
  - **Factor Weights & Sub-Model Logic:**
    - **Rainfall Intensity ($w_P = 0.40$):** Piecewise linear function based on IMD thresholds ($15.6\text{ mm/hr}$ moderate, $64.5\text{ mm/hr}$ heavy, $100\text{ mm/hr}$ cloudburst).
    - **Terrain Vulnerability ($w_T = 0.20$):** $60\%$ elevation basin penalty ($<515\text{m}$) $+ 40\%$ flat slope penalty ($<1.5^\circ$).
    - **Drainage Proximity ($w_D = 0.20$):** Inverse distance decay to mapped nalas ($<50\text{m} \implies 95$).
    - **Land Cover Imperviousness ($w_L = 0.10$):** ESA WorldCover built-up score ($90$).
    - **Historical Recurrence ($w_H = 0.10$):** Proximity to verified October 2020 flood points ($<150\text{m} \implies 100$).
  - **Dynamic Weight Renormalization:** If a layer is missing, remaining weights are rescaled so $\sum w_i = 1.0$.
* **Recommended Visual / Diagram:**
  - Risk formula breakdown graphic with weighted slider icons and risk tier thresholds: Low (<40), Moderate (40–69.9), High ($\ge 70$).
* **Important Technical Talking Points:**
  - "Unlike opaque neural networks, our risk engine is fully explainable to municipal engineers. Every point on the map has a clear breakdown showing exactly which factor drove the risk."
  - "If an elevation raster is missing or corrupted, the system dynamically renormalizes the remaining four weights, preventing the score from artificially collapsing to zero."
* **Suggested Speaking Duration:** 75 seconds

---

## Slide 9: Incident Management Workflow

* **Slide Title:** Incident Lifecycle Coordination & State Machine
* **Key Content:**
  - **Lifecycle Finite State Machine:**
    $$\text{REPORTED} \longrightarrow \text{ASSIGNED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{RESOLVED}$$
  - **Incident Schema & Input Validation:**
    - Bounding box coordinate clamping ($17.20^\circ - 17.60^\circ\text{N}$, $78.20^\circ - 78.60^\circ\text{E}$).
    - Standardized incident types: `WATERLOGGING`, `CELLAR_FLOODING`, `ROAD_SEVERANCE`, `DRAIN_OVERFLOW`, `STRUCTURAL_HAZARD`.
    - Severity ratings: `LOW`, `MODERATE`, `HIGH`, `CRITICAL`.
  - **Automated Side Effects:**
    - Resolving an incident automatically releases linked resources back to `AVAILABLE`.
    - Every state change triggers an append-only audit trail entry.
* **Recommended Visual / Diagram:**
  - State machine transition diagram showing allowed transitions, rejecting invalid status skips with HTTP 400 Bad Request.
* **Important Technical Talking Points:**
  - "Incident management is implemented as a strict state machine in FastAPI. Operators cannot transition an incident directly from REPORTED to RESOLVED without passing through proper operational states."
  - "When an operator marks an incident RESOLVED, the backend automatically transitions all attached emergency resources back to AVAILABLE."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 10: Resource Recommendation & Assignment

* **Slide Title:** Capability-Matched Emergency Dispatch Engine
* **Key Content:**
  - **Two-Stage Dispatch Algorithm:**
    1. *Capability Filtering:* Matches incident type to required equipment (e.g., `WATERLOGGING` $\to$ `PUMPING`, `DRAIN_OVERFLOW` $\to$ `DEBRIS_CLEARING`).
    2. *Geodetic Proximity Ranking:* Computes Great-Circle Haversine distance between resource depot and incident coordinates.
  - **Strict Mutual Exclusion (Duplicate Assignment Prevention):**
    - Enforced in `resource_service.py`: If a resource is already `ASSIGNED`, any secondary assignment attempt throws a validation conflict.
  - **Transparent Metric Disclosure:**
    - Displayed clearly on the dashboard as straight-line distance, avoiding confusion with road network travel distance.
* **Recommended Visual / Diagram:**
  - Recommendation card UI screenshot showing top-ranked dewatering pump (`RES-PUMP-01`) at 0.74 km distance with capability match badge.
* **Important Technical Talking Points:**
  - "The dispatch engine filters only available units matching the required operational capability. It then ranks them using spherical geodesy."
  - "We built strict duplicate assignment prevention into the service layer—a resource currently deployed at Alkapur Township cannot be double-booked to Puppalaguda."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 11: Synthetic Rainfall Scenario Simulation

* **Slide Title:** Deterministic Scenario Simulation: `MANI-HEAVY-001`
* **Key Content:**
  - **Scenario Profile:** Calibrated 120mm / 3-hour synthetic Chicago hyetograph representing a high-intensity monsoon convective storm.
  - **Four Operational MVP Timesteps:**
    - *Step 1 (T=15m):* 12.5 mm/hr — Baseline rain, Moderate risk.
    - *Step 2 (T=30m):* 35.0 mm/hr — Heavy rain, High risk.
    - *Step 3 (T=45m):* 70.0 mm/hr — Peak cloudburst, Critical risk, automated injection of incident `INC-SIM-001` (Alkapur road inundation).
    - *Step 4 (T=60m):* 18.0 mm/hr — Receding rain, recovery phase.
  - **Strict Simulation Isolation & Safe Reset:**
    - Purges only records tagged `SIMULATED`. Real-world historical records remain untouched.
* **Recommended Visual / Diagram:**
  - Hyetograph curve showing rainfall rate peaking at 70 mm/hr alongside the corresponding risk gauge escalation and incident injection trigger point.
* **Important Technical Talking Points:**
  - "To allow repeatable training and demonstration without corrupting operational logs, AQUILA features a deterministic scenario engine."
  - "Advancing to Step 3 simulates a 70 mm/hr downpour, dynamically pushing risk over 70 and automatically injecting a realistic simulated incident."
  - "Clicking Reset cleanly purges simulated data while preserving all manual reports."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 12: System Architecture & Technology Stack

* **Slide Title:** Multi-Tier Architecture & Production Standards
* **Key Content:**
  - **Modern Python 3.13 Runtime:** High-performance async backend and clean dependency closure.
  - **REST API Tier (FastAPI & Pydantic V2):** Fully documented OpenAPI Swagger endpoints with strict coordinate boundary validation.
  - **Storage Tier (SQLAlchemy & SQLite):** Relational schema with normalized UTC timestamps (`utc_now()`), eliminating Python 3.13 deprecation warnings.
  - **Presentation Tier (Streamlit & Folium):** Responsive command-center dashboard with multi-layer geospatial toggles and Plotly risk gauges.
  - **Audit Logging:** Append-only relational audit history tracking all user and system actions.
* **Recommended Visual / Diagram:**
  - Component architecture diagram illustrating the interaction between the Streamlit UI, FastAPI REST endpoints, SQLAlchemy ORM, and the SQLite database.
* **Important Technical Talking Points:**
  - "AQUILA is built on Python 3.13 using FastAPI for the service tier and Streamlit with Folium for interactive GIS mapping."
  - "We eliminated all 56 Python 3.13 deprecation warnings by modernizing our Pydantic schemas to V2 and standardizing all database timestamps to timezone-naive UTC."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 13: Testing, Validation & Results

* **Slide Title:** Automated Quality Assurance & Verification
* **Key Content:**
  - **100% Pass Rate Across 57 Automated Pytest Tests:**
    - **41 Geospatial Data Tests:** Validates EPSG:4326 CRS, geometry topology, bounding box confinement, DEM elevation limits (450–700m), slope limits (0–90°), road connectivity (94.7%), and simulation isolation.
    - **16 Backend Integration Tests:** Validates API health, database seeding, risk engine calculations, missing-data weight renormalization, incident lifecycle transitions, duplicate dispatch rejection, and scenario determinism.
  - **Execution Performance:**
    - Full test suite executes in **2.39 seconds**.
    - Risk engine calculation latency: **$< 4\text{ ms}$**.
    - Database transaction latency: **$< 12\text{ ms}$**.
* **Recommended Visual / Diagram:**
  - Terminal screenshot showing `pytest -v` output: 57 passed in 2.39s, alongside a pie chart of test categories.
* **Important Technical Talking Points:**
  - "Academic rigor requires empirical verification. We implemented 57 automated tests covering both GIS dataset integrity and backend application workflows."
  - "The entire test suite executes in under 2.5 seconds, proving the computational efficiency and stability of our architecture."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 14: Limitations & Ethical Considerations

* **Slide Title:** Technical Boundaries & Ethical Disclosures
* **Key Content:**
  - **Multi-Factor Index vs. Hydrodynamic 2D Modeling:** Computes relative vulnerability (0–100), not hydrodynamic water depth ($h(x,y,t)$) or Saint-Venant fluid momentum.
  - **Underground Drainage Gap:** OpenStreetMap captures surface nalas; municipal underground pipe diameters and siltation levels are not publicly available in GIS format.
  - **DEM Resolution (30m):** Copernicus DSM averages micro-topography; road curbs (15cm) and building plinths cannot be resolved without sub-meter LiDAR.
  - **Straight-Line Distance:** Haversine metric ranks proximity as the crow flies; does not account for flooded road closures.
  - **Institutional Boundary:** Academic decision-support prototype; does not claim statutory authority or replace GHMC, HYDRAA, or IMD.
* **Recommended Visual / Diagram:**
  - Table of engineering trade-offs comparing MVP design decisions against production requirements.
* **Important Technical Talking Points:**
  - "Good engineering demands intellectual honesty. AQUILA does not claim to run 2D Navier-Stokes hydrodynamic equations, nor does it possess unverified municipal underground pipe data."
  - "We clearly label all synthetic resources and communicate that our risk index indicates relative geographic vulnerability, not certified flood depths."
* **Suggested Speaking Duration:** 60 seconds

---

## Slide 15: Conclusion & Future Roadmap

* **Slide Title:** Conclusions, Key Contributions & Future Roadmap
* **Key Content:**
  - **Project Achievements:**
    - Successfully demonstrated end-to-end urban flood intelligence for Manikonda across a 55.63 km² envelope.
    - Built a robust, fully tested Python 3.13 platform integrating geospatial rasters, vectors, and relational dispatch logic.
    - Established a transparent, reproducible benchmark for academic decision-support prototypes.
  - **Future Roadmap:**
    - *Phase 4:* Integration of open-source 2D overland hydrodynamic solvers (EPA-SWMM / HEC-RAS).
    - *Phase 5:* IoT ultrasonic water-level sensor telemetry at critical nala bridges and dynamic flood-impeded A* road routing.
* **Recommended Visual / Diagram:**
  - Visual roadmap timeline showing Phase 1 (Research) $\to$ Phase 2 (Geospatial) $\to$ Phase 3 (Emergency MVP) $\to$ Future Phases (Hydrodynamic & IoT).
* **Important Technical Talking Points:**
  - "In conclusion, AQUILA fulfills all objectives established in our project charter within the allotted time and scope."
  - "It provides a solid, verifiable foundation that future researchers can extend with high-resolution LiDAR and real-time IoT river gauges."
  - "Thank you. I am now ready to take your questions."
* **Suggested Speaking Duration:** 60 seconds

