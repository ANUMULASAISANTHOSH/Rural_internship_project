# AQUILA — MVP Known Limitations & Engineering Trade-Offs

## 1. Executive Summary

To deliver a working, integrated end-to-end prototype within the strict two-day implementation window, conscious architectural trade-offs were made.

In accordance with academic and engineering integrity standards, this document records all trade-offs, simplified proxies, and deferred enterprise capabilities. No limitation is concealed.

---

## 2. Technical Limitations & Trade-Off Matrix

| System Domain | MVP Implementation Proxy | Full Production Target | Impact on Decision Support |
|---|---|---|---|
| **Database Architecture** | **SQLite (`aquila_mvp.db`)** via SQLAlchemy | PostgreSQL 16 + PostGIS 3.4 Spatial Database | Transactional tables run in SQLite; spatial layers load via GeoPandas. Concurrency is limited to single-operator sessions. |
| **Frontend Framework** | **Streamlit + Folium** Python Dashboard | React / TypeScript SPA + MapLibre GL | Rapid single-language cockpit; page transitions involve Streamlit session reruns rather than client-side virtual DOM rendering. |
| **Resource Routing Distance** | **Haversine Great-Circle Distance** (Straight-line) | Dijkstra / A* Shortest Path on OSM Road Graph | Distances indicate geometric proximity (~20–30% shorter than road network travel distance). Does not account for turn restrictions or real-time road closures. |
| **Flood Modeling Fidelity** | **5-Factor Rule-Based Geographic Risk Index** | 2D Shallow Water Hydrodynamic Modeling (SWMM / HEC-RAS) | Index indicates topographic and precipitation vulnerability (0–100); does not calculate precise physical water velocity ($v$) or dynamic floodwave propagation. |
| **Weather Telemetry** | **Historical Proxy Stations & Synthetic Hyetograph** | Real-time authenticated TGDPS / IMD IoT streaming | Live ingestion is deferred due to the absence of public authenticated REST APIs on `tsdps.telangana.gov.in`. |
| **Drainage Network** | **Open Surface Waterways & Lakes Only (21 features)** | Full Cadastral Subsurface Stormwater Network | Underground closed box drains and roadside gutter grates are unmapped in public OSM; DEM flow accumulation acts as terrain proxy only. |
| **Authentication & Access** | **Single-Operator Session** | JWT Role-Based Access Control (RBAC) & OAuth2 | Administrative actions are open without user permission gates; audit log tracks actions globally without operator ID attribution. |
| **Multi-Tenancy** | **Single Catchment (Manikonda, 55.63 km²)** | Multi-Catchment / Metropolitan Scalable | System configured specifically for Manikonda pilot bounding coordinates; requires config modification to switch catchments. |

---

## 3. Detailed Component Limitations

### 3.1 Haversine Distance vs. Road Network Routing
- **Why Implemented:** Haversine distance executes in sub-millisecond time ($O(1)$) with zero dependency on routing graph indexes or geometry snapping, ensuring immediate resource recommendation responsiveness.
- **Limitation:** In urban Manikonda, natural terrain ridges and limited cross-drainage culverts create physical barriers (e.g., Khajaguda granite ridge separates Gachibowli from Puppalaguda). A straight-line distance of 1.2 km may correspond to a 3.5 km driving detour.
- **Mitigation in UI:** The dashboard explicitly labels the distance as *"Haversine Great-Circle (Straight-line)"* and does not claim to provide road travel times.

### 3.2 Geographic Risk Index vs. Hydrodynamic Flood Forecasting
- **Why Implemented:** Physics-based 2D shallow water hydrodynamic modeling requires high-performance computing clusters and takes hours to solve differential Saint-Venant equations for a 55 km² catchment at 5m resolution.
- **Limitation:** The 5-factor index ($R = 0.40P + 0.20T + 0.20D + 0.10L + 0.10H$) is an empirical vulnerability indicator, not a deterministic water depth simulation.
- **Mitigation in UI:** The output is explicitly badged as a *"Geographic Risk Index"*, avoiding unscientific claims of authoritative flood warnings.

### 3.3 Subsurface Urban Drainage Absence
- **Limitation:** Greater Hyderabad Municipal Corporation (GHMC) maintains closed box drain cadastre maps internally. These are not published in OpenStreetMap.
- **Mitigation:** AQUILA relies on surface terrain gradients derived from Copernicus DEM GLO-30 to evaluate natural depression storage, and explicitly documents that underground stormwater capacities are unverified.

---

## 4. Phase 4 & Production Roadmap (Deferred Capabilities)

The following enterprise capabilities were explicitly excluded from Phase 3 scope reduction and are slated for subsequent development:
1. Docker Compose multi-container deployment (`fastapi`, `postgis`, `streamlit`, `nginx`).
2. Full PostGIS migration using spatial SQL queries (`ST_DWithin`, `ST_Distance`).
3. NetworkX shortest-path road distance integration with live flood-depth weight penalties.
4. Celery / Redis asynchronous task queue for background simulation steps.
5. User authentication, citizen mobile reporting portal, and role-based incident triage.

