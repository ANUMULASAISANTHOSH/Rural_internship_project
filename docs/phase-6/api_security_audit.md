# AQUILA Phase 6: API Security, Validation & Reliability Audit

## 1. Executive Summary

This document presents a comprehensive application security and reliability audit of all FastAPI REST endpoints in **AQUILA**.

As an academic emergency decision-support prototype intended for research demonstrations and peer evaluation, security engineering focuses on:
- Strict schema validation and boundary checks.
- Sanitized exception handling with zero server filesystem or stack-trace leakage.
- Clear separation between state-modifying endpoints and idempotent read-only endpoints.
- Configurable Cross-Origin Resource Sharing (CORS).
- Zero storage or transmission of credentials or sensitive personal information.

---

## 2. Endpoint Security & Operation Matrix

All 18 endpoints are classified below by operational state mutation and access controls:

| # | HTTP Method | Endpoint Route | Type | Validation Controls | Security Measures |
|---|---|---|---|---|---|
| 1 | `GET` | `/health` | **READ-ONLY** | None | System diagnostic probe; no path/PII exposure |
| 2 | `GET` | `/api/v1/health` | **READ-ONLY** | None | Deep subsystem probe; returns operational status |
| 3 | `GET` | `/api/summary` | **READ-ONLY** | None | Aggregated database metrics; read-only session |
| 4 | `GET` | `/api/layers` | **READ-ONLY** | None | Vector feature count inventory |
| 5 | `GET` | `/api/layers/{layer_name}` | **READ-ONLY** | Whitelist lookup (`LAYER_FILES`) | Sanitized 404 response; zero server path leak |
| 6 | `GET` | `/api/rainfall` | **READ-ONLY** | `limit` integer clamp | Paginated query; no SQL injection surface |
| 7 | `GET` | `/api/risk` | **READ-ONLY** | Bounded floats (`ge`, `le`) | Parameter bounds clamping; no divide-by-zero |
| 8 | `POST` | `/api/risk` | **READ-ONLY** | Pydantic `RiskRequest` | JSON schema validation; weight sum verification |
| 9 | `GET` | `/api/incidents` | **READ-ONLY** | Query parameters | Parameterized SQLAlchemy query |
| 10 | `POST` | `/api/incidents` | **STATE-MODIFYING** | Pydantic `IncidentCreate` | Strict type, coordinate $[17.2, 17.6]$, $[78.2, 78.6]$, severity enum |
| 11 | `PATCH` | `/api/incidents/{id}/status` | **STATE-MODIFYING** | Status whitelist | Validated state machine transition; cascade resource release |
| 12 | `GET` | `/api/resources` | **READ-ONLY** | Query filters | Parameterized SQLAlchemy query |
| 13 | `POST` | `/api/incidents/{id}/recommend-resource` | **READ-ONLY** | Incident ID lookup | Algorithmic recommendation; does not modify DB |
| 14 | `POST` | `/api/incidents/{id}/assign-resource` | **STATE-MODIFYING** | Pydantic request | Foreign key integrity check; updates availability |
| 15 | `POST` | `/api/scenarios/start` | **STATE-MODIFYING** | None | Audit-logged scenario lifecycle event |
| 16 | `POST` | `/api/scenarios/advance` | **STATE-MODIFYING** | None | Deterministic time-step advance; simulated tags |
| 17 | `POST` | `/api/scenarios/reset` | **STATE-MODIFYING** | None | Atomic purge of simulated entities; real data preserved |
| 18 | `GET` | `/api/scenarios/status` | **READ-ONLY** | None | In-memory status query |
| 19 | `GET` | `/api/audit-history` | **READ-ONLY** | `limit` integer clamp | Append-only historical operational log |
| 20 | `GET` | `/api/v1/routing/network-summary` | **READ-ONLY** | None | Graph structural metrics |
| 21 | `GET` | `/api/v1/routing/shortest` | **READ-ONLY** | Coordinate bounds check | Snaps within $[17.2, 17.6]$, $[78.2, 78.6]$; Dijkstra |
| 22 | `GET` | `/api/v1/routing/lowest-risk` | **READ-ONLY** | Coordinates & $\lambda \in [0, 50]$ | Bounded risk multiplier; edge weight calculation |
| 23 | `GET` | `/api/v1/routing/compare` | **READ-ONLY** | Coordinates & $\lambda \in [0, 50]$ | Comparison matrix; read-only |
| 24 | `GET` | `/api/v1/accessibility/facilities` | **READ-ONLY** | Coordinates & Category filter | Provenance `OSM_UNVERIFIED` strictly tagged |
| 25 | `GET` | `/api/v1/scenarios/compare` | **READ-ONLY** | None | Deterministic scenario matrix synthesis |
| 26 | `GET` | `/api/v1/scenarios/sensitivity` | **READ-ONLY** | `perturbation_fraction` $[0.05, 0.50]$ | One-At-a-Time sensitivity analysis |
| 27 | `GET` | `/api/v1/infrastructure/vulnerability` | **READ-ONLY** | Rainfall float clamp & Category | Ranks 65 facilities; OSM provenance preserved |
| 28 | `GET` | `/api/v1/incidents/priorities` | **READ-ONLY** | None | Evaluates priority queue; requires human approval |
| 29 | `GET` | `/api/v1/analytics/summary` | **READ-ONLY** | None | Aggregated system analytics |

---

## 3. Key Security Safeguards Implemented

### 1. Zero Filesystem Path Exposure
Previously, when requesting an invalid or unmapped layer at `/api/layers/{layer_name}`, the server could return the raw Python `FileNotFoundError` message displaying the absolute local directory path:
`"FileNotFoundError: [Errno 2] No such file or directory: 'C:\\AI\\Rural_internship_project\\data\\...'"`

In Phase 6, [`app/api/main.py`](file:///c:/AI/Rural_internship_project/app/api/main.py) was updated:
- Validates `layer_name` against the exact whitelist `LAYER_FILES.keys()`.
- Catches and logs internal filesystem errors server-side via `app_logger`.
- Returns a sanitized client response:
  ```json
  {
    "detail": "Layer 'invalid_layer' not found. Available: ['drainage', 'historical_flood_points', 'infrastructure', 'monitoring_locations', 'roads', 'settlements', 'study_area_bbox', 'water_bodies']"
  }
  ```

### 2. Global Sanitized Exception Handler
A centralized exception handler catches unhandled exceptions across all routes:
```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An internal server error occurred while processing the request.",
            "status_code": 500
        }
    )
```
This guarantees that unhandled database or runtime exceptions never expose Python stack traces or internal implementation details.

### 3. Spatial Coordinate Bounding
All geographic routing and facility endpoints enforce bounding box validation via `_validate_routing_coords`:
- Latitude: $[17.20^\circ\text{N}, 17.60^\circ\text{N}]$
- Longitude: $[78.20^\circ\text{E}, 78.60^\circ\text{E}]$

Requests outside this geographic domain are rejected immediately with HTTP 400 Bad Request, preventing arbitrary coordinate snapping or KDTree memory corruption.

### 4. Configurable Cross-Origin Resource Sharing (CORS)
The CORS middleware is configured via the `AQUILA_CORS_ORIGINS` environment variable, defaulting to safe localhost origins (`http://localhost:8501,http://127.0.0.1:8501`) when deployed in demonstration environments.

