# AQUILA — Phase 4: Road Network Graph Architecture & Spatial Indexing

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Pilot Area:** Manikonda, Hyderabad, Telangana, India  
**Document Type:** Transportation Network Specification & Topological Architecture  
**Location:** `docs/phase-4/road_network_architecture.md`  

---

## 1. Graph Formalism & Topology

The transportation network of the Manikonda pilot area is modeled as a weighted directed multigraph $G = (V, E)$, instantiated via NetworkX in [`app/services/road_network_service.py`](file:///C:/AI/Rural_internship_project/app/services/road_network_service.py).

```mermaid
graph LR
    subgraph OSMGeoJSON["OSM Processed Roads (6,659 Features)"]
        F1["LineString: Secretariat Main Road"]
        F2["LineString: Puppalaguda Residential Lane"]
        F3["LineString: Alkapur Sector Arterial"]
    end

    subgraph DualCRS["Dual-CRS Coordinate Pipeline"]
        WGS84["EPSG:4326 (WGS 84)\nDecimal Degrees [Lon, Lat]"]
        UTM44N["EPSG:32644 (UTM Zone 44N)\nPlanar Metres [X, Y]"]
        WGS84 -->|PyProj Transformer| UTM44N
    end

    subgraph NetworkXGraph["Topological Graph G(V, E)"]
        N1["Node u (x, y, lon, lat)"]
        N2["Node v (x, y, lon, lat)"]
        E1["Edge (u, v): length_m, risk_cost, highway, name"]
        E2["Edge (v, u): bidirectional if not oneway"]
        N1 --> E1 --> N2
        N2 --> E2 --> N1
    end

    subgraph SpatialIndex["Fast Snapping (SciPy cKDTree)"]
        KD["cKDTree on Largest Component (22,531 Nodes)"]
        QUERY["GPS Query (lat, lon)"] -->|O(log N)| SNAP["Snapped Intersection Node (< 0.1ms)"]
    end

    OSMGeoJSON --> DualCRS
    DualCRS --> NetworkXGraph
    NetworkXGraph --> SpatialIndex
```

---

## 2. Quantitative Graph Invariants

| Attribute / Metric | Benchmark Value | Description / Engineering Verification |
| :--- | :--- | :--- |
| **Source Dataset** | `roads_manikonda_processed.geojson` | 6,659 cleaned OSM road segments in EPSG:4326. |
| **Total Graph Nodes ($|V|$)** | **23,802 nodes** | Road intersections, curve vertices, and dead-ends. |
| **Total Directed Edges ($|E|$)** | **48,391 edges** | Bidirectional street segments unless tagged `oneway == "yes"`. |
| **Connected Components** | **132 components** | Evaluated via `nx.weakly_connected_components(G)`. |
| **Largest Connected Component** | **22,531 nodes (94.7%)** | Main contiguous vehicular network; exceeds NFR-004 ($\ge 90\%$). |
| **Disconnected Island Nodes** | **1,271 nodes (5.3%)** | Gated community internal pedestrian paths and boundary-clipped stubs. |
| **Spatial Snapping Index** | `scipy.spatial.cKDTree` | Built exclusively over the 22,531 largest component nodes. |
| **Average Snapping Latency** | **$< 0.08\text{ ms}$** | Logarithmic Euclidean nearest-neighbor search in projected meters. |

---

## 3. Dual Coordinate Reference System (CRS) Design

To ensure mathematical precision and eliminate spatial distortion, AQUILA enforces a strict dual-CRS policy:

### 3.1 Storage & Web Interoperability: `EPSG:4326` (WGS 84)
- **Units:** Decimal degrees (latitude, longitude).
- **Application:** Storage in GeoJSON, SQLite spatial columns, API JSON request/response payloads, and Leaflet/Folium web map polylines.

### 3.2 Planar Computational Projection: `EPSG:32644` (UTM Zone 44N)
- **Units:** Metres ($m$).
- **Application:** Edge length calculations, buffer generation, spatial snapping, and Dijkstra traversal costs.
- **Why It Is Essential:** At Hyderabad's latitude ($17.4^\circ\text{N}$):
  $$1^\circ \text{ Longitude} \approx 106.1\text{ km}, \quad 1^\circ \text{ Latitude} \approx 110.7\text{ km}$$
  Calculating Euclidean distance directly in degrees ($\sqrt{\Delta \text{lon}^2 + \Delta \text{lat}^2}$) produces anisotropic directional distortion of up to $4.3\%$. Transforming coordinates to UTM Zone 44N via `pyproj.Transformer` ensures isotropic metric distance accuracy:
  $$L(e) = \sqrt{(x_v - x_u)^2 + (y_v - y_u)^2}$$

---

## 4. Road Segment Attribute Model

Every directed edge $e = (u, v)$ in the NetworkX graph maintains rich physical, hydrological, and operational attributes:

```python
edge_attributes = {
    "length_m": 142.5,               # Metric segment length in projected UTM meters
    "highway": "residential",        # OSM classification (primary, secondary, residential, etc.)
    "name": "Alkapur Main Road",     # Street name or 'Unnamed Road'
    "osm_id": 142981042,             # Original OSM way identifier
    "mid_lon": 78.384210,            # Midpoint longitude for spatial queries
    "mid_lat": 17.391520,            # Midpoint latitude for spatial queries
    "elevation_m": 512.4,            # Local surface elevation sampled from Copernicus DEM
    "slope_degrees": 1.2,            # Topographic slope sampled from slope raster
    "distance_waterway_m": 65.0,     # Metric distance to nearest mapped nala/lake
    "distance_flood_point_m": 120.0, # Metric distance to nearest Oct 2020 flood point
    "base_risk_score": 78.1,         # Baseline risk at standard 25 mm/hr rain
    "current_risk_score": 78.1,      # Dynamically recalculated risk under active rainfall
    "incident_penalty": 0.0,         # Proximity penalty from active flood incidents
    "disruption_penalty": 0.0,       # Penalty from confirmed or simulated road disruptions
    "shortest_cost": 142.5,          # Pure distance cost for shortest-path Dijkstra
    "risk_cost": 476.3,              # Risk-amplified cost for lowest-risk Dijkstra
    "geometry": [[78.384, 17.391],   # LineString vertex coordinates for map rendering
                 [78.385, 17.392]]
}
```

---

## 5. Spatial Snapping & Disconnection Handling

### 5.1 Snapping to the Largest Connected Component
In urban networks, snapped points can accidentally latch onto isolated gated-colony dead ends or pedestrian courtyard paths that do not connect to the broader street grid. If an origin snaps to an isolated component and the destination snaps to the main network, standard Dijkstra pathfinding fails with a `NetworkXNoPath` exception.

**Engineering Solution:**
AQUILA constructs the `kdtree_largest_cc` spatial index exclusively using the **22,531 nodes belonging to the largest connected component**. Any GPS query coordinate is guaranteed to snap to a node that has continuous topological connectivity across the entire Manikonda road network.

### 5.2 Exception Isolation
If a path between two nodes cannot be resolved (e.g., if a simulated road disruption completely severs a cul-de-sac), the service intercepts `NetworkXNoPath` and returns a structured response:
```json
{
  "route_type": "LOWEST_RISK",
  "found": false,
  "error": "No viable path avoids active road disruptions.",
  "snapping_distance_origin_m": 42.1,
  "snapping_distance_dest_m": 35.8
}
```
This guarantees that the web API and dashboard remain stable and responsive without unhandled 500 server crashes.

