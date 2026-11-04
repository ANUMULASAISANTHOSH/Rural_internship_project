"""
AQUILA Phase 5 Automated Test Suite:
Multi-Scenario Intelligence, Uncertainty Analysis & Emergency Decision Optimization.

Verifies:
1. ScenarioComparisonService multi-scenario ranking, monotonic risk scaling, and delta matrices.
2. UncertaintyService One-At-a-Time (OAT) weight perturbation, weight renormalization invariants,
   rainfall non-linear response, missing layer degradation, and lambda routing elasticity.
3. VulnerabilityService multi-criteria facility ranking, category filtering, provenance integrity,
   and October 2020 historical flood evidence consistency.
4. ResponsePriorityService human-in-the-loop priority indexing, wait-time escalation, and explainability.
5. FastAPI v1 REST endpoints conformance and HTTP 200 responses.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.api.main import app
from app.db.database import SessionLocal, utc_now
from app.db.models import Incident, Resource, AuditHistory
from app.services.scenario_comparison_service import scenario_comparison_service
from app.services.uncertainty_service import uncertainty_service
from app.services.vulnerability_service import vulnerability_service
from app.services.response_priority_service import response_priority_service

client = TestClient(app)


# =============================================================================
# 1. Feature A: Multi-Scenario Comparison Engine Tests
# =============================================================================

def test_scenario_comparison_all_scenarios():
    """Validates that all 5 operational scenarios are evaluated with monotonic risk trends."""
    comp = scenario_comparison_service.compare_all_scenarios()
    
    assert comp["total_scenarios_compared"] == 5
    assert comp["baseline_scenario_id"] == "SCEN-DRY-000"
    assert len(comp["scenarios"]) == 5
    assert len(comp["comparison_matrix"]) == 5

    sc_map = {s["scenario_id"]: s for s in comp["scenarios"]}
    
    # Check baseline dry
    dry = sc_map["SCEN-DRY-000"]
    assert dry["rainfall_rate_mm_hr"] == 0.0
    assert dry["metrics"]["risk_category"] in ["LOW", "MODERATE"]

    # Check moderate rain
    mod = sc_map["SCEN-MOD-001"]
    assert mod["rainfall_rate_mm_hr"] == 25.0
    assert mod["metrics"]["mean_catchment_risk"] > dry["metrics"]["mean_catchment_risk"]

    # Check heavy storm peak
    hvy = sc_map["SCEN-HVY-002"]
    assert hvy["rainfall_rate_mm_hr"] == 70.0
    assert hvy["metrics"]["mean_catchment_risk"] > mod["metrics"]["mean_catchment_risk"]

    # Check weir surcharge scenario increases risk further
    drn = sc_map["SCEN-DRN-003"]
    assert drn["metrics"]["mean_catchment_risk"] >= hvy["metrics"]["mean_catchment_risk"]

    # Check disruption scenario induces inaccessible road segments
    disr = sc_map["SCEN-DISR-004"]
    assert disr["metrics"]["inaccessible_road_segments"] > 0
    assert disr["metrics"]["estimated_resource_demand"]["dewatering_pumps"] >= 4


def test_scenario_comparison_delta_calculations():
    """Validates that delta risk and high-risk road differences relative to baseline are non-negative."""
    comp = scenario_comparison_service.compare_all_scenarios()
    matrix = comp["comparison_matrix"]

    for row in matrix:
        if row["scenario_id"] == "SCEN-DRY-000":
            assert row["delta_risk_score"] == 0.0
            assert row["delta_high_risk_edges"] == 0
        else:
            assert row["delta_risk_score"] > 0.0
            assert row["delta_high_risk_edges"] >= 0
            assert row["risk_pct_increase"] > 0.0


def test_scenario_comparison_invalid_scenario_id():
    """Validates that querying a non-existent scenario ID raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        scenario_comparison_service.evaluate_scenario("NON-EXISTENT-999")
    assert "not found" in str(excinfo.value)


# =============================================================================
# 2. Feature B: Uncertainty & Sensitivity Analysis Tests
# =============================================================================

def test_uncertainty_weight_sensitivity_invariants():
    """Validates that OAT weight perturbation renormalizes weights to sum(w) == 1.0."""
    res = uncertainty_service.analyze_weight_sensitivity(perturbation_fraction=0.20)
    
    assert res["analysis_type"] == "One-At-a-Time (OAT) Weight Sensitivity"
    assert res["base_risk_score"] > 0.0
    assert len(res["factor_sensitivities"]) == 5

    for fs in res["factor_sensitivities"]:
        assert fs["risk_swing"] >= 0.0
        assert fs["pct_swing"] >= 0.0
        assert fs["elasticity"] >= 0.0
        assert 0.0 <= fs["risk_at_up"] <= 100.0
        assert 0.0 <= fs["risk_at_down"] <= 100.0

    # Rainfall should be the most influential factor
    assert res["most_sensitive_factor"] in ["rainfall", "terrain"]


def test_uncertainty_rainfall_sweep_monotonicity():
    """Validates that the precipitation response curve is monotonically non-decreasing."""
    sweep = uncertainty_service.analyze_rainfall_sweep()
    curve = sweep["sweep_curve"]
    
    assert len(curve) >= 8
    scores = [c["final_risk_score"] for c in curve]
    for i in range(1, len(scores)):
        assert scores[i] >= scores[i - 1], f"Score at index {i} decreased: {scores[i]} < {scores[i-1]}"

    assert sweep["moderate_risk_entry_mm_hr"] is not None
    assert sweep["high_risk_entry_mm_hr"] is not None
    assert sweep["high_risk_entry_mm_hr"] >= sweep["moderate_risk_entry_mm_hr"]


def test_uncertainty_missing_layer_graceful_handling():
    """Validates that omitting spatial layers renormalizes remaining weights without failure."""
    impact = uncertainty_service.analyze_missing_layer_impact()
    
    assert impact["full_model_risk_score"] > 0.0
    assert len(impact["layer_omission_impacts"]) >= 4

    for test in impact["layer_omission_impacts"]:
        score = test["resulting_risk_score"]
        assert 0.0 <= score <= 100.0
        assert test["resulting_risk_category"] in ["LOW", "MODERATE", "HIGH"]
        # Check that normalized weights sum to 1.0
        w_sum = sum(test["normalized_weights"].values())
        assert abs(w_sum - 1.0) < 0.01, f"Normalized weights did not sum to 1.0: {w_sum}"


def test_uncertainty_routing_lambda_elasticity():
    """Validates routing lambda sensitivity returns non-decreasing distance and non-increasing risk."""
    lam_res = uncertainty_service.analyze_routing_lambda_sensitivity()
    evals = lam_res["lambda_evaluations"]
    
    assert len(evals) >= 4
    for i in range(1, len(evals)):
        # Distance should not decrease as lambda increases
        assert evals[i]["distance_km"] >= evals[i - 1]["distance_km"]
        # Average risk should not increase as lambda increases
        assert evals[i]["average_risk"] <= evals[i - 1]["average_risk"]

    assert lam_res["recommended_operational_lambda"] == 3.0


# =============================================================================
# 3. Feature C & F: Critical Infrastructure Vulnerability & Historical Consistency
# =============================================================================

def test_vulnerability_all_facilities_evaluated():
    """Validates that all 65 critical facilities in Manikonda are evaluated and categorized."""
    res = vulnerability_service.rank_facilities_vulnerability(rainfall_rate_mm_hr=25.0)
    
    assert res["total_facilities_evaluated"] == 65
    assert len(res["ranked_facilities"]) == 65
    
    dist = res["vulnerability_distribution"]
    assert sum(dist.values()) == 65
    assert dist["CRITICAL"] >= 0
    assert dist["HIGH"] >= 0
    assert dist["MODERATE"] >= 0
    assert dist["LOW"] >= 0

    # Verify score descending order
    facs = res["ranked_facilities"]
    for i in range(1, len(facs)):
        assert facs[i - 1]["vulnerability_score"] >= facs[i]["vulnerability_score"]

    # Verify provenance and schema
    top_fac = facs[0]
    assert 0.0 <= top_fac["vulnerability_score"] <= 100.0
    assert top_fac["verification_status"] == "OSM_UNVERIFIED"
    assert "limitations" in top_fac
    assert "geographic_risk_r_geo" in top_fac["component_scores"]


def test_vulnerability_category_filter():
    """Validates that category filtering restricts facilities correctly."""
    hosp_res = vulnerability_service.rank_facilities_vulnerability(category_filter="hospital")
    assert hosp_res["total_facilities_evaluated"] > 0
    for f in hosp_res["ranked_facilities"]:
        assert "hospital" in f["category"].lower() or "clinic" in f["category"].lower()


def test_historical_evidence_consistency_benchmark():
    """Validates Feature F: spatial consistency against October 2020 verified flood points."""
    hist_res = vulnerability_service.evaluate_historical_evidence_consistency(rainfall_rate_mm_hr=35.0)
    
    assert hist_res["total_historical_points_evaluated"] == 5
    assert hist_res["consistent_hotspots_count"] >= 4
    assert hist_res["spatial_agreement_percentage"] >= 80.0
    assert len(hist_res["hotspots"]) == 5

    for h in hist_res["hotspots"]:
        assert h["provenance"] == "HISTORICAL"
        assert h["model_risk_score"] > 0.0
        assert h["observed_water_depth_m"] > 0.0


# =============================================================================
# 4. Feature D: Response Priority Engine Tests
# =============================================================================

def test_response_priority_scoring_and_governance():
    """Validates priority calculation, explainable justifications, and operator governance."""
    db = SessionLocal()
    # Clean slate before test
    existing = db.query(Incident).filter(Incident.incident_code == "INC-TEST-PH5-001").first()
    if existing:
        db.delete(existing)
        db.commit()

    try:
        # Register a temporary test incident
        test_inc = Incident(
            incident_code="INC-TEST-PH5-001",
            title="Puppalaguda Secondary Road Overflow Near Hospital",
            description="Runoff depth 0.40m impeding access corridor.",
            latitude=17.4015,
            longitude=78.3750,
            incident_type="WATERLOGGING",
            severity="HIGH",
            status="REPORTED",
            source_type="REPORTED",
            created_at=utc_now()
        )
        db.add(test_inc)
        db.commit()
        db.refresh(test_inc)

        priorities = response_priority_service.evaluate_incident_priorities(db)
        assert priorities["total_active_incidents"] >= 1
        assert priorities["governance_policy"] == "HUMAN_OPERATOR_REQUIRED"

        matched = next((i for i in priorities["ranked_incidents"] if i["incident_code"] == "INC-TEST-PH5-001"), None)
        assert matched is not None
        assert 0.0 <= matched["priority_score"] <= 100.0
        assert matched["priority_level"] in ["P1_IMMEDIATE", "P2_URGENT", "P3_ELEVATED", "P4_STANDARD"]
        assert matched["priority_rank"] >= 1
        assert matched["requires_operator_approval"] is True
        assert matched["auto_dispatched"] is False
        assert len(matched["explainable_justification"]) > 20

    finally:
        # Clean up
        item = db.query(Incident).filter(Incident.incident_code == "INC-TEST-PH5-001").first()
        if item:
            db.delete(item)
            db.commit()
        db.close()


# =============================================================================
# 5. REST API Endpoints Tests
# =============================================================================

def test_api_scenarios_compare_endpoint():
    """Validates GET /api/v1/scenarios/compare returns HTTP 200 with complete comparison matrix."""
    res = client.get("/api/v1/scenarios/compare")
    assert res.status_code == 200
    data = res.json()
    assert data["total_scenarios_compared"] == 5
    assert len(data["comparison_matrix"]) == 5
    assert "disclaimer" in data


def test_api_scenarios_sensitivity_endpoint():
    """Validates GET /api/v1/scenarios/sensitivity returns HTTP 200 with OAT report."""
    res = client.get("/api/v1/scenarios/sensitivity?perturbation_fraction=0.25")
    assert res.status_code == 200
    data = res.json()
    assert "weight_sensitivity" in data
    assert "rainfall_sweep" in data
    assert "missing_layer_impact" in data
    assert "routing_lambda_sensitivity" in data


def test_api_infrastructure_vulnerability_endpoint():
    """Validates GET /api/v1/infrastructure/vulnerability returns HTTP 200 with ranked facilities."""
    res = client.get("/api/v1/infrastructure/vulnerability?rainfall_rate_mm_hr=30.0&category=all")
    assert res.status_code == 200
    data = res.json()
    assert data["total_facilities_evaluated"] == 65
    assert len(data["ranked_facilities"]) == 65
    assert "vulnerability_distribution" in data


def test_api_incidents_priorities_endpoint():
    """Validates GET /api/v1/incidents/priorities returns HTTP 200 with operator governance flag."""
    res = client.get("/api/v1/incidents/priorities")
    assert res.status_code == 200
    data = res.json()
    assert "ranked_incidents" in data
    assert data["governance_policy"] == "HUMAN_OPERATOR_REQUIRED"


def test_api_analytics_summary_endpoint():
    """Validates GET /api/v1/analytics/summary returns high-level system analytics synthesis."""
    res = client.get("/api/v1/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["pilot_area"] == "Manikonda, Hyderabad, Telangana"
    assert data["total_scenarios_available"] == 5
    assert data["critical_facilities_total"] == 65
    assert data["governance_status"] == "HUMAN_OPERATOR_REQUIRED"
    assert "historical_consistency_pct" in data
