"""
AQUILA MVP - Backend & Integration Test Suite
Tests:
1. Application health endpoint.
2. Database connection and seeding.
3. Geospatial dataset loading.
4. Risk score calculation.
5. Risk category classification.
6. Incident creation.
7. Incident status updates.
8. Resource compatibility filtering.
9. Resource recommendation.
10. Scenario start, advance and reset.
11. Synthetic data labelling.
12. Audit history generation.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.api.main import app
from app.db.database import get_db, SessionLocal
from app.db.models import Incident, Resource, AuditHistory, RainfallObservation
from app.services.risk_engine import compute_geographic_risk, calculate_rainfall_score

client = TestClient(app)

# 1. Health Endpoint
def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "AQUILA MVP" in data["platform"]

# 2. Database Connection & Seed Check
def test_db_seeding():
    db = SessionLocal()
    resources = db.query(Resource).all()
    assert len(resources) >= 6
    audit_count = db.query(AuditHistory).count()
    assert audit_count > 0
    db.close()

# 3. Geospatial Dataset Loading
def test_geospatial_layers_endpoint():
    response = client.get("/api/layers")
    assert response.status_code == 200
    data = response.json()
    assert "roads" in data
    assert "study_area_bbox" in data
    assert data["roads"]["available"] is True
    assert data["roads"]["features_count"] > 5000

    # Test single layer fetch
    res_bbox = client.get("/api/layers/study_area_bbox")
    assert res_bbox.status_code == 200
    bbox_geo = res_bbox.json()
    assert bbox_geo["type"] == "FeatureCollection"

# 4. Risk Score Calculation
def test_risk_score_calculation():
    # Zero rainfall in low-vulnerability area
    low_risk = compute_geographic_risk(
        rainfall_rate_mm_hr=0.0,
        elevation_m=620.0,
        slope_degrees=15.0,
        distance_to_waterway_m=800.0,
        landcover_class=10,
        distance_to_flood_point_m=1500.0
    )
    assert low_risk["final_risk_score"] < 40.0
    assert low_risk["risk_category"] == "LOW"

    # Extreme rainfall in high-vulnerability area
    high_risk = compute_geographic_risk(
        rainfall_rate_mm_hr=85.0,
        elevation_m=505.0,
        slope_degrees=1.0,
        distance_to_waterway_m=30.0,
        landcover_class=50,
        distance_to_flood_point_m=100.0
    )
    assert high_risk["final_risk_score"] >= 70.0
    assert high_risk["risk_category"] == "HIGH"

# 5. Risk Category Classification Boundaries
def test_risk_classification_boundaries():
    assert calculate_rainfall_score(0.0) == 0.0
    assert calculate_rainfall_score(15.6) >= 40.0
    assert calculate_rainfall_score(64.5) >= 75.0
    assert calculate_rainfall_score(120.0) == 100.0

# 6. Incident Creation
def test_incident_creation():
    payload = {
        "title": "Puppalaguda Road Depression Waterlogging",
        "description": "0.40m standing water causing vehicular bottleneck.",
        "latitude": 17.4015,
        "longitude": 78.3750,
        "incident_type": "WATERLOGGING",
        "severity": "HIGH",
        "source_type": "REPORTED"
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "INC-" in data["incident_code"]
    assert data["status"] == "REPORTED"
    assert data["source_type"] == "REPORTED"
    assert data["title"] == payload["title"]

# 7. Incident Status Updates
def test_incident_status_update():
    # Create incident first
    payload = {
        "title": "Test Incident for Status Update",
        "description": "Test description",
        "latitude": 17.3920,
        "longitude": 78.3820,
        "incident_type": "ROAD_SEVERANCE",
        "severity": "MODERATE",
        "source_type": "REPORTED"
    }
    create_res = client.post("/api/incidents", json=payload)
    inc_id = create_res.json()["id"]

    # Update to UNDER_REVIEW
    patch_res = client.patch(f"/api/incidents/{inc_id}/status", json={"status": "UNDER_REVIEW"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "UNDER_REVIEW"

    # Update to RESOLVED
    patch_res2 = client.patch(f"/api/incidents/{inc_id}/status", json={"status": "RESOLVED"})
    assert patch_res2.status_code == 200
    assert patch_res2.json()["status"] == "RESOLVED"

# 8. Resource Compatibility Filtering & Listing
def test_resource_listing_and_filtering():
    res_all = client.get("/api/resources")
    assert res_all.status_code == 200
    resources = res_all.json()
    assert len(resources) >= 6

    # Filter by capability
    res_pump = client.get("/api/resources?capability=PUMPING")
    assert res_pump.status_code == 200
    pumps = res_pump.json()
    assert len(pumps) >= 2
    for p in pumps:
        assert "PUMPING" in p["capability"]

# 9. Emergency Resource Recommendation & Assignment
def test_resource_recommendation_and_assignment():
    # Create waterlogging incident
    payload = {
        "title": "Neknampur Culvert Flooding for Dispatch Test",
        "description": "Water overflowing culvert",
        "latitude": 17.3912,
        "longitude": 78.3845,
        "incident_type": "WATERLOGGING",
        "severity": "CRITICAL",
        "source_type": "REPORTED"
    }
    create_res = client.post("/api/incidents", json=payload)
    inc_id = create_res.json()["id"]

    # Request recommendation
    rec_res = client.post(f"/api/incidents/{inc_id}/recommend-resource")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "resource_code" in rec_data
    assert rec_data["assignment_status"] == "RECOMMENDED"
    assert rec_data["distance_km"] > 0
    res_id = rec_data["resource_id"]

    # Approve assignment
    assign_res = client.post(f"/api/incidents/{inc_id}/assign-resource", json={"resource_id": res_id})
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "ASSIGNED"

    # Verify incident status is now ASSIGNED
    inc_check = client.get(f"/api/incidents?status=ASSIGNED")
    assert any(inc["id"] == inc_id for inc in inc_check.json())

    # Release resource for subsequent tests
    client.patch(f"/api/incidents/{inc_id}/status", json={"status": "RESOLVED"})


# 10. Scenario Start, Step Advance, and Reset
def test_scenario_lifecycle():
    # Start scenario
    start_res = client.post("/api/scenarios/start")
    assert start_res.status_code == 200
    assert start_res.json()["is_active"] is True
    assert start_res.json()["current_step"] == 0

    # Advance steps up to step 3 (injects INC-SIM-001)
    client.post("/api/scenarios/advance")  # step 1
    client.post("/api/scenarios/advance")  # step 2
    step3_res = client.post("/api/scenarios/advance")  # step 3
    assert step3_res.status_code == 200
    assert step3_res.json()["current_step"] == 3
    assert "INC-SIM-001" in step3_res.json().get("generated_incidents", [])

    # Check simulated incident exists in database
    inc_sim = client.get("/api/incidents?source_type=SIMULATED")
    assert any(i["incident_code"] == "INC-SIM-001" for i in inc_sim.json())

    # Reset scenario
    reset_res = client.post("/api/scenarios/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "RESET_SUCCESSFUL"

    # Verify simulated incidents were purged
    inc_sim_after = client.get("/api/incidents?source_type=SIMULATED")
    assert len(inc_sim_after.json()) == 0

# 11. Synthetic Data Labelling Verification
def test_synthetic_data_labelling():
    # Start scenario and advance to inject simulated incident
    client.post("/api/scenarios/start")
    client.post("/api/scenarios/advance")
    client.post("/api/scenarios/advance")
    client.post("/api/scenarios/advance")

    db = SessionLocal()
    sim_inc = db.query(Incident).filter(Incident.incident_code == "INC-SIM-001").first()
    assert sim_inc is not None
    assert sim_inc.source_type == "SIMULATED"

    sim_rain = db.query(RainfallObservation).filter(RainfallObservation.source_type == "SIMULATED").first()
    assert sim_rain is not None
    assert sim_rain.is_synthetic is True
    db.close()

    # Reset to leave clean
    client.post("/api/scenarios/reset")

# 12. Audit History Generation
def test_audit_history_trail():
    audit_res = client.get("/api/audit-history")
    assert audit_res.status_code == 200
    records = audit_res.json()
    assert len(records) > 0
    actions = [r["action"] for r in records]
    assert any("CREATED" in a or "STATUS_UPDATED" in a or "SCENARIO" in a for a in actions)

# 13. Risk Engine Missing Data & Renormalization
def test_risk_missing_data_renormalization():
    # Pass None for terrain and historical
    result = compute_geographic_risk(
        rainfall_rate_mm_hr=40.0,
        elevation_m=None,
        slope_degrees=None,
        distance_to_waterway_m=100.0,
        landcover_class=50,
        distance_to_flood_point_m=None
    )
    assert result["final_risk_score"] > 0
    assert "terrain" in result["missing_components"]
    assert "historical" in result["missing_components"]
    assert sum(result["weights_applied"].values()) == pytest.approx(0.70, 0.01)

# 14. Input Validation & Error Handling
def test_input_validation_errors():
    # Out of bounds coordinates (e.g., latitude 99.0)
    bad_coords = {
        "title": "Invalid Coords Test",
        "latitude": 99.0,
        "longitude": 78.38,
        "incident_type": "WATERLOGGING",
        "severity": "MODERATE"
    }
    res_bad_coords = client.post("/api/incidents", json=bad_coords)
    assert res_bad_coords.status_code == 422

    # Invalid status value
    res_bad_status = client.patch("/api/incidents/1/status", json={"status": "INVALID_STATUS_FOO"})
    assert res_bad_status.status_code == 400

# 15. Duplicate Resource Assignment Prevention
def test_duplicate_resource_assignment_prevention():
    # Create two distinct incidents
    inc1 = client.post("/api/incidents", json={
        "title": "Conflict Incident 1",
        "latitude": 17.395,
        "longitude": 78.385,
        "incident_type": "WATERLOGGING",
        "severity": "HIGH"
    }).json()

    inc2 = client.post("/api/incidents", json={
        "title": "Conflict Incident 2",
        "latitude": 17.396,
        "longitude": 78.386,
        "incident_type": "WATERLOGGING",
        "severity": "HIGH"
    }).json()

    # Recommend resource for inc1
    rec = client.post(f"/api/incidents/{inc1['id']}/recommend-resource").json()
    res_id = rec["resource_id"]

    # Assign resource to inc1
    assign1 = client.post(f"/api/incidents/{inc1['id']}/assign-resource", json={"resource_id": res_id})
    assert assign1.status_code == 200

    # Attempt to assign the SAME resource to inc2 while still assigned -> Should fail with 400
    assign2 = client.post(f"/api/incidents/{inc2['id']}/assign-resource", json={"resource_id": res_id})
    assert assign2.status_code == 400
    assert "already deployed" in assign2.json()["detail"]

    # Resolve inc1 -> Should release resource back to AVAILABLE
    client.patch(f"/api/incidents/{inc1['id']}/status", json={"status": "RESOLVED"})

    # Now assigning to inc2 should succeed
    assign2_retry = client.post(f"/api/incidents/{inc2['id']}/assign-resource", json={"resource_id": res_id})
    assert assign2_retry.status_code == 200
    client.patch(f"/api/incidents/{inc2['id']}/status", json={"status": "RESOLVED"})

# 16. Scenario Deterministic Reproducibility
def test_scenario_deterministic_twice():
    # Run 1
    client.post("/api/scenarios/start")
    client.post("/api/scenarios/advance")  # step 1
    client.post("/api/scenarios/advance")  # step 2
    r1_step3 = client.post("/api/scenarios/advance").json()  # step 3
    assert r1_step3["current_step"] == 3
    assert "INC-SIM-001" in r1_step3.get("generated_incidents", [])
    client.post("/api/scenarios/reset")

    # Run 2
    client.post("/api/scenarios/start")
    client.post("/api/scenarios/advance")
    client.post("/api/scenarios/advance")
    r2_step3 = client.post("/api/scenarios/advance").json()
    assert r2_step3["current_step"] == 3
    assert "INC-SIM-001" in r2_step3.get("generated_incidents", [])
    client.post("/api/scenarios/reset")


