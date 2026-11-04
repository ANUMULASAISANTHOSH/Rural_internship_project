# AQUILA — Phase 4: Known Limitations, Technical Boundaries & Disclosures

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Pilot Area:** Manikonda, Hyderabad, Telangana, India  
**Document Type:** Technical Architecture Disclosures & System Boundaries  
**Location:** `docs/phase-4/known_limitations.md`  

---

## 1. Executive Disclosure

AQUILA Phase 4 introduces flood-aware transportation modeling and facility accessibility analysis as an **academic decision-support prototype**.

> [!IMPORTANT]
> **AQUILA is not a certified emergency vehicle navigation system or real-world traffic management tool.** It does not replace, override, or interface with:
> * Statutory 112 / 108 Emergency Response Dispatchers.
> * Greater Hyderabad Municipal Corporation (GHMC) Traffic Police closures.
> * Real-time commercial vehicular navigation platforms (e.g., Google Maps, Apple Maps, Waze).

All system outputs must be interpreted strictly within the engineering assumptions, mathematical abstractions, and data limitations documented below.

---

## 2. Risk Cost vs. Physical Flood Water Depth

### 2.1 Dimensionless Risk Abstraction
The routing algorithm penalizes road segments using the composite risk score $R(e) \in [0, 100]$:
$$C_{\text{risk}}(e) = L(e) \cdot \left(1.0 + \lambda \cdot \frac{R(e)}{100} + P_{\text{incident}} + P_{\text{disruption}}\right)$$
* **Limitation:** $R(e)$ is a **dimensionless vulnerability index**, not a physical measurement of flood depth ($h$) in centimeters or flow velocity ($v$) in m/s.
* **Operational Implication:** A road segment with a risk score of 75 may have 10 cm of slow sheet runoff (easily passable by an emergency fire truck or high-axle dewatering unit) or 60 cm of rushing stormwater (completely impassable). The prototype assumes higher risk warrants a precautionary detour, but cannot verify whether a specific vehicle's exhaust or chassis clearance permits traversal.

---

## 3. Road Network Data & Traffic Dynamics

### 3.1 Absence of Live Vehicular Traffic Telemetry
* AQUILA computes distance-optimal and risk-optimal routes using physical street lengths ($L(e)$).
* **Limitation:** The platform does **not** ingest real-time traffic congestion telemetry (e.g., live vehicle speeds, stalled traffic queues, or traffic signal timings).
* **Operational Implication:** A shortest path may be geographically unflooded but gridlocked by stalled civilian cars fleeing the storm. True travel-time optimization requires integration with municipal traffic camera feeds or commercial probe data.

### 3.2 Turn Restrictions and Intersection Delays
* Road topology respects street connectivity and basic `oneway` tags.
* **Limitation:** Complex urban intersection turn prohibitions (e.g., "No Right Turn", concrete median dividers, pedestrian signal delays, or grade-separated flyover entrance ramps) are not fully encoded in OpenStreetMap vector extracts for Manikonda.

---

## 4. Infrastructure Provenance & Evacuation Capability

### 4.1 Crowdsourced OpenStreetMap Facilities
* All 65 critical facilities (hospitals, clinics, pharmacies) carry the provenance classification `OSM_UNVERIFIED`.
* **Limitation:** Facilities were extracted via Overpass API queries without on-site municipal field audits.
* **Operational Implication:** A mapped clinic might be a small outpatient dispensary with closed gates at night, rather than a 24/7 emergency trauma hospital. Municipal operators must independently verify facility operational readiness before routing casualties.

### 4.2 Exclusion of Certified Evacuation Shelters
* The platform does **not** designate public schools or community buildings as evacuation shelters.
* Authoritative shelter designation is an executive statutory power reserved exclusively for the District Collector and GHMC Disaster Management Commissioner.

---

## 5. Summary of Phase 4 Engineering Trade-Offs

| System Dimension | Current Phase 4 Implementation | Production / Future Phase Target |
| :--- | :--- | :--- |
| **Routing Metric** | Dual-cost Dijkstra on metric length & risk index | Real-time dynamic A* with hydrodynamic flood depth clearance |
| **Traffic Integration**| Static topological road graph from OSM | Live floating-car probe telemetry (Uber/Google Traffic feeds) |
| **Vehicle Types** | Uniform vehicular routing | Vehicle-specific clearance profiles (sedan vs. 4x4 vs. boat) |
| **Road Closures** | Dynamic distance-decay incident penalties | Physical sensor-gated municipal road closure barricades |
| **Facility Audit** | OpenStreetMap crowdsource (`OSM_UNVERIFIED`) | Official Telangana Directorate of Medical Education cadastre |
| **Audit Traceability** | Append-only SQLite relational audit log | Cryptographically hashed write-once cloud event stream |

