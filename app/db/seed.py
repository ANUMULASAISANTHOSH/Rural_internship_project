"""
AQUILA MVP - Database Initialization & Seeder
Creates tables and seeds realistic synthetic emergency resources and initial rainfall records.
All synthetic resources are explicitly tagged with [DEMO SYNTHETIC] and provenance="SIMULATED".
"""

import os
import sys
import csv
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.database import engine, Base, SessionLocal, utc_now
from app.db.models import Resource, RainfallObservation, AuditHistory, Incident

INITIAL_RESOURCES = [
    {
        "resource_code": "RES-PUMP-01",
        "resource_name": "[DEMO SYNTHETIC] GHMC High-Capacity Dewatering Squad A",
        "resource_type": "DEWATERING_PUMP",
        "latitude": 17.3990,
        "longitude": 78.3810,
        "availability_status": "AVAILABLE",
        "capability": "PUMPING",
        "provenance": "SIMULATED"
    },
    {
        "resource_code": "RES-PUMP-02",
        "resource_name": "[DEMO SYNTHETIC] Alkapur Emergency Trailer Pump Unit",
        "resource_type": "DEWATERING_PUMP",
        "latitude": 17.3930,
        "longitude": 78.3750,
        "availability_status": "AVAILABLE",
        "capability": "PUMPING",
        "provenance": "SIMULATED"
    },
    {
        "resource_code": "RES-BOAT-01",
        "resource_name": "[DEMO SYNTHETIC] HYDRAA Inflatable Rescue Boat Unit 1",
        "resource_type": "RESCUE_BOAT",
        "latitude": 17.3890,
        "longitude": 78.3860,
        "availability_status": "AVAILABLE",
        "capability": "WATER_RESCUE",
        "provenance": "SIMULATED"
    },
    {
        "resource_code": "RES-AMB-01",
        "resource_name": "[DEMO SYNTHETIC] Continental Emergency Medical Ambulance 1",
        "resource_type": "AMBULANCE",
        "latitude": 17.4170,
        "longitude": 78.3530,
        "availability_status": "AVAILABLE",
        "capability": "MEDICAL_EVAC",
        "provenance": "SIMULATED"
    },
    {
        "resource_code": "RES-SQUAD-01",
        "resource_name": "[DEMO SYNTHETIC] Puppalaguda Monsoon Quick Response Team",
        "resource_type": "MONSOON_SQUAD",
        "latitude": 17.4040,
        "longitude": 78.3770,
        "availability_status": "AVAILABLE",
        "capability": "ROAD_CLEARING",
        "provenance": "SIMULATED"
    },
    {
        "resource_code": "RES-EARTH-01",
        "resource_name": "[DEMO SYNTHETIC] GHMC Heavy Excavator / Culvert Clearer",
        "resource_type": "HEAVY_EARTHMOVER",
        "latitude": 17.4080,
        "longitude": 78.3950,
        "availability_status": "AVAILABLE",
        "capability": "DEBRIS_CLEARING",
        "provenance": "SIMULATED"
    }
]

def init_db(seed_resources=True):
    print("[DB] Initializing SQLite database schema...")
    Base.metadata.create_all(bind=engine)

    if not seed_resources:
        return

    db = SessionLocal()
    try:
        # Check if resources already seeded
        existing_res = db.query(Resource).count()
        if existing_res == 0:
            print("[DB] Seeding synthetic emergency response resources...")
            for res_data in INITIAL_RESOURCES:
                res = Resource(
                    resource_code=res_data["resource_code"],
                    resource_name=res_data["resource_name"],
                    resource_type=res_data["resource_type"],
                    latitude=res_data["latitude"],
                    longitude=res_data["longitude"],
                    availability_status=res_data["availability_status"],
                    capability=res_data["capability"],
                    provenance=res_data.get("provenance", "SIMULATED"),
                    created_at=utc_now()
                )
                db.add(res)
            
            # Log to audit history
            audit = AuditHistory(
                entity_type="SYSTEM",
                entity_id="SEED-001",
                action="INITIAL_SEED",
                details=f"Seeded {len(INITIAL_RESOURCES)} synthetic emergency demonstration resources for Manikonda pilot.",
                timestamp=utc_now()
            )
            db.add(audit)
            db.commit()
            print(f"[DB] Successfully seeded {len(INITIAL_RESOURCES)} resources.")
        else:
            # Ensure availability is reset to AVAILABLE and names guaranteed [DEMO SYNTHETIC]
            for res_data in INITIAL_RESOURCES:
                r = db.query(Resource).filter(Resource.resource_code == res_data["resource_code"]).first()
                if r:
                    r.availability_status = "AVAILABLE"
                    if "[DEMO SYNTHETIC]" not in r.resource_name:
                        r.resource_name = res_data["resource_name"]
            db.commit()
            print(f"[DB] Resources verified ({existing_res} records found).")

        # Seed baseline rainfall if empty
        existing_rain = db.query(RainfallObservation).count()
        if existing_rain == 0:
            rain_csv = os.path.join(BASE_DIR, "data", "processed", "vector", "rainfall_historical_validated.csv")
            if os.path.exists(rain_csv):
                with open(rain_csv, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        obs = RainfallObservation(
                            station_id=row["station_id"],
                            rainfall_mm_per_hour=float(row["rainfall_rate_mm_hr"]),
                            observation_time=utc_now(),
                            source_type=row.get("provenance", "HISTORICAL"),
                            is_synthetic=False
                        )
                        db.add(obs)
                db.commit()
                print("[DB] Seeded baseline rainfall observations from Phase 2 archive.")
    except Exception as e:
        db.rollback()
        print(f"[DB] Seeding error: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
