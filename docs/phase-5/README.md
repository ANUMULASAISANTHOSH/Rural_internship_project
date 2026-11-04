# AQUILA Phase 5: Multi-Scenario Intelligence, Uncertainty Analysis & Emergency Decision Optimization
## Comprehensive Phase Overview & System Index

### Project Identity
- **System**: AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform
- **Pilot Catchment**: Manikonda, Hyderabad, Telangana, India ($55.63\text{ km}^2$, bounding box $[17.360^\circ\text{N}, 78.330^\circ\text{E}]$ to $[17.435^\circ\text{N}, 78.415^\circ\text{E}]$)
- **Phase 5 Objective**: Multi-Scenario Comparative Intelligence, Algorithmic Uncertainty & Sensitivity Analysis, Critical Infrastructure Vulnerability Ranking, and Human-in-the-Loop Emergency Response Prioritization.

---

## 1. Documentation Index

The Phase 5 documentation suite consists of the following 11 architectural, algorithmic, and verification documents:

| # | Document | Purpose & Scope |
|---|---|---|
| 01 | [README.md](file:///c:/AI/Rural_internship_project/docs/phase-5/README.md) | Master overview, system directory, and Phase 5 feature matrix |
| 02 | [implementation_plan.md](file:///c:/AI/Rural_internship_project/docs/phase-5/implementation_plan.md) | Scope boundaries, mathematical formulations, and engineering roadmap |
| 03 | [scenario_comparison_architecture.md](file:///c:/AI/Rural_internship_project/docs/phase-5/scenario_comparison_architecture.md) | Architecture of the 5 operational scenarios and comparative delta matrices |
| 04 | [uncertainty_and_sensitivity.md](file:///c:/AI/Rural_internship_project/docs/phase-5/uncertainty_and_sensitivity.md) | OAT parameter perturbation, weight renormalization invariants, and routing elasticity |
| 05 | [infrastructure_vulnerability.md](file:///c:/AI/Rural_internship_project/docs/phase-5/infrastructure_vulnerability.md) | Multi-criteria vulnerability index ($V$) for 65 critical assets and provenance tags |
| 06 | [response_priority_model.md](file:///c:/AI/Rural_internship_project/docs/phase-5/response_priority_model.md) | Emergency response priority index ($P$), explainability, and operator governance |
| 07 | [historical_evidence_comparison.md](file:///c:/AI/Rural_internship_project/docs/phase-5/historical_evidence_comparison.md) | Spatial consistency benchmark against October 2020 verified flood points |
| 08 | [api_documentation.md](file:///c:/AI/Rural_internship_project/docs/phase-5/api_documentation.md) | Specification of the 5 FastAPI endpoints with schemas and payloads |
| 09 | [testing_report.md](file:///c:/AI/Rural_internship_project/docs/phase-5/testing_report.md) | Verification logs, test suite coverage (91/91 passing tests), and zero-regression report |
| 10 | [known_limitations.md](file:///c:/AI/Rural_internship_project/docs/phase-5/known_limitations.md) | Explicit disclosures of unmodeled factors, OSM caveats, and hydrodynamic boundaries |
| 11 | [phase_5_completion_report.md](file:///c:/AI/Rural_internship_project/docs/phase-5/phase_5_completion_report.md) | Executive summary, defense-ready talking points, and academic evaluation rubric alignment |

---

## 2. Core Service Deliverables

1. **Multi-Scenario Comparison Engine** (`app/services/scenario_comparison_service.py`):
   - Compares 5 operational scenarios: `SCEN-DRY-000` (Baseline Dry), `SCEN-MOD-001` (Moderate 25 mm/hr), `SCEN-HVY-002` (Heavy Storm 70 mm/hr), `SCEN-DRN-003` (Weir Surcharge), and `SCEN-DISR-004` (Storm + Road Severance).
   - Generates side-by-side matrices comparing mean risk, high-risk road edge percentages, severed road segments, at-risk facilities, and equipment demand deltas.

2. **Uncertainty & Sensitivity Service** (`app/services/uncertainty_service.py`):
   - One-At-a-Time (OAT) factor weight perturbation ($\pm 20\%$) with strict weight renormalization invariants ($\sum w_i = 1.0$).
   - Precipitation non-linear response curves across IMD thresholds ($0$ to $120\text{ mm/hr}$).
   - Missing-layer graceful degradation tests.
   - Routing risk penalty ($\lambda$) sensitivity analyzing distance vs flood avoidance trade-offs.

3. **Critical Infrastructure Vulnerability & Historical Consistency** (`app/services/vulnerability_service.py`):
   - Multi-criteria vulnerability score ($V \in [0, 100]$) for 65 mapped facilities:
     $$V = 0.35 R_{\text{geo}} + 0.25 S_{\text{flood\_prox}} + 0.20 S_{\text{drain\_prox}} + 0.20 S_{\text{access\_risk}}$$
   - Categorization into CRITICAL ($V \ge 70$), HIGH ($50 \le V < 70$), MODERATE ($30 \le V < 50$), and LOW ($V < 30$).
   - Feature F: Spatial agreement benchmark against 5 documented October 2020 flood evidence locations.

4. **Emergency Response Priority Engine** (`app/services/response_priority_service.py`):
   - Human-in-the-Loop decision scoring ($P \in [0, 100]$):
     $$P = 0.30 S_{\text{severity}} + 0.25 R_{\text{geo}} + 0.20 S_{\text{med\_prox}} + 0.15 S_{\text{road\_tier}} + 0.10 S_{\text{age}}$$
   - Natural-language explainable justification strings for every priority assignment.
   - Mandatory human operator authorization policy before any simulated or physical unit dispatch.

5. **REST API Extensions** (`app/api/main.py`):
   - `GET /api/v1/scenarios/compare`
   - `GET /api/v1/scenarios/sensitivity`
   - `GET /api/v1/infrastructure/vulnerability`
   - `GET /api/v1/incidents/priorities`
   - `GET /api/v1/analytics/summary`

6. **Dashboard Command Centre** (`app/dashboard/main.py`):
   - New dedicated navigation mode: **"Scenario Intelligence & Analytics"** with 4 interactive tabs.

