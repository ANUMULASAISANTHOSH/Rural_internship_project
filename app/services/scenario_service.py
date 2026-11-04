"""
AQUILA MVP - Scenario Simulator Engine
Scenario ID: MANI-HEAVY-001 (Heavy Rainfall - Manikonda)
Loads the 120mm synthetic hyetograph, steps through timeline,
recalculates risk index dynamically, and deterministically injects simulated incidents.
"""

import os
import csv
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.database import utc_now
from app.db.models import Incident, Resource, RainfallObservation, RiskAssessment, IncidentAssignment, AuditHistory, RoadDisruption
from app.services.risk_engine import compute_geographic_risk
from app.services.road_network_service import road_network_service

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HYETOGRAPH_CSV = os.path.join(BASE_DIR, "data", "processed", "vector", "rainfall_synthetic_hyetograph_validated.csv")

class ScenarioManager:
    def __init__(self):
        self.scenario_id = "MANI-HEAVY-001"
        self.scenario_name = "Heavy Rainfall — Manikonda"
        self.is_active = False
        self.current_step = 0
        self.steps: List[Dict[str, Any]] = []
        self._load_hyetograph()

    def _load_hyetograph(self):
        self.steps = []
        if os.path.exists(HYETOGRAPH_CSV):
            with open(HYETOGRAPH_CSV, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    self.steps.append({
                        "step_index": i,
                        "time_minutes": int(row.get("time_minutes", i * 15)),
                        "rainfall_rate_mm_hr": float(row.get("rainfall_rate_mm_hr", 0.0)),
                        "cumulative_depth_mm": float(row.get("cumulative_depth_mm", 0.0)),
                        "severity_label": row.get("severity_label", "Moderate"),
                        "provenance": "SIMULATED"
                    })
        else:
            # Fallback default steps if file missing
            for i, r in enumerate([5.0, 15.0, 35.0, 70.0, 65.0, 45.0, 30.0, 20.0, 12.0, 8.0, 4.0, 2.0, 0.0]):
                self.steps.append({
                    "step_index": i,
                    "time_minutes": i * 15,
                    "rainfall_rate_mm_hr": r,
                    "cumulative_depth_mm": round(r * 0.25, 2),
                    "severity_label": "Simulated",
                    "provenance": "SIMULATED"
                })

    def get_status(self) -> Dict[str, Any]:
        total_steps = len(self.steps)
        current_data = self.steps[self.current_step] if self.steps and self.current_step < total_steps else {}
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "is_active": self.is_active,
            "current_step": self.current_step,
            "total_steps": total_steps,
            "current_time_minutes": current_data.get("time_minutes", 0),
            "current_rainfall_rate_mm_hr": current_data.get("rainfall_rate_mm_hr", 0.0),
            "cumulative_depth_mm": current_data.get("cumulative_depth_mm", 0.0),
            "provenance": "SIMULATED",
            "is_completed": self.current_step >= total_steps - 1
        }

    def start_scenario(self, db: Session) -> Dict[str, Any]:
        self.is_active = True
        self.current_step = 0
        
        # Log to audit history
        audit = AuditHistory(
            entity_type="SCENARIO",
            entity_id=self.scenario_id,
            action="SCENARIO_STARTED",
            details=f"Operator initiated scenario {self.scenario_name} (MANI-HEAVY-001).",
            timestamp=utc_now()
        )
        db.add(audit)
        db.commit()
        return self.get_status()

    def advance_step(self, db: Session) -> Dict[str, Any]:
        if not self.is_active:
            self.start_scenario(db)

        if self.current_step < len(self.steps) - 1:
            self.current_step += 1

        step_data = self.steps[self.current_step]
        rate = step_data["rainfall_rate_mm_hr"]
        t_min = step_data["time_minutes"]

        # Record simulated rainfall observation
        sim_obs = RainfallObservation(
            station_id="SCENARIO-MKD-SYNTH",
            rainfall_mm_per_hour=rate,
            observation_time=utc_now(),
            source_type="SIMULATED",
            is_synthetic=True
        )
        db.add(sim_obs)

        # Compute dynamic risk
        risk = compute_geographic_risk(
            rainfall_rate_mm_hr=rate,
            elevation_m=518.0,
            slope_degrees=1.8,
            distance_to_waterway_m=80.0,
            landcover_class=50,
            distance_to_flood_point_m=200.0
        )

        risk_rec = RiskAssessment(
            location_id=f"SCENARIO-T{t_min}",
            rainfall_score=risk["component_breakdown"]["rainfall_score"],
            terrain_score=risk["component_breakdown"]["terrain_score"],
            drainage_score=risk["component_breakdown"]["drainage_score"],
            landcover_score=risk["component_breakdown"]["landcover_score"],
            historical_score=risk["component_breakdown"]["historical_score"],
            final_risk_score=risk["final_risk_score"],
            risk_category=risk["risk_category"],
            assessment_time=utc_now(),
            source_type="SIMULATED"
        )
        db.add(risk_rec)

        generated_incidents = []
        generated_disruptions = []
        # Deterministic Incident Generation Rule:
        # Step 3: Peak intensity 70 mm/hr (t = 45m) -> Generates Alkapur road flooding
        if self.current_step == 3:
            existing_inc = db.query(Incident).filter(Incident.incident_code == "INC-SIM-001").first()
            if not existing_inc:
                inc1 = Incident(
                    incident_code="INC-SIM-001",
                    title="Alkapur Township Sector 1 Roadway Inundation",
                    description="Severe overland sheet runoff ponding across main sector arterial. Depth approx 0.45m; sedan traffic stalled.",
                    latitude=17.3912,
                    longitude=78.3845,
                    incident_type="WATERLOGGING",
                    severity="HIGH",
                    status="REPORTED",
                    source_type="SIMULATED",
                    created_at=utc_now()
                )
                db.add(inc1)
                generated_incidents.append("INC-SIM-001")

            # Deterministic simulated road disruption for Phase 4 routing
            existing_dis = db.query(RoadDisruption).filter(RoadDisruption.disruption_code == "DISR-SIM-001").first()
            if not existing_dis:
                dis1 = RoadDisruption(
                    disruption_code="DISR-SIM-001",
                    title="Puppalaguda Main Road Culvert Overtopping & Debris Blockage",
                    description="Backwater stagnation from Chinna Cheruvu outfall culvert; road impassable for light vehicles.",
                    latitude=17.3985,
                    longitude=78.3810,
                    radius_meters=200.0,
                    penalty_factor=25.0,
                    status="ACTIVE",
                    provenance="SIMULATED",
                    created_at=utc_now()
                )
                db.add(dis1)
                generated_disruptions.append("DISR-SIM-001")

        # Step 5: (t = 75m) -> Generates Neknampur Lake weir breach
        elif self.current_step == 5:
            existing_inc = db.query(Incident).filter(Incident.incident_code == "INC-SIM-002").first()
            if not existing_inc:
                inc2 = Incident(
                    incident_code="INC-SIM-002",
                    title="Neknampur Lake Spillway Overtopping",
                    description="Lake storage reached Full Tank Level; uncontrolled discharge overtopping weir into downstream colony culvert.",
                    latitude=17.3895,
                    longitude=78.3855,
                    incident_type="DRAIN_OVERFLOW",
                    severity="CRITICAL",
                    status="REPORTED",
                    source_type="SIMULATED",
                    created_at=utc_now()
                )
                db.add(inc2)
                generated_incidents.append("INC-SIM-002")

        # Update road network edge weights dynamically for flood-aware routing
        road_network_service.update_edge_weights(db_session=db, rainfall_rate_mm_hr=rate)

        # Audit history log
        audit = AuditHistory(
            entity_type="SCENARIO",
            entity_id=self.scenario_id,
            action="STEP_ADVANCED",
            details=f"Advanced to Step {self.current_step} (T={t_min}m). Rainfall={rate} mm/hr. Risk={risk['final_risk_score']} ({risk['risk_category']}). Injected Incidents: {generated_incidents}. Disruptions: {generated_disruptions}",
            timestamp=utc_now()
        )
        db.add(audit)
        db.commit()

        status = self.get_status()
        status["latest_risk"] = risk
        status["generated_incidents"] = generated_incidents
        status["generated_disruptions"] = generated_disruptions
        return status

    def reset_scenario(self, db: Session) -> Dict[str, Any]:
        """
        Deletes ONLY records tagged as SIMULATED, preserving all REPORTED or HISTORICAL data.
        Restores any assigned resources to AVAILABLE.
        """
        # Find simulated incidents
        sim_incidents = db.query(Incident).filter(Incident.source_type == "SIMULATED").all()
        sim_inc_ids = [inc.id for inc in sim_incidents]

        # Reset assigned resources linked to simulated incidents
        if sim_inc_ids:
            assignments = db.query(IncidentAssignment).filter(IncidentAssignment.incident_id.in_(sim_inc_ids)).all()
            for asg in assignments:
                res = db.query(Resource).filter(Resource.id == asg.resource_id).first()
                if res and res.availability_status == "ASSIGNED":
                    res.availability_status = "AVAILABLE"

            # Delete simulated assignments
            db.query(IncidentAssignment).filter(IncidentAssignment.incident_id.in_(sim_inc_ids)).delete(synchronize_session=False)

        # Delete simulated incidents
        deleted_incidents = len(sim_incidents)
        db.query(Incident).filter(Incident.source_type == "SIMULATED").delete(synchronize_session=False)

        # Delete simulated rainfall observations
        deleted_rain = db.query(RainfallObservation).filter(RainfallObservation.source_type == "SIMULATED").delete(synchronize_session=False)

        # Delete simulated risk assessments
        db.query(RiskAssessment).filter(RiskAssessment.source_type == "SIMULATED").delete(synchronize_session=False)

        # Delete simulated road disruptions
        deleted_disruptions = db.query(RoadDisruption).filter(RoadDisruption.provenance == "SIMULATED").delete(synchronize_session=False)

        # Reset road network graph edge weights to baseline
        road_network_service.update_edge_weights(db_session=db, rainfall_rate_mm_hr=0.0)

        self.is_active = False
        self.current_step = 0

        # Audit log
        audit = AuditHistory(
            entity_type="SCENARIO",
            entity_id=self.scenario_id,
            action="SCENARIO_RESET",
            details=f"Scenario reset completed. Purged {deleted_incidents} simulated incidents, {deleted_disruptions} simulated disruptions, and {deleted_rain} simulated rainfall records. Historical and real-world records preserved.",
            timestamp=utc_now()
        )
        db.add(audit)
        db.commit()

        return {
            "status": "RESET_SUCCESSFUL",
            "scenario_id": self.scenario_id,
            "deleted_simulated_incidents": deleted_incidents,
            "deleted_simulated_disruptions": deleted_disruptions,
            "deleted_simulated_rainfall_records": deleted_rain,
            "preserved_records": "Historical and user-reported records untouched."
        }

scenario_manager = ScenarioManager()

