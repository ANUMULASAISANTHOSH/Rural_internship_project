"""
AQUILA Phase 6 - Empirical Performance Benchmarking Suite
Measures real computational latencies and memory consumption across core platform subsystems.
Outputs statistics (mean, median, min, max, p95) for release certification.
"""

import os
import sys
import time
import platform
import statistics
from typing import List, Dict, Any
import psutil

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def run_benchmarks() -> Dict[str, Any]:
    print("=" * 70)
    print("AQUILA EMPIRICAL PERFORMANCE BENCHMARKING SUITE")
    print("=" * 70)

    # 1. System Metadata
    mem = psutil.virtual_memory()
    sys_info = {
        "os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
        "processor": platform.processor(),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "total_ram_gb": round(mem.total / (1024**3), 2),
        "python_version": platform.python_version()
    }
    print(f"OS: {sys_info['os']}")
    print(f"CPU: {sys_info['processor']} ({sys_info['cpu_count_logical']} logical cores)")
    print(f"RAM: {sys_info['total_ram_gb']} GB")
    print(f"Python: {sys_info['python_version']}")
    print("-" * 70)

    results = {}

    # 2. Database Initialization Time
    from app.db.seed import init_db
    t0 = time.perf_counter()
    init_db(seed_resources=True)
    t_db = (time.perf_counter() - t0) * 1000.0
    results["db_initialization_ms"] = round(t_db, 2)
    print(f"1. Database Initialization (init_db): {t_db:.2f} ms")

    # 3. Road Network Graph & KDTree Construction
    from app.services.road_network_service import road_network_service
    # Service already singleton initialized, measure edge & node counts
    nodes_count = road_network_service.graph.number_of_nodes()
    edges_count = road_network_service.graph.number_of_edges()
    largest_cc = len(road_network_service.largest_cc_nodes)
    results["road_network"] = {
        "nodes": nodes_count,
        "edges": edges_count,
        "largest_cc_nodes": largest_cc,
        "connectivity_pct": round((largest_cc / max(1, nodes_count)) * 100, 1)
    }
    print(f"2. Road Graph Loaded: {nodes_count} nodes, {edges_count} edges (Largest CC: {largest_cc})")

    # 4. Risk Calculation Latency (1,000 repetitions)
    from app.services.risk_engine import compute_geographic_risk
    latencies_risk: List[float] = []
    for _ in range(1000):
        t_start = time.perf_counter()
        compute_geographic_risk(
            rainfall_rate_mm_hr=35.0,
            elevation_m=518.0,
            slope_degrees=1.8,
            distance_to_waterway_m=85.0,
            landcover_class=50,
            distance_to_flood_point_m=220.0
        )
        latencies_risk.append((time.perf_counter() - t_start) * 1000.0)

    results["risk_calculation_ms"] = {
        "repetitions": 1000,
        "mean": round(statistics.mean(latencies_risk), 4),
        "median": round(statistics.median(latencies_risk), 4),
        "min": round(min(latencies_risk), 4),
        "max": round(max(latencies_risk), 4)
    }
    print(f"3. Risk Calculation (1000 reps): Mean={results['risk_calculation_ms']['mean']} ms, "
          f"Median={results['risk_calculation_ms']['median']} ms, Max={results['risk_calculation_ms']['max']} ms")

    # 5. Scenario Comparison Latency (20 repetitions)
    from app.services.scenario_comparison_service import scenario_comparison_service
    latencies_scen: List[float] = []
    for _ in range(20):
        t_start = time.perf_counter()
        scenario_comparison_service.compare_all_scenarios()
        latencies_scen.append((time.perf_counter() - t_start) * 1000.0)

    results["scenario_comparison_ms"] = {
        "repetitions": 20,
        "mean": round(statistics.mean(latencies_scen), 2),
        "median": round(statistics.median(latencies_scen), 2),
        "min": round(min(latencies_scen), 2),
        "max": round(max(latencies_scen), 2)
    }
    print(f"4. Scenario Comparison (20 reps): Mean={results['scenario_comparison_ms']['mean']} ms, "
          f"Median={results['scenario_comparison_ms']['median']} ms")

    # 6. Sensitivity Analysis Latency (20 repetitions)
    from app.services.uncertainty_service import uncertainty_service
    latencies_sens: List[float] = []
    for _ in range(20):
        t_start = time.perf_counter()
        uncertainty_service.get_full_sensitivity_report()
        latencies_sens.append((time.perf_counter() - t_start) * 1000.0)

    results["sensitivity_analysis_ms"] = {
        "repetitions": 20,
        "mean": round(statistics.mean(latencies_sens), 2),
        "median": round(statistics.median(latencies_sens), 2),
        "min": round(min(latencies_sens), 2),
        "max": round(max(latencies_sens), 2)
    }
    print(f"5. Sensitivity Analysis (20 reps): Mean={results['sensitivity_analysis_ms']['mean']} ms, "
          f"Median={results['sensitivity_analysis_ms']['median']} ms")

    # 7. Shortest Path Routing Latency (50 repetitions)
    # Alkapur to Puppalaguda Hospital corridor
    latencies_shortest: List[float] = []
    for _ in range(50):
        t_start = time.perf_counter()
        road_network_service.find_shortest_path(17.3912, 78.3845, 17.3980, 78.3920)
        latencies_shortest.append((time.perf_counter() - t_start) * 1000.0)

    results["shortest_route_ms"] = {
        "repetitions": 50,
        "mean": round(statistics.mean(latencies_shortest), 2),
        "median": round(statistics.median(latencies_shortest), 2),
        "min": round(min(latencies_shortest), 2),
        "max": round(max(latencies_shortest), 2)
    }
    print(f"6. Shortest Path Routing (50 reps): Mean={results['shortest_route_ms']['mean']} ms, "
          f"Median={results['shortest_route_ms']['median']} ms")

    # 8. Lowest-Risk Routing Latency (50 repetitions)
    latencies_risk_route: List[float] = []
    for _ in range(50):
        t_start = time.perf_counter()
        road_network_service.find_lowest_risk_path(17.3912, 78.3845, 17.3980, 78.3920, lambda_param=3.0)
        latencies_risk_route.append((time.perf_counter() - t_start) * 1000.0)

    results["lowest_risk_route_ms"] = {
        "repetitions": 50,
        "mean": round(statistics.mean(latencies_risk_route), 2),
        "median": round(statistics.median(latencies_risk_route), 2),
        "min": round(min(latencies_risk_route), 2),
        "max": round(max(latencies_risk_route), 2)
    }
    print(f"7. Lowest-Risk Routing (50 reps): Mean={results['lowest_risk_route_ms']['mean']} ms, "
          f"Median={results['lowest_risk_route_ms']['median']} ms")

    # 9. Facility Accessibility Calculation (20 repetitions)
    from app.services.accessibility_service import accessibility_service
    latencies_fac: List[float] = []
    for _ in range(20):
        t_start = time.perf_counter()
        accessibility_service.find_accessible_facilities(17.3912, 78.3845, facility_category="hospital", max_results=5)
        latencies_fac.append((time.perf_counter() - t_start) * 1000.0)

    results["facility_accessibility_ms"] = {
        "repetitions": 20,
        "mean": round(statistics.mean(latencies_fac), 2),
        "median": round(statistics.median(latencies_fac), 2),
        "min": round(min(latencies_fac), 2),
        "max": round(max(latencies_fac), 2)
    }
    print(f"8. Facility Accessibility (20 reps): Mean={results['facility_accessibility_ms']['mean']} ms, "
          f"Median={results['facility_accessibility_ms']['median']} ms")

    # 10. Memory Usage
    proc = psutil.Process()
    mem_info = proc.memory_info()
    results["memory"] = {
        "rss_mb": round(mem_info.rss / (1024**2), 2),
        "vms_mb": round(mem_info.vms / (1024**2), 2)
    }
    print(f"9. Memory Footprint: RSS={results['memory']['rss_mb']} MB, VMS={results['memory']['vms_mb']} MB")
    print("=" * 70)

    return {
        "system_info": sys_info,
        "benchmarks": results
    }

if __name__ == "__main__":
    run_benchmarks()

