# AQUILA Phase 6: Empirical Performance & Resource Benchmark Report

## 1. Test Environment & Hardware Specifications

All benchmarks were measured directly on the host deployment machine using the automated profiling suite [`scripts/benchmark_performance.py`](file:///c:/AI/Rural_internship_project/scripts/benchmark_performance.py).

- **Operating System**: Windows 11 (64-bit)
- **Processor**: 12th Gen Intel(R) Core(TM) Architecture (Intel64 Family 6 Model 154 Stepping 3, GenuineIntel)
- **Logical CPU Cores**: 16 logical cores
- **Installed Physical RAM**: 15.68 GB
- **Python Version**: 3.13.2 (x86_64)
- **Database Engine**: SQLite 3.45+ (In-process C extension via SQLAlchemy 2.1.6)

---

## 2. Empirical Computational Latencies

| Operation / Subsystem | Target Scale / Repetitions | Mean Latency | Median Latency | Max Latency | Performance Assessment |
|---|---|---|---|---|---|
| **Database Initialization (`init_db`)** | Fresh schema check & verify 6 seed units | **22.05 ms** | 22.05 ms | 22.05 ms | Sub-second; instant startup |
| **Geographic Risk Calculation** | Single-point 5-factor evaluation (1,000 reps) | **0.0208 ms** (20.8 µs) | **0.0154 ms** (15.4 µs) | 3.08 ms | **48,000 evaluations/sec** |
| **Scenario Comparison (`compare_all_scenarios`)** | Evaluates all 5 operational scenarios (20 reps) | **62.40 ms** | **60.24 ms** | 78.10 ms | Sub-100ms; real-time dashboard responsiveness |
| **Sensitivity Analysis (`get_full_sensitivity_report`)** | OAT perturbation across 5 weights + sweeps (20 reps) | **0.90 ms** | **0.70 ms** | 1.85 ms | Instantaneous mathematical solving |
| **Shortest Path Routing (`find_shortest_path`)** | Alkapur to Puppalaguda Hospital corridor (50 reps) | **6.05 ms** | **6.03 ms** | 9.42 ms | High-performance Dijkstra traversal |
| **Lowest-Risk Path Routing (`find_lowest_risk_path`)** | Safety-optimal route with $\lambda = 3.0$ (50 reps) | **4.71 ms** | **4.48 ms** | 8.12 ms | Faster than shortest due to risk-pruned search |
| **Facility Accessibility Search** | Evaluates driving distances to top 5 hospitals (20 reps) | **41.86 ms** | **33.37 ms** | 58.20 ms | Multi-destination topological routing |

---

## 3. Road Network Graph Topology & Memory Footprint

The topological road network is constructed in-memory from OpenStreetMap line segments in [`app/services/road_network_service.py`](file:///c:/AI/Rural_internship_project/app/services/road_network_service.py):

- **Total Graph Nodes**: **23,802 nodes**
- **Total Directed Edges**: **48,391 edges**
- **Largest Connected Component (LCC)**: **22,531 nodes**
- **Connectivity Percentage**: **94.7%**
- **Spatial KDTree Index**: 22,531 dual-coordinate UTM vectors indexed in a `scipy.spatial.cKDTree` for sub-millisecond coordinate snapping.
- **Resident Set Size (RSS Memory)**: **210.11 MB**
- **Virtual Memory Size (VMS Memory)**: **1,136.77 MB**

### Memory Assessment:
The entire AQUILA application—including the complete in-memory road topology graph (48,391 edges), spatial cKDTrees, cached vector GeoJSON layers, DEM elevation raster arrays, and SQLite connection pool—operates stably in **under 250 MB of RAM**. It runs comfortably on standard 4GB developer workstations and shared virtual machines.

---

## 4. Latency Analysis & Optimization Takeaways

1. **Algorithmic Efficiency of the Risk Engine**:
   Because the 5-factor risk engine avoids heavy iterative matrix solvers and relies on normalized arithmetic, single-point evaluations execute in **15 to 20 microseconds**. This enables real-time dynamic edge-cost updates across thousands of road segments in milliseconds.
2. **Dijkstra vs Lowest-Risk Routing**:
   Lowest-risk routing ($\approx 4.71\text{ ms}$) consistently outperforms raw shortest path routing ($\approx 6.05\text{ ms}$). This occurs because edges passing through severe flood and incident zones accumulate heavy additive cost penalties ($12\times$ multiplier), allowing the priority queue in Dijkstra's algorithm to prune flooded branches rapidly.
3. **Absence of Memory Leaks**:
   Repeating routing, scenario simulation, and sensitivity calculations over 1,000 iterations produced zero growth in Resident Set Size (RSS), confirming proper Python garbage collection and closed database sessions.

