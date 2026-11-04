"""
AQUILA Phase 2 - Rainfall Data Processing
Module: process_rainfall.py
Description:
    Validates and normalizes rainfall observation records.
    Enforces strict provenance tagging (OBSERVED, HISTORICAL, SIMULATED).
    Outputs validated CSVs and a JSON station inventory.
"""

import os, json, csv, sys
from datetime import datetime

BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_HIST  = os.path.join(BASE_DIR, "data", "raw", "rainfall", "historical_october_2020_rainfall.csv")
RAW_SIM   = os.path.join(BASE_DIR, "data", "raw", "rainfall", "synthetic_120mm_storm_hyetograph.csv")
OUT_DIR   = os.path.join(BASE_DIR, "data", "processed", "vector")
os.makedirs(OUT_DIR, exist_ok=True)

# IMD standard rainfall severity thresholds (mm/hr)
SEVERITY_THRESHOLDS = [
    (0.0,   2.5,   "Light"),
    (2.5,   15.6,  "Moderate"),
    (15.6,  64.5,  "Heavy"),
    (64.5,  115.5, "Very Heavy"),
    (115.5, 9999,  "Extremely Heavy"),
]

def classify_severity(rate_mm_hr):
    for lo, hi, label in SEVERITY_THRESHOLDS:
        if lo <= rate_mm_hr < hi:
            return label
    return "Extremely Heavy"


def validate_rainfall_record(row, row_num):
    errors = []
    try:
        rate = float(row.get("rainfall_rate_mm_hr", ""))
        if rate < 0:
            errors.append(f"row {row_num}: negative rainfall ({rate})")
        if rate > 250:
            errors.append(f"row {row_num}: physically implausible rainfall ({rate} mm/hr > 250)")
    except (ValueError, TypeError):
        errors.append(f"row {row_num}: non-numeric rainfall_rate_mm_hr")

    provenance = row.get("provenance", "")
    if provenance not in ("OBSERVED", "HISTORICAL", "SIMULATED", "MANUALLY_SEEDED", "MODEL_ESTIMATE"):
        errors.append(f"row {row_num}: invalid provenance tag: '{provenance}'")

    return errors


def process_historical_rainfall():
    print("[RAIN] Processing historical rainfall records...")
    if not os.path.exists(RAW_HIST):
        print(f"[RAIN] WARNING: Historical rainfall file not found: {RAW_HIST}")
        return {}

    with open(RAW_HIST, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    all_errors = []
    valid_rows = []
    station_registry = {}

    for i, row in enumerate(rows):
        errs = validate_rainfall_record(row, i + 2)
        if errs:
            all_errors.extend(errs)
            continue

        # Add severity classification
        rate = float(row["rainfall_rate_mm_hr"])
        row["severity_imd"] = classify_severity(rate)

        # Station registry
        sid = row.get("station_id", "UNKNOWN")
        if sid not in station_registry:
            station_registry[sid] = {
                "station_id":   sid,
                "station_name": row.get("station_name", ""),
                "provider":     row.get("provider", ""),
                "latitude":     float(row.get("latitude", 0)),
                "longitude":    float(row.get("longitude", 0)),
                "distance_to_manikonda_centroid_km": round(
                    ((float(row.get("longitude", 0)) - 78.3825)**2 * (104**2) +
                     (float(row.get("latitude",  0)) - 17.3925)**2 * (111**2)) ** 0.5,
                    2),
                "provenance":   row.get("provenance"),
                "coverage_note": (
                    "Station is not within Manikonda municipal boundary. "
                    "Used as nearest available spatial proxy. "
                    "Spatial interpolation (IDW) required for grid estimation."
                ) if float(row.get("longitude", 0)) < 78.35 or float(row.get("longitude", 0)) > 78.42
                else "Station within pilot study area approximate bounds.",
                "manikonda_coverage": "PROXY_STATION"
            }
        valid_rows.append(row)

    stats = {
        "total_raw_records": len(rows),
        "validated_records": len(valid_rows),
        "rejected_records": len(rows) - len(valid_rows),
        "validation_errors": all_errors,
        "stations": list(station_registry.values()),
        "tgdps_live_api_status": (
            "NOT_AVAILABLE: TGDPS portal (tsdps.telangana.gov.in) does not expose a public "
            "machine-readable REST API. Data requires manual download from the portal or "
            "institutional access. These records are based on published post-event reports "
            "and are classified HISTORICAL."
        ),
        "imd_gridded_api_status": (
            "ACCESSIBLE_WITH_LIMITATIONS: IMD gridded daily rainfall (0.25° × 0.25°) "
            "is available via IMD Pune for academic use but resolution (~25 km grid) is "
            "insufficient to distinguish Manikonda from surrounding Hyderabad districts."
        )
    }

    # Write validated output
    out_path = os.path.join(OUT_DIR, "rainfall_historical_validated.csv")
    if valid_rows:
        fieldnames = list(valid_rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(valid_rows)
    print(f"[RAIN] Validated historical records: {out_path} ({len(valid_rows)} rows)")
    print(f"[RAIN] Stations: {list(station_registry.keys())}")

    rpt_path = os.path.join(OUT_DIR, "rainfall_validation_report.json")
    with open(rpt_path, "w") as f:
        json.dump(stats, f, indent=2)
    return stats


def process_synthetic_hyetograph():
    print("[RAIN] Processing synthetic hyetograph...")
    if not os.path.exists(RAW_SIM):
        print(f"[RAIN] WARNING: Synthetic hyetograph not found: {RAW_SIM}")
        return {}

    with open(RAW_SIM, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    valid_rows = []
    all_errors = []
    cumulative_check = 0.0

    for i, row in enumerate(rows):
        errs = validate_rainfall_record(row, i + 2)
        if errs:
            all_errors.extend(errs)
            continue

        provenance = row.get("provenance", "")
        if provenance != "SIMULATED":
            all_errors.append(f"row {i+2}: synthetic hyetograph must have provenance=SIMULATED, got {provenance}")
            continue

        cumulative_check += float(row.get("incremental_depth_mm", 0))
        valid_rows.append(row)

    total_depth = round(cumulative_check, 2)
    scenario_note = (
        "DESIGN STORM NOTE: This 120 mm / 3-hour hyetograph is a CALIBRATED ILLUSTRATIVE scenario, "
        "NOT a directly measured event. The asymmetric triangular distribution (Chicago Design Storm "
        "pattern) peaks at 70 mm/hr at T=45 min. It is calibrated to approximate a 1-in-25 to "
        "1-in-50 year design storm depth for Hyderabad western sub-catchments based on IMD gridded "
        "rainfall frequency analysis and the October 2020 event analog. "
        "Return period assumption (1-in-25 yr) is UNVERIFIED and requires validation against "
        "official IDF curves from IMD or GHMC Stormwater Master Plan."
    )

    stats = {
        "scenario_designation": "SCN-MKD-001 — Heavy Rainfall Manikonda",
        "total_steps": len(valid_rows),
        "total_cumulative_depth_mm": total_depth,
        "peak_rainfall_rate_mm_hr": 70.0,
        "duration_minutes": 180,
        "time_step_minutes": 15,
        "provenance": "SIMULATED",
        "design_storm_profile": "Asymmetric Triangular / Chicago Design Storm pattern",
        "assumed_return_period": "1-in-25 to 1-in-50 year (UNVERIFIED — ILLUSTRATIVE ONLY)",
        "validation_errors": all_errors,
        "scenario_note": scenario_note
    }

    out_path = os.path.join(OUT_DIR, "rainfall_synthetic_hyetograph_validated.csv")
    if valid_rows:
        fieldnames = list(valid_rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(valid_rows)
    print(f"[RAIN] Synthetic hyetograph validated: {out_path}")
    print(f"[RAIN] Total scenario depth: {total_depth} mm over {stats['duration_minutes']} min")

    rpt_path = os.path.join(OUT_DIR, "rainfall_synthetic_report.json")
    with open(rpt_path, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"[RAIN] Scenario note: {scenario_note[:120]}...")
    return stats


def main():
    print("=" * 60)
    print("AQUILA PHASE 2: RAINFALL DATA PROCESSING")
    print("=" * 60)
    h_stats = process_historical_rainfall()
    s_stats = process_synthetic_hyetograph()
    print("=" * 60)
    print(f"[SUCCESS] Historical records: {h_stats.get('validated_records', 0)}, "
          f"Synthetic steps: {s_stats.get('total_steps', 0)}")
    print("=" * 60)


if __name__ == "__main__":
    main()

