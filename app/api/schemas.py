"""
AQUILA MVP - Pydantic Request & Response Schemas (Pydantic V2 Compliant)
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

# Incident Schemas
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, json_schema_extra={"example": "Puppalaguda Main Road Waterlogging"})
    description: Optional[str] = Field(None, max_length=2000, json_schema_extra={"example": "Water depth 0.35m near junction."})
    latitude: float = Field(..., ge=17.20, le=17.60, json_schema_extra={"example": 17.4015})
    longitude: float = Field(..., ge=78.20, le=78.60, json_schema_extra={"example": 78.3750})
    incident_type: str = Field(..., json_schema_extra={"example": "WATERLOGGING"})
    severity: str = Field(default="MODERATE", json_schema_extra={"example": "HIGH"})
    source_type: str = Field(default="REPORTED", json_schema_extra={"example": "REPORTED"})

class IncidentStatusUpdate(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "IN_PROGRESS"})

class IncidentResponse(BaseModel):
    id: int
    incident_code: str
    title: str
    description: Optional[str]
    latitude: float
    longitude: float
    incident_type: str
    severity: str
    status: str
    source_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Resource Schemas
class ResourceResponse(BaseModel):
    id: int
    resource_code: str
    resource_name: str
    resource_type: str
    latitude: float
    longitude: float
    availability_status: str
    capability: str
    provenance: Optional[str] = "SIMULATED"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Recommendation & Assignment Schemas
class ResourceAssignRequest(BaseModel):
    resource_id: int

class RecommendationResponse(BaseModel):
    assignment_id: int
    incident_id: int
    incident_code: str
    resource_id: int
    resource_code: str
    resource_name: str
    resource_type: str
    capability: str
    distance_km: float
    distance_metric: str
    assignment_status: str

# Risk Query Schema
class RiskRequest(BaseModel):
    rainfall_rate_mm_hr: float = 25.0
    elevation_m: float = 525.0
    slope_degrees: float = 2.5
    distance_to_waterway_m: float = 120.0
    landcover_class: int = 50
    distance_to_flood_point_m: float = 250.0
    custom_weights: Optional[Dict[str, float]] = None

# Audit History Schema
class AuditHistoryResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: str
    action: str
    details: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# Phase 4: Flood-Aware Routing & Accessibility Schemas
class RouteResponse(BaseModel):
    route_type: str
    found: bool
    total_distance_meters: float = 0.0
    total_distance_km: float = 0.0
    average_risk_score: float = 0.0
    risk_category: str = "LOW"
    high_risk_segment_count: int = 0
    incident_affected_segment_count: int = 0
    disruption_affected_segment_count: int = 0
    node_count: int = 0
    primary_roads_traversed: List[str] = []
    coordinates: List[List[float]] = []
    snapping_distance_origin_m: Optional[float] = None
    snapping_distance_dest_m: Optional[float] = None
    lambda_param_applied: Optional[float] = None
    error: Optional[str] = None


class RouteComparisonResponse(BaseModel):
    origin: Dict[str, float]
    destination: Dict[str, float]
    shortest_route: Dict[str, Any]
    lowest_risk_route: Dict[str, Any]
    comparison: Dict[str, Any]


class FacilityRecommendationItem(BaseModel):
    facility_id: str
    facility_name: str
    facility_category: str
    latitude: float
    longitude: float
    straight_line_distance_km: float
    road_network_distance_km: Optional[float] = None
    road_network_distance_meters: Optional[float] = None
    route_average_risk_score: Optional[float] = None
    route_risk_category: str = "UNKNOWN"
    incident_affected_segments: int = 0
    disruption_affected_segments: int = 0
    accessibility_status: str
    data_provenance: str = "MANUALLY_SEEDED"
    verification_status: str = "OSM_UNVERIFIED"
    disclaimer: str


class FacilityAccessibilityResponse(BaseModel):
    origin: Dict[str, float]
    requested_category: str
    facilities_found_count: int
    accessible_count: int
    unreachable_count: int
    facilities: List[FacilityRecommendationItem]


class RoadNetworkSummaryResponse(BaseModel):
    total_nodes: int
    total_directed_edges: int
    largest_connected_component_nodes: int
    connectivity_percentage: float
    highway_type_distribution: Dict[str, int]
    spatial_projection: str
    storage_crs: str
    road_features_source: str


# Phase 5: Multi-Scenario Intelligence, Uncertainty & Decision Optimization Schemas
class ScenarioDetailMetrics(BaseModel):
    mean_catchment_risk: float
    risk_category: str
    total_road_edges: int
    high_risk_edges: int
    moderate_risk_edges: int
    low_risk_edges: int
    high_risk_road_pct: float
    inaccessible_road_segments: int
    caution_road_segments: int
    total_critical_facilities: int
    facilities_at_risk: int
    facilities_isolated: int
    facility_vulnerability_pct: float
    estimated_resource_demand: Dict[str, int]


class ScenarioEvaluationItem(BaseModel):
    scenario_id: str
    scenario_name: str
    rainfall_rate_mm_hr: float
    drainage_surcharge_factor: float
    description: str
    active_disruptions_count: int
    active_incidents_count: int
    provenance: str
    metrics: ScenarioDetailMetrics


class ScenarioComparisonMatrixRow(BaseModel):
    scenario_id: str
    scenario_name: str
    rainfall_rate_mm_hr: float
    mean_catchment_risk: float
    risk_category: str
    delta_risk_score: float
    risk_pct_increase: float
    high_risk_edges: int
    delta_high_risk_edges: int
    inaccessible_road_segments: int
    facilities_at_risk: int
    delta_facilities_at_risk: int
    facilities_isolated: int
    dewatering_pumps_needed: int
    rescue_boats_needed: int
    monsoon_squad_teams_needed: int


class ScenarioComparisonResponse(BaseModel):
    baseline_scenario_id: str
    total_scenarios_compared: int
    scenarios: List[ScenarioEvaluationItem]
    comparison_matrix: List[ScenarioComparisonMatrixRow]
    methodology: str
    disclaimer: str


class SensitivityAnalysisResponse(BaseModel):
    report_title: str
    study_area: str
    weight_sensitivity: Dict[str, Any]
    rainfall_sweep: Dict[str, Any]
    missing_layer_impact: Dict[str, Any]
    routing_lambda_sensitivity: Dict[str, Any]
    disclaimer: str


class FacilityVulnerabilityItem(BaseModel):
    facility_id: str
    name: str
    category: str
    latitude: float
    longitude: float
    vulnerability_score: float
    vulnerability_category: str
    component_scores: Dict[str, float]
    spatial_context: Dict[str, Any]
    provenance: str
    verification_status: str
    limitations: str


class FacilityVulnerabilityResponse(BaseModel):
    total_facilities_evaluated: int
    rainfall_rate_applied_mm_hr: float
    category_filter: str
    vulnerability_distribution: Dict[str, int]
    ranked_facilities: List[FacilityVulnerabilityItem]
    formula: str
    disclaimer: str


class IncidentPriorityItem(BaseModel):
    incident_id: int
    incident_code: str
    title: str
    incident_type: str
    severity: str
    status: str
    latitude: float
    longitude: float
    priority_score: float
    priority_level: str
    priority_rank: Optional[int] = None
    sub_scores: Dict[str, float]
    spatial_details: Dict[str, Any]
    candidate_resource: Optional[Dict[str, Any]] = None
    explainable_justification: str
    requires_operator_approval: bool
    auto_dispatched: bool
    created_at: str


class IncidentPrioritiesResponse(BaseModel):
    total_active_incidents: int
    current_rainfall_mm_hr: float
    ranked_incidents: List[IncidentPriorityItem]
    governance_policy: str
    formula: str
    decision_disclaimer: str


class AnalyticsSummaryResponse(BaseModel):
    generated_at: datetime
    pilot_area: str
    total_scenarios_available: int
    critical_facilities_total: int
    critical_facilities_vulnerable_count: int
    active_incidents_count: int
    top_priority_incident: Optional[Dict[str, Any]] = None
    most_sensitive_parameter: str
    historical_consistency_pct: float
    governance_status: str


