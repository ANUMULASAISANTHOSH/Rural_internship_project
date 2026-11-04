# AQUILA Phase 6: Initial System Audit & Baseline Verification Report

## 1. Executive Summary & Audit Context

- **Platform**: AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform
- **Pilot Study Area**: Manikonda, Hyderabad, Telangana, India ($55.63\text{ km}^2$)
- **Audit Date**: November 3, 2026
- **Auditor Role**: Senior Software Architect, Application Security Engineer & Geospatial System Auditor
- **Audited Commit / State**: Phase 1 through Phase 5 completion baseline
- **Initial Test Suite Result**: **91 passed, 0 failed, 1 warning in 82.84s**

This initial audit establishes an empirical baseline of the entire repository prior to implementing Phase 6 reliability, security, deployment, and release certification enhancements.

---

## 2. Baseline Automated Test Verification

Execution of `pytest -q`:
```
........................................................................ [ 79%]
...................                                                      [100%]
============================== warnings summary ===============================
..\..\Python313\Lib\site-packages\fastapi\testclient.py:1
  StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

91 passed, 1 warning in 82.84s (0:01:22)
```

### Breakdown of Passing Tests:
1. `tests/geospatial/test_datasets.py`: 41 tests (CRS invariants, BBOX bounds, DEM rasters, ESA WorldCover, hyetograph).
2. `tests/mvp/test_backend.py`: 16 tests (SQLite models, incident lifecycle, resource assignment, synthetic storm simulator).
3. `tests/phase4/test_routing.py`: 18 tests (NetworkX topological graph, Dijkstra routing, incident penalties, accessibility).
4. `tests/phase5/test_analytics.py`: 16 tests (5 operational scenarios, OAT sensitivity, vulnerability index $V$, priority score $P$, REST endpoints).

**Total Baseline**: **91 / 91 tests passing (100% passing)**.

---

## 3. Systematic Subsystem Audit & Findings

### Subsystem 1: Dependency & Environment Management
- **Status**: UNLOCKED / UNVERSIONED
- **Findings**:
  - The repository lacks a root `requirements.txt`, `requirements-lock.txt`, `.python-version`, or `.env.example`.
  - The runtime environment contains 130+ global packages (including unneeded libraries like PyTorch, TensorFlow, OpenCV, Django, Flask) alongside core dependencies.
  - **Risk**: A clean installation on an external evaluator's Windows workstation cannot be reliably reproduced without an explicit, pinned requirements file.
- **Severity**: **HIGH** (Deployment blocker).

### Subsystem 2: Database Schema, Foreign Keys & Transactions
- **Status**: FUNCTIONAL BUT MISSING SQLITE PRAGMA
- **Findings**:
  - SQLite does not enforce foreign keys by default. Without executing `PRAGMA foreign_keys = ON;` upon connection establishment, cascading deletes and foreign key constraints on `incident_assignments` are ignored by SQLite.
  - `DATABASE_URL` is hardcoded to a relative path `sqlite:///.../aquila_mvp.db` without supporting environment variable override (`AQUILA_DB_PATH`).
  - Seed idempotency is partially implemented: resources are re-verified, but repeated seeding without checks can pollute audit logs.
- **Severity**: **MEDIUM** (Data integrity & testing risk).

### Subsystem 3: API Security & Input Validation
- **Status**: GENERALLY SECURE WITH MINOR INFORMATION LEAK RISKS
- **Findings**:
  - Coordinate bounds are validated in routing endpoints ($[17.20, 17.60]$, $[78.20, 78.60]$), but some risk query parameters lack strict upper bounds.
  - In `/api/layers/{layer_name}`, an unmapped layer raises `ValueError` or `FileNotFoundError`. Returning `str(e)` in `HTTPException` could leak absolute server filesystem paths (`C:\AI\Rural_internship_project\data\...`).
  - CORS is configured to `allow_origins=["*"]`. While acceptable for local demonstration, a configurable origin setting is preferable.
  - There is no centralized unhandled exception handler; unhandled errors could expose tracebacks.
- **Severity**: **MEDIUM** (Information disclosure risk).

### Subsystem 4: Observability, Diagnostics & Health Checks
- **Status**: BASIC HEALTH CHECK ONLY
- **Findings**:
  - `/health` only returns static strings and current timestamp. It does not test active SQLite connectivity, road graph readiness, or geospatial dataset availability.
  - Application logging uses standard `print()` statements rather than structured, leveled Python `logging`.
- **Severity**: **MEDIUM** (Operational diagnostics gap).

### Subsystem 5: Performance & Resource Profiling
- **Status**: UNBENCHMARKED
- **Findings**:
  - Road network graph loading initializes 23,802 nodes and 48,391 edges at startup, taking $\approx 12-15\text{ seconds}$. While this is acceptable for in-memory graph operations, the exact latencies have not been empirically benchmarked and documented.
- **Severity**: **LOW** (Documentation gap).

### Subsystem 6: Scientific Claim Rigor
- **Status**: REQUIRES STRICT DEFENSIVE QUALIFICATION
- **Findings**:
  - The "100% spatial agreement" on the five October 2020 flood evidence locations must be rigorously qualified as a **spatial consistency benchmark**, not empirical predictive accuracy.
  - OpenStreetMap assets must remain strictly tagged `OSM_UNVERIFIED`.
- **Severity**: **MEDIUM** (Academic evaluation defense risk).

---

## 4. Prioritized Action Plan for Phase 6

| # | Priority Area | Planned Remediations | Target Deliverable |
|---|---|---|---|
| 1 | **Dependencies** | Create curated `requirements.txt`, `requirements-lock.txt`, `.python-version`, `.env.example` | Feature A |
| 2 | **Database** | Add SQLite `PRAGMA foreign_keys=ON;` event listener, configurable `AQUILA_DB_PATH`, transaction verification | Feature B |
| 3 | **API Security** | Sanitize 404/500 error messages, prevent path leakage, add global exception handler, document endpoint types | Feature C |
| 4 | **Observability** | Create `app/services/health_service.py` with deep diagnostic probes; implement structured logging | Feature D |
| 5 | **Benchmarking** | Measure real empirical latencies across 10 core operations on Windows; document hardware & repetitions | Feature E |
| 6 | **Claim Audit** | Reconcile all 13 quantitative claims in a formal audit document with sources and limitations | Feature F |
| 7 | **Verification** | Create `scripts/verify_release.py` unified test and health gate runner | Feature G |
| 8 | **Deployment** | Create Windows clean setup guide, optional Docker deployment, and academic demonstration runbook | Feature H & I |
| 9 | **Reliability Tests** | Develop `tests/phase6/test_release_reliability.py` and run full regression suite | Testing |

