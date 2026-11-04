# AQUILA — Operator Demonstration Walkthrough Guide
**Demonstration Script: 3-Minute End-to-End Evaluation**

This guide provides a step-by-step operational script to verify all 13 acceptance criteria specified in Section 16 of the AQUILA MVP project specification.

---

## Pre-Demonstration Setup (15 Seconds)

Ensure the backend and dashboard are running locally:

```powershell
# Terminal 1: Launch FastAPI Backend (Optional, background service)
uvicorn app.api.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Launch Streamlit Dashboard
streamlit run app/dashboard/main.py --server.port 8501
```

Open a web browser at: **`http://localhost:8501`**

---

## 13-Step Demonstration Walkthrough

### Step 1: Launch the Application & Verify Command Overview
- **Action:** Open `http://localhost:8501`. Ensure the navigation sidebar is set to **"Command Overview"**.
- **What to Observe:**
  - Active Incidents and Available Resources counters.
  - Current Rainfall rate (defaults to historical baseline).
  - Geographic Risk Gauge showing the composite score and rating (`LOW` or `MODERATE`).
  - Factor Breakdown Bar Chart displaying normalized scores for Rainfall ($P$), Terrain ($T$), Drainage ($D$), Land Cover ($L$), and Historical ($H$).

---

### Step 2: Explore the Interactive Geospatial Map
- **Action:** In the sidebar navigation, select **"Interactive Map"**.
- **What to Observe:**
  - Manikonda pilot area rendered with dark blue water bodies (Neknampur Lake, Puppalaguda Cheruvu).
  - Cyan lines showing drainage waterways and nalas.
  - Red/orange/blue dots showing critical facilities (Continental Hospital, schools, fire stations) tagged as `OSM_UNVERIFIED`.
  - Dark red hazard markers highlighting verified October 2020 flood evidence locations.
  - Colored weather station pins distinguishing `OBSERVED` AWS from `MANUALLY_SEEDED` proposed gauges.
  - Use the checkbox controls above the map to toggle layers on and off.

---

### Step 3: Verify Rainfall Telemetry & Provenance Standards
- **Action:** Note the rainfall metric on the Overview page or review rainfall records in the database.
- **What to Observe:**
  - Real-world records display provenance `HISTORICAL` or `OBSERVED`.
  - The UI clearly labels that no physical AWS station exists within Manikonda municipal boundaries, with telemetry originating from perimeter stations (Gachibowli, Begumpet).

---

### Step 4: Start the Heavy Rainfall — Manikonda Scenario
- **Action:** In the sidebar navigation, select **"Scenario Simulator"**.
- **Action:** Click the button **"▶️ Start / Restart Scenario"**.
- **What to Observe:**
  - Scenario `MANI-HEAVY-001` initializes at $T = 0$ minutes.
  - Rainfall rate displays initial light onset ($5.0$ mm/hr).
  - Risk Index displays a low value (~$15$ to $25$).
  - Hyetograph bar chart highlights Step 1 in red.

---

### Step 5: Advance the Scenario to Peak Intensity & Observe Risk Escalation
- **Action:** Click **"⏩ Advance 15-Minute Step"** repeatedly to step through $T=15$ min, $T=30$ min, and reach **$T = 45$ min (Step 4)**.
- **What to Observe:**
  - Rainfall intensity spikes to **$70.0$ mm/hr** (Extremely Heavy cloudburst).
  - Cumulative storm depth reaches $28.8$ mm.
  - The Dynamic Risk Score surges above **$75.0$ / 100**, shifting the category indicator to **`HIGH` (Red)**.
  - An injected incident appears in the table below:
    - **Code:** `INC-SIM-001`
    - **Title:** *Alkapur Township Sector 1 Roadway Inundation*
    - **Severity:** `HIGH` | **Type:** `WATERLOGGING` | **Tag:** `SIMULATED`

---

### Step 6: Create an Additional Manual Operator Incident
- **Action:** In the sidebar navigation, switch to **"Incident Management"** and select the **"Create New Incident"** tab.
- **Action:** Enter:
  - **Title:** *Puppalaguda Culvert Roadway Flooding*
  - **Type:** `WATERLOGGING`
  - **Severity:** `CRITICAL`
  - **Coordinates:** Lat `17.4015`, Lon `78.3750`
  - **Provenance Tag:** Select `REPORTED`
- **Action:** Click **"Register Incident"**.
- **What to Observe:** A new incident code (e.g. `INC-2026-0002`) is generated with status `REPORTED`.

---

### Step 7: Request Emergency Resource Recommendation
- **Action:** Switch to the **"Active Incidents Queue"** tab.
- **Action:** Select `INC-SIM-001` or your newly created incident from the dropdown.
- **Action:** Under *Emergency Resource Recommendation*, click **"🎯 Find Nearest Compatible Resource"**.
- **What to Observe:**
  - The recommendation engine filters for compatible capabilities (`PUMPING`).
  - Displays:
    - **Recommended Resource:** `RES-PUMP-01` (*GHMC High-Capacity Dewatering Squad A*)
    - **Capability:** `PUMPING`
    - **Haversine Distance:** **~0.94 km** (Straight-line distance)
    - **Status:** `RECOMMENDED`

---

### Step 8: Approve & Deploy the Resource
- **Action:** Click **"✅ Approve & Deploy Resource"**.
- **What to Observe:**
  - Assignment transitions from `RECOMMENDED` to `ASSIGNED`.
  - Resource `RES-PUMP-01` status switches from `AVAILABLE` to `ASSIGNED`.
  - Incident status updates to `ASSIGNED`.

---

### Step 9: Update Incident Lifecycle Status & Resolve Incident
- **Action:** In the *Operator Actions* box, change status from `ASSIGNED` to **`IN_PROGRESS`** and click **"Apply Status Change"**.
- **Action:** Once operational response concludes, select **`RESOLVED`** and click **"Apply Status Change"**.
- **What to Observe:**
  - Incident status becomes `RESOLVED`.
  - The assigned dewatering pump (`RES-PUMP-01`) is automatically released back to `AVAILABLE` in the fleet registry.

---

### Step 10: Inspect the System Audit Trail
- **Action:** In the sidebar navigation, select **"Audit Trail"**.
- **What to Observe:**
  - An immutable chronologically sorted log displaying:
    - Scenario initiation and step advancements.
    - Incident registration (`CREATED`).
    - Recommendation generated (`RECOMMENDED`).
    - Operator dispatch approval (`ASSIGNED`).
    - Status transitions to `RESOLVED`.
    - Every row features an exact UTC timestamp.

---

### Step 11: Reset the Scenario (Clean Simulation Isolation)
- **Action:** In the sidebar navigation, return to **"Scenario Simulator"**.
- **Action:** Click **"🔄 Reset Scenario (Purge SIMULATED Data)"**.
- **What to Observe:**
  - Warning alert confirms safe purge of simulated records.
  - Incident `INC-SIM-001` is removed from the active queue.
  - User-reported incident `INC-2026-0002` and historical baseline data remain completely preserved.
  - System returns to idle state ready for subsequent demonstrations.

