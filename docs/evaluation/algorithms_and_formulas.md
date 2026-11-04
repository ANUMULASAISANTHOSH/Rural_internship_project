# AQUILA — Mathematical and Algorithmic Defense

**Project:** AQUILA — Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform  
**Target Area:** Manikonda Pilot Area, Hyderabad, Telangana, India  
**Document Type:** Algorithmic Specification & Mathematical Validation Reference  
**Document Location:** `docs/evaluation/algorithms_and_formulas.md`  

---

## 1. Algorithmic Overview

This document provides a comprehensive mathematical defense of the analytical algorithms and formulas implemented in the AQUILA platform. Every equation presented is verified directly against the underlying Python source code in:
- [`app/services/risk_engine.py`](file:///C:/AI/Rural_internship_project/app/services/risk_engine.py)
- [`app/services/resource_service.py`](file:///C:/AI/Rural_internship_project/app/services/resource_service.py)
- [`scripts/geospatial/process_dem.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_dem.py)
- [`scripts/geospatial/process_roads.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_roads.py)
- [`scripts/geospatial/process_rainfall.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_rainfall.py)

---

## 2. Multi-Factor Rule-Based Risk Engine

### 2.1 Mathematical Formulation
The core risk engine computes a composite dimensionless Geographic Risk Index $R \in [0, 100]$:

$$R = \frac{\sum_{i=1}^{n} w_i \cdot S_i}{\sum_{i=1}^{n} w_i}$$

Under full data availability, the default weights sum to $1.00$:

$$R = 0.40 \cdot S_P + 0.20 \cdot S_T + 0.20 \cdot S_D + 0.10 \cdot S_L + 0.10 \cdot S_H$$

Where:
* $S_P$: Normalized Precipitation Hazard Score ($0 - 100$)
* $S_T$: Normalized Terrain Vulnerability Score ($0 - 100$)
* $S_D$: Normalized Drainage Proximity Score ($0 - 100$)
* $S_L$: Normalized Land Cover Runoff Score ($0 - 100$)
* $S_H$: Normalized Historical Flood Recurrence Score ($0 - 100$)

---

### 2.2 Factor Definitions & Sub-Model Logic

#### A. Precipitation Hazard Component ($S_P$, $w_P = 0.40$)
Implemented in `calculate_rainfall_score(rate_mm_hr)`:
Normalizes continuous rainfall intensity (mm/hr) using standard IMD meteorological classification breakpoints:
* **0.0 mm/hr:** $S_P = 0.0$
* **0.1 to 15.6 mm/hr (Light to Moderate):**
  $$S_P = \left( \frac{\text{rate}}{15.6} \right) \times 40.0$$
* **15.6 to 64.5 mm/hr (Heavy Rainfall):**
  $$S_P = 40.0 + \left( \frac{\text{rate} - 15.6}{64.5 - 15.6} \right) \times 35.0$$
* **64.5 to 100.0 mm/hr (Very Heavy Rainfall):**
  $$S_P = 75.0 + \left( \frac{\text{rate} - 64.5}{100.0 - 64.5} \right) \times 25.0$$
* **$\ge 100.0$ mm/hr (Cloudburst scale):**
  $$S_P = 100.0$$

#### B. Terrain Vulnerability Component ($S_T$, $w_T = 0.20$)
Implemented in `calculate_terrain_score(elevation_m, slope_degrees)`:
Combines local elevation basin accumulation ($60\%$) and gravitational slope drainage ($40\%$):

$$S_T = 0.60 \cdot S_{\text{elev}} + 0.40 \cdot S_{\text{slope}}$$

* **Elevation Sub-Score ($S_{\text{elev}}$):** Evaluated across Manikonda's 492m to 638m relief:
  - If $\text{elev} \le 495.0\text{ m}$: $S_{\text{elev}} = 100.0$ (Valley bottom / depression)
  - If $\text{elev} \ge 600.0\text{ m}$: $S_{\text{elev}} = 10.0$ (Ridge top)
  - Intermediate ($495 < \text{elev} < 600$):
    $$S_{\text{elev}} = 100.0 - \left( \frac{\text{elev} - 495.0}{600.0 - 495.0} \right) \times 90.0$$

* **Slope Sub-Score ($S_{\text{slope}}$):** Evaluates gravitational runoff drainage:
  - If $\text{slope} \le 1.5^\circ$: $S_{\text{slope}} = 100.0$ (Flat, severe stagnation risk)
  - If $\text{slope} \ge 15.0^\circ$: $S_{\text{slope}} = 15.0$ (Steep slope, rapid gravity drainage)
  - Intermediate ($1.5 < \text{slope} < 15.0$):
    $$S_{\text{slope}} = 100.0 - \left( \frac{\text{slope} - 1.5}{15.0 - 1.5} \right) \times 85.0$$

#### C. Drainage Proximity Component ($S_D$, $w_D = 0.20$)
Implemented in `calculate_drainage_score(distance_to_waterway_m)`:
Stepwise distance decay function representing backwater and overtopping hazard from mapped open nalas:
* $d \le 50.0\text{ m}$: $S_D = 95.0$
* $50.0 < d \le 150.0\text{ m}$: $S_D = 75.0$
* $150.0 < d \le 300.0\text{ m}$: $S_D = 45.0$
* $300.0 < d \le 600.0\text{ m}$: $S_D = 25.0$
* $d > 600.0\text{ m}$: $S_D = 10.0$

#### D. Land Cover Imperviousness Component ($S_L$, $w_L = 0.10$)
Implemented in `calculate_landcover_score(class_id)`:
Lookup table mapping ESA WorldCover 10m raster classes to runoff potential:
* **Class 80 (Permanent Water Body buffer):** $S_L = 95.0$
* **Class 50 (Built-up / Impervious Urban):** $S_L = 90.0$
* **Class 60 (Bare rock / Soil):** $S_L = 65.0$
* **Class 40 (Cropland):** $S_L = 35.0$
* **Class 30 (Grassland):** $S_L = 30.0$
* **Class 20 (Shrubland):** $S_L = 20.0$
* **Class 10 (Tree cover / Forest):** $S_L = 15.0$
* *Default / Unknown:* $S_L = 50.0$

#### E. Historical Flood Recurrence Component ($S_H$, $w_H = 0.10$)
Implemented in `calculate_historical_score(distance_to_flood_point_m)`:
Proximity decay to verified October 2020 inundation ground truth points:
* $d \le 150.0\text{ m}$: $S_H = 100.0$
* $150.0 < d \le 300.0\text{ m}$: $S_H = 75.0$
* $300.0 < d \le 600.0\text{ m}$: $S_H = 45.0$
* $600.0 < d \le 1000.0\text{ m}$: $S_H = 20.0$
* $d > 1000.0\text{ m}$: $S_H = 5.0$

---

### 2.3 Dynamic Weight Renormalization & Missing Data Handling
When any geospatial layer is missing or null, the risk engine dynamically prunes that factor from the active weight set and renormalizes the remaining components:

$$R = \frac{\sum_{i \in \text{Active}} w_i \cdot S_i}{\sum_{i \in \text{Active}} w_i}$$

**Verification Example:**
If the terrain layer is missing ($S_T$ is null):
- Missing weight: $w_T = 0.20$
- Sum of active weights: $\sum_{\text{active}} w_i = 0.40 + 0.20 + 0.10 + 0.10 = 0.80$
- Effective weights become:
  - Rainfall ($w_P^*$): $0.40 / 0.80 = 0.500$
  - Drainage ($w_D^*$): $0.20 / 0.80 = 0.250$
  - Landcover ($w_L^*$): $0.10 / 0.80 = 0.125$
  - Historical ($w_H^*$): $0.10 / 0.80 = 0.125$
  - Sum: $0.500 + 0.250 + 0.125 + 0.125 = 1.000$

This prevents the risk score from falsely collapsing toward zero due to missing data.

---

### 2.4 Risk Classification Thresholds
Implemented in `classify_risk(final_score)`:
* **$0.0 \le R < 40.0$:** `LOW` (Routine stormwater maintenance; drainage canals flowing normally).
* **$40.0 \le R < 70.0$:** `MODERATE` (Advisory monitoring; roadside culverts near capacity).
* **$70.0 \le R \le 100.0$:** `HIGH` (Critical emergency threshold; flash flooding imminent or occurring; priority resource dispatch triggered).

*(Note on Documentation Consistency: While early Phase 1 notes discussed an optional 4-tier scheme with a CRITICAL category above 75, the actual production implementation in `risk_engine.py` strictly operates on this 3-tier boundary: `<40`, `<70`, and `\ge 70`).*

---

### 2.5 Worked Numerical Example

**Evaluation Coordinates:** Alkapur Township Sector 1 Depression (`17.3912°N, 78.3845°E`)  
**Input Conditions:**
- Rainfall Rate: $50.0\text{ mm/hr}$ (Heavy monsoon thunderstorm)
- Elevation: $512.0\text{ m}$
- Slope: $1.2^\circ$ (Flat depression)
- Distance to Mapped Nala: $65.0\text{ m}$
- Land Cover: ESA Class 50 (Built-up urban)
- Distance to Historical Flood Hotspot: $120.0\text{ m}$

**Step-by-Step Sub-Score Computations:**
1. **Precipitation ($S_P$):**
   Rate is $50.0\text{ mm/hr}$, which falls between $15.6$ and $64.5\text{ mm/hr}$:
   $$S_P = 40.0 + \left( \frac{50.0 - 15.6}{64.5 - 15.6} \right) \times 35.0 = 40.0 + \left( \frac{34.4}{48.9} \right) \times 35.0 = 40.0 + 24.62 = 64.62$$

2. **Terrain ($S_T$):**
   - Elevation factor ($512.0\text{ m}$):
     $$S_{\text{elev}} = 100.0 - \left( \frac{512.0 - 495.0}{600.0 - 495.0} \right) \times 90.0 = 100.0 - \left( \frac{17.0}{105.0} \right) \times 90.0 = 100.0 - 14.57 = 85.43$$
   - Slope factor ($1.2^\circ \le 1.5^\circ$):
     $$S_{\text{slope}} = 100.0$$
   - Combined Terrain Score:
     $$S_T = 0.60 \times 85.43 + 0.40 \times 100.0 = 51.26 + 40.0 = 91.26$$

3. **Drainage Proximity ($S_D$):**
   Distance is $65.0\text{ m}$, falling in $50 < d \le 150$:
   $$S_D = 75.0$$

4. **Land Cover Imperviousness ($S_L$):**
   Class 50 (Built-up):
   $$S_L = 90.0$$

5. **Historical Recurrence ($S_H$):**
   Distance is $120.0\text{ m}$, falling in $d \le 150$:
   $$S_H = 100.0$$

**Composite Risk Score Calculation:**
$$R = 0.40(64.62) + 0.20(91.26) + 0.20(75.0) + 0.10(90.0) + 0.10(100.0)$$
$$R = 25.85 + 18.25 + 15.00 + 9.00 + 10.00 = 78.10$$

**Final Result:**
- **Risk Score:** **$78.1$**
- **Risk Category:** **`HIGH`** ($\ge 70.0$)

---

## 3. Spatial Interpolation: Inverse Distance Weighting (IDW)

### 3.1 Mathematical Formula
When estimating continuous rainfall across the study envelope from $N$ surrounding perimeter proxy stations (Gachibowli, Serilingampally, Begumpet, Rajendranagar), AQUILA employs Inverse Distance Weighting:

$$Z(\mathbf{x}) = \frac{\sum_{i=1}^{N} w_i(\mathbf{x}) Z_i}{\sum_{i=1}^{N} w_i(\mathbf{x})}, \quad \text{where } w_i(\mathbf{x}) = \frac{1}{d(\mathbf{x}, \mathbf{x}_i)^p}$$

* $\mathbf{x} = (\lambda, \phi)$: Target coordinates in Manikonda.
* $\mathbf{x}_i$: Coordinates of weather station $i$.
* $Z_i$: Rainfall intensity recorded at station $i$ (mm/hr).
* $d(\mathbf{x}, \mathbf{x}_i)$: Geodesic or planar Euclidean distance between target and station.
* $p$: Power parameter (Standard: $p = 2.0$, inverse square distance).

### 3.2 Limitations & Disclosures
1. **No Extrapolation Beyond Bounds:** IDW estimates are strictly bounded by $\min(Z_i) \le Z(\mathbf{x}) \le \max(Z_i)$. An intense localized cloudburst occurring directly over Manikonda cannot be predicted if peripheral stations register low rain.
2. **Bullseye Effect:** Isolated peaks form around individual station points when $p \ge 2$.
3. **Density Deficiency:** With only 4 proxy stations separated by 5 to 10 km, IDW provides a regional trend rather than street-level precipitation variability.

---

## 4. Spherical Geodesy: Great-Circle Haversine Distance

### 4.1 Mathematical Formulation
Implemented in `haversine_distance_km(lat1, lon1, lat2, lon2)` in [`app/services/resource_service.py`](file:///C:/AI/Rural_internship_project/app/services/resource_service.py):

$$\Delta \phi = \phi_2 - \phi_1, \quad \Delta \lambda = \lambda_2 - \lambda_1 \quad (\text{in radians})$$

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta \lambda}{2}\right)$$

$$c = 2 \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$

$$d = R_{\text{earth}} \cdot c$$

Where:
* $R_{\text{earth}} = 6371.0\text{ km}$ (Mean volumetric radius of the Earth).
* Inputs: Latitude and Longitude in decimal degrees, converted to radians via $\text{radians} = \text{deg} \times \frac{\pi}{180}$.
* Output: Geodesic distance $d$ in kilometres, rounded to 3 decimal places ($1\text{ metre}$ precision).

### 4.2 Haversine vs. Road Network Travel Distance
> [!WARNING]
> Haversine computes straight-line distance ("as the crow flies") across the spherical globe. It does **NOT** equal road driving distance:
> 1. **Circuitous Urban Streets:** In Manikonda, winding residential lanes, dead-end cul-de-sacs, and gated community perimeter walls introduce a tortuosity factor of $1.35$ to $1.65$ over straight-line distance.
> 2. **Flood Inundation Severance:** A depot located 0.8 km away by Haversine may be completely unreachable if an intervening culvert is submerged under 0.6m of floodwater.
> 3. **Turn-by-Turn Routing Target:** Full road graph routing using NetworkX Dijkstra/A* shortest path with dynamic flood impedance weights is designated for Phase 4/5.

---

## 5. Digital Terrain Slope Calculation

### 5.1 Horn's Method (8-Neighbor Formulation) vs. NumPy Implementation
In GIS theory and GDAL DEM tools, Horn's (1981) method is commonly applied using a $3 \times 3$ sliding kernel:

$$\begin{bmatrix} a & b & c \\ d & e & f \\ g & h & i \end{bmatrix}$$

$$\left(\frac{\partial z}{\partial x}\right)_{\text{Horn}} = \frac{(c + 2f + i) - (a + 2d + g)}{8 \cdot \Delta x}$$

$$\left(\frac{\partial z}{\partial y}\right)_{\text{Horn}} = \frac{(g + 2h + i) - (a + 2b + c)}{8 \cdot \Delta y}$$

$$\text{Slope}_{\text{rad}} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right), \quad \text{Slope}_{\text{deg}} = \text{Slope}_{\text{rad}} \times \frac{180}{\pi}$$

**Actual Implementation in AQUILA (`process_dem.py`):**
AQUILA executes NumPy's 2nd-order central finite difference scheme:
```python
res_m = src.res[0] * 111320  # ~30.9 metres/pixel
dy, dx = np.gradient(data, res_m, res_m)
slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
slope_deg = np.degrees(slope_rad)
```
On interior points, NumPy computes:
$$\frac{\partial z}{\partial x} \approx \frac{z_{i+1, j} - z_{i-1, j}}{2 \cdot \Delta x}, \quad \frac{\partial z}{\partial y} \approx \frac{z_{i, j+1} - z_{i, j-1}}{2 \cdot \Delta y}$$

*Differences:*
- Horn's method applies higher weight ($2\times$) to orthogonal neighbors, providing slight noise attenuation over noisy radar surfaces.
- NumPy central difference provides equivalent gradient magnitudes across smoothly interpolated DEM rasters while executing in $<100\text{ ms}$ vectorized C code.

### 5.2 Resolution Limitations
A 30-meter pixel represents a ground footprint of $900\text{ m}^2$. A gradient computed across $2 \cdot \Delta x \approx 61.8\text{ m}$ averages out curbs, stormwater gutters, and compound walls. Localized depressions narrower than 30m cannot be resolved without high-resolution LiDAR (<1m).

---

## 6. Road Network Graph Topology & Connectivity

### 6.1 Graph Formalism
The road network is modeled in [`scripts/geospatial/process_roads.py`](file:///C:/AI/Rural_internship_project/scripts/geospatial/process_roads.py) as a directed topological graph $G = (V, E)$:
* **Vertices ($V$):** Road intersections and dead-ends. Vertex IDs are assigned uniquely by rounding geographic coordinates to 6 decimal places ($~0.1\text{m}$ precision):
  $$\text{key} = (\operatorname{round}(\lambda, 6), \operatorname{round}(\phi, 6))$$
* **Edges ($E$):** Road segments connecting adjacent vertices.
  - Edge weights: Length in metres calculated via projected Euclidean approximation:
    $$dx = (v_\lambda - u_\lambda) \cdot 111320 \cdot \cos(\bar{\phi}), \quad dy = (v_\phi - u_\phi) \cdot 111320$$
    $$\text{length}_m = \sqrt{dx^2 + dy^2}$$
  - Bidirectional edges added unless the OSM feature has `oneway == "yes"`.

### 6.2 Connected Component Analysis & The 94.7% Metric
A directed graph is *weakly connected* if replacing all directed edges with undirected edges produces a connected graph.
Connectivity is evaluated via `nx.weakly_connected_components(G)`:

$$\text{Largest CC Percentage} = \frac{|V_{\text{largest}}|}{|V_{\text{total}}|} \times 100 = \mathbf{94.7\%}$$

### 6.3 What the 94.7% Connectivity Metric Establishes
* **What It Proves:**
  1. High topological integrity: 94.7% of all extracted road junctions and endpoints in the Manikonda study envelope belong to a single connected vehicular network.
  2. The network exceeds the Phase 1 Non-Functional Requirement (NFR-004 target: $\ge 90\%$).
* **What It Does NOT Establish:**
  1. It does **not** prove that all roads are drivable during a flood (does not model waterlogging).
  2. It does **not** guarantee 100% attribute completeness (street names or lane counts may be missing in OSM).
  3. The remaining 5.3% of nodes represent disconnected internal gated-colony layouts or roads cut off at the bounding box boundary.

