"""
AQUILA Phase 6 Automated Test Suite:
Release Reliability, Database Integrity, API Security & Observability Diagnostics.

Verifies:
1. SQLite PRAGMA foreign_keys enforcement and referential integrity violations.
2. Transaction rollback isolation under simulated failure.
3. Seed script idempotency across repeated runs.
4. API sanitized error responses (zero filesystem path leakage).
5. Coordinate validation bounds rejection on routing endpoints.
6. Health diagnostic probes and subsystem readiness.
7. Scenario reset data isolation (purges SIMULATED while preserving OBSERVED/REPORTED).
8. Structured logger path sanitization.
"""

import os
import sys
import pytest
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.api.main import app
from app.db.database import SessionLocal, utc_now
from app.db.models import Incident, Resource, IncidentAssignment, AuditHistory, RainfallObservation
from app.db.seed import init_db
from app.services.health_service import health_service
from app.services.scenario_service import scenario_manager
from app.core.logging_config import StructuredFormatter
import logging

client = TestClient(app)


# =============================================================================
# 1. Database Reliability & Foreign Key Enforcement Tests
# =============================================================================

def test_sqlite_foreign_key_referential_integrity():
    """Validates that SQLite PRAGMA foreign_keys is active and rejects orphaned assignment records."""
    db = SessionLocal()
    try:
        # Attempt to insert an assignment referencing non-existent incident and resource
        invalid_asg = IncidentAssignment(
            incident_id=999999,
            resource_id=999999,
            recommendation_distance=1.5,
            assignment_status="ASSIGNED",
            created_at=utc_now()
        )
        db.add(invalid_asg)
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_database_transaction_rollback():
    """Validates that rolling back a transaction leaves the database state completely clean."""
    db = SessionLocal()
    unique_code = "INC-ROLLBACK-TEST"
    try:
        inc = Incident(
            incident_code=unique_code,
            title="Rollback Test Incident",
            latitude=17.4000,
            longitude=78.3800,
            incident_type="WATERLOGGING",
            severity="LOW",
            status="REPORTED",
            created_at=utc_now()
        )
        db.add(inc)
        # Explicit rollback before commit
        db.rollback()

        # Query should return None
        found = db.query(Incident).filter(Incident.incident_code == unique_code).first()
        assert found is None
    finally:
        db.close()


def test_seed_idempotency_repeated_execution():
    """Validates that executing init_db repeatedly is safe and does not duplicate resources."""
    # Run seed twice
    init_db(seed_resources=True)
    init_db(seed_resources=True)

    db = SessionLocal()
    try:
        res_count = db.query(Resource).count()
        assert res_count == 6
        # All resources should be AVAILABLE
        avail_count = db.query(Resource).filter(Resource.availability_status == "AVAILABLE").count()
        assert avail_count == 6
    finally:
        db.close()


# =============================================================================
# 2. API Security & Input Validation Tests
# =============================================================================

def test_api_sanitized_error_handling_no_path_leak():
    """Validates that requesting a non-existent layer returns 404 without leaking server paths."""
    res = client.get("/api/layers/secret_host_directory")
    assert res.status_code == 404
    detail = res.json().get("detail", "")
    assert "secret_host_directory" in detail
    assert "C:\\" not in detail
    assert "Rural_internship_project" not in detail
    assert "data\\processed" not in detail


def test_api_coordinate_validation_rejection():
    """Validates that routing endpoints reject coordinates outside the pilot catchment envelope."""
    # Latitude outside [17.20, 17.60]
    res_lat = client.get("/api/v1/routing/shortest?origin_lat=99.99&origin_lon=78.38&dest_lat=17.40&dest_lon=78.39")
    assert res_lat.status_code == 400
    assert "latitude" in res_lat.json()["detail"].lower()

    # Longitude outside [78.20, 78.60]
    res_lon = client.get("/api/v1/routing/shortest?origin_lat=17.40&origin_lon=10.00&dest_lat=17.40&dest_lon=78.39")
    assert res_lon.status_code == 400
    assert "longitude" in res_lon.json()["detail"].lower()


def test_api_risk_parameter_validation_bounds():
    """Validates that negative rainfall rate violates validation constraints."""
    res = client.get("/api/risk?rainfall_rate=-25.0")
    assert res.status_code == 422  # Pydantic validation error for ge=0.0


# =============================================================================
# 3. Observability & Health Service Tests
# =============================================================================

def test_health_service_probes_directly():
    """Validates that individual subsystem probes report HEALTHY status."""
    db_h = health_service.check_database()
    assert db_h["status"] == "HEALTHY"
    assert db_h["counts"]["resources"] == 6

    ds_h = health_service.check_datasets()
    assert ds_h["status"] == "HEALTHY"
    assert ds_h["missing_count"] == 0

    graph_h = health_service.check_road_graph()
    assert graph_h["status"] == "HEALTHY"
    assert graph_h["total_nodes"] > 20000
    assert graph_h["total_directed_edges"] > 40000

    risk_h = health_service.check_risk_engine()
    assert risk_h["status"] == "HEALTHY"


def test_api_health_endpoint_response_structure():
    """Validates that GET /health and /api/v1/health return complete diagnostic payloads."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "HEALTHY"
    assert "subsystems" in data
    assert "environment" in data
    assert data["version"] == "0.6.0"

    res_v1 = client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["overall_status"] == "HEALTHY"


# =============================================================================
# 4. Scenario Reset Isolation & Provenance Integrity Tests
# =============================================================================

def test_scenario_reset_data_isolation():
    """Validates that reset_scenario purges transient simulated records while preserving observed ones."""
    db = SessionLocal()
    # Clean slate for test codes
    for c in ["INC-REAL-PRESERVE-01", "INC-SIM-PURGE-01"]:
        existing = db.query(Incident).filter(Incident.incident_code == c).first()
        if existing:
            db.delete(existing)
    db.commit()

    try:
        # Ingest a real-like reported incident
        real_inc = Incident(
            incident_code="INC-REAL-PRESERVE-01",
            title="Real Field Reported Waterlogging",
            latitude=17.3950,
            longitude=78.3850,
            incident_type="WATERLOGGING",
            severity="HIGH",
            status="REPORTED",
            source_type="REPORTED",
            created_at=utc_now()
        )
        db.add(real_inc)

        # Ingest a simulated incident
        sim_inc = Incident(
            incident_code="INC-SIM-PURGE-01",
            title="Transient Simulated Downpour Overflow",
            latitude=17.3912,
            longitude=78.3845,
            incident_type="WATERLOGGING",
            severity="HIGH",
            status="REPORTED",
            source_type="SIMULATED",
            created_at=utc_now()
        )
        db.add(sim_inc)
        db.commit()

        # Execute scenario reset
        reset_res = scenario_manager.reset_scenario(db)
        assert reset_res["deleted_simulated_incidents"] >= 1

        # Assert real incident is preserved
        preserved = db.query(Incident).filter(Incident.incident_code == "INC-REAL-PRESERVE-01").first()
        assert preserved is not None

        # Assert simulated incident is purged
        purged = db.query(Incident).filter(Incident.incident_code == "INC-SIM-PURGE-01").first()
        assert purged is None

    finally:
        # Cleanup test records safely using ORM cascade
        for c in ["INC-REAL-PRESERVE-01", "INC-SIM-PURGE-01"]:
            item = db.query(Incident).filter(Incident.incident_code == c).first()
            if item:
                db.delete(item)
        db.commit()
        db.close()


def test_structured_logger_path_sanitization():
    """Validates that the logging formatter strips local host filesystem paths."""
    formatter = StructuredFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg=f"Error accessing file {BASE_DIR}\\data\\processed\\vector\\test.geojson",
        args=(),
        exc_info=None
    )
    record.component = "TEST_COMP"
    record.operation = "TEST_OP"

    formatted = formatter.format(record)
    assert BASE_DIR not in formatted
    assert "[TEST_COMP]" in formatted
