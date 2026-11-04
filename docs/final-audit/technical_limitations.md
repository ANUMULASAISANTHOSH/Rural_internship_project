# AQUILA — Technical Limitations, System Boundaries & Engineering Disclosures

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Pilot Area:** Manikonda, Hyderabad, Telangana, India  
**Document Type:** Technical Architecture Disclosure & Academic Boundary Analysis  
**Date:** November 2026  
**Status:** Approved for Academic Evaluation  

---

## 1. Executive Disclosure

AQUILA is an **academic decision-support prototype** engineered to demonstrate the feasibility of integrating geospatial data layers, terrain models, rainfall observations, multi-criteria risk scoring, and emergency resource allocation for urban flood management.

> [!IMPORTANT]
> **AQUILA is not an operational flood forecasting or statutory emergency warning system.** It does not replace or override the executive authority, monitoring networks, or emergency protocols of:
> * **GHMC** (Greater Hyderabad Municipal Corporation)
> * **HYDRAA** (Hyderabad Disaster Response and Asset Monitoring and Protection Agency)
> * **IMD** (India Meteorological Department)
> * **TSDPS** (Telangana State Development Planning Society)
> * **NDRF / SDRF** (National & State Disaster Response Forces)

All prospective users, evaluators, and system developers must interpret platform outputs within the technical boundaries, assumptions, and constraints documented below.

---

## 2. Hydrodynamic Modeling vs. Multi-Factor Risk Indexing

### 2.1 Theoretical Contrast
| Aspect | Full Hydrodynamic 2D Simulation (e.g., SWMM, HEC-RAS, TUFLOW) | AQUILA Multi-Criteria Risk Engine (MVP) |
| :--- | :--- | :--- |
| **Physical Basis** | Numerical integration of 2D Shallow Water Equations (Saint-Venant equations: conservation of mass & momentum). | Empirical, weighted multi-criteria index ($R \in [0, 100]$) combining precipitation, slope, drainage proximity, land use, and recurrence. |
| **Flow Dynamics** | Computes velocity vectors ($\vec{u}, \vec{v}$), water depth ($h(x, y, t)$), dynamic backwater effects, and pipe pressurized surcharge. | Static hazard index; identifies relative vulnerability without computing dynamic fluid momentum or wave propagation. |
| **Computational Overhead** | High (minutes to hours per rainfall event on multi-core CPU/GPU clusters). Unsuitable for real-time web interactivity. | Extremely low ($< 5\text{ ms}$ per coordinate query on standard single-core CPU). Ideal for real-time web dashboards. |
| **Data Requirements** | Continuous cross-sections, pipe friction coefficients (Manning's $n$), outfall boundary tides/levels, soil infiltration rate curves. | Classified raster terrain slope, digitized drainage centerlines, land cover raster, and rainfall hyetographs. |

### 2.2 Operational Trade-Offs
AQUILA deliberately employs the 5-factor rule-based risk engine to achieve sub-second responsiveness on interactive web clients without requiring supercomputing clusters. However, this introduces the following limitations:
1. **No Water Depth Prediction:** AQUILA outputs a dimensionless *Risk Score* (0–100) and qualitative tiers (*Low*, *Moderate*, *High*, *Critical*), not hydraulic inundation depth in meters or flood volume in cubic meters.
2. **Absence of Backwater Effect Modeling:** When the Musi River or downstream receiving lakes reach capacity, upstream nalas in Manikonda experience backwater stagnation. The static index cannot compute this downstream hydraulic boundary condition.
3. **No Dynamic Surface Runoff Accumulation:** Runoff routing over time (hydrograph travel time from upper slopes to depression basins) is simplified; rainfall is evaluated against local slope rather than accumulating upstream discharge.

---

## 3. Underground Stormwater Drainage Cadastre Deficiencies

### 3.1 Data Availability Bottleneck
In rapidly urbanizing zones like Manikonda (which transitioned from panchayat jurisdiction to municipality and GHMC peripheral circle within the last decade), comprehensive GIS cadastres of underground stormwater networks are not publicly accessible:
* **Missing Attributes:** Underground conduit diameters, pipe shapes, invert elevations, manhole coordinates, drop inlet capacities, and structural siltation levels are unavailable in digital vector format.
* **Open Channel Proxy:** AQUILA relies on open drainage channels, nalas, and surface canals digitized from OpenStreetMap and verified against TSDI open benchmarks.

### 3.2 Implication on Flood Accuracy
In dense commercial and residential colonies (e.g., Puppalguda Road, Lanco Hills Road), flood ponding often results from clogged roadside drop inlets or undersized culverts under arterial roads. Because AQUILA only models proximity to major surface channels, localized micro-drainage blockages cannot be directly inferred without field telemetry.

---

## 4. Digital Elevation Model (DEM) Spatial Resolution

```
Spatial Resolution Comparison:
+-------------------------------------------------------------------+
|  1m LiDAR Grid:    [Road Crown] -> [Gutter (15cm)] -> [Curb/Plinth]| (Captures street gutters)
|  30m DEM Cell:     [========= Single Averaged Elevation =========]| (Blurs micro-topography)
+-------------------------------------------------------------------+
```

### 4.1 Grid Cell Averaging
* AQUILA utilizes the **Copernicus GLO-30 DSM** (30-meter horizontal resolution), downsampled and clipped to the Manikonda pilot boundary.
* A single $30\text{m} \times 30\text{m}$ grid cell ($900\text{ m}^2$) spans entire street widths, multiple building plinths, and roadside drains.
* Elevation values represent an area-weighted surface average rather than ground-level bare earth elevation.

### 4.2 Impact on Micro-Depression Detection
Urban stormwater runoff is heavily governed by micro-topography: road crown camber (2%), curb heights (10–15 cm), compound walls, and basement ramp thresholds. A 30m DEM smooths these features, meaning roadside gutters and shallow localized puddles cannot be resolved from satellite elevation grids alone.

---

## 5. Rainfall Observation Network Density & Spatial Interpolation

### 5.1 Weather Station Distribution
* As of 2026, there is no official India Meteorological Department (IMD) or TSDPS Automated Weather Station (AWS) located physically within the central core of Manikonda.
* Nearest official reporting stations are:
  - **Gachibowli AWS:** $\approx 4.8\text{ km}$ Northwest
  - **Rajendranagar AWS:** $\approx 8.2\text{ km}$ South
  - **Shaikpet / Jubilee Hills AWS:** $\approx 5.5\text{ km}$ Northeast

### 5.2 Micro-Cell Downpour Limitations
Monsoon thunderstorms in Hyderabad frequently exhibit intense convective micro-cells where a single neighborhood experiences $80\text{ mm/hr}$ cloudburst rain while an adjacent colony 3 km away records under $15\text{ mm/hr}$. Without high-density municipal IoT rain gauges or X-band Doppler radar precipitation grids, rainfall values assigned to Manikonda represent spatially interpolated or regionalized estimates.

---

## 6. Emergency Resource Fleet Modeling

### 6.1 Synthetic Fleet Classification
Due to statutory security policies, GHMC Disaster Response Force (DRF) teams, HYDRAA emergency squads, and Telangana State Fire Service assets do not expose public real-time GPS Automatic Vehicle Location (AVL) feeds.

### 6.2 Data Integrity Guardrails
* All emergency response units in AQUILA (mobile dewatering pumps, rescue inflatable boats, DRF quick-response teams, earthmovers) are synthetic demonstration entities.
* To prevent misleading municipal stakeholders:
  - Every resource record is tagged with `provenance="SIMULATED"`.
  - Display names are permanently prefixed with `[DEMO SYNTHETIC]`.
  - Depots are mapped to plausible public infrastructure locations (e.g., Manikonda Municipal Ward Office, Puppalguda Fire Station).

---

## 7. Geodesic Distance vs. Road Network Graph Routing

### 7.1 Current Dispatch Metric: Spherical Haversine
In the MVP implementation, the emergency resource recommendation engine ranks available units using the **Great-Circle Haversine distance formula**:
$$d = 2r \arcsin \left( \sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)} \right)$$

### 7.2 Routing Limitations
1. **Linear Straight-Line Approximation:** Haversine calculates straight-line distance ("as the crow flies"), neglecting actual street driving distance and winding neighborhood layout.
2. **No Dynamic Flood Impassability:** The current dispatcher does not check whether the intervening road network between the depot and incident site is inundated or blocked by stalled vehicles.
3. **Turn-by-Turn Guidance:** The system provides proximity ranking and dispatch assignment, but does not yet generate Dijkstra or A* turn-by-turn navigation paths on the NetworkX road graph.

---

## 8. Summary of Engineering Disclosures & Research Readiness

| Domain | Current Implementation (MVP) | Production / Research Target |
| :--- | :--- | :--- |
| **Hydraulic Accuracy** | 5-Factor Weighted Multi-Criteria Risk Index | Coupled 1D-2D Hydrodynamic Solver (SWMM + TUFLOW) |
| **Drainage Network** | Surface open nalas & major canals (OSM / TSDI) | Subsurface stormwater pipe cadastre with invert levels |
| **Terrain Elevation** | 30-meter Copernicus GLO-30 DSM | Sub-meter Airborne LiDAR / Drone Photogrammetric DEM |
| **Precipitation Input** | Regional AWS interpolation & synthetic scenarios | Real-time municipal IoT acoustic rain gauges + Doppler radar |
| **Emergency Resources** | Synthetic fleet with `[DEMO SYNTHETIC]` tag | Secure API integration with GHMC DRF / 112 CAD systems |
| **Routing Metric** | Spherical Haversine geodesic proximity | Dynamic flood-aware A* routing with road impassability tags |
| **Audit Logging** | Append-only SQLite relational audit log | Cryptographically hashed write-once tamper-evident store |

---

## 9. Conclusion

These limitations represent conscious engineering decisions to deliver a robust, fully validated, and verifiable academic prototype within a strict two-day MVP constraint. AQUILA succeeds as a modular proof-of-concept demonstrating modern software architecture, rigorous geospatial testing, and end-to-end incident coordination for urban flood management.

