# AQUILA Phase 5: Known Limitations & Methodological Disclosures

## 1. Context & Defensive Academic Integrity

A distinguishing hallmark of an authentic, defense-ready engineering prototype is the **unflinching disclosure of its limitations**. Academic viva examiners and technical auditors rigorously scrutinize prototypes that overclaim capabilities or present heuristic proxies as empirical physics.

This document enumerates the known theoretical, data, and operational boundaries of AQUILA Phase 5.

---

## 2. Geospatial & Hydrodynamic Limitations

### 1. Absence of Full 2D Hydrodynamic Modeling
- **Current State**: AQUILA employs a multi-factor geographic risk heuristic:
  $$R = 0.40P + 0.20T + 0.20D + 0.10L + 0.10H$$
- **Boundary**: This is an empirical vulnerability index, **not** a numerical solution of the 2D Saint-Venant shallow-water momentum and continuity differential equations (e.g., as performed by HEC-RAS 2D or TUFLOW).
- **Practical Implication**: The model indicates where water is mathematically expected to accumulate based on slope, depression, and drainage proximity; it does not model velocity vectors, dynamic momentum exchange, or backwater waves in sub-second time steps.

### 2. Static Surface DEM vs Subsurface Stormwater Network
- **Current State**: Terrain elevation is derived from Copernicus GLO-30 / SRTM 30m DEM resampled to $10\text{m}$.
- **Boundary**: Mapped drainage channels represent surface nalas and open waterways. The subsurface municipal closed-pipe stormwater drain network (culverts, underground RCC pipes, catch pits, and manholes) is not comprehensively inventoried across Manikonda by municipal GIS.
- **Practical Implication**: Unmodeled localized pipe blockages, siltation, or clandestine sewer interconnections can cause surface flooding on streets that appear topographically well-drained in the DEM.

### 3. Static Road Elevation Profiling
- **Current State**: Road network nodes and segment midpoints sample raster elevation from the surface DEM.
- **Boundary**: 30m DEMs often smooth micro-topographic features such as curb heights, concrete median dividers, flyover ramps, and road embankments.
- **Practical Implication**: A road constructed on an elevated $1.5\text{m}$ embankment may register the lower elevation of the adjacent agricultural field in the coarse DEM, leading to conservative overestimation of road vulnerability.

---

## 4. Data Provenance & OpenStreetMap Limitations

### 1. `OSM_UNVERIFIED` Status of Critical Infrastructure
- **Current State**: 65 critical assets (hospitals, pharmacies, clinics) are tagged `OSM_UNVERIFIED`.
- **Boundary**: OpenStreetMap points are crowdsourced. While spatial coordinates are generally accurate within $15\text{m}$, operational attributes—such as emergency bed capacity, whether backup generators are flood-proofed, or whether a pharmacy maintains 24/7 service—have not been verified by a physical field survey.
- **Defensive Position**: The system strictly flags this provenance on every API response and dashboard table.

### 2. Historical Flood Points Sample Size ($N=5$)
- **Current State**: Five high-confidence inundation locations from the October 2020 event are used as spatial calibration anchors (`FLD-2020-MKD-01` to `05`).
- **Boundary**: While these 5 points represent verified, documented high-hazard locations from official field logs and traffic advisories, they do not constitute a continuous satellite-derived SAR inundation extent raster.
- **Defensive Position**: Evaluated as a **Spatial Consistency Benchmark**, not as a statistical training dataset.

---

## 5. Transportation Network & Routing Assumptions

### 1. Static Free-Flow Speed Assumptions
- **Current State**: Edge costs are computed based on metric segment length and flood risk penalties:
  $$\text{Cost}(e) = \text{Length}(e) \cdot \left(1.0 + \lambda \cdot \frac{R(e)}{100.0} + P_{\text{incident}}\right)$$
- **Boundary**: Live traffic congestion feeds (e.g., Google Maps Traffic API or TomTom live vehicle speeds) are not ingested. Detours assume free-flow speeds on residential roads.
- **Practical Implication**: In a real disaster, a residential detour route that avoids waterlogging may experience severe vehicular gridlock due to bottlenecking.

### 2. Pedestrian vs High-Clearance Emergency Vehicles
- **Current State**: Waterlogging incidents above $0.30\text{m}$ trigger routing avoidance across all vehicle classes.
- **Boundary**: Heavy multi-axle fire tenders, NDRF trucks, and high-clearance tractors can navigate water depths up to $0.60\text{m}$, whereas civilian sedans stall at $0.25\text{m}$.
- **Future Work**: Implementing multi-modal routing profiles parameterized by vehicle wading depth thresholds.

---

## 6. Algorithmic Sensitivity vs Probabilistic Uncertainty

- **Current State**: One-At-a-Time (OAT) parameter sensitivity measures local gradient elasticity ($\Delta R$).
- **Boundary**: OAT evaluates the sensitivity of the algorithm to its own parameter weights. It does not measure the probabilistic uncertainty of atmospheric cloudburst occurrence, nor does it generate Monte Carlo ensembles of rainfall spatial distributions.
- **Defensive Position**: Clearly stated in all documentation, API schemas, and dashboard disclaimers.

