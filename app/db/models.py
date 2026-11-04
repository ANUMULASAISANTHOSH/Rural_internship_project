"""
AQUILA MVP - SQLAlchemy Database Models
Minimum 6 core tables:
1. Incidents
2. Resources
3. Rainfall Observations
4. Risk Assessments
5. Incident Assignments
6. Audit History
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base, utc_now

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    incident_type = Column(String(50), nullable=False)  # WATERLOGGING, ROAD_SEVERANCE, CELLAR_FLOODING, DRAIN_OVERFLOW, STRUCTURAL_HAZARD
    severity = Column(String(20), nullable=False, default="MODERATE")  # LOW, MODERATE, HIGH, CRITICAL
    status = Column(String(30), nullable=False, default="REPORTED")    # REPORTED, UNDER_REVIEW, ASSIGNED, IN_PROGRESS, RESOLVED
    source_type = Column(String(30), nullable=False, default="REPORTED") # REPORTED, SIMULATED, HISTORICAL
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    assignments = relationship("IncidentAssignment", back_populates="incident", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    resource_code = Column(String(50), unique=True, index=True, nullable=False)
    resource_name = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)  # DEWATERING_PUMP, RESCUE_BOAT, AMBULANCE, MONSOON_SQUAD, HEAVY_EARTHMOVER
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    availability_status = Column(String(30), nullable=False, default="AVAILABLE") # AVAILABLE, ASSIGNED, MAINTENANCE
    capability = Column(String(100), nullable=False)   # PUMPING, WATER_RESCUE, MEDICAL_EVAC, DEBRIS_CLEARING, ROAD_CLEARING
    provenance = Column(String(30), nullable=False, default="SIMULATED") # Explicit demonstration fleet tagging
    created_at = Column(DateTime, default=utc_now, nullable=False)

    assignments = relationship("IncidentAssignment", back_populates="resource")


class RainfallObservation(Base):
    __tablename__ = "rainfall_observations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String(50), index=True, nullable=False)
    rainfall_mm_per_hour = Column(Float, nullable=False)
    observation_time = Column(DateTime, default=utc_now, nullable=False)
    source_type = Column(String(30), nullable=False, default="OBSERVED") # OBSERVED, HISTORICAL, SIMULATED
    is_synthetic = Column(Boolean, default=False, nullable=False)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(String(100), index=True, nullable=False)
    rainfall_score = Column(Float, nullable=False)
    terrain_score = Column(Float, nullable=False)
    drainage_score = Column(Float, nullable=False)
    landcover_score = Column(Float, nullable=False)
    historical_score = Column(Float, nullable=False, default=0.0)
    final_risk_score = Column(Float, nullable=False)
    risk_category = Column(String(20), nullable=False) # LOW, MODERATE, HIGH
    assessment_time = Column(DateTime, default=utc_now, nullable=False)
    source_type = Column(String(30), nullable=False, default="MODEL_ESTIMATE")


class IncidentAssignment(Base):
    __tablename__ = "incident_assignments"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    recommendation_distance = Column(Float, nullable=False) # In kilometres
    assignment_status = Column(String(30), nullable=False, default="RECOMMENDED") # RECOMMENDED, ASSIGNED, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=utc_now, nullable=False)

    incident = relationship("Incident", back_populates="assignments")
    resource = relationship("Resource", back_populates="assignments")


class AuditHistory(Base):
    __tablename__ = "audit_history"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False) # INCIDENT, RESOURCE, ASSIGNMENT, SCENARIO, RISK
    entity_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)      # CREATED, STATUS_UPDATED, RECOMMENDED, ASSIGNED, SCENARIO_STARTED, SCENARIO_RESET
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False)


class RoadDisruption(Base):
    __tablename__ = "road_disruptions"

    id = Column(Integer, primary_key=True, index=True)
    disruption_code = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, default=150.0, nullable=False)
    penalty_factor = Column(Float, default=10.0, nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False) # ACTIVE, CLEARED
    provenance = Column(String(30), default="SIMULATED", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


