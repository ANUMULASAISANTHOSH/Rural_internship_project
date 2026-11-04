# AQUILA — Phase 4: Flood-Aware Routing, Safe Accessibility & Intelligent Navigation

**Pilot Study Area:** Manikonda, Hyderabad, Telangana, India  
**Sub-Catchment Extent:** 55.63 km² Analysis Bounding Box  
**Module Version:** 1.0.0 (Phase 4 Release)  
**Status:** Integrated, Documented & Verified (75/75 Tests Passing)  

---

## 1. Overview & Objective

Phase 4 transforms AQUILA from a geographic risk-indexing and point-based resource allocation tool into an **explainable, flood-aware transportation routing and facility accessibility platform**.

During intense urban flash floods, Euclidean straight-line distance ("as the crow flies") is fundamentally misleading. A hospital 1.0 km away across a submerged culvert is unreachable, whereas a hospital 2.5 km away along elevated dry ridges is immediately accessible. Phase 4 provides:
1. **Dynamic Road Network Topology:** Graph construction across 6,659 OpenStreetMap road segments using NetworkX and projected coordinate transformations (`EPSG:32644` UTM Zone 44N).
2. **Dual-Cost Pathfinding:** Shortest path (distance-optimal) vs. Lowest-risk path (safety-optimal) with configurable risk-aversion parameter $\lambda$.
3. **Incident & Disruption Penalties:** Proximity cost amplification around active flood incidents (`REPORTED`, `UNDER_REVIEW`, `ASSIGNED`, `IN_PROGRESS`) and simulated road disruptions.
4. **Critical Facility Accessibility:** Provenance-aware (`OSM_UNVERIFIED`) ranking of accessible medical facilities comparing straight-line vs. real road driving distance.
5. **Explainable Route Decision-Support:** Automated human-readable justifications explaining distance trade-offs, flood exposure reduction, and avoided hazards.
6. **Scenario Stress-Testing:** Deterministic disruption injection during scenario `MANI-HEAVY-001` with clean, isolated reset rollback.

---

## 2. Directory Structure & Documentation Navigation

```text
docs/phase-4/
├── README.md                           [This Overview & Quickstart Guide]
├── implementation_plan.md              [Initial Scope, Architecture & Execution Blueprint]
├── road_network_architecture.md        [Graph Topology, Snapping & Dual CRS Design]
├── routing_algorithms.md               [Mathematical Cost Formulations & Dijkstra Traversal]
├── incident_road_penalty_model.md      [Proximity Decay & Disruption Cost Amplification]
├── facility_accessibility.md           [Medical Infrastructure Search & Provenance Rules]
├── api_documentation.md                [FastAPI Routing Endpoints & OpenAPI Contracts]
├── testing_report.md                   [Execution Trace & Audit for 75 Automated Tests]
├── known_limitations.md                [Technical Boundaries, Disclosures & Future Scope]
└── phase_4_completion_report.md        [Phase 4 Sign-Off & Verification Audit]
```

---

## 3. Quickstart & Verification

### Run the Complete Automated Test Suite (75 Tests)
```powershell
# Navigate to project root
cd C:\AI\Rural_internship_project

# Run complete test suite (Geospatial + MVP Backend + Phase 4 Routing)
pytest -v
```

### Launch the Application
```powershell
# Terminal 1: Launch FastAPI REST Backend
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Launch Streamlit Command Centre
streamlit run app/dashboard/main.py --server.port 8501
```
Navigate to **`🧭 Flood-Aware Routing`** in the dashboard sidebar to explore dual-route visualization and accessible facility recommendations.

