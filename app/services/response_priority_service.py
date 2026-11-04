"""
AQUILA Phase 5 - Emergency Response Priority Engine
Calculates explainable multi-criteria priority scores (P in [0, 100]) for active flood incidents:
    P = 0.30 * S_severity + 0.25 * R_geo + 0.20 * S_med_prox + 0.15 * S_road_tier + 0.10 * S_age

Human-in-the-Loop Governance:
- Ranks incidents and identifies candidate response resources.
- Strictly enforces operator authorization before any physical or simulated dispatch.
- Provides natural-language justification for every priority ranking.
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.database import utc_now, SessionLocal
from app.db.models import Incident, Resource, RainfallObservation
from app.services.risk_engine import compute_geographic_risk
from app.services.road_network_service import road_network_service
from app.services.accessibility_service import accessibility_service
from app.services.resource_service import haversine_distance_km, recommend_resource_for_incident

SEVERITY_SCORES = {
    "CRITICAL": 100.0,
    "HIGH": 75.0,
    "MODERATE": 50.0,
    "LOW": 25.0
}

HIGHWAY_TIER_SCORES = {
    "motorway": 100.0,
    "trunk": 95.0,
    "primary": 90.0,
    "secondary": 80.0,
    "tertiary": 60.0,
    "residential": 40.0,
    "service": 30.0,
    "unclassified": 25.0
}


class ResponsePriorityService:
    def __init__(self):
        pass

    def _get_medical_proximity(self, lat: float, lon: float) -> Dict[str, Any]:
        """Finds nearest medical facility and computes proximity impact score."""
        facilities = accessibility_service.facilities
        medical_facs = [f for f in facilities if f["category"] in ["hospital", "clinic", "pharmacy"]]
        if not medical_facs:
            medical_facs = facilities

        nearest_fac = None
        min_dist_m = 999999.0

        for f in medical_facs:
            dist_km = haversine_distance_km(lat, lon, f["latitude"], f["longitude"])
            dist_m = dist_km * 1000.0
            if dist_m < min_dist_m:
                min_dist_m = dist_m
                nearest_fac = f

        # Score formulation: Closer to medical facility = higher urgency
        if min_dist_m <= 300.0:
            score = 100.0
        elif min_dist_m <= 600.0:
            score = 80.0
        elif min_dist_m <= 1200.0:
            score = 55.0
        elif min_dist_m <= 2500.0:
            score = 30.0
        else:
            score = 15.0

        return {
            "score": score,
            "distance_m": round(min_dist_m, 1),
            "nearest_facility_name": nearest_fac["name"] if nearest_fac else "None within catchment",
            "nearest_facility_type": nearest_fac["category"] if nearest_fac else "unknown"
        }

    def _get_road_tier(self, lat: float, lon: float) -> Dict[str, Any]:
        """Snaps incident coordinate to road network and gets highway tier."""
        try:
            node_id, snap_dist_m = road_network_service.snap_to_node(lat, lon, must_be_in_largest_cc=True)
            out_edges = list(road_network_service.graph.out_edges(node_id, data=True))
            if out_edges:
                edge_data = out_edges[0][2]
                hw = edge_data.get("highway", "residential").lower()
                score = HIGHWAY_TIER_SCORES.get(hw, 40.0)
                return {
                    "score": score,
                    "highway_type": hw,
                    "snapped_distance_m": round(snap_dist_m, 1)
                }
        except Exception:
            pass
        return {"score": 40.0, "highway_type": "residential", "snapped_distance_m": 0.0}

    def _calculate_age_score(self, created_at: datetime) -> Dict[str, Any]:
        """Calculates age in minutes and escalating wait-time score."""
        now = utc_now()
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        delta_seconds = max(0.0, (now - created_at).total_seconds())
        minutes_open = round(delta_seconds / 60.0, 1)
        # Escalation: 1.5 points per minute, capped at 100
        score = min(100.0, round(minutes_open * 1.5, 2))
        return {
            "score": score,
            "minutes_open": minutes_open
        }

    def _find_candidate_resource(self, db: Session, inc: Incident) -> Optional[Dict[str, Any]]:
        """Finds nearest compatible available resource in read-only mode without mutating database."""
        from app.services.resource_service import CAPABILITY_MAPPING
        compatible_caps = CAPABILITY_MAPPING.get(inc.incident_type, ["PUMPING", "ROAD_CLEARING"])
        available_res = db.query(Resource).filter(Resource.availability_status == "AVAILABLE").all()
        best_res = None
        min_dist = 999999.0
        for r in available_res:
            if any(cap in r.capability for cap in compatible_caps):
                dist = haversine_distance_km(inc.latitude, inc.longitude, r.latitude, r.longitude)
                if dist < min_dist:
                    min_dist = dist
                    best_res = r
        if best_res:
            return {
                "resource_id": best_res.id,
                "resource_code": best_res.resource_code,
                "resource_name": best_res.resource_name,
                "resource_type": best_res.resource_type,
                "capability": best_res.capability,
                "distance_km": round(min_dist, 2)
            }
        return None

    def evaluate_incident_priorities(self, db: Session) -> Dict[str, Any]:
        """
        Evaluates and ranks all active incidents in the database.
        Active statuses: REPORTED, UNDER_REVIEW, ASSIGNED, IN_PROGRESS.
        """
        active_incidents = (
            db.query(Incident)
            .filter(Incident.status.in_(["REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS"]))
            .all()
        )

        # Get latest rainfall observation for real-time risk calculation
        latest_rain = db.query(RainfallObservation).order_by(RainfallObservation.id.desc()).first()
        current_rain_mm_hr = latest_rain.rainfall_mm_per_hour if latest_rain else 25.0

        prioritized_items = []

        for inc in active_incidents:
            lat = inc.latitude
            lon = inc.longitude

            # 1. Severity Score S_severity (30%)
            s_sev = SEVERITY_SCORES.get(inc.severity.upper(), 50.0)

            # 2. Local Geographic Risk R_geo (25%)
            elev = road_network_service._sample_elevation(lon, lat)
            slope = road_network_service._sample_slope(lon, lat)
            drain_dist = road_network_service._sample_waterway_distance(lon, lat)
            hist_dist = road_network_service._sample_flood_distance(lon, lat)

            geo_res = compute_geographic_risk(
                rainfall_rate_mm_hr=current_rain_mm_hr,
                elevation_m=elev,
                slope_degrees=slope,
                distance_to_waterway_m=drain_dist,
                landcover_class=50,
                distance_to_flood_point_m=hist_dist
            )
            r_geo = geo_res["final_risk_score"]

            # 3. Medical Proximity Score S_med_prox (20%)
            med_info = self._get_medical_proximity(lat, lon)
            s_med = med_info["score"]

            # 4. Road Tier Score S_road_tier (15%)
            road_info = self._get_road_tier(lat, lon)
            s_road = road_info["score"]

            # 5. Incident Age Score S_age (10%)
            age_info = self._calculate_age_score(inc.created_at)
            s_age = age_info["score"]

            # Composite Priority Formula:
            # P = 0.30*S_sev + 0.25*R_geo + 0.20*S_med + 0.15*S_road + 0.10*S_age
            p_score = round(0.30 * s_sev + 0.25 * r_geo + 0.20 * s_med + 0.15 * s_road + 0.10 * s_age, 2)
            p_score = min(100.0, max(0.0, p_score))

            if p_score >= 75.0:
                p_level = "P1_IMMEDIATE"
            elif p_score >= 55.0:
                p_level = "P2_URGENT"
            elif p_score >= 40.0:
                p_level = "P3_ELEVATED"
            else:
                p_level = "P4_STANDARD"

            # Check candidate resource recommendation in read-only mode without mutating DB
            candidate_resource = self._find_candidate_resource(db, inc)

            # Construct natural-language explainability justification
            justification = (
                f"{inc.severity} severity {inc.incident_type} (Sev={s_sev:.0f}); "
                f"local flood risk {r_geo:.1f}; "
                f"{road_info['highway_type'].title()} road arterial (Tier={s_road:.0f}); "
                f"{med_info['distance_m']}m from {med_info['nearest_facility_name']} (MedProx={s_med:.0f}); "
                f"pending for {age_info['minutes_open']}m (AgeEsc={s_age:.0f})."
            )

            prioritized_items.append({
                "incident_id": inc.id,
                "incident_code": inc.incident_code,
                "title": inc.title,
                "incident_type": inc.incident_type,
                "severity": inc.severity,
                "status": inc.status,
                "latitude": lat,
                "longitude": lon,
                "priority_score": p_score,
                "priority_level": p_level,
                "sub_scores": {
                    "severity_score": s_sev,
                    "geographic_risk_score": r_geo,
                    "medical_proximity_score": s_med,
                    "road_tier_score": s_road,
                    "age_escalation_score": s_age
                },
                "spatial_details": {
                    "nearest_medical_facility": med_info["nearest_facility_name"],
                    "medical_distance_m": med_info["distance_m"],
                    "road_classification": road_info["highway_type"],
                    "minutes_open": age_info["minutes_open"]
                },
                "candidate_resource": candidate_resource,
                "explainable_justification": justification,
                "requires_operator_approval": True,
                "auto_dispatched": False,
                "created_at": inc.created_at.isoformat()
            })

        # Sort descending by priority score P
        prioritized_items.sort(key=lambda x: x["priority_score"], reverse=True)

        # Assign rank numbers
        for rank_idx, item in enumerate(prioritized_items, start=1):
            item["priority_rank"] = rank_idx

        return {
            "total_active_incidents": len(prioritized_items),
            "current_rainfall_mm_hr": current_rain_mm_hr,
            "ranked_incidents": prioritized_items,
            "governance_policy": "HUMAN_OPERATOR_REQUIRED",
            "formula": "P = 0.30*S_severity + 0.25*R_geo + 0.20*S_med_prox + 0.15*S_road_tier + 0.10*S_age",
            "decision_disclaimer": (
                "Priority rankings and candidate resource allocations are algorithmic recommendations only. "
                "Physical or virtual dispatch requires explicit human operator confirmation."
            )
        }

response_priority_service = ResponsePriorityService()

