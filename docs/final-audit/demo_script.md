# AQUILA — Demonstration Script & Operational Walkthrough

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Area:** Manikonda Pilot Area, Hyderabad, Telangana, India  
**Target Audience:** Academic Evaluation Panel, Project Examiners, and Technical Reviewers  
**Target Duration:** 3 to 5 Minutes  
**Author:** QA Engineering & Systems Integration Team  
**Date:** November 2026  

---

## 1. Demonstration Overview & Preparation

This script provides an exact, step-by-step operational narrative designed for a live 3–5 minute evaluation of the AQUILA platform. It highlights the full decision-support loop: geospatial data visualization, rainfall-driven geographic risk computation, deterministic incident injection via scenario simulation, proximity-based emergency resource recommendation, operator dispatch, and tamper-evident audit logging.

### 1.1 Pre-Flight Setup Checklist

Before initiating the presentation, execute the pre-flight check in a terminal session:

```powershell
# 1. Navigate to project root
cd C:\AI\Rural_internship_project

# 2. Run automated test suite to ensure clean state (57/57 tests passing)
pytest -q

# 3. Seed / Reset database to pristine baseline
python app/db/seed.py

# 4. Terminal 1: Launch FastAPI Backend Server
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload

# 5. Terminal 2: Launch Streamlit Command Centre
streamlit run app/dashboard/main.py --server.port 8501
```

Open a browser window at `http://localhost:8501`. Ensure the browser is maximized at 100% zoom.

---

## 2. Step-by-Step Demonstration Script

```
+----------------------------------------------------------------------------------------------------+
|                                    DEMO TIMELINE (3-5 MINUTES)                                     |
|                                                                                                    |
|  [0:00 - 0:45] Step 1: System Overview & Geospatial Multi-Layer Dashboard                          |
|  [0:45 - 1:30] Step 2: Five-Factor Rule-Based Risk Engine & Transparent Scoring                   |
|  [1:30 - 2:30] Step 3: Scenario Simulation (MANI-HEAVY-001) & Automated Incident Injection         |
|  [2:30 - 3:30] Step 4: Proximity Emergency Dispatch & Resource Allocation                         |
|  [3:30 - 4:15] Step 5: Incident Resolution & Operational Audit Log Verification                   |
|  [4:15 - 4:45] Step 6: Safe Scenario Reset & Simulation Isolation Q&A Handover                    |
+----------------------------------------------------------------------------------------------------+
```

---

### Step 1: System Overview & Geospatial Intelligence Dashboard (0:00 – 0:45)

* **Location on Screen:** Main Dashboard view (`http://localhost:8501`), top banner and central interactive Folium map.
* **Action to Perform:**
  1. Point out the top header: *"AQUILA — Urban Flood Intelligence & Emergency Response Platform (Manikonda Pilot)"*.
  2. In the left sidebar under **"Map Layer Controls"**, toggle on/off:
     - **"Arterial Roads"** (cyan lines).
     - **"Water Bodies & Lakes"** (deep blue polygons, highlighting Neknampur Chinna Cheruvu and Puppalguda lakes).
     - **"Drainage & Nalas"** (dodger blue channels representing the natural Musi watershed outflow).
     - **"Historical Inundation Hotspots"** (red markers indicating verified waterlogging locations from Phase 2).
* **What to Observe:**
  - The map smoothly re-renders the study area bounding box `[17.380°N, 78.360°E]` to `[17.420°N, 78.410°E]`.
  - GeoJSON geometries load instantly from disk through GeoPandas with zero coordinate distortion (EPSG:4326).
* **Technical Talking Point:**
  > *"AQUILA integrates official open geospatial datasets covering Manikonda's 20.8 km² pilot area. Unlike static map viewers, AQUILA combines road infrastructure networks, natural nalas, open water bodies, and Copernicus 30m DEM terrain into a unified coordinate frame for real-time risk overlay."*

---

### Step 2: Five-Factor Rule-Based Risk Engine (0:45 – 1:30)

* **Location on Screen:** Left sidebar accordion **"Risk Engine Simulator"** or Risk Calculation section.
* **Action to Perform:**
  1. Expand the **"Manual Risk Assessment"** control panel.
  2. Set coordinates to Manikonda Central: Latitude `17.3980`, Longitude `78.3850`.
  3. Enter rainfall rate: `65 mm/hr` (Heavy convective monsoon downpour).
  4. Click **"Compute Geographic Risk"**.
* **What to Observe:**
  - The UI immediately renders a risk gauge: **Risk Score: ~74 / 100 — CRITICAL / HIGH**.
  - Component breakdown appears as a breakdown bar:
    - *Precipitation Hazard (40% weight)*: High intensity penalty.
    - *Terrain Slope Factor (20% weight)*: Flat depression / low slope.
    - *Drainage Proximity (20% weight)*: Proximity to obstructed natural nala.
    - *Land Use Imperviousness (10% weight)*: High urban built-up density.
    - *Historical Inundation Recurrence (10% weight)*: Near known recurrence node.
* **Technical Talking Point:**
  > *"Rather than using an opaque black-box model, AQUILA's risk engine uses a transparent, defensible 5-factor weighted formulation normalized between 0 and 100. If any geospatial layer is unavailable, the engine dynamically renormalizes the remaining factor weights to sum to 1.0, ensuring mathematical stability without zero-biasing."*

---

### Step 3: Scenario Simulation & Automated Incident Injection (1:30 – 2:30)

* **Location on Screen:** Top-right or sidebar **"Scenario Simulator"** panel.
* **Action to Perform:**
  1. Select the pre-configured scenario: **"MANI-HEAVY-001: Heavy Monsoon Storm (Peak 70mm/hr)"**.
  2. Click **"Start Scenario"**.
  3. Advance the simulation step slider to **Step 3 (Peak Downpour - 70 mm/hr)**.
  4. Click **"Execute Step"**.
* **What to Observe:**
  - The simulated rainfall jumps from baseline `5.0 mm/hr` to `70.0 mm/hr`.
  - The risk level across low-lying Manikonda corridors automatically escalates to **CRITICAL**.
  - A new simulated incident appears on the map with a glowing pulsing marker:
    - **ID:** `INC-SIM-001`
    - **Type:** `FLASH_FLOOD`
    - **Location:** `Secretariat Road Low Point (17.3995°N, 78.3842°E)`
    - **Severity:** `CRITICAL`
    - **Status:** `REPORTED`
* **Technical Talking Point:**
  > *"Scenario `MANI-HEAVY-001` proves the platform's deterministic behavior under synthetic stress conditions. As rainfall crosses the 60 mm/hr flash-flood threshold, the system automatically injects realistic incident reports derived from historical vulnerability nodes without polluting real field records."*

---

### Step 4: Proximity Emergency Dispatch & Resource Allocation (2:30 – 3:30)

* **Location on Screen:** Central **"Incident Management & Dispatch"** panel.
* **Action to Perform:**
  1. Select incident `INC-SIM-001` from the active incidents table.
  2. Click **"Find Recommended Emergency Resources"**.
  3. Inspect the recommended resource cards.
  4. Select the top-ranked resource: **`RES-PUMP-01` ([DEMO SYNTHETIC] Manikonda Ward Mobile Dewatering Pump)**.
  5. Click **"Dispatch / Assign Resource"**.
* **What to Observe:**
  - The algorithm calculates the Haversine distance from the resource depot to the incident site (e.g., `0.74 km`).
  - Resource status changes from `AVAILABLE` to `ASSIGNED`.
  - Incident status transitions from `REPORTED` to `ASSIGNED`.
  - The map immediately updates to draw the incident-resource linkage.
* **Technical Talking Point:**
  > *"AQUILA's dispatch service filters available response units by capability matching (e.g., dewatering pumps for flash floods, rescue boats for inundated lakes) and ranks them using spherical geodesy. The system strictly prevents duplicate assignments—if a resource is currently deployed, it cannot be double-booked."*

---

### Step 5: Incident Resolution & Operational Audit Log Verification (3:30 – 4:15)

* **Location on Screen:** Incident Status controls and **"Operational Audit Trail"** table at the bottom of the dashboard.
* **Action to Perform:**
  1. Update incident `INC-SIM-001` status to **`IN_PROGRESS`** with operator notes: *"Pump deployed; draining water into stormwater canal"*.
  2. Click **"Update Status"**.
  3. Update status to **`RESOLVED`** with operator notes: *"Road cleared. Water receded by 40cm"*.
  4. Scroll down to the **"Operational Audit Trail"** section.
* **What to Observe:**
  - The incident list updates to show `INC-SIM-001` as resolved.
  - The audit log displays chronological, immutable records with UTC timestamps:
    1. `CREATE` — Incident `INC-SIM-001` created via scenario simulator (`SYSTEM`).
    2. `DISPATCH` — Assigned `RES-PUMP-01` to `INC-SIM-001` (`OPERATOR`).
    3. `STATUS_UPDATE` — `REPORTED` $\to$ `ASSIGNED` $\to$ `IN_PROGRESS` $\to$ `RESOLVED`.
* **Technical Talking Point:**
  > *"AQUILA maintains an append-only operational audit trail for municipal accountability. Every state change, timestamp, and actor identity is permanently recorded in the database, allowing post-disaster audits by municipal commissioners or emergency taskforces."*

---

### Step 6: Safe Scenario Reset & Simulation Isolation (4:15 – 4:45)

* **Location on Screen:** Scenario Control section.
* **Action to Perform:**
  1. Click **"Reset Scenario / Purge Simulation Data"**.
  2. Confirm the reset dialog.
* **What to Observe:**
  - Rainfall observation reverts to baseline `0.0 mm/hr`.
  - Synthetic incident `INC-SIM-001` and its temporary scenario state are purged.
  - Resource `RES-PUMP-01` is released back to `AVAILABLE`.
  - **Crucially:** Real-world historical flood points and verified infrastructure records remain completely untouched.
* **Technical Talking Point:**
  > *"To maintain strict scientific integrity, AQUILA enforces complete simulation isolation. Simulated entities carry the `SIMULATED` provenance flag, and scenario reset operations clean synthetic records without corrupting baseline operational records."*

---

## 3. Evaluator Q&A Cheat Sheet

| Expected Evaluator Question | Recommended Technical Response |
| :--- | :--- |
| **"Is this model doing 2D hydrodynamic flood routing?"** | *"No. For this Phase 3 MVP, AQUILA implements an operational 5-factor multi-criteria risk engine designed for sub-second decision support. Full 2D Saint-Venant hydraulic modeling is computationally prohibitive for interactive web dashboards and is planned for Phase 4 batch computing."* |
| **"Where did you get the drainage and road data?"** | *"The vector layers were extracted from OpenStreetMap, verified against Telangana Spatial Data Infrastructure (TSDI) benchmarks, topologically cleaned using Shapely/GeoPandas, and verified with 41 automated geospatial tests."* |
| **"Can an operator dispatch a resource that is already busy?"** | *"No. The service tier enforces mutual exclusion. In `resource_service.py`, attempting to assign a non-AVAILABLE resource throws a 400 Bad Request error, as verified by test `test_duplicate_resource_assignment_prevention`."* |
| **"Is the audit log cryptographically tamper-proof like a blockchain?"** | *"It is an append-only relational audit table with UTC timestamps and actor tags designed for administrative transparency. In production, this can be streamed to a write-once cloud storage bucket."* |
| **"How does the system handle missing sensor or GIS layers?"** | *"The risk engine dynamically renormalizes the weights of available layers. If drainage data is missing, the remaining four factors are scaled by `1.0 / (1.0 - 0.20) = 1.25`, ensuring risk remains correctly calibrated between 0 and 100."* |

---

## 4. Emergency Fallback & Recovery Procedures

If during the live demonstration:
1. **Streamlit UI appears disconnected:**
   - Press `R` in the browser or click the top-right **"Always Rerun"** button.
   - Verify Terminal 1 (FastAPI on port 8000) has not terminated.
2. **Database state is cluttered from previous test runs:**
   - Execute in a spare terminal: `python app/db/seed.py`
   - Refresh the browser. The database will re-initialize to pristine baseline within 500ms.

