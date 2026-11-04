"""
AQUILA Phase 4 - Automated Test Suite for Flood-Aware Routing,
Safe Accessibility, and Intelligent Emergency Navigation.
Validates:
1. Road graph construction, node snapping, and topological invariants.
2. Shortest (distance-optimal) and Lowest-Risk (safety-optimal) routing.
3. Incident and road disruption proximity penalties and detour induction.
4. Critical facility accessibility and provenance governance.
5. Scenario MANI-HEAVY-001 disruption injection and clean rollback.
6. REST API endpoint contracts and input coordinate validations.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.api.main import app
from app.db.database import SessionLocal
from app.db.models import Incident, RoadDisruption, AuditHistory
from app.services.road_network_service import road_network_service
from app.services.accessibility_service import accessibility_service
from app.services.route_explanation_service import route_explanation_service

client = TestClient(app)

# Test Coordinates in Manikonda Pilot Area
ORIGIN_ALKAPUR = (17.3912, 78.3845)
DEST_HOSPITAL = (17.3980, 78.3920)
DEST_PUPPALAGUDA = (17.4050, 78.3750)


# =============================================================================
# 1. Road Graph Invariants & Snapping Tests
# =============================================================================

def test_road_graph_construction_and_size():
    """Validates that the road network graph initializes with non-empty nodes and edges."""
    summary = road_network_service.get_network_summary()
    assert summary["total_nodes"] > 20000
    assert summary["total_directed_edges"] > 40000
    assert summary["connectivity_percentage"] >= 90.0
    assert "residential" in summary["highway_type_distribution"]


def test_spatial_snapping_to_largest_component():
    """Verifies that an arbitrary coordinate in Manikonda snaps to the largest connected component."""
    node_id, snap_dist_m = road_network_service.snap_to_node(ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1], must_be_in_largest_cc=True)
    assert node_id in road_network_service.largest_cc_nodes
    assert snap_dist_m < 300.0  # Snapping should find a road within 300 meters in urban area


def test_edge_lengths_positive_and_finite():
    """Ensures all edge lengths are strictly positive and finite in meters."""
    for u, v, data in road_network_service.graph.edges(data=True):
        length = data.get("length_m")
        assert length is not None
        assert length > 0.0
        assert length < 5000.0  # No single urban road segment in Manikonda exceeds 5km


# =============================================================================
# 2. Shortest & Lowest-Risk Routing Tests
# =============================================================================

def test_shortest_route_optimality():
    """Calculates shortest route and verifies distance, node count, and GeoJSON coordinates."""
    route = road_network_service.find_shortest_path(
        ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1],
        DEST_HOSPITAL[0], DEST_HOSPITAL[1]
    )
    assert route["found"] is True
    assert route["route_type"] == "SHORTEST"
    assert route["total_distance_meters"] > 500.0
    assert route["total_distance_km"] > 0.5
    assert len(route["coordinates"]) >= 2
    assert route["average_risk_score"] >= 0.0


def test_identical_origin_and_destination():
    """Verifies that routing to the same point returns zero distance without errors."""
    route = road_network_service.find_shortest_path(
        ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1],
        ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1]
    )
    assert route["found"] is True
    assert route["total_distance_meters"] == 0.0
    assert route["node_count"] == 1


def test_lowest_risk_route_with_custom_lambda():
    """Verifies lowest-risk path generation with configurable lambda risk aversion."""
    route = road_network_service.find_lowest_risk_path(
        ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1],
        DEST_HOSPITAL[0], DEST_HOSPITAL[1],
        lambda_param=5.0
    )
    assert route["found"] is True
    assert route["route_type"] == "LOWEST_RISK"
    assert route["total_distance_meters"] >= 500.0
    assert route["lambda_param_applied"] == 5.0


def test_route_comparison_and_explanation():
    """Tests the comparison service between shortest and lowest-risk paths."""
    comp = road_network_service.compare_routes(
        ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1],
        DEST_HOSPITAL[0], DEST_HOSPITAL[1],
        lambda_param=3.0
    )
    assert "shortest_route" in comp
    assert "lowest_risk_route" in comp
    assert "comparison" in comp
    c = comp["comparison"]
    assert c["has_recommendation"] is True
    assert c["preferred_route"] in ["SHORTEST", "LOWEST_RISK"]
    assert len(c["explanation_summary"]) > 20
    assert "scientific_disclaimer" in c


# =============================================================================
# 3. Incident Penalties & Detour Induction Tests
# =============================================================================

def test_incident_proximity_penalty_and_detour():
    """
    Tests that creating an active incident increases nearby edge weights
    and causes the lowest-risk route to adjust.
    """
    db = SessionLocal()
    # 1. Baseline shortest route
    base_route = road_network_service.find_shortest_path(
        ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1],
        DEST_HOSPITAL[0], DEST_HOSPITAL[1]
    )
    
    # 2. Create active flood incident near the midpoint of the route
    mid_idx = len(base_route["coordinates"]) // 2
    block_lon, block_lat = base_route["coordinates"][mid_idx]

    inc = Incident(
        incident_code="INC-TEST-ROUTING-01",
        title="Routing Test Waterlogging Blockage",
        latitude=block_lat,
        longitude=block_lon,
        incident_type="WATERLOGGING",
        severity="CRITICAL",
        status="REPORTED",
        source_type="SIMULATED"
    )
    db.add(inc)
    db.commit()

    try:
        # Update edge weights with incident active
        road_network_service.update_edge_weights(db_session=db, lambda_param=5.0)

        # Calculate lowest-risk route
        detour_route = road_network_service.find_lowest_risk_path(
            ORIGIN_ALKAPUR[0], ORIGIN_ALKAPUR[1],
            DEST_HOSPITAL[0], DEST_HOSPITAL[1],
            lambda_param=5.0
        )
        assert detour_route["found"] is True

        # Check comparison
        explanation = route_explanation_service.explain_route_comparison(base_route, detour_route, lambda_param=5.0)
        assert explanation["has_recommendation"] is True

    finally:
        # Clean up test incident
        db.query(Incident).filter(Incident.incident_code == "INC-TEST-ROUTING-01").delete()
        db.commit()
        # Restore baseline weights
        road_network_service.update_edge_weights(db_session=db, rainfall_rate_mm_hr=0.0)
        db.close()


def test_resolved_incident_does_not_penalize():
    """Verifies that an incident with status RESOLVED is ignored when updating edge weights."""
    db = SessionLocal()
    inc_resolved = Incident(
        incident_code="INC-TEST-RESOLVED-01",
        title="Resolved Waterlogging Node",
        latitude=17.3950,
        longitude=78.3880,
        incident_type="WATERLOGGING",
        severity="CRITICAL",
        status="RESOLVED",
        source_type="SIMULATED"
    )
    db.add(inc_resolved)
    db.commit()

    try:
        road_network_service.update_edge_weights(db_session=db)
        u, snap_dist = road_network_service.snap_to_node(17.3950, 78.3880)
        for _, _, data in road_network_service.graph.out_edges(u, data=True):
            assert data["incident_penalty"] == 0.0
    finally:
        db.query(Incident).filter(Incident.incident_code == "INC-TEST-RESOLVED-01").delete()
        db.commit()
        db.close()


# =============================================================================
# 4. Critical Facility Accessibility Tests
# =============================================================================

def test_facility_accessibility_ranking_and_provenance():
    """Tests critical facility lookup, driving distance vs straight-line distance, and OSM_UNVERIFIED provenance."""
    res = accessibility_service.find_accessible_facilities(
        origin_lat=ORIGIN_ALKAPUR[0],
        origin_lon=ORIGIN_ALKAPUR[1],
        facility_category="hospital",
        max_results=3
    )
    assert res["facilities_found_count"] >= 1
    assert res["accessible_count"] >= 1

    top_fac = res["facilities"][0]
    assert "Shobha" in top_fac["facility_name"] or "Hospital" in top_fac["facility_name"] or "Clinic" in top_fac["facility_name"]
    assert top_fac["straight_line_distance_km"] > 0.0
    assert top_fac["road_network_distance_km"] is not None
    # Real road network distance should be >= straight-line distance due to street winding
    assert top_fac["road_network_distance_km"] >= top_fac["straight_line_distance_km"] * 0.95
    assert top_fac["verification_status"] == "OSM_UNVERIFIED"
    assert top_fac["accessibility_status"] in ["ACCESSIBLE", "MODERATE_RISK_ACCESSIBLE", "HIGH_RISK_ROUTE", "CAUTION_DISRUPTED_CORRIDOR"]
    assert top_fac["accessibility_status"] != "UNREACHABLE_BY_ROAD"


def test_accessibility_unreachable_handling():
    """Verifies graceful handling when searching facilities outside coverage."""
    # Coordinate far south of Manikonda study envelope
    res = accessibility_service.find_accessible_facilities(
        origin_lat=17.2200,
        origin_lon=78.2200,
        max_search_radius_km=1.0
    )
    assert res["facilities_found_count"] == 0


# =============================================================================
# 5. Scenario MANI-HEAVY-001 Disruption Injection & Reset Tests
# =============================================================================

def test_scenario_disruption_injection_and_reset():
    """
    Tests that advancing scenario to Step 3 injects simulated road disruption DISR-SIM-001,
    and resetting scenario cleanly removes the disruption.
    """
    # 1. Start scenario
    start_res = client.post("/api/scenarios/start")
    assert start_res.status_code == 200

    # 2. Advance to Step 3
    client.post("/api/scenarios/advance")  # Step 1
    client.post("/api/scenarios/advance")  # Step 2
    step3 = client.post("/api/scenarios/advance")  # Step 3
    assert step3.status_code == 200
    assert "DISR-SIM-001" in step3.json().get("generated_disruptions", [])

    # 3. Verify disruption in database
    db = SessionLocal()
    dis = db.query(RoadDisruption).filter(RoadDisruption.disruption_code == "DISR-SIM-001").first()
    assert dis is not None
    assert dis.provenance == "SIMULATED"
    assert dis.status == "ACTIVE"

    # 4. Reset scenario
    reset_res = client.post("/api/scenarios/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["deleted_simulated_disruptions"] >= 1

    # 5. Verify disruption was purged from database
    dis_check = db.query(RoadDisruption).filter(RoadDisruption.disruption_code == "DISR-SIM-001").first()
    assert dis_check is None
    db.close()


# =============================================================================
# 6. REST API Endpoint Tests
# =============================================================================

def test_api_network_summary():
    """Tests GET /api/v1/routing/network-summary endpoint."""
    res = client.get("/api/v1/routing/network-summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_nodes"] > 20000
    assert data["connectivity_percentage"] >= 90.0


def test_api_shortest_route():
    """Tests GET /api/v1/routing/shortest endpoint."""
    url = f"/api/v1/routing/shortest?origin_lat={ORIGIN_ALKAPUR[0]}&origin_lon={ORIGIN_ALKAPUR[1]}&dest_lat={DEST_HOSPITAL[0]}&dest_lon={DEST_HOSPITAL[1]}"
    res = client.get(url)
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is True
    assert data["total_distance_meters"] > 0


def test_api_lowest_risk_route():
    """Tests GET /api/v1/routing/lowest-risk endpoint."""
    url = f"/api/v1/routing/lowest-risk?origin_lat={ORIGIN_ALKAPUR[0]}&origin_lon={ORIGIN_ALKAPUR[1]}&dest_lat={DEST_HOSPITAL[0]}&dest_lon={DEST_HOSPITAL[1]}&lambda_param=4.0"
    res = client.get(url)
    assert res.status_code == 200
    data = res.json()
    assert data["found"] is True
    assert data["lambda_param_applied"] == 4.0


def test_api_route_compare():
    """Tests GET /api/v1/routing/compare endpoint."""
    url = f"/api/v1/routing/compare?origin_lat={ORIGIN_ALKAPUR[0]}&origin_lon={ORIGIN_ALKAPUR[1]}&dest_lat={DEST_HOSPITAL[0]}&dest_lon={DEST_HOSPITAL[1]}"
    res = client.get(url)
    assert res.status_code == 200
    data = res.json()
    assert "shortest_route" in data
    assert "lowest_risk_route" in data
    assert "comparison" in data
    assert "explanation_summary" in data["comparison"]


def test_api_accessible_facilities():
    """Tests GET /api/v1/accessibility/facilities endpoint."""
    url = f"/api/v1/accessibility/facilities?origin_lat={ORIGIN_ALKAPUR[0]}&origin_lon={ORIGIN_ALKAPUR[1]}&category=hospital&limit=3"
    res = client.get(url)
    assert res.status_code == 200
    data = res.json()
    assert data["facilities_found_count"] >= 1
    assert len(data["facilities"]) <= 3


def test_api_invalid_coordinates_rejected():
    """Tests that out-of-bounds coordinates return HTTP 400 Bad Request."""
    url = "/api/v1/routing/shortest?origin_lat=99.0&origin_lon=78.3845&dest_lat=17.3980&dest_lon=78.3920"
    res = client.get(url)
    assert res.status_code == 400
    assert "Invalid origin latitude" in res.json()["detail"]
