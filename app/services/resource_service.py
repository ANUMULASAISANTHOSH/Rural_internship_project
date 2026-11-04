"""
AQUILA MVP - Emergency Resource Recommendation & Dispatch Service
Calculates Haversine distances, filters by capability, and manages recommendation/assignment lifecycles.
"""

import math
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.database import utc_now
from app.db.models import Resource, Incident, IncidentAssignment, AuditHistory

# Earth radius in kilometres
EARTH_RADIUS_KM = 6371.0

CAPABILITY_MAPPING = {
    "WATERLOGGING": ["PUMPING", "ROAD_CLEARING"],
    "CELLAR_FLOODING": ["PUMPING"],
    "ROAD_SEVERANCE": ["ROAD_CLEARING", "DEBRIS_CLEARING"],
    "DRAIN_OVERFLOW": ["DEBRIS_CLEARING", "PUMPING"],
    "STRUCTURAL_HAZARD": ["WATER_RESCUE", "MEDICAL_EVAC"]
}

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two coordinates in kilometres.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 3)

def recommend_resource_for_incident(db: Session, incident_id: int) -> Optional[Dict[str, Any]]:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError(f"Incident with ID {incident_id} not found.")

    compatible_caps = CAPABILITY_MAPPING.get(incident.incident_type, ["PUMPING", "ROAD_CLEARING"])

    # Query available resources matching capabilities
    candidates = (
        db.query(Resource)
        .filter(Resource.availability_status == "AVAILABLE")
        .all()
    )

    scored_candidates = []
    for res in candidates:
        is_compatible = res.capability in compatible_caps or any(c in res.capability for c in compatible_caps)
        dist_km = haversine_distance_km(incident.latitude, incident.longitude, res.latitude, res.longitude)
        scored_candidates.append({
            "resource": res,
            "distance_km": dist_km,
            "compatible": is_compatible
        })

    # Sort primarily by compatibility, secondarily by distance
    scored_candidates.sort(key=lambda x: (not x["compatible"], x["distance_km"]))

    if not scored_candidates:
        return None

    best = scored_candidates[0]
    best_res = best["resource"]
    dist = best["distance_km"]

    # Record or update assignment record in RECOMMENDED state
    assignment = (
        db.query(IncidentAssignment)
        .filter(IncidentAssignment.incident_id == incident.id, IncidentAssignment.resource_id == best_res.id)
        .first()
    )
    if not assignment:
        assignment = IncidentAssignment(
            incident_id=incident.id,
            resource_id=best_res.id,
            recommendation_distance=dist,
            assignment_status="RECOMMENDED",
            created_at=utc_now()
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

    # Log audit entry
    audit = AuditHistory(
        entity_type="ASSIGNMENT",
        entity_id=str(assignment.id),
        action="RECOMMENDED",
        details=f"Recommended resource {best_res.resource_code} ({best_res.resource_name}) at distance {dist} km for incident {incident.incident_code}.",
        timestamp=utc_now()
    )
    db.add(audit)
    db.commit()

    return {
        "assignment_id": assignment.id,
        "incident_id": incident.id,
        "incident_code": incident.incident_code,
        "resource_id": best_res.id,
        "resource_code": best_res.resource_code,
        "resource_name": best_res.resource_name,
        "resource_type": best_res.resource_type,
        "capability": best_res.capability,
        "distance_km": dist,
        "distance_metric": "Haversine Great-Circle (Straight-line)",
        "assignment_status": assignment.assignment_status
    }

def assign_resource_to_incident(db: Session, incident_id: int, resource_id: int) -> Dict[str, Any]:
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not incident:
        raise ValueError(f"Incident {incident_id} not found.")
    if not resource:
        raise ValueError(f"Resource {resource_id} not found.")

    # Check for conflict: prevent duplicate assignment to another active incident
    if resource.availability_status == "ASSIGNED":
        active_other = (
            db.query(IncidentAssignment)
            .filter(
                IncidentAssignment.resource_id == resource.id,
                IncidentAssignment.incident_id != incident.id,
                IncidentAssignment.assignment_status == "ASSIGNED"
            )
            .first()
        )
        if active_other:
            other_inc = db.query(Incident).filter(Incident.id == active_other.incident_id).first()
            other_code = other_inc.incident_code if other_inc else str(active_other.incident_id)
            raise ValueError(f"Resource {resource.resource_code} is already deployed to another active incident ({other_code}).")

    dist = haversine_distance_km(incident.latitude, incident.longitude, resource.latitude, resource.longitude)

    assignment = (
        db.query(IncidentAssignment)
        .filter(IncidentAssignment.incident_id == incident.id, IncidentAssignment.resource_id == resource.id)
        .first()
    )
    if not assignment:
        assignment = IncidentAssignment(
            incident_id=incident.id,
            resource_id=resource.id,
            recommendation_distance=dist,
            assignment_status="ASSIGNED",
            created_at=utc_now()
        )
        db.add(assignment)
    else:
        assignment.assignment_status = "ASSIGNED"

    # Update resource and incident statuses
    resource.availability_status = "ASSIGNED"
    incident.status = "ASSIGNED"

    # Audit log
    audit = AuditHistory(
        entity_type="ASSIGNMENT",
        entity_id=str(assignment.id),
        action="ASSIGNED",
        details=f"Operator approved deployment of {resource.resource_code} to incident {incident.incident_code}.",
        timestamp=utc_now()
    )
    db.add(audit)
    db.commit()

    return {
        "assignment_id": assignment.id,
        "incident_code": incident.incident_code,
        "resource_code": resource.resource_code,
        "status": "ASSIGNED",
        "distance_km": dist
    }

