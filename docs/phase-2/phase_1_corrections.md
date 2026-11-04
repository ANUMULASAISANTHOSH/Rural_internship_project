# AQUILA — Phase 1 Corrections & Research Validation

## 1. Executive Summary

Phase 2 mandates an empirical and scholarly audit of statements, figures, and technical assumptions recorded during Phase 1. Rather than silently accepting preliminary claims, this document reconciles discrepancies between Phase 1 specifications and primary data sources acquired during geospatial processing.

---

## 2. Historical Flood Statistics (October 2020 Event)

### Discrepancy Analysis: Fatalities and Damage Scope

In Phase 1 documentation, preliminary text referenced *"over 80 fatalities"* associated with the October 2020 floods. An audit of primary institutional disaster reports demonstrates that fatality counts vary widely depending on the reporting boundary (Telangana State vs. Greater Hyderabad Municipal Corporation vs. Old City districts).

| Metric | Phase 1 Preliminary Claim | Verified Primary Figure | Geographic Scope | Reporting Period | Source Authority | Publication Date & Reference | Provenance & Verification |
|---|---|---|---|---|---|---|---|
| **Human Fatalities** | "Over 80 deaths across Hyderabad" | **33 fatalities** | Greater Hyderabad Municipal Corporation (GHMC) limits | Oct 13–15, 2020 | NITI Aayog Case Study on Urban Floods | 2021 ([NITI Aayog Report Node 328](https://origin04082023-niti.nic.in/node/328)) | DIRECTLY_VERIFIED (Official Government Audit) |
| **Statewide Fatalities** | Unspecified | **81 fatalities** | Entire Telangana State (33 districts, primarily Ranga Reddy, Medchal-Malkajgiri, Hyderabad) | Oct 11–21, 2020 | Government of Telangana Disaster Management Dept / NDMA | Oct 2020 State Memorandum to MHA | SECONDARY_REPORTING (Consolidated State Total) |
| **Peak 24-hr Rainfall** | "Up to 320 mm" | **324.5 mm** | Ghatkesar AWS, Medchal-Malkajgiri | 08:30 IST Oct 13 to 08:30 IST Oct 14, 2020 | Telangana Development Planning Society (TGDPS) | Oct 14, 2020 Weather Bulletin | DIRECTLY_VERIFIED (Automated Weather Station) |
| **Western Corridor Rainfall** | "Extreme precipitation" | **163.5 mm** (Gachibowli), **205.0 mm** (Serilingampally) | Western Hyderabad IT Corridor / Manikonda perimeter | Oct 13–14, 2020 | TGDPS Network Archive | Oct 2020 Rainfall Log | DIRECTLY_VERIFIED (Automated Weather Station) |
| **Direct Economic Loss** | "Over ₹5,000 Crores" | **₹6,700 Crores (initial estimate)**; ₹5,000 Cr requested from National Disaster Response Fund (NDRF) | GHMC and surrounding urban agglomeration | October 2020 | Chief Minister's Office (CMO) Telangana Assessment | Oct 16, 2020 Official Communiqué | SECONDARY_REPORTING (Government Assessment) |

> [!IMPORTANT]
> **Resolution:** AQUILA Phase 2 adopts the **33 fatalities within GHMC** figure for Hyderabad municipal analysis and explicitly notes the **81 fatalities statewide** figure when discussing regional disaster impact. Casualties across different administrative levels are never conflated.

---

## 3. Manikonda Geographical & Environmental Claims

### 3.1 Catchment Area & Boundary Definition
- **Phase 1 Preliminary Claim:** Catchment area was stated as a fixed `15.5 km²`.
- **Phase 2 Audit & Geospatial Measurement:**
  - The `15.5 km²` figure corresponds approximately to the municipal jurisdiction of the newly created Manikonda Municipality (constituted in 2019 from Manikonda and Puppalaguda gram panchayats).
  - The actual hydrological catchment draining through the Manikonda-Puppalaguda valley into Neknampur Lake encompasses approximately **22.4 km²**, bounded by the granite ridgelines of Khajaguda to the north and Gandipet to the west.
  - The active computational study envelope defined in AQUILA (`78.3455°E to 78.4195°E, 17.3605°N to 17.4245°N`) encompasses **55.63 km²** to capture upstream boundary inflows and downstream receiving channels without boundary truncation.
- **Correction Status:** Corrected. Boundaries are now categorized into (a) Municipal Administrative Entity, (b) Natural Hydrological Catchment, and (c) Analysis Bounding Box.

### 3.2 Elevation and Slope Dynamics
- **Phase 1 Preliminary Claim:** Elevation range was reported as `580 m to 515 m` (total relief: 65 m).
- **Phase 2 DEM Measurement (Copernicus GLO-30 DSM):**
  - Minimum elevation: **492.7 m** (downstream channel exiting southeast towards Golconda/Shaikpet).
  - Maximum elevation: **638.7 m** (Khajaguda Hills granitic ridge / telecom towers).
  - Mean elevation: **538.8 m ± 24.9 m**.
  - Slope range: **0.0° to 36.85°** (mean slope: 3.84°).
  - Over 62% of the pilot area exhibits shallow slopes (< 3.0°), indicating natural flat valley bottoms prone to extended ponding when drainage channels are restricted.
- **Correction Status:** Corrected. Phase 1 underreported the total topographic relief by 81 m because it evaluated only urban settlements rather than the surrounding terrain ridges.

### 3.3 Impervious Surface Fraction
- **Phase 1 Preliminary Claim:** Impervious surface was cited as `>75%`.
- **Phase 2 Satellite Measurement (ESA WorldCover 10m 2021 v200):**
  - Across the entire 55.63 km² pilot analysis envelope:
    - **Class 50 (Built-up): 51.72%** (28.77 km²)
    - **Vegetation, Shrubland & Open Ground: 44.26%** (24.62 km²)
    - **Class 80 (Permanent Water Bodies): 0.44%** (0.24 km²)
    - **Class 60 (Bare Soil / Rock Outcrops): 3.58%** (1.99 km²)
  - Within dense urbanized settlement pockets (Alkapur Township Sector 1–12, Puppalaguda Main Road corridor), localized imperviousness does reach **72%–84%**.
- **Correction Status:** Refined. The blanket assertion that the entire catchment is >75% impervious is refuted at the regional scale, but confirmed as accurate for dense residential sub-clusters.

---

## 4. Institutional Capabilities & Scope Boundaries

Phase 1 preliminary documentation contained ambiguous phrases that could be misconstrued as implying Hyderabad lacks functional flood management systems.

### Clarifications and Boundaries
1. **HYDRAA (Hyderabad Disaster Response and Asset Monitoring and Protection Agency):**
   - *Existing Capability:* HYDRAA actively monitors lake encroachments, coordinates heavy machinery for emergency culvert clearing, and operates monsoon disaster rescue teams.
   - *AQUILA Boundary:* AQUILA does not issue official orders, enforce zoning laws, or dispatch municipal personnel. AQUILA provides decision-support risk modeling and routing analytics.
2. **GHMC Emergency Operation Centre (EOC):**
   - *Existing Capability:* Operates monsoon squads, static de-watering pumps, and receives public complaints via Dial 100 and GHMC App.
   - *AQUILA Boundary:* AQUILA is an academic prototype. It does not replace the official municipal grievance ticketing system.
3. **IMD & TGDPS:**
   - *Existing Capability:* IMD issues authoritative Nowcasts, Color-coded Warnings (Yellow/Orange/Red), and radar mosaics. TGDPS operates an automated weather network across Telangana.
   - *AQUILA Boundary:* AQUILA ingests weather observations as inputs to spatial models. It does not generate independent weather forecasts or issue statutory public alerts.

---

## 5. Rainfall Data Access Reality

- **Phase 1 Assumption:** Direct live API polling of the TGDPS telemetry portal.
- **Phase 2 Reality Check:**
  - TGDPS does not provide a public, unauthenticated REST API for automated streaming ingestion. Data on `tsdps.telangana.gov.in` is published via server-side rendered HTML tables and PDF weather summaries.
  - Furthermore, **no official AWS station exists within the core Manikonda municipal polygon**. The nearest automated stations are Gachibowli (~3.8 km north), Serilingampally (~13.5 km northwest), and Rajendranagar (~8.2 km south).
- **Correction Status:** Updated architecture. AQUILA uses historical records from perimeter stations as spatial proxies and incorporates a verified synthetic hyetograph module for demonstration and simulation modes.

---

## 6. Synthetic Scenario Rainfall Specification

- **Phase 1 Preliminary Claim:** A "120 mm rainfall event" was referenced without specifying temporal distribution, storm duration, or return period.
- **Phase 2 Scientific Specification:**
  - Storm profile: 120 mm cumulative design storm over 3 hours (180 minutes).
  - Methodology: Chicago Design Storm synthetic hyetograph discretized into 13 time steps of 15 minutes.
  - Peak intensity: **70.0 mm/hr** occurring at minute 75 (hour 1.25), reflecting convective monsoon cloudburst characteristics.
  - Frequency / Return Period: Approximately equivalent to a 25-to-50 year return period storm for western Hyderabad based on IMD Intensity-Duration-Frequency (IDF) empirical relationships.
  - Provenance: Classified strictly as `SIMULATED`.

---

## 7. Summary of Phase 1 Status Updates

| Phase 1 Statement | Initial Status | Phase 2 Audit Result | Final Classification |
|---|---|---|---|
| 80+ deaths in Hyderabad (Oct 2020) | Asserted | 33 in GHMC; 81 statewide | CORRECTED |
| Catchment area = 15.5 km² | Asserted | 15.5 km² = Admin; 22.4 km² = Hydrological; 55.6 km² = Study BBOX | REFINED & DISTINGUISHED |
| Elevation 515–580 m | Asserted | Actual DEM: 492.7 m to 638.7 m | CORRECTED |
| Imperviousness >75% | Asserted | Regional: 51.72%; Urban core: 70–84% | REFINED WITH EMPIRICAL DATA |
| Live TGDPS API | Assumed | No public REST API; HTML tables only | WORKAROUND ARCHITECTED |
| Complete OSM Drainage Network | Assumed | Only 21 surface channels mapped (Major gap) | DOCUMENTED WITH MITIGATION |
| 120 mm Storm Parameters | Unspecified | 180 min Chicago hyetograph, peak 70 mm/hr | SPECIFIED AS `SIMULATED` |

