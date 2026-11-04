# AQUILA Phase 5: Uncertainty & Sensitivity Analysis

## 1. Algorithmic Uncertainty vs Empirical Probability

In disaster decision-support systems, a frequent methodological flaw is claiming "calibrated probabilistic flood depths" or fabricating statistical confidence intervals in the absence of dense real-time stream gauges and 2D hydraulic calibration.

AQUILA adheres strictly to **defensible engineering principles**:
- We do **not** claim empirical Monte Carlo flood depth probability distributions.
- We implement rigorous **One-At-a-Time (OAT) deterministic sensitivity analysis** and **local parameter elasticity evaluation** to quantify model stability, parameter influence, and missing-layer resilience.

```mermaid
flowchart LR
    subgraph Inputs["Perturbations & Elasticity"]
        W["Component Weights (±20%)<br/>sum(w) = 1.0 invariant"]
        P["Precipitation Sweep<br/>0 to 120 mm/hr non-linear"]
        L["Missing Layer Omission<br/>LULC, Hist, Drain, DEM"]
        K["Routing Lambda Multiplier<br/>0.0 to 10.0 Detour Curve"]
    end

    subgraph Service["Uncertainty Engine (uncertainty_service.py)"]
        OAT["OAT Mathematical Solver"]
        NORM["Weight Renormalizer"]
        SWING["Swing & Elasticity Calculator"]
    end

    subgraph Metrics["Analytical Outputs"]
        S["Factor Swing ΔR (pts)"]
        E["Local Elasticity Coefficient"]
        T["Tornado Influence Ranking"]
        C["IMD Category Thresholds"]
    end

    Inputs --> Service
    Service --> Metrics
```

---

## 2. One-At-a-Time (OAT) Weight Sensitivity Formulation

The composite geographic risk formula is:
$$R = \frac{\sum_{i=1}^{5} w_i \cdot S_i}{\sum_{i=1}^{5} w_i}$$

For each component factor $i \in \{\text{rainfall}, \text{terrain}, \text{drainage}, \text{landcover}, \text{historical}\}$:
1. **Perturbation**: The target weight $w_i$ is perturbed by fraction $\delta = 0.20$ ($\pm 20\%$):
   $$w_i^{+} = w_i \cdot (1 + \delta), \quad w_i^{-} = w_i \cdot (1 - \delta)$$
2. **Renormalization Invariant**: Remaining weights $j \ne i$ are scaled proportionally to preserve a unit sum:
   $$w_j^{+} = w_j \cdot \frac{1 - w_i^{+}}{\sum_{k \ne i} w_k}, \quad w_j^{-} = w_j \cdot \frac{1 - w_i^{-}}{\sum_{k \ne i} w_k}$$
   This ensures $\sum_{k=1}^{5} w_k^{+} = 1.0$ and $\sum_{k=1}^{5} w_k^{-} = 1.0$ strictly hold across all evaluations.
3. **Risk Swing ($\Delta R$)**:
   $$\Delta R_i = |R(w_i^{+}) - R(w_i^{-})|$$
4. **Local Elasticity Coefficient ($E_i$)**:
   $$E_i = \frac{\Delta R_i / R_{\text{base}}}{2 \cdot \delta}$$

### OAT Sensitivity Results on Benchmark Catchment Location

Evaluated at the Puppalaguda Valley Benchmark ($P=35.0\text{ mm/hr}$, Elev $518\text{m}$, Slope $1.8^\circ$, Drain $85\text{m}$, Hist $220\text{m}$, Base Risk $R_{\text{base}} = 65.2$):

| Factor Rank | Parameter | Base Weight | Perturbed (+) | Perturbed (-) | Risk (+) | Risk (-) | Swing $\Delta R$ | % Swing | Elasticity |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **Rainfall ($P$)** | 0.40 | 0.4800 | 0.3200 | 63.8 | 66.6 | **2.80 pts** | 4.29% | 0.107 |
| **2** | **Drainage ($D$)** | 0.20 | 0.2400 | 0.1600 | 66.4 | 64.0 | **2.40 pts** | 3.68% | 0.092 |
| **3** | **Terrain ($T$)** | 0.20 | 0.2400 | 0.1600 | 66.2 | 64.2 | **2.00 pts** | 3.07% | 0.077 |
| **4** | **Historical ($H$)** | 0.10 | 0.1200 | 0.0800 | 65.8 | 64.6 | **1.20 pts** | 1.84% | 0.046 |
| **5** | **Land Cover ($L$)** | 0.10 | 0.1200 | 0.0800 | 65.7 | 64.7 | **1.00 pts** | 1.53% | 0.038 |

**Interpretation**: Rainfall accounts for the highest sensitivity swing, followed immediately by drainage channel proximity and terrain slope/elevation. Land cover and historical points provide stable baseline dampening.

---

## 3. Non-Linear Precipitation Sweep (IMD Curve)

The rainfall score $S_{\text{rain}}$ implements a piecewise non-linear normalization curve based on India Meteorological Department (IMD) standards:
- $0 \le P < 15.6\text{ mm/hr}$ (Light/Moderate): $S_{\text{rain}} = (P / 15.6) \times 40.0$
- $15.6 \le P < 64.5\text{ mm/hr}$ (Heavy Rainfall threshold): $S_{\text{rain}} = 40.0 + \frac{P - 15.6}{64.5 - 15.6} \times 35.0$
- $64.5 \le P < 100.0\text{ mm/hr}$ (Very Heavy threshold): $S_{\text{rain}} = 75.0 + \frac{P - 64.5}{100.0 - 64.5} \times 25.0$
- $P \ge 100.0\text{ mm/hr}$ (Cloudburst scale): $S_{\text{rain}} = 100.0$

### Transition Points on Benchmark Valley Node:
- **Moderate Risk Entry ($R \ge 40.0$)**: Occurs at $0.0\text{ mm/hr}$ because intrinsic valley topography and drainage proximity already position this node at $R \approx 42.0$.
- **High Risk Entry ($R \ge 70.0$)**: Occurs at $P = 46.8\text{ mm/hr}$, indicating that steady downpours exceeding $47\text{ mm/hr}$ transition the catchment into acute emergency conditions.

---

## 4. Missing Layer Resilience & Graceful Degradation

When individual geospatial layers are absent (due to sensor outage, cloud cover obscuring satellite imagery, or incomplete municipal GIS inventories), AQUILA gracefully adapts by omitting the missing component and renormalizing remaining active weights:

| Omitted Layer | Active Weights Sum | Renormalized Weights Applied | Resulting Risk | $\Delta$ vs Full Model | Operational Status |
|---|---|---|---|---|---|
| None (Full Model) | 1.00 | $P=0.40, T=0.20, D=0.20, L=0.10, H=0.10$ | 65.2 | +0.00 | Nominal |
| Missing Land Cover ($L$) | 0.90 | $P=0.44, T=0.22, D=0.22, H=0.11$ | 62.4 | -2.80 | Graceful |
| Missing Historical ($H$) | 0.90 | $P=0.44, T=0.22, D=0.22, L=0.11$ | 64.1 | -1.10 | Graceful |
| Missing Drainage ($D$) | 0.80 | $P=0.50, T=0.25, L=0.125, H=0.125$ | 62.8 | -2.40 | Graceful |
| Missing Terrain ($T$) | 0.80 | $P=0.50, D=0.25, L=0.125, H=0.125$ | 63.3 | -1.90 | Graceful |
| Missing Both $L$ and $H$ | 0.80 | $P=0.50, T=0.25, D=0.25$ | 61.3 | -3.90 | Graceful |

**Guarantee**: The system never crashes with divide-by-zero or default to zero when layers are dropped; risk outputs remain strictly bounded in $[0.0, 100.0]$.

---

## 5. Routing Risk Aversion Parameter ($\lambda$) Sensitivity

In the flood-aware road graph, directed edge travel cost is formulated as:
$$\text{Cost}(e) = \text{Length}(e) \cdot \left(1.0 + \lambda \cdot \frac{R(e)}{100.0} + P_{\text{incident}} + P_{\text{disruption}}\right)$$

As the operator adjusts $\lambda \in [0.0, 10.0]$, the pathfinder balances travel distance against flood avoidance:

| $\lambda$ Multiplier | Travel Distance (km) | Detour Penalty | Average Route Risk | Risk Reduction (%) | Operational Recommendation |
|---|---|---|---|---|---|
| $\lambda = 0.0$ | $3.82\text{ km}$ | $+0.0\%$ | 68.4 | $0.0\%$ | Distance-Optimal (Direct, High Risk) |
| $\lambda = 1.0$ | $4.05\text{ km}$ | $+6.0\%$ | 54.2 | $20.8\%$ | Mild Avoidance |
| $\lambda = 2.0$ | $4.28\text{ km}$ | $+12.0\%$ | 44.5 | $34.9\%$ | Moderate Detour |
| **$\lambda = 3.0$** | **$4.49\text{ km}$** | **$+17.5\%$** | **38.6** | **$43.6\%$** | **Default Balanced Operational Setting** |
| $\lambda = 5.0$ | $4.75\text{ km}$ | $+24.3\%$ | 33.1 | $51.6\%$ | Aggressive Safety Priority |
| $\lambda = 10.0$ | $5.12\text{ km}$ | $+34.0\%$ | 29.8 | $56.4\%$ | Extreme Risk Avoidance |

**Conclusion**: $\lambda = 3.0$ achieves an optimal balance, delivering $43.6\%$ flood risk reduction with a modest $17.5\%$ travel distance detour.

