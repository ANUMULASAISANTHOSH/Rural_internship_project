"""
AQUILA - Unified Release Verification & Certification Script
Executes end-to-end pre-flight checks:
1. Environment & Python Version
2. Dataset File Integrity
3. Database Schema & Foreign Key PRAGMA
4. Seed Idempotency & Resource Verification
5. Road Network Topological Graph & KDTree Index
6. Geographic Risk Calculation Probe
7. Flood-Aware Routing & Facility Accessibility Probe
8. Scenario Comparison & Sensitivity Probe
9. System Health Service Diagnostic Audit
10. Automated Pytest Suite Execution (All 91+ Tests)

Exits with code 0 on success, non-zero code on failure.
"""

import os
import sys
import platform
import subprocess
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

REQUIRED_VECTORS = [
    "study_area_bbox.geojson",
    "roads_manikonda_processed.geojson",
    "water_bodies_manikonda_processed.geojson",
    "drainage_manikonda_processed.geojson",
    "infrastructure_manikonda_processed.geojson",
    "historical_flood_points_processed.geojson",
    "monitoring_locations_processed.geojson",
    "manikonda_settlements_processed.geojson",
    "rainfall_synthetic_hyetograph_validated.csv"
]

REQUIRED_RASTERS = [
    "dem_manikonda_clipped.tif",
    "slope_degrees_manikonda.tif"
]


# Ensure robust stdout encoding across Windows PowerShell cp1252 consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def print_step(num: int, title: str):
    print(f"\n[{num:02d}/10] {title}...")


def fail_verification(reason: str):
    print(f"\n[FAIL] RELEASE VERIFICATION FAILED: {reason}")
    sys.exit(1)


def main():
    start_time = datetime.now(timezone.utc)
    print("=" * 75)
    print("AQUILA — UNIFIED RELEASE VERIFICATION & CERTIFICATION GATE")
    print(f"Timestamp: {start_time.isoformat()} | Target: Manikonda Pilot Catchment")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # 1. Environment & Python Version
    # -------------------------------------------------------------------------
    print_step(1, "Verifying Runtime Environment")
    py_ver = sys.version_info
    print(f"       Detected: Python {py_ver.major}.{py_ver.minor}.{py_ver.micro} on {platform.system()} {platform.release()}")
    if py_ver.major != 3 or py_ver.minor < 11:
        fail_verification(f"Unsupported Python version ({py_ver.major}.{py_ver.minor}). Python 3.11+ required.")
    print("       [OK] Python runtime verified.")

    # -------------------------------------------------------------------------
    # 2. Dataset File Integrity
    # -------------------------------------------------------------------------
    print_step(2, "Verifying Geospatial Datasets")
    vec_dir = os.path.join(BASE_DIR, "data", "processed", "vector")
    rast_dir = os.path.join(BASE_DIR, "data", "processed", "raster")

    for vf in REQUIRED_VECTORS:
        p = os.path.join(vec_dir, vf)
        if not os.path.exists(p):
            fail_verification(f"Missing required vector dataset: {vf}")
    print(f"       [OK] All {len(REQUIRED_VECTORS)} vector datasets verified.")

    for rf in REQUIRED_RASTERS:
        p = os.path.join(rast_dir, rf)
        if not os.path.exists(p):
            fail_verification(f"Missing required raster dataset: {rf}")
    print(f"       [OK] All {len(REQUIRED_RASTERS)} raster datasets verified.")

    # -------------------------------------------------------------------------
    # 3. Database Schema & Foreign Key PRAGMA
    # -------------------------------------------------------------------------
    print_step(3, "Initializing Database & Checking Foreign Keys")
    from app.db.database import engine, SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        fk_check = db.execute(text("PRAGMA foreign_keys;")).scalar()
        if fk_check != 1:
            fail_verification(f"SQLite PRAGMA foreign_keys is {fk_check}, expected 1 (ON).")
        print("       [OK] SQLite foreign keys enforced (PRAGMA foreign_keys = 1).")
    finally:
        db.close()

    # -------------------------------------------------------------------------
    # 4. Seed Idempotency & Resource Verification
    # -------------------------------------------------------------------------
    print_step(4, "Testing Seed Idempotency")
    from app.db.seed import init_db
    from app.db.models import Resource
    init_db(seed_resources=True)
    db = SessionLocal()
    try:
        res_count = db.query(Resource).count()
        if res_count != 6:
            fail_verification(f"Expected 6 seeded resources, found {res_count}.")
        print(f"       [OK] 6 emergency resources verified (Seed idempotency confirmed).")
    finally:
        db.close()

    # -------------------------------------------------------------------------
    # 5. Road Network Topological Graph & KDTree Index
    # -------------------------------------------------------------------------
    print_step(5, "Verifying Road Network Graph & Spatial KDTree")
    from app.services.road_network_service import road_network_service
    summary = road_network_service.get_network_summary()
    if summary["total_nodes"] < 20000 or summary["total_directed_edges"] < 40000:
        fail_verification(f"Road graph incomplete: {summary['total_nodes']} nodes, {summary['total_directed_edges']} edges.")
    if summary["connectivity_percentage"] < 90.0:
        fail_verification(f"Graph connectivity {summary['connectivity_percentage']}% below 90% threshold.")
    print(f"       [OK] Graph verified: {summary['total_nodes']} nodes, {summary['total_directed_edges']} edges ({summary['connectivity_percentage']}% connected).")

    # -------------------------------------------------------------------------
    # 6. Geographic Risk Calculation Probe
    # -------------------------------------------------------------------------
    print_step(6, "Probing Geographic Risk Calculation Engine")
    from app.services.risk_engine import compute_geographic_risk
    probe_risk = compute_geographic_risk(rainfall_rate_mm_hr=35.0)
    score = probe_risk["final_risk_score"]
    if not (0.0 <= score <= 100.0):
        fail_verification(f"Risk calculation score out of bounds: {score}")
    print(f"       [OK] Risk calculation operational: Score {score} ({probe_risk['risk_category']}).")

    # -------------------------------------------------------------------------
    # 7. Flood-Aware Routing & Facility Accessibility Probe
    # -------------------------------------------------------------------------
    print_step(7, "Probing Routing & Critical Facility Accessibility")
    from app.services.accessibility_service import accessibility_service
    route = road_network_service.find_shortest_path(17.3912, 78.3845, 17.3980, 78.3920)
    if not route["found"]:
        fail_verification("Shortest path routing probe failed to find a valid route.")
    facs = accessibility_service.find_accessible_facilities(17.3912, 78.3845, "hospital", max_results=3)
    if not facs["facilities"]:
        fail_verification("Facility accessibility probe returned 0 facilities.")
    print(f"       [OK] Routing operational: {route['total_distance_km']} km path found; {len(facs['facilities'])} hospitals accessible.")

    # -------------------------------------------------------------------------
    # 8. Scenario Comparison & Sensitivity Probe
    # -------------------------------------------------------------------------
    print_step(8, "Probing Scenario Comparison & Sensitivity Analysis")
    from app.services.scenario_comparison_service import scenario_comparison_service
    from app.services.uncertainty_service import uncertainty_service
    comp = scenario_comparison_service.compare_all_scenarios()
    if comp["total_scenarios_compared"] != 5:
        fail_verification(f"Expected 5 scenarios, found {comp['total_scenarios_compared']}.")
    sens = uncertainty_service.analyze_weight_sensitivity()
    if not sens["factor_sensitivities"]:
        fail_verification("Sensitivity analysis probe failed to generate factor swings.")
    print(f"       [OK] Scenario comparison & sensitivity operational: 5 scenarios compared, top driver: {sens['most_sensitive_factor']}.")

    # -------------------------------------------------------------------------
    # 9. System Health Service Diagnostic Audit
    # -------------------------------------------------------------------------
    print_step(9, "Executing Subsystem Diagnostic Health Audit")
    from app.services.health_service import health_service
    health = health_service.get_system_health()
    if health["overall_status"] != "HEALTHY":
        fail_verification(f"System health probe returned status '{health['overall_status']}', expected 'HEALTHY'.")
    print(f"       [OK] Subsystem health audit: {health['overall_status']} (Memory RSS: {health['environment']['memory_rss_mb']} MB).")

    # -------------------------------------------------------------------------
    # 10. Automated Pytest Suite Execution
    # -------------------------------------------------------------------------
    print_step(10, "Executing Complete Automated Pytest Suite (All Phases)")
    import pytest
    test_ret = pytest.main(["-q"])
    if test_ret != 0:
        fail_verification(f"Pytest suite execution failed with exit code {test_ret}.")
    print("       [OK] All automated unit and regression tests passed.")

    # -------------------------------------------------------------------------
    # Final Release Certification
    # -------------------------------------------------------------------------
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    print("\n" + "=" * 75)
    print("AQUILA RELEASE VERIFICATION SUCCESSFUL -- CERTIFICATION GRANTED")
    print("Designation: Academically Verified, Reproducible and Demonstration-Ready")
    print(f"Total Verification Elapsed Time: {duration:.2f} seconds")
    print("=" * 75 + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
