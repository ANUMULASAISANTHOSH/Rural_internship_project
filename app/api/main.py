"""
AQUILA MVP - FastAPI Application Server
Implements core endpoints for GIS Layers, Risk Indexing, Incidents,
Emergency Resource Recommendation, and Heavy Rainfall Simulation.
"""

import os
import sys
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.logging_config import app_logger
from app.db.database import get_db, engine, Base, utc_now
from app.db.models import Incident, Resource, RainfallObservation, RiskAssessment, IncidentAssignment, AuditHistory
from app.db.seed import init_db
from app.api.schemas import (
    IncidentCreate, IncidentResponse, IncidentStatusUpdate,
    ResourceResponse, ResourceAssignRequest, RecommendationResponse,
    RiskRequest, AuditHistoryResponse,
    RouteResponse, RouteComparisonResponse, FacilityAccessibilityResponse, RoadNetworkSummaryResponse,
    ScenarioComparisonResponse, SensitivityAnalysisResponse, FacilityVulnerabilityResponse,
    IncidentPrioritiesResponse, AnalyticsSummaryResponse
)
from app.services.risk_engine import compute_geographic_risk
from app.services.resource_service import recommend_resource_for_incident, assign_resource_to_incident
from app.services.scenario_service import scenario_manager
from app.services.geo_service import get_layer, get_layer_summary, LAYER_FILES
from app.services.road_network_service import road_network_service
from app.services.accessibility_service import accessibility_service
from app.services.scenario_comparison_service import scenario_comparison_service
from app.services.uncertainty_service import uncertainty_service
from app.services.vulnerability_service import vulnerability_service
from app.services.response_priority_service import response_priority_service
from app.services.health_service import health_service

# Ensure DB initialized
init_db(seed_resources=True)

app = FastAPI(
    title="AQUILA Decision-Support API",
    description="Urban Flood Intelligence, Infrastructure Monitoring and Emergency Response Platform — Phase 6 Certified Release",
    version="0.6.0"
)

# Configurable CORS
cors_origins_env = os.environ.get("AQUILA_CORS_ORIGINS", "*")
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] if cors_origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global sanitized exception handler to prevent path leakage
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    app_logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An internal server error occurred while processing the request.",
            "status_code": 500
        }
    )

VALID_STATUSES = {"REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"}
VALID_INCIDENT_TYPES = {"WATERLOGGING", "ROAD_SEVERANCE", "CELLAR_FLOODING", "DRAIN_OVERFLOW", "STRUCTURAL_HAZARD"}
VALID_SEVERITIES = {"LOW", "MODERATE", "HIGH", "CRITICAL"}

# 1. Health Endpoints [READ-ONLY]
@app.get("/health", tags=["System [READ-ONLY]"])
def health_check():
    """[READ-ONLY] System health and operational readiness summary."""
    return health_service.get_system_health()


@app.get("/api/v1/health", tags=["System [READ-ONLY]"])
def get_detailed_health():
    """[READ-ONLY] Deep subsystem diagnostic health inspection."""
    return health_service.get_system_health()

# 2. High-Level Summary
@app.get("/api/summary", tags=["Overview"])
def get_system_summary(db: Session = Depends(get_db)):
    total_incidents = db.query(Incident).count()
    active_incidents = db.query(Incident).filter(Incident.status.in_(["REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS"])).count()
    resolved_incidents = db.query(Incident).filter(Incident.status == "RESOLVED").count()
    total_resources = db.query(Resource).count()
    available_resources = db.query(Resource).filter(Resource.availability_status == "AVAILABLE").count()
    
    # Latest rainfall
    latest_rain = db.query(RainfallObservation).order_by(RainfallObservation.id.desc()).first()
    curr_rate = latest_rain.rainfall_mm_per_hour if latest_rain else 0.0

    # Current geographic risk at centroid
    risk_summary = compute_geographic_risk(rainfall_rate_mm_hr=curr_rate)

    return {
        "total_incidents": total_incidents,
        "active_incidents": active_incidents,
        "resolved_incidents": resolved_incidents,
        "total_resources": total_resources,
        "available_resources": available_resources,
        "current_rainfall_mm_hr": curr_rate,
        "rainfall_source": latest_rain.source_type if latest_rain else "HISTORICAL_ARCHIVE",
        "current_risk_score": risk_summary["final_risk_score"],
        "risk_category": risk_summary["risk_category"],
        "scenario_status": scenario_manager.get_status()
    }

# 3. Geospatial Layer Endpoints [READ-ONLY]
@app.get("/api/layers", tags=["Geospatial [READ-ONLY]"])
def list_layers():
    """[READ-ONLY] Lists available vector GeoJSON layers and feature counts."""
    return get_layer_summary()

@app.get("/api/layers/{layer_name}", tags=["Geospatial [READ-ONLY]"])
def get_geojson_layer(layer_name: str):
    """[READ-ONLY] Returns validated GeoJSON vector features with sanitized path protection."""
    if layer_name not in LAYER_FILES:
        raise HTTPException(
            status_code=404,
            detail=f"Layer '{layer_name}' not found. Available: {sorted(list(LAYER_FILES.keys()))}"
        )
    try:
        return get_layer(layer_name)
    except Exception as e:
        app_logger.error(f"Error reading layer '{layer_name}': {e}")
        raise HTTPException(status_code=404, detail=f"Layer '{layer_name}' is currently unavailable.")

# 4. Rainfall Telemetry
@app.get("/api/rainfall", tags=["Meteorology"])
def get_rainfall_observations(db: Session = Depends(get_db), limit: int = 20):
    records = db.query(RainfallObservation).order_by(RainfallObservation.id.desc()).limit(limit).all()
    return records

# 5. Risk Calculation [READ-ONLY]
@app.get("/api/risk", tags=["Risk Engine [READ-ONLY]"])
def get_risk_index(
    rainfall_rate: float = Query(25.0, ge=0.0, le=500.0, description="Rainfall rate in mm/hr [0.0 - 500.0]"),
    elevation: float = Query(525.0, ge=400.0, le=1000.0, description="Elevation in metres [400.0 - 1000.0]"),
    slope: float = Query(2.5, ge=0.0, le=90.0, description="Slope in degrees [0.0 - 90.0]"),
    waterway_dist: float = Query(120.0, ge=0.0, le=50000.0, description="Distance to nearest waterway in metres [0.0 - 50000.0]"),
    landcover: int = Query(50, ge=10, le=100, description="ESA WorldCover class ID [10 - 100]"),
    flood_dist: float = Query(250.0, ge=0.0, le=50000.0, description="Distance to historical flood point in metres [0.0 - 50000.0]")
):
    """[READ-ONLY] Evaluates multi-factor geographic risk score with bounded parameter validation."""
    return compute_geographic_risk(
        rainfall_rate_mm_hr=rainfall_rate,
        elevation_m=elevation,
        slope_degrees=slope,
        distance_to_waterway_m=waterway_dist,
        landcover_class=landcover,
        distance_to_flood_point_m=flood_dist
    )

@app.post("/api/risk", tags=["Risk Engine"])
def compute_risk_custom(req: RiskRequest):
    return compute_geographic_risk(
        rainfall_rate_mm_hr=req.rainfall_rate_mm_hr,
        elevation_m=req.elevation_m,
        slope_degrees=req.slope_degrees,
        distance_to_waterway_m=req.distance_to_waterway_m,
        landcover_class=req.landcover_class,
        distance_to_flood_point_m=req.distance_to_flood_point_m,
        custom_weights=req.custom_weights
    )

# 6. Incident Management
@app.get("/api/incidents", response_model=List[IncidentResponse], tags=["Incidents"])
def list_incidents(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if source_type:
        query = query.filter(Incident.source_type == source_type)
    return query.order_by(Incident.id.desc()).all()

@app.post("/api/incidents", response_model=IncidentResponse, tags=["Incidents"])
def create_incident(inc: IncidentCreate, db: Session = Depends(get_db)):
    if inc.incident_type not in VALID_INCIDENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid incident_type '{inc.incident_type}'. Allowed: {sorted(list(VALID_INCIDENT_TYPES))}")
    if inc.severity not in VALID_SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity '{inc.severity}'. Allowed: {sorted(list(VALID_SEVERITIES))}")

    # Auto-generate incident code
    count = db.query(Incident).count() + 1
    code = f"INC-2026-{count:04d}"

    db_incident = Incident(
        incident_code=code,
        title=inc.title,
        description=inc.description,
        latitude=inc.latitude,
        longitude=inc.longitude,
        incident_type=inc.incident_type,
        severity=inc.severity,
        status="REPORTED",
        source_type=inc.source_type,
        created_at=utc_now(),
        updated_at=utc_now()
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    # Log to audit history
    audit = AuditHistory(
        entity_type="INCIDENT",
        entity_id=code,
        action="CREATED",
        details=f"Incident {code} created: '{inc.title}' ({inc.severity}, {inc.incident_type}) at [{inc.latitude}, {inc.longitude}]. Provenance: {inc.source_type}.",
        timestamp=utc_now()
    )
    db.add(audit)
    db.commit()

    return db_incident

@app.patch("/api/incidents/{incident_id}/status", response_model=IncidentResponse, tags=["Incidents"])
def update_incident_status(
    incident_id: int,
    update: IncidentStatusUpdate,
    db: Session = Depends(get_db)
):
    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status '{update.status}'. Allowed: {sorted(list(VALID_STATUSES))}")

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_status = incident.status
    incident.status = update.status
    incident.updated_at = utc_now()

    # If resolved, release any assigned resources
    if update.status == "RESOLVED":
        assignments = db.query(IncidentAssignment).filter(IncidentAssignment.incident_id == incident.id).all()
        for asg in assignments:
            asg.assignment_status = "COMPLETED"
            res = db.query(Resource).filter(Resource.id == asg.resource_id).first()
            if res:
                res.availability_status = "AVAILABLE"

    # Audit log
    audit = AuditHistory(
        entity_type="INCIDENT",
        entity_id=incident.incident_code,
        action="STATUS_UPDATED",
        details=f"Status changed from {old_status} to {update.status}.",
        timestamp=utc_now()
    )
    db.add(audit)
    db.commit()
    db.refresh(incident)
    return incident

# 7. Resource Management & Dispatch
@app.get("/api/resources", response_model=List[ResourceResponse], tags=["Resources"])
def list_resources(
    availability: Optional[str] = None,
    capability: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Resource)
    if availability:
        query = query.filter(Resource.availability_status == availability)
    if capability:
        query = query.filter(Resource.capability.contains(capability))
    return query.all()

@app.post("/api/incidents/{incident_id}/recommend-resource", response_model=RecommendationResponse, tags=["Dispatch"])
def recommend_resource(incident_id: int, db: Session = Depends(get_db)):
    try:
        rec = recommend_resource_for_incident(db, incident_id)
        if not rec:
            raise HTTPException(status_code=404, detail="No available compatible resources found.")
        return rec
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/incidents/{incident_id}/assign-resource", tags=["Dispatch"])
def assign_resource(incident_id: int, req: ResourceAssignRequest, db: Session = Depends(get_db)):
    try:
        return assign_resource_to_incident(db, incident_id, req.resource_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 8. Scenario Controls
@app.post("/api/scenarios/start", tags=["Scenario Simulator"])
def start_scenario(db: Session = Depends(get_db)):
    return scenario_manager.start_scenario(db)

@app.post("/api/scenarios/advance", tags=["Scenario Simulator"])
def advance_scenario(db: Session = Depends(get_db)):
    return scenario_manager.advance_step(db)

@app.post("/api/scenarios/reset", tags=["Scenario Simulator"])
def reset_scenario(db: Session = Depends(get_db)):
    return scenario_manager.reset_scenario(db)

@app.get("/api/scenarios/status", tags=["Scenario Simulator"])
def get_scenario_status():
    return scenario_manager.get_status()

# 9. Audit History
@app.get("/api/audit-history", response_model=List[AuditHistoryResponse], tags=["Audit Trail"])
def get_audit_trail(db: Session = Depends(get_db), limit: int = 50):
    return db.query(AuditHistory).order_by(AuditHistory.id.desc()).limit(limit).all()


# ─────────────────────────────────────────────────────────────────────────────
# 10. Phase 4: Flood-Aware Routing & Safe Accessibility Endpoints
# ─────────────────────────────────────────────────────────────────────────────

def _validate_routing_coords(lat: float, lon: float, label: str):
    if not (17.20 <= lat <= 17.60):
        raise HTTPException(status_code=400, detail=f"Invalid {label} latitude '{lat}'. Must be within [17.20, 17.60].")
    if not (78.20 <= lon <= 78.60):
        raise HTTPException(status_code=400, detail=f"Invalid {label} longitude '{lon}'. Must be within [78.20, 78.60].")


@app.get("/api/v1/routing/network-summary", response_model=RoadNetworkSummaryResponse, tags=["Routing"])
def get_routing_network_summary():
    """Returns road network topological summary, edge counts, and connectivity metrics."""
    return road_network_service.get_network_summary()


@app.get("/api/v1/routing/shortest", response_model=RouteResponse, tags=["Routing"])
def calculate_shortest_route(
    origin_lat: float = Query(..., description="Origin latitude [17.20, 17.60]"),
    origin_lon: float = Query(..., description="Origin longitude [78.20, 78.60]"),
    dest_lat: float = Query(..., description="Destination latitude [17.20, 17.60]"),
    dest_lon: float = Query(..., description="Destination longitude [78.20, 78.60]")
):
    """Calculates distance-optimal shortest route using NetworkX Dijkstra algorithm."""
    _validate_routing_coords(origin_lat, origin_lon, "origin")
    _validate_routing_coords(dest_lat, dest_lon, "destination")
    return road_network_service.find_shortest_path(origin_lat, origin_lon, dest_lat, dest_lon)


@app.get("/api/v1/routing/lowest-risk", response_model=RouteResponse, tags=["Routing"])
def calculate_lowest_risk_route(
    origin_lat: float = Query(..., description="Origin latitude [17.20, 17.60]"),
    origin_lon: float = Query(..., description="Origin longitude [78.20, 78.60]"),
    dest_lat: float = Query(..., description="Destination latitude [17.20, 17.60]"),
    dest_lon: float = Query(..., description="Destination longitude [78.20, 78.60]"),
    lambda_param: float = Query(3.0, ge=0.0, le=50.0, description="Risk avoidance multiplier λ >= 0"),
    db: Session = Depends(get_db)
):
    """Calculates safety-optimal lowest-risk route avoiding high-vulnerability and incident zones."""
    _validate_routing_coords(origin_lat, origin_lon, "origin")
    _validate_routing_coords(dest_lat, dest_lon, "destination")
    road_network_service.update_edge_weights(db_session=db, lambda_param=lambda_param)
    return road_network_service.find_lowest_risk_path(origin_lat, origin_lon, dest_lat, dest_lon, lambda_param=lambda_param)


@app.get("/api/v1/routing/compare", response_model=RouteComparisonResponse, tags=["Routing"])
def compare_routes(
    origin_lat: float = Query(..., description="Origin latitude [17.20, 17.60]"),
    origin_lon: float = Query(..., description="Origin longitude [78.20, 78.60]"),
    dest_lat: float = Query(..., description="Destination latitude [17.20, 17.60]"),
    dest_lon: float = Query(..., description="Destination longitude [78.20, 78.60]"),
    lambda_param: float = Query(3.0, ge=0.0, le=50.0, description="Risk avoidance multiplier λ >= 0"),
    db: Session = Depends(get_db)
):
    """Compares shortest and lowest-risk routes and returns an explainable trade-off summary."""
    _validate_routing_coords(origin_lat, origin_lon, "origin")
    _validate_routing_coords(dest_lat, dest_lon, "destination")
    road_network_service.update_edge_weights(db_session=db, lambda_param=lambda_param)
    return road_network_service.compare_routes(origin_lat, origin_lon, dest_lat, dest_lon, lambda_param=lambda_param)


@app.get("/api/v1/accessibility/facilities", response_model=FacilityAccessibilityResponse, tags=["Accessibility"])
def get_accessible_facilities(
    origin_lat: float = Query(..., description="Origin latitude [17.20, 17.60]"),
    origin_lon: float = Query(..., description="Origin longitude [78.20, 78.60]"),
    facility_category: str = Query("hospital", description="Facility category (hospital, clinic, pharmacy, all)"),
    limit: int = Query(5, ge=1, le=20, description="Maximum facilities to return"),
    db: Session = Depends(get_db)
):
    """Recommends nearest accessible critical medical facilities with driving distance and provenance."""
    _validate_routing_coords(origin_lat, origin_lon, "origin")
    road_network_service.update_edge_weights(db_session=db)
    return accessibility_service.find_accessible_facilities(
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        facility_category=facility_category,
        max_results=limit
    )


# -----------------------------------------------------------------------------
# Phase 5: Multi-Scenario Intelligence & Decision Optimization Endpoints
# -----------------------------------------------------------------------------

@app.get("/api/v1/scenarios/compare", response_model=ScenarioComparisonResponse, tags=["Scenario Intelligence"])
def compare_scenarios():
    """Returns side-by-side comparative KPI matrix across 5 operational flood scenarios."""
    return scenario_comparison_service.compare_all_scenarios()


@app.get("/api/v1/scenarios/sensitivity", response_model=SensitivityAnalysisResponse, tags=["Uncertainty & Sensitivity"])
def get_sensitivity_analysis(
    perturbation_fraction: float = Query(0.20, ge=0.05, le=0.50, description="OAT weight perturbation fraction (default: 0.20 for ±20%)")
):
    """Returns One-At-a-Time parameter sensitivity, non-linear rainfall response, and missing-layer elasticity."""
    report = uncertainty_service.get_full_sensitivity_report()
    if perturbation_fraction != 0.20:
        report["weight_sensitivity"] = uncertainty_service.analyze_weight_sensitivity(perturbation_fraction=perturbation_fraction)
    return report


@app.get("/api/v1/infrastructure/vulnerability", response_model=FacilityVulnerabilityResponse, tags=["Infrastructure Intelligence"])
def get_infrastructure_vulnerability(
    rainfall_rate_mm_hr: float = Query(25.0, ge=0.0, le=200.0, description="Rainfall intensity in mm/hr for risk context"),
    category: Optional[str] = Query("all", description="Facility category filter (hospital, clinic, pharmacy, all)")
):
    """Evaluates and ranks all 65 critical facilities by multi-criteria vulnerability index with provenance."""
    cat_filter = None if category == "all" else category
    return vulnerability_service.rank_facilities_vulnerability(
        rainfall_rate_mm_hr=rainfall_rate_mm_hr,
        category_filter=cat_filter
    )


@app.get("/api/v1/incidents/priorities", response_model=IncidentPrioritiesResponse, tags=["Emergency Prioritization"])
def get_incident_priorities(db: Session = Depends(get_db)):
    """Returns active incidents ranked by explainable priority score with human-in-the-loop governance."""
    return response_priority_service.evaluate_incident_priorities(db)


@app.get("/api/v1/analytics/summary", response_model=AnalyticsSummaryResponse, tags=["Analytics Overview"])
def get_analytics_summary(db: Session = Depends(get_db)):
    """Returns high-level synthesis of multi-scenario metrics, vulnerability distribution, and priority queue."""
    scen_comp = scenario_comparison_service.compare_all_scenarios()
    vuln_data = vulnerability_service.rank_facilities_vulnerability()
    hist_cons = vulnerability_service.evaluate_historical_evidence_consistency()
    priorities = response_priority_service.evaluate_incident_priorities(db)
    sens = uncertainty_service.analyze_weight_sensitivity()

    top_inc = priorities["ranked_incidents"][0] if priorities["ranked_incidents"] else None

    # Count facilities in HIGH or CRITICAL
    crit_high_facs = vuln_data["vulnerability_distribution"].get("CRITICAL", 0) + vuln_data["vulnerability_distribution"].get("HIGH", 0)

    return {
        "generated_at": utc_now(),
        "pilot_area": "Manikonda, Hyderabad, Telangana",
        "total_scenarios_available": scen_comp["total_scenarios_compared"],
        "critical_facilities_total": vuln_data["total_facilities_evaluated"],
        "critical_facilities_vulnerable_count": crit_high_facs,
        "active_incidents_count": priorities["total_active_incidents"],
        "top_priority_incident": top_inc,
        "most_sensitive_parameter": sens["most_sensitive_factor"],
        "historical_consistency_pct": hist_cons["spatial_agreement_percentage"],
        "governance_status": "HUMAN_OPERATOR_REQUIRED"
    }



