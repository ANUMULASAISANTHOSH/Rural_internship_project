# AQUILA Phase 6: Data Integrity & Scientific Claim Audit

## 1. Executive Summary & Purpose

Academic software evaluation and technical peer review demand uncompromising honesty regarding quantitative claims. Exaggerated claims of "100% predictive accuracy" or conflating heuristic policy weights with physical hydraulic equations immediately undermine credibility during technical defenses.

This document performs a line-by-line verification of every quantitative metric in AQUILA, establishing its exact mathematical origin, geographic scope, data provenance, and scientific limitations.

---

## 2. Reconciliation Matrix of 13 Core Quantitative Claims

| # | Claimed Metric | Source Authority / Dataset | Computation / Method | Units & Scope | Status | Scientific Safeguards & Disclosures |
|---|---|---|---|---|---|---|
| 1 | **$55.63\text{ km}^2$ Analysis Envelope** | Derived bounding box | Envelope $[78.3455^\circ\text{E}, 17.3605^\circ\text{N}]$ to $[78.4195^\circ\text{E}, 17.4245^\circ\text{N}]$ | $\text{km}^2$ (Rectangular bounding box) | **VERIFIED** | Bounding box is an artificial computational envelope chosen to capture upstream ridges (Khajaguda) and downstream discharge into Neknampur Lake. It does not represent a natural boundary. |
| 2 | **$15.5\text{ km}^2$ Municipal Boundary** | Manikonda Municipality / Gandipet Mandal records | Estimated administrative area from municipal ward outlines | $\text{km}^2$ (Administrative) | **QUALIFIED** | Statutory municipal boundary GIS polygons are restricted by GHMC/HMDA. Sourced as an approximate administrative baseline; not a verified cadastral survey. |
| 3 | **$22.4\text{ km}^2$ Natural Catchment** | SRTM/Copernicus DEM watershed delineation | Topographic watershed boundary draining toward Neknampur Lake | $\text{km}^2$ (Hydrological basin) | **VERIFIED** | Natural watershed boundaries cross administrative municipal borders, draining runoff across multiple wards. |
| 4 | **$51.72\%$ Built-up Land Share** | ESA WorldCover 10m 2021 Sentinel-1/2 | Pixel classification count: 352,754 of 681,984 pixels classified as Class 50 (Built-up) | % within $55.63\text{ km}^2$ envelope | **VERIFIED** | Direct pixel count from ESA WorldCover 2021 raster clipped to study bounding box. Reflects high impervious surface fraction. |
| 5 | **6,659 OSM Road Segments** | OpenStreetMap Overpass API (Ingested Phase 2) | Filtered, cleaned, and topological-validated LineString segments | Feature count | **VERIFIED** | Raw OSM features (6,904) cleaned by removing 244 duplicates and 1 invalid highway. Exactly 6,659 segments accepted. |
| 6 | **$94.7\%$ Largest Connected Component** | NetworkX weakly connected components analysis | 22,531 nodes in largest component / 23,802 total nodes | % graph nodes | **VERIFIED** | Confirms high topological connectivity. The remaining 5.3% represent disconnected cul-de-sacs or gated layout access stubs. |
| 7 | **65 Critical Facilities (`OSM_UNVERIFIED`)** | OpenStreetMap point extraction (`amenity=*`, `healthcare=*`) | Verified point features within analysis envelope | Feature count | **VERIFIED & RESTRICTED** | **Provenance: `OSM_UNVERIFIED`**. Crowdsourced points; spatial coordinates are valid, but operational readiness and basement flood-proofing are unverified by municipal audit. |
| 8 | **5 Historical Flood Evidence Locations** | October 2020 Deep Depression records | Documented flood points from Cyberabad Police, GHMC logs, and media archives | Point records (`FLD-01` to `05`) | **VERIFIED** | Sourced from field logs and post-disaster advisories. Point evidence only; does not represent continuous water extent. |
| 9 | **$120\text{ mm}$ / 3-Hour Synthetic Design Storm** | Synthetic Chicago Design Storm pattern | Asymmetric triangular hyetograph peaking at $70\text{ mm/hr}$ at $T=45\text{ min}$ | $\text{mm}$ depth over 180 min | **ILLUSTRATIVE** | **Provenance: `SIMULATED`**. Calibrated to approximate a 1-in-25 to 1-in-50 year storm depth. Not a real-time rain gauge recording. |
| 10 | **57-to-91 Test Suite Progression** | Pytest test execution logs | Phase 2 (41) + Phase 3 (16) = 57; Phase 4 (+18) = 75; Phase 5 (+16) = 91 | Automated test count | **VERIFIED** | Exactly 91 passing tests across unit, integration, invariant, and API suites. |
| 11 | **Scenario Mean Risk Scores** | `ScenarioComparisonService` | Multi-point catchment sampling under 0, 25, 70 mm/hr and surcharge | Scale $0 - 100$ | **CALCULATED** | Reflects deterministic mathematical evaluation of the 5-factor risk formula. Not an empirical flood depth measurement. |
| 12 | **100% Spatial Agreement** | `VulnerabilityService.evaluate_historical_evidence_consistency` | All 5 historical flood points classified as MODERATE or HIGH risk ($R \ge 40.0$) | % concordance (5/5 points) | **CRITICAL SAFEGUARD** | **Spatial Consistency Benchmark ONLY**. This is NOT 100% predictive accuracy. It confirms the heuristic flags documented hotspots. |
| 13 | **OAT Sensitivity Results** | `UncertaintyService.analyze_weight_sensitivity` | Perturbation ($\pm 20\%$) with $\sum w_i = 1.0$ invariant | $\Delta R$ swing (points) | **VERIFIED** | Evaluates mathematical parameter elasticity of the formula. Does NOT represent Monte Carlo hydrodynamic depth uncertainty. |

---

## 3. Critical Scientific Safeguards & Disclosures

### Safeguard A: Reconciling "100% Spatial Agreement" vs "Predictive Accuracy"
- **What Spatial Agreement Actually Measures**:
  Evaluating the 5-factor risk engine at the exact geographic coordinates of the five documented October 2020 flood evidence locations produces risk scores ranging from $67.8$ to $83.5$. Because all five scores exceed the $40.0$ threshold (falling into the MODERATE or HIGH risk tiers), the spatial agreement score is $\frac{5}{5} = 100\%$.
- **Why It Must NEVER Be Called "Predictive Accuracy"**:
  1. **Absence of Negative Controls**: The benchmark tests known flooded points (true positives) but does not evaluate verified dry points (true negatives) to measure false positive rates.
  2. **Sample Size ($N=5$)**: Five point locations cannot statistically establish generalized predictive performance across a $55.63\text{ km}^2$ heterogeneous catchment.
  3. **Correct Scientific Label**: It must be reported strictly as a **Qualitative Spatial Concordance Benchmark**.

### Safeguard B: Nature of the IMD Precipitation Normalization Curve
The precipitation normalization curve in `calculate_rainfall_score(P)` maps rainfall intensity $P$ into a $0 - 100$ score:
- The threshold breakpoints ($15.6\text{ mm/hr}$ Heavy, $64.5\text{ mm/hr}$ Very Heavy, $100.0\text{ mm/hr}$ Cloudburst) correspond to **official India Meteorological Department (IMD) meteorological terminology**.
- The score assignment ($0 \to 40 \to 75 \to 100$) is an **operational heuristic policy mapping**, not a calibrated physical infiltration-runoff curve.

### Safeguard C: Status of Risk and Vulnerability Weights
The weights in the risk engine ($0.40P + 0.20T + 0.20D + 0.10L + 0.10H$) and the infrastructure vulnerability index ($0.35R + 0.25S_{\text{flood}} + 0.20S_{\text{drain}} + 0.20S_{\text{access}}$) are **multi-criteria decision analysis (MCDA) expert policy weights**. They represent domain-informed priorities, not statistically regressed coefficients from historical insurance loss data.

---

## 4. Rigorous Provenance Taxonomy

To prevent data misattribution, AQUILA strictly enforces and emits five standardized provenance tags:

1. `OBSERVED`: Real-world empirical measurements (e.g., TGDPS Gachibowli automated weather station coordinates, ESA WorldCover satellite imagery).
2. `HISTORICAL`: Verified post-disaster flood documentation from the October 2020 event (`historical_flood_points_processed.geojson`).
3. `MANUALLY_SEEDED`: Synthetic simulation entities created for demonstration (e.g., the 6 synthetic emergency resources in `INITIAL_RESOURCES`).
4. `SIMULATED`: Transient dynamic data generated during scenario runs (e.g., Chicago storm rainfall steps, injected flood incidents `INC-SIM-001`).
5. `MODEL_ESTIMATE`: Calculated outputs produced by algorithmic formulas (e.g., geographic risk scores, vulnerability index $V$, priority score $P$).
6. `OSM_UNVERIFIED`: Crowdsourced OpenStreetMap assets whose existence is mapped but whose operational status is unverified.

