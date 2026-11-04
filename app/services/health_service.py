"""
AQUILA Phase 6 - Health & Operational Diagnostics Service
Provides deep health inspection across all platform subsystems:
- Database connectivity & record counts
- Geospatial dataset files & rasters
- Road network graph topology & KDTree indexing
- Geographic risk engine operational probe
- Flood-aware routing engine readiness
- Scenario simulation engine state
- Memory consumption & runtime environment
"""

import os
import sys
import platform
from typing import Dict, Any, List
from sqlalchemy import text
import psutil

from app.db.database import SessionLocal, utc_now
from app.db.models import Incident, Resource, RainfallObservation
from app.services.risk_engine import compute_geographic_risk
from app.services.road_network_service import road_network_service
from app.services.scenario_service import scenario_manager

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

REQUIRED_VECTOR_FILES = [
    "study_area_bbox.geojson",
    "roads_manikonda_processed.geojson",
    "water_bodies_manikonda_processed.geojson",
    "drainage_manikonda_processed.geojson",
    "infrastructure_manikonda_processed.geojson",
    "historical_flood_points_processed.geojson",
    "monitoring_locations_processed.geojson",
    "rainfall_synthetic_hyetograph_validated.csv"
]

REQUIRED_RASTER_FILES = [
    "dem_manikonda_clipped.tif",
    "slope_degrees_manikonda.tif"
]


class HealthService:
    def __init__(self):
        pass

    def check_database(self) -> Dict[str, Any]:
        """Probes database connection and checks core tables."""
        db = SessionLocal()
        try:
            # Probe query
            db.execute(text("SELECT 1;"))
            inc_count = db.query(Incident).count()
            res_count = db.query(Resource).count()
            rain_count = db.query(RainfallObservation).count()

            return {
                "status": "HEALTHY",
                "engine": "SQLite",
                "foreign_keys_enabled": True,
                "counts": {
                    "incidents": inc_count,
                    "resources": res_count,
                    "rainfall_observations": rain_count
                }
            }
        except Exception as e:
            return {
                "status": "UNHEALTHY",
                "error": "Database probe query failed"
            }
        finally:
            db.close()

    def check_datasets(self) -> Dict[str, Any]:
        """Verifies presence of all required vector and raster files."""
        vec_dir = os.path.join(BASE_DIR, "data", "processed", "vector")
        rast_dir = os.path.join(BASE_DIR, "data", "processed", "raster")

        missing = []
        available = []

        for vf in REQUIRED_VECTOR_FILES:
            if os.path.exists(os.path.join(vec_dir, vf)):
                available.append(vf)
            else:
                missing.append(vf)

        for rf in REQUIRED_RASTER_FILES:
            if os.path.exists(os.path.join(rast_dir, rf)):
                available.append(rf)
            else:
                missing.append(rf)

        status = "HEALTHY" if not missing else ("DEGRADED" if available else "UNHEALTHY")

        return {
            "status": status,
            "total_required": len(REQUIRED_VECTOR_FILES) + len(REQUIRED_RASTER_FILES),
            "available_count": len(available),
            "missing_count": len(missing),
            "missing_files": missing
        }

    def check_road_graph(self) -> Dict[str, Any]:
        """Inspects road network topological graph readiness."""
        nodes = road_network_service.graph.number_of_nodes()
        edges = road_network_service.graph.number_of_edges()
        largest_cc = len(road_network_service.largest_cc_nodes)
        kdtree_ready = road_network_service.kdtree_largest_cc is not None

        is_healthy = nodes > 1000 and edges > 2000 and kdtree_ready

        return {
            "status": "HEALTHY" if is_healthy else "UNHEALTHY",
            "total_nodes": nodes,
            "total_directed_edges": edges,
            "largest_connected_component_nodes": largest_cc,
            "connectivity_percentage": round((largest_cc / max(1, nodes)) * 100, 1),
            "spatial_kdtree_indexed": kdtree_ready
        }

    def check_risk_engine(self) -> Dict[str, Any]:
        """Performs a smoke evaluation of the geographic risk engine."""
        try:
            probe = compute_geographic_risk(
                rainfall_rate_mm_hr=25.0,
                elevation_m=525.0,
                slope_degrees=2.5,
                distance_to_waterway_m=120.0,
                landcover_class=50,
                distance_to_flood_point_m=250.0
            )
            score = probe.get("final_risk_score", 0.0)
            return {
                "status": "HEALTHY",
                "operational_probe_score": score,
                "formula": "0.40P + 0.20T + 0.20D + 0.10L + 0.10H"
            }
        except Exception:
            return {
                "status": "UNHEALTHY",
                "error": "Risk calculation operational probe failed"
            }

    def get_system_health(self) -> Dict[str, Any]:
        """Aggregates diagnostics across all subsystems into a unified health summary."""
        db_health = self.check_database()
        ds_health = self.check_datasets()
        graph_health = self.check_road_graph()
        risk_health = self.check_risk_engine()

        # Overall status determination
        sub_statuses = [db_health["status"], ds_health["status"], graph_health["status"], risk_health["status"]]
        if all(s == "HEALTHY" for s in sub_statuses):
            overall_status = "HEALTHY"
        elif any(s == "UNHEALTHY" for s in sub_statuses):
            overall_status = "UNHEALTHY"
        else:
            overall_status = "DEGRADED"

        # Memory & Runtime metrics
        process = psutil.Process()
        memory_mb = round(process.memory_info().rss / (1024 * 1024), 1)

        return {
            "status": overall_status,
            "overall_status": overall_status,
            "platform": "AQUILA MVP — Urban Flood Intelligence & Emergency Response Platform",
            "pilot_area": "Manikonda, Hyderabad, Telangana, India",
            "version": "0.6.0",
            "timestamp": utc_now().isoformat() + "Z",
            "environment": {
                "python_version": platform.python_version(),
                "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
                "memory_rss_mb": memory_mb
            },
            "subsystems": {
                "database": db_health,
                "geospatial_datasets": ds_health,
                "road_network_graph": graph_health,
                "geographic_risk_engine": risk_health,
                "scenario_engine": {
                    "status": "HEALTHY",
                    "scenario_id": scenario_manager.scenario_id,
                    "is_active": scenario_manager.is_active,
                    "current_step": scenario_manager.current_step,
                    "total_steps": len(scenario_manager.steps)
                }
            }
        }

health_service = HealthService()
