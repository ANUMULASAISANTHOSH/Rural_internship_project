# AQUILA — Phase 4: REST API Documentation & OpenAPI Specification

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Pilot Area:** Manikonda, Hyderabad, Telangana, India  
**Document Type:** REST API Developer Reference & Schema Specification  
**Location:** `docs/phase-4/api_documentation.md`  

---

## 1. API Architecture & Standards

Phase 4 introduces high-performance, asynchronous REST API endpoints implemented via FastAPI and Pydantic V2 in [`app/api/main.py`](file:///C:/AI/Rural_internship_project/app/api/main.py).

* **Base URL:** `http://127.0.0.1:8000`
* **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`
* **OpenAPI Specification:** `http://127.0.0.1:8000/openapi.json`
* **Input Coordinate Boundaries:** Latitude $\in [17.20, 17.60]$, Longitude $\in [78.20, 78.60]$.
* **Standard Response Format:** `application/json`

---

## 2. Phase 4 Endpoint Catalog

| HTTP Method | Endpoint Path | Description | Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/routing/network-summary` | Returns topological stats of the road graph. | None |
| `GET` | `/api/v1/routing/shortest` | Computes distance-optimal shortest path. | `origin_lat`, `origin_lon`, `dest_lat`, `dest_lon` |
| `GET` | `/api/v1/routing/lowest-risk` | Computes safety-optimal lowest-risk path. | `origin_lat`, `origin_lon`, `dest_lat`, `dest_lon`, `lambda_param` |
| `GET` | `/api/v1/routing/compare` | Compares shortest and lowest-risk paths with explanation. | `origin_lat`, `origin_lon`, `dest_lat`, `dest_lon`, `lambda_param` |
| `GET` | `/api/v1/accessibility/facilities` | Ranks nearest accessible medical facilities. | `origin_lat`, `origin_lon`, `facility_category`, `limit` |

---

## 3. Detailed Endpoint Specifications

### 3.1 Network Summary: `GET /api/v1/routing/network-summary`
Returns graph scale, edge distributions, and connected component metrics.

**Sample Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/routing/network-summary"
```

**Sample Response (`200 OK`):**
```json
{
  "total_nodes": 23802,
  "total_directed_edges": 48391,
  "largest_connected_component_nodes": 22531,
  "connectivity_percentage": 94.7,
  "highway_type_distribution": {
    "residential": 34759,
    "service": 5928,
    "tertiary": 3340,
    "secondary": 1579,
    "living_street": 1290,
    "primary": 560,
    "trunk": 245,
    "motorway": 210,
    "unclassified": 214
  },
  "spatial_projection": "EPSG:32644 (UTM Zone 44N)",
  "storage_crs": "EPSG:4326 (WGS 84)",
  "road_features_source": "OpenStreetMap Manikonda Extract"
}
```

---

### 3.2 Shortest Route: `GET /api/v1/routing/shortest`
Calculates distance-optimal route using edge length in meters.

**Sample Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/routing/shortest?origin_lat=17.3912&origin_lon=78.3845&dest_lat=17.3980&dest_lon=78.3920"
```

**Sample Response (`200 OK`):**
```json
{
  "route_type": "SHORTEST",
  "found": true,
  "total_distance_meters": 2488.1,
  "total_distance_km": 2.488,
  "average_risk_score": 68.4,
  "risk_category": "MODERATE",
  "high_risk_segment_count": 8,
  "incident_affected_segment_count": 3,
  "disruption_affected_segment_count": 0,
  "node_count": 64,
  "primary_roads_traversed": ["Puppalaguda Road", "Manikonda Main Road"],
  "coordinates": [
    [78.3845, 17.3912],
    [78.3849, 17.3918],
    [78.3920, 17.3980]
  ],
  "snapping_distance_origin_m": 14.2,
  "snapping_distance_dest_m": 8.5
}
```

---

### 3.3 Lowest-Risk Route: `GET /api/v1/routing/lowest-risk`
Calculates safety-optimal path with risk avoidance multiplier $\lambda$.

**Sample Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/routing/lowest-risk?origin_lat=17.3912&origin_lon=78.3845&dest_lat=17.3980&dest_lon=78.3920&lambda_param=3.0"
```

**Sample Response (`200 OK`):**
```json
{
  "route_type": "LOWEST_RISK",
  "found": true,
  "total_distance_meters": 2674.3,
  "total_distance_km": 2.674,
  "average_risk_score": 45.0,
  "risk_category": "MODERATE",
  "high_risk_segment_count": 1,
  "incident_affected_segment_count": 0,
  "disruption_affected_segment_count": 0,
  "node_count": 71,
  "primary_roads_traversed": ["Secretariat Main Road", "Alkapur Township Boulevard"],
  "coordinates": [
    [78.3845, 17.3912],
    [78.3852, 17.3925],
    [78.3920, 17.3980]
  ],
  "lambda_param_applied": 3.0
}
```

---

### 3.4 Route Comparison & Trade-Off: `GET /api/v1/routing/compare`
Compares both route options and synthesizes a human-readable decision-support explanation.

**Sample Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/routing/compare?origin_lat=17.3912&origin_lon=78.3845&dest_lat=17.3980&dest_lon=78.3920&lambda_param=3.0"
```

**Sample Response (`200 OK`):**
```json
{
  "origin": {"latitude": 17.3912, "longitude": 78.3845},
  "destination": {"latitude": 17.3980, "longitude": 78.3920},
  "shortest_route": { ... },
  "lowest_risk_route": { ... },
  "comparison": {
    "has_recommendation": true,
    "preferred_route": "LOWEST_RISK",
    "explanation_summary": "The lowest-risk route is recommended. It requires a 7.5% distance detour (+186 m, total 2674 m vs 2488 m) but successfully bypasses 3 active flood incident corridors, reducing overall flood hazard exposure by 34.2% (from 68.4 to 45.0/100).",
    "distance_delta_meters": 186.2,
    "distance_delta_pct": 7.5,
    "shortest_average_risk": 68.4,
    "lowest_risk_average_risk": 45.0,
    "risk_reduction_pct": 34.2,
    "avoided_high_risk_segments": 7,
    "avoided_incident_segments": 3,
    "avoided_disruption_segments": 0,
    "lambda_risk_weight": 3.0,
    "scientific_disclaimer": "Recommendation is generated by AQUILA's decision-support heuristic (λ=3.0). It evaluates relative multi-factor vulnerability and incident proximity; it does not certify physical flood water depth or real-time vehicular passability."
  }
}
```

---

### 3.5 Accessible Facilities: `GET /api/v1/accessibility/facilities`
Ranks nearest medical facilities by real road-network driving distance.

**Sample Request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/accessibility/facilities?origin_lat=17.3912&origin_lon=78.3845&facility_category=hospital&limit=2"
```

**Sample Response (`200 OK`):**
```json
{
  "origin": {"latitude": 17.3912, "longitude": 78.3845},
  "requested_category": "hospital",
  "facilities_found_count": 2,
  "accessible_count": 2,
  "unreachable_count": 0,
  "facilities": [
    {
      "facility_id": "node/2354679489",
      "facility_name": "Shobha Hospital",
      "facility_category": "hospital",
      "latitude": 17.3980,
      "longitude": 78.3920,
      "straight_line_distance_km": 1.04,
      "road_network_distance_km": 1.46,
      "road_network_distance_meters": 1456.2,
      "route_average_risk_score": 48.5,
      "route_risk_category": "MODERATE",
      "incident_affected_segments": 0,
      "disruption_affected_segments": 0,
      "accessibility_status": "MODERATE_RISK_ACCESSIBLE",
      "data_provenance": "MANUALLY_SEEDED",
      "verification_status": "OSM_UNVERIFIED",
      "disclaimer": "Facility sourced from OpenStreetMap; operational readiness not verified on ground."
    }
  ]
}
```

---

## 4. Error Handling & HTTP Status Codes

* **`400 Bad Request`:** Raised when coordinates fall outside the study envelope bounds:
  ```json
  {"detail": "Invalid origin latitude '99.0'. Must be within [17.20, 17.60]."}
  ```
* **`404 Not Found`:** Returned when no path exists between disconnected island nodes or if facilities cannot be found within the search radius.
* **`422 Unprocessable Entity`:** Pydantic validation failure (e.g., non-numeric coordinate string).

