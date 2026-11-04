"""
AQUILA Phase 4 - Critical Facility Accessibility Service
Evaluates road-network accessibility from any origin/incident coordinate to mapped
hospitals, clinics, and emergency infrastructure in Manikonda.
Ensures strict provenance transparency (OSM_UNVERIFIED).
"""

import os
import json
import math
from typing import Dict, Any, List, Optional

from app.services.road_network_service import road_network_service
from app.services.resource_service import haversine_distance_km

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INFRASTRUCTURE_GEOJSON = os.path.join(BASE_DIR, "data", "processed", "vector", "infrastructure_manikonda_processed.geojson")


class AccessibilityService:
    def __init__(self):
        self.facilities: List[Dict[str, Any]] = []
        self._load_facilities()

    def _load_facilities(self):
        """Loads critical facilities from validated processed GeoJSON."""
        if not os.path.exists(INFRASTRUCTURE_GEOJSON):
            print(f"[ACCESSIBILITY] Warning: Facility GeoJSON not found at: {INFRASTRUCTURE_GEOJSON}")
            return

        with open(INFRASTRUCTURE_GEOJSON, encoding="utf-8") as f:
            data = json.load(f)

        self.facilities = []
        for feat in data.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") != "Point":
                continue
            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue

            props = feat.get("properties", {})
            fac_type = props.get("facility_type") or props.get("amenity") or "public_facility"
            name = props.get("name") or f"Unnamed {fac_type.title()}"
            osm_id = props.get("osm_id") or feat.get("id")

            self.facilities.append({
                "facility_id": str(osm_id),
                "name": name,
                "category": fac_type.lower(),
                "latitude": float(coords[1]),
                "longitude": float(coords[0]),
                "provenance": props.get("provenance", "MANUALLY_SEEDED"),
                "verification_status": props.get("verification_status", "OSM_UNVERIFIED"),
                "operational_readiness": props.get("operational_readiness", "UNKNOWN_UNVERIFIED"),
                "emergency_service": props.get("emergency_service", "unknown"),
                "limitations": props.get("limitations", "Extracted from OpenStreetMap; not field-verified by municipal audit.")
            })

        print(f"[ACCESSIBILITY] Loaded {len(self.facilities)} critical facilities.")

    def find_accessible_facilities(
        self,
        origin_lat: float,
        origin_lon: float,
        facility_category: str = "hospital",
        max_results: int = 5,
        max_search_radius_km: float = 8.0,
        lambda_param: float = 3.0
    ) -> Dict[str, Any]:
        """
        Identifies and ranks geographically accessible critical facilities from an origin coordinate.
        Calculates both straight-line Haversine distance and actual road-network driving route.
        """
        category_lower = facility_category.lower()

        # Categorization filter mapping
        category_aliases = {
            "hospital": ["hospital", "clinic", "doctors", "nursing_home", "health_centre"],
            "medical": ["hospital", "clinic", "doctors", "pharmacy", "health_centre"],
            "clinic": ["clinic", "doctors", "health_centre"],
            "pharmacy": ["pharmacy"],
            "all": []
        }

        target_categories = category_aliases.get(category_lower, [category_lower])

        candidates = []
        for fac in self.facilities:
            if target_categories and fac["category"] not in target_categories:
                # Substring match if exact match fails
                if not any(cat in fac["category"] for cat in target_categories):
                    continue

            h_dist = haversine_distance_km(origin_lat, origin_lon, fac["latitude"], fac["longitude"])
            if h_dist <= max_search_radius_km:
                candidates.append((fac, h_dist))

        # Sort candidate facilities by straight-line distance first
        candidates.sort(key=lambda x: x[1])

        results = []
        for fac, straight_line_km in candidates[: max_results * 2]:
            # Calculate road-network path
            route = road_network_service.find_lowest_risk_path(
                origin_lat, origin_lon,
                fac["latitude"], fac["longitude"],
                lambda_param=lambda_param
            )

            if route.get("found"):
                road_dist_km = route["total_distance_km"]
                avg_risk = route["average_risk_score"]
                inc_segments = route["incident_affected_segment_count"]
                dis_segments = route["disruption_affected_segment_count"]

                # Determine accessibility classification
                if dis_segments > 0 or inc_segments >= 3:
                    acc_status = "CAUTION_DISRUPTED_CORRIDOR"
                elif avg_risk >= 70.0:
                    acc_status = "HIGH_RISK_ROUTE"
                elif avg_risk >= 40.0:
                    acc_status = "MODERATE_RISK_ACCESSIBLE"
                else:
                    acc_status = "ACCESSIBLE"

                results.append({
                    "facility_id": fac["facility_id"],
                    "facility_name": fac["name"],
                    "facility_category": fac["category"],
                    "latitude": fac["latitude"],
                    "longitude": fac["longitude"],
                    "straight_line_distance_km": straight_line_km,
                    "road_network_distance_km": road_dist_km,
                    "road_network_distance_meters": route["total_distance_meters"],
                    "route_average_risk_score": avg_risk,
                    "route_risk_category": route["risk_category"],
                    "incident_affected_segments": inc_segments,
                    "disruption_affected_segments": dis_segments,
                    "accessibility_status": acc_status,
                    "route_geometry": route["coordinates"],
                    "primary_roads": route["primary_roads_traversed"],
                    "data_provenance": fac["provenance"],
                    "verification_status": fac["verification_status"],
                    "disclaimer": "Facility sourced from OpenStreetMap; operational readiness not verified on ground."
                })
            else:
                results.append({
                    "facility_id": fac["facility_id"],
                    "facility_name": fac["name"],
                    "facility_category": fac["category"],
                    "latitude": fac["latitude"],
                    "longitude": fac["longitude"],
                    "straight_line_distance_km": straight_line_km,
                    "road_network_distance_km": None,
                    "road_network_distance_meters": None,
                    "route_average_risk_score": None,
                    "route_risk_category": "UNKNOWN",
                    "incident_affected_segments": 0,
                    "disruption_affected_segments": 0,
                    "accessibility_status": "UNREACHABLE_BY_ROAD",
                    "route_geometry": [],
                    "primary_roads": [],
                    "data_provenance": fac["provenance"],
                    "verification_status": fac["verification_status"],
                    "disclaimer": "Facility unreachable due to road network severance or bounding-box disconnection."
                })

            if len(results) >= max_results:
                break

        # Sort final results by road network distance if available, else straight line
        results.sort(key=lambda x: (x["road_network_distance_km"] is None, x["road_network_distance_km"] or x["straight_line_distance_km"]))

        return {
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "requested_category": facility_category,
            "facilities_found_count": len(results),
            "accessible_count": sum(1 for r in results if r["road_network_distance_km"] is not None and "UNREACHABLE" not in r["accessibility_status"]),
            "unreachable_count": sum(1 for r in results if r["accessibility_status"] == "UNREACHABLE_BY_ROAD"),
            "facilities": results
        }


accessibility_service = AccessibilityService()
