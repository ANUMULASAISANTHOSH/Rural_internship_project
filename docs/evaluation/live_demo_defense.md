# AQUILA — Live Demonstration Defense & Examiner Walkthrough Guide

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Pilot Area:** Manikonda, Hyderabad, Telangana, India  
**Target Duration:** 5 Minutes  
**Document Type:** Practical Viva Live Demonstration & Examiner Defense Protocol  
**Document Location:** `docs/evaluation/live_demo_defense.md`  

---

## 1. Pre-Flight Verification & Launch Commands

All commands below are strictly verified against the repository structure. Execute them in order before calling the evaluation committee to your terminal.

### Step 1: Health Check and Test Suite Execution
In Terminal 1 (PowerShell), run:
```powershell
# Navigate to project root
cd C:\AI\Rural_internship_project

# Run the automated test suite
pytest -v
```
*Expected Output:*
```
======================== 57 passed, 1 warning in 2.39s ========================
```
*Examiner Defense Note:* This immediately proves system stability and code quality to the examiners before launching the UI.

---

### Step 2: Database Baseline Initialization
```powershell
python app/db/seed.py
```
*Expected Output:*
```
[SEED] Database tables created.
[SEED] Baseline rainfall observations seeded (1 records).
[SEED] Seeded 6 synthetic emergency resources.
[SUCCESS] Database initialization and seeding complete.
```

---

### Step 3: Launch FastAPI Backend Server
In Terminal 1, start the API:
```powershell
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected Output:*
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```
*(Verify health at `http://127.0.0.1:8000/health` in browser)*.

---

### Step 4: Launch Streamlit Operational Dashboard
Open a new terminal window (Terminal 2) and execute:
```powershell
cd C:\AI\Rural_internship_project
streamlit run app/dashboard/main.py --server.port 8501
```
*Expected Output:*
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```
Open your browser to `http://localhost:8501`. Ensure the window is maximized at 100% zoom.

---

## 2. Five-Minute Live Demonstration Timeline

```
+-----------------------------------------------------------------------------------------------------+
|                                    LIVE DEMONSTRATION WORKFLOW                                      |
|                                                                                                     |
|  [0:00 - 0:45] Screen 1: Command Overview & Active Metrics                                          |
|  [0:45 - 1:45] Screen 2: Interactive Geospatial GIS Map & Multi-Layer Controls                      |
|  [1:45 - 2:45] Screen 3: Scenario Simulator (MANI-HEAVY-001) & Automated Incident Injection         |
|  [2:45 - 3:45] Screen 4: Incident Management & Proximity Emergency Dispatch                         |
|  [3:45 - 4:30] Screen 5: Lifecycle Resolution & Operational Audit Log Verification                  |
|  [4:30 - 5:00] Screen 6: Safe Scenario Reset & Simulation Isolation Q&A Handover                     |
+-----------------------------------------------------------------------------------------------------+
```

---

### Screen 1: Command Overview & High-Level Metrics (0:00 – 0:45)

* **Navigation:** Click **"Command Overview"** in the left sidebar radio selector.
* **Action to Perform:**
  1. Point out the top header: *"AQUILA — Urban Flood Intelligence & Emergency Response Platform"*.
  2. Direct the committee's attention to the summary KPI metric cards:
     - **Total Incidents:** `0` (or baseline count).
     - **Active Incidents:** `0`.
     - **Available Resources:** `6` (all 6 seeded units available).
     - **Current Rainfall Rate:** `0.0 mm/hr` (Baseline archive).
     - **Current Geographic Risk Score:** `~28.5 / 100` (`LOW` category).
* **What to Explain to Examiners:**
  > *"Respected committee, we begin at the Command Overview. AQUILA continuously integrates meteorological readings and baseline terrain models. At zero rainfall, the baseline geographic risk across Manikonda is categorized as LOW (28.5/100), reflecting normal dry-weather conditions. Our emergency fleet shows six response units fully available across municipal depots."*

---

### Screen 2: Interactive Geospatial GIS Map (0:45 – 1:45)

* **Navigation:** Click **"Interactive Map"** in the left sidebar radio selector.
* **Action to Perform:**
  1. Scroll down to view the central Folium Leaflet map centered at `[17.3925°N, 78.3825°E]`.
  2. In the sidebar or top layer controls, toggle the map layers on and off:
     - Check **"Arterial Roads"** (cyan road corridors).
     - Check **"Water Bodies & Lakes"** (deep blue polygons showing Neknampur and Puppalguda cheruvus).
     - Check **"Drainage & Nalas"** (dodger blue lines showing the 21 mapped open channels).
     - Check **"Critical Infrastructure"** (green marker pins for substations and clinics).
     - Check **"Historical Flood Hotspots"** (red markers indicating verified October 2020 points).
* **What to Explain to Examiners:**
  > *"This interactive map renders our validated geospatial datasets in EPSG:4326. We explicitly delineate the 55.63 km² pilot analysis envelope. Notice how the open drainage channels naturally flow southwards through Puppalguda into Neknampur Lake. Our road network layer contains 6,659 cleaned segments with 94.7% connectivity in its largest component. Every layer is tagged with standard provenance metadata."*

---

### Screen 3: Scenario Simulator — Advancing `MANI-HEAVY-001` (1:45 – 2:45)

* **Navigation:** Click **"Scenario Simulator"** in the left sidebar radio selector.
* **Action to Perform:**
  1. Show the scenario selector: **`MANI-HEAVY-001` (Heavy Rainfall — Manikonda)**.
  2. Point out that the scenario status is currently `INACTIVE`.
  3. Click the button **"Start Scenario"**.
  4. Note that Step 0 starts with light rain ($5.0\text{ mm/hr}$).
  5. Click **"Advance Step"** twice to reach **Step 3 (T = 45 min)**.
* **Expected Observation:**
  - Rainfall rate jumps to **$70.0\text{ mm/hr}$** (Peak convective cloudburst).
  - Cumulative depth increases to **$45.0\text{ mm}$**.
  - Dynamic Risk Score escalates to **$78.1 / 100$** (`HIGH` risk category).
  - Green banner notification: *"Injected Incidents: ['INC-SIM-001']"*.
* **What to Explain to Examiners:**
  > *"Because municipal evaluators cannot wait for live monsoon storms, AQUILA features a deterministic scenario engine. We advance to Step 3 of our calibrated Chicago hyetograph, simulating a 70 mm/hr cloudburst. The risk engine immediately responds: the risk score surges to 78.1 (HIGH), and the system automatically injects incident INC-SIM-001 at the low-lying Alkapur Township Sector 1 depression."*

---

### Screen 4: Incident Management & Emergency Proximity Dispatch (2:45 – 3:45)

* **Navigation:** Click **"Incident Management"** in the left sidebar radio selector.
* **Action to Perform:**
  1. In the **Active Incidents Table**, locate incident **`INC-SIM-001`**:
     - *Title:* Alkapur Township Sector 1 Roadway Inundation
     - *Severity:* `HIGH`
     - *Status:* `REPORTED`
     - *Type:* `WATERLOGGING`
  2. Select `INC-SIM-001` from the dropdown selector.
  3. Click **"Find Recommended Emergency Resources"**.
  4. Inspect the top recommendation card:
     - **Resource Code:** `RES-PUMP-01`
     - **Resource Name:** `[DEMO SYNTHETIC] Manikonda Ward Mobile Dewatering Pump`
     - **Capability:** `PUMPING, ROAD_CLEARING` (Compatible)
     - **Distance:** `~0.74 km` (Haversine Great-Circle straight-line distance)
  5. Click **"Dispatch / Assign Resource"**.
* **Expected Observation:**
  - Resource status changes to `ASSIGNED`.
  - Incident status automatically updates to `ASSIGNED`.
  - Success message: *"Successfully assigned RES-PUMP-01 to incident INC-SIM-001"*.
* **What to Explain to Examiners:**
  > *"Here we see our automated dispatch logic. The system filters available assets by capability matching—identifying high-capacity dewatering pumps rather than rescue boats. It ranks available units by Haversine distance, identifying the Manikonda Ward mobile pump just 740 meters away. Upon operator approval, the unit is locked, and the incident moves to ASSIGNED status. Our service layer strictly enforces mutual exclusion—this pump cannot be double-booked to another incident."*

---

### Screen 5: Lifecycle Resolution & Operational Audit Trail (3:45 – 4:30)

* **Navigation:** Still on **"Incident Management"**, then click **"Audit Trail"**.
* **Action to Perform:**
  1. Under the incident status dropdown for `INC-SIM-001`, update status to **`IN_PROGRESS`** $\to$ click **"Update Status"**.
  2. Next, update status to **`RESOLVED`** $\to$ click **"Update Status"**.
  3. Notice that `RES-PUMP-01` is automatically released back to `AVAILABLE`.
  4. Switch navigation to **"Audit Trail"**.
* **Expected Observation:**
  - The audit table displays chronological, timestamped records:
    - `SCENARIO` — `STEP_ADVANCED` (Rainfall=70 mm/hr, Injected: INC-SIM-001)
    - `ASSIGNMENT` — `RECOMMENDED` (RES-PUMP-01 at 0.74 km)
    - `ASSIGNMENT` — `ASSIGNED` (Operator approved deployment)
    - `INCIDENT` — `STATUS_UPDATED` (REPORTED $\to$ ASSIGNED $\to$ IN_PROGRESS $\to$ RESOLVED)
* **What to Explain to Examiners:**
  > *"AQUILA enforces a formal incident lifecycle state machine. Transitioning the incident to RESOLVED automatically releases the assigned pump back into the available pool. Furthermore, every state change, dispatch decision, and scenario event is permanently captured in this append-only operational audit log with UTC timestamps for post-disaster accountability."*

---

### Screen 6: Safe Scenario Reset & Simulation Isolation (4:30 – 5:00)

* **Navigation:** Return to **"Scenario Simulator"**.
* **Action to Perform:**
  1. Click **"Reset Scenario / Purge Simulation Data"**.
  2. Return to **"Command Overview"**.
* **Expected Observation:**
  - All simulated incidents (`INC-SIM-*`) and synthetic rainfall observations are cleanly purged.
  - Rainfall rate reverts to baseline `0.0 mm/hr`.
  - Real-world historical flood points and baseline infrastructure remain completely untouched.
* **What to Explain to Examiners:**
  > *"Finally, we demonstrate strict simulation isolation. Clicking reset purges only entities tagged as SIMULATED. Our baseline GIS records and historical field data remain untouched. This completes the full decision-support loop. Thank you, and I look forward to your questions."*

---

## 3. Emergency Troubleshooting & Fallback Procedures

If during the live demonstration an unexpected glitch occurs, use these tested recovery steps:

| Symptom / Failure | Root Cause | Immediate Recovery Action (Under 10 Seconds) |
| :--- | :--- | :--- |
| **Streamlit page shows "Connection Error" or blank** | Streamlit process disconnected or browser socket dropped | 1. Press `R` in browser to trigger a full Streamlit rerun.<br>2. If unresolved, check Terminal 2. If exited, restart: `streamlit run app/dashboard/main.py --server.port 8501`. |
| **FastAPI returns 500 or Connection Refused** | Uvicorn server stopped in Terminal 1 | In Terminal 1, restart: `uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload`. |
| **Database state is cluttered from prior tests** | Extra simulated incidents or dirty assignment states | In a spare terminal, run: `python app/db/seed.py`. Refresh browser. Re-initializes in $<500\text{ ms}$. |
| **Folium map does not display road layer** | Browser WebGL or Leaflet memory timeout | Deselect "Arterial Roads" checkbox and recheck it, or refresh the browser page (`Ctrl + F5`). |
| **Examiner asks: "Show me the tests right now"** | Examiner wants immediate verification of test claims | In any open terminal, run `pytest -q`. The 57 tests will pass on screen in 2.4 seconds. |

