# AQUILA Phase 6: Clean Deployment & Demonstration Runbook

## 1. Overview

This guide provides end-to-end instructions for deploying and running **AQUILA** on:
1. **Native Windows Environment (Primary Academic Demonstration Target)**
2. **Containerized Docker Environment (Optional Portable Setup)**

AQUILA requires zero external database servers (uses self-contained SQLite) and zero cloud subscriptions. Everything executes locally.

---

## 2. Option A: Native Windows Setup (Recommended)

### Prerequisites:
- Windows 11 or Windows 10 (64-bit)
- Python 3.13 (or 3.11+) installed with "Add Python to PATH" enabled
- Git or unpacked project directory

### Step 1: Open PowerShell in Project Root
```powershell
cd C:\AI\Rural_internship_project
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create isolated environment
python -m venv venv

# Set execution policy if script activation is restricted
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Pinned Dependencies
```powershell
# Upgrade base packaging tools
python -m pip install --upgrade pip setuptools wheel

# Install locked dependencies
pip install -r requirements-lock.txt
```

### Step 4: Configure Environment Settings
```powershell
Copy-Item .env.example .env
```

### Step 5: Run Automated Pre-Flight Release Verification
```powershell
python scripts/verify_release.py
```
This script will test the database, dataset files, road graph, routing, health diagnostics, and run the complete automated test suite. It should output:
`🎉 AQUILA RELEASE VERIFICATION SUCCESSFUL — CERTIFICATION GRANTED`

### Step 6: Start the FastAPI Application Server
In your first terminal window:
```powershell
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
- Health Diagnostic Probe: `http://127.0.0.1:8000/health`

### Step 7: Launch the Streamlit Command Centre Dashboard
In a second terminal window (with virtual environment activated):
```powershell
streamlit run app/dashboard/main.py
```
- Dashboard URL: `http://localhost:8501`

---

## 3. Option B: Docker Container Deployment (Optional)

If demonstrating on a machine without Python installed, Docker can be used:

```bash
# Build and launch both API and Dashboard containers
docker-compose up --build -d

# Check running containers
docker ps

# Inspect logs
docker logs -f aquila-api-server

# Access services:
# - API: http://localhost:8000/docs
# - Dashboard: http://localhost:8501

# Shutdown
docker-compose down
```

---

## 4. Academic Demonstration Walkthrough & Runbook

For a live demonstration to academic evaluators, execute the following 5-act demonstration sequence:

### Act 1: Operational Baseline & Data Provenance (2 mins)
1. Open `http://localhost:8501` to **Command Overview**.
2. Point out the live telemetry metrics: Active Incidents, Available Resources (6 synthetic units), Current Rainfall, and Centroid Geographic Risk Index.
3. Highlight the provenance badges: `[DEMO SYNTHETIC]`, `OBSERVED`, `HISTORICAL`, `OSM_UNVERIFIED`.

### Act 2: Interactive Geospatial Layers (2 mins)
1. Navigate to **Interactive Map**.
2. Toggle layers: DEM Elevation Contour, Nala Drainage Network, and 65 Critical Facilities.
3. Show the five documented October 2020 flood evidence locations (orange markers) and click a marker to display observed water depth ($0.45 - 0.70\text{m}$) and source authority.

### Act 3: Incident Creation & Resource Recommendation (3 mins)
1. Navigate to **Incident Management**.
2. Register a new waterlogging incident:
   - Title: `Alkapur Sector 2 Drainage Surcharge`
   - Coordinates: $17.3912, 78.3845$
   - Type: `WATERLOGGING`, Severity: `HIGH`
3. Click **"Request Nearest Resource Recommendation"**.
4. Show that the system recommends `RES-PUMP-01` (GHMC High-Capacity Dewatering Unit) located $1.25\text{ km}$ away.
5. Click **"Confirm & Assign Resource"** and show the status transition to `ASSIGNED` in the audit log.

### Act 4: Flood-Aware Safe Emergency Navigation (3 mins)
1. Navigate to **Flood-Aware Routing**.
2. Set Origin ($17.3912, 78.3845$) and Destination Continental Hospital ($17.3980, 78.3920$).
3. Click **"Compute Route Alternative Analysis"**.
4. Contrast the **Shortest Route (Cyan)** vs **Lowest-Risk Route (Purple)**:
   - Point out the explainable trade-off card: e.g., $+15.2\%$ detour reduces flood risk exposure by $41.8\%$.
5. Inspect the **Accessible Critical Facilities** table below the map.

### Act 5: Scenario Intelligence, Uncertainty & Historical Consistency (4 mins)
1. Navigate to **Scenario Intelligence & Analytics**.
2. **Tab 1 (Multi-Scenario Comparison)**: Show the bar chart comparing Baseline Dry ($43.4$) vs Cloudburst Storm ($73.8$) and the equipment surge delta table.
3. **Tab 2 (Uncertainty & Sensitivity)**: Adjust the perturbation slider ($\pm 20\%$) and show the factor swing tornado chart proving rainfall is the dominant driver. Show the non-linear IMD rainfall curve.
4. **Tab 3 (Infrastructure Vulnerability & Historical Consistency)**: Show the ranked list of 65 facilities by index $V$. Highlight the **Historical Spatial Consistency Card** demonstrating $100\%$ spatial concordance with October 2020 flood evidence.
5. **Tab 4 (Response Priority Queue)**: Show active incidents ranked by priority score $P$, explain the sub-score breakdown bars, and highlight the **Human-in-the-Loop Operator Authorization Rule**.

---

## 5. Troubleshooting & Recovery Procedures

| Symptom | Probable Cause | Recovery Command / Action |
|---|---|---|
| `sqlite3.OperationalError: database is locked` | Concurrent write collision | The 5,000ms busy timeout resolves transient locks automatically. If stuck, close other Python terminals accessing `aquila_mvp.db`. |
| `FileNotFoundError: dem_manikonda_clipped.tif` | Missing raster layer | Ensure you are executing from the project root (`C:\AI\Rural_internship_project`). Check `data/processed/raster/`. |
| Port 8000 already in use | Previous Uvicorn instance running | Find and terminate PID: `Get-Process python \| Stop-Process` or use `--port 8001`. |
| Streamlit white screen | Browser WebSocket disconnected | Hard refresh browser with `Ctrl + F5`. |
| Simulated data polluting demo | Previous scenario run not reset | Open **Scenario Simulator** and click `🔄 Reset Scenario (Purge SIMULATED Data)`. |

