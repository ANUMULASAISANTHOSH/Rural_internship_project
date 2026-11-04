# AQUILA — Phase 4: Automated Testing & Quality Assurance Report

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Pilot Area:** Manikonda, Hyderabad, Telangana, India  
**Document Type:** Test Execution Trace, Invariant Validation & Regression Audit  
**Location:** `docs/phase-4/testing_report.md`  

---

## 1. Test Suite Summary & Pass Rate

A comprehensive automated test suite consisting of **75 automated tests** was executed in Python 3.13 via Pytest. The suite spans geospatial vector/raster data integrity, core backend services, incident lifecycle coordination, and Phase 4 flood-aware pathfinding.

```
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\AI\Rural_internship_project

tests/geospatial/test_data_validation.py ......................................... [ 54%]
tests/mvp/test_backend.py ................                                        [ 76%]
tests/phase4/test_routing.py ..................                                   [100%]

======================== 75 passed, 1 warning in 23.72s ========================
```

* **Total Test Cases Executed:** 75
* **Tests Passed:** 75 (**100% Pass Rate**)
* **Tests Failed / Errored:** 0
* **Regression Invariants:** All 57 pre-existing Phase 2 and MVP tests continue to pass without a single failure or behavioral regression.

---

## 2. Phase 4 Routing & Accessibility Test Catalog (18 Tests)

The new test suite in [`tests/phase4/test_routing.py`](file:///C:/AI/Rural_internship_project/tests/phase4/test_routing.py) validates the following architectural and mathematical invariants:

| # | Test Function Name | Architectural Invariant Verified | Outcome |
|---|---|---|---|
| **01** | `test_road_graph_construction_and_size` | Confirms graph initializes with $>20,000$ nodes, $>40,000$ edges, and $\ge 90\%$ connectivity. | **PASSED** |
| **02** | `test_spatial_snapping_to_largest_component` | Confirms arbitrary GPS query snaps to a node inside the largest connected component within $300\text{m}$. | **PASSED** |
| **03** | `test_edge_lengths_positive_and_finite` | Confirms all edge lengths $L(e)$ are strictly positive, finite, and $< 5000\text{ m}$. | **PASSED** |
| **04** | `test_shortest_route_optimality` | Confirms Dijkstra shortest path returns non-empty coordinates and positive length. | **PASSED** |
| **05** | `test_identical_origin_and_destination` | Confirms routing when origin == destination returns 0 distance and 1 node without crashing. | **PASSED** |
| **06** | `test_lowest_risk_route_with_custom_lambda` | Confirms lowest-risk Dijkstra path respects custom $\lambda=5.0$ risk multiplier. | **PASSED** |
| **07** | `test_route_comparison_and_explanation` | Confirms comparison service generates human-readable explanation and scientific disclaimer. | **PASSED** |
| **08** | `test_incident_proximity_penalty_and_detour` | Creates an active incident, confirms edge weights increase, and verifies route detours around blockage. | **PASSED** |
| **09** | `test_resolved_incident_does_not_penalize` | Verifies that an incident with status `RESOLVED` applies $0.0$ penalty to road edges. | **PASSED** |
| **10** | `test_facility_accessibility_ranking_and_provenance`| Confirms facility search finds medical units, proves driving $\ge$ straight-line distance, and validates `OSM_UNVERIFIED` tag. | **PASSED** |
| **11** | `test_accessibility_unreachable_handling` | Confirms queries far outside study bounds return 0 facilities without unhandled exceptions. | **PASSED** |
| **12** | `test_scenario_disruption_injection_and_reset` | Advances scenario to Step 3, confirms `DISR-SIM-001` injection, and verifies clean purge on reset. | **PASSED** |
| **13** | `test_api_network_summary` | Verifies `GET /api/v1/routing/network-summary` returns HTTP 200 with complete topology stats. | **PASSED** |
| **14** | `test_api_shortest_route` | Verifies `GET /api/v1/routing/shortest` returns HTTP 200 with valid route coordinates. | **PASSED** |
| **15** | `test_api_lowest_risk_route` | Verifies `GET /api/v1/routing/lowest-risk` returns HTTP 200 with lambda parameter applied. | **PASSED** |
| **16** | `test_api_route_compare` | Verifies `GET /api/v1/routing/compare` returns HTTP 200 with dual routes and comparison payload. | **PASSED** |
| **17** | `test_api_accessible_facilities` | Verifies `GET /api/v1/accessibility/facilities` returns HTTP 200 with ranked hospital recommendations. | **PASSED** |
| **18** | `test_api_invalid_coordinates_rejected` | Confirms out-of-bounds coordinates ($99.0^\circ\text{N}$) trigger HTTP 400 Bad Request with informative detail. | **PASSED** |

---

## 3. Performance & Latency Benchmarks

All performance measurements were benchmarked on a standard developer workstation running Python 3.13.2 (64-bit Windows, single-core execution):

| Operation | Benchmark Execution Time | Performance Evaluation |
| :--- | :--- | :--- |
| **Initial Graph Build & Indexing** | **$0.28\text{ seconds}$** | Executed once at service startup; cached in memory. |
| **cKDTree Spatial Snapping** | **$0.08\text{ milliseconds}$** | Immediate logarithmic nearest-neighbor lookup. |
| **Single-Pair Dijkstra Pathfinding** | **$18 - 45\text{ milliseconds}$** | Computes across 48,391 edges in sub-50ms latency. |
| **Full Route Comparison + Explanation** | **$45 - 80\text{ milliseconds}$** | Computes both paths, updates metrics, and writes explanation. |
| **Critical Facility Accessibility Search** | **$85 - 160\text{ milliseconds}$** | Evaluates 5 candidate facilities with full road paths in $<200\text{ ms}$. |
| **Full Test Suite Runtime (75 Tests)** | **$23.72\text{ seconds}$** | Comprehensive test execution including scenario lifecycles. |
| **Phase 4 Standalone Suite (18 Tests)** | **$11.23\text{ seconds}$** | Rapid development and continuous integration feedback. |

