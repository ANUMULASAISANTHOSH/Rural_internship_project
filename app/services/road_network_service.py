"""
AQUILA Phase 4 - Flood-Aware Road Network Service
Constructs and manages an indexed NetworkX topological graph from OpenStreetMap road segments.
Supports shortest path (distance-optimal) and lowest-risk path (safety-optimal) calculations,
spatial snapping via cKDTree, localized risk sampling, and incident-based edge cost penalization.
"""

import os
import json
import math
from typing import Dict, Any, List, Tuple, Optional
import networkx as nx
import numpy as np
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import shape, Point, LineString
from shapely.strtree import STRtree
import rasterio

from app.db.database import SessionLocal, utc_now
from app.db.models import Incident, RoadDisruption, RainfallObservation
from app.services.risk_engine import compute_geographic_risk, calculate_rainfall_score

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROADS_GEOJSON = os.path.join(BASE_DIR, "data", "processed", "vector", "roads_manikonda_processed.geojson")
DRAINAGE_GEOJSON = os.path.join(BASE_DIR, "data", "processed", "vector", "drainage_manikonda_processed.geojson")
WATER_BODIES_GEOJSON = os.path.join(BASE_DIR, "data", "processed", "vector", "water_bodies_manikonda_processed.geojson")
HISTORICAL_FLOOD_GEOJSON = os.path.join(BASE_DIR, "data", "processed", "vector", "historical_flood_points_processed.geojson")
DEM_RASTER = os.path.join(BASE_DIR, "data", "processed", "raster", "dem_manikonda_clipped.tif")
SLOPE_RASTER = os.path.join(BASE_DIR, "data", "processed", "raster", "slope_degrees_manikonda.tif")


class RoadNetworkService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RoadNetworkService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.graph = nx.DiGraph()
        self.node_map: Dict[Tuple[float, float], int] = {}
        self.node_coords_utm: List[Tuple[float, float]] = []
        self.node_ids_in_order: List[int] = []
        self.largest_cc_nodes: set = set()
        self.largest_cc_node_indices: List[int] = []
        self.largest_cc_coords_utm: List[Tuple[float, float]] = []
        self.kdtree: Optional[cKDTree] = None
        self.kdtree_largest_cc: Optional[cKDTree] = None
        
        # Spatial Transformer: EPSG:4326 (WGS84) to EPSG:32644 (UTM Zone 44N)
        self.transformer = Transformer.from_crs("EPSG:4326", "EPSG:32644", always_xy=True)
        
        # Spatial reference data for risk computation
        self._waterway_geoms: List[Any] = []
        self._waterway_tree: Optional[STRtree] = None
        self._flood_points: List[Tuple[float, float]] = []
        self._dem_data: Optional[np.ndarray] = None
        self._dem_inv_transform = None
        self._slope_data: Optional[np.ndarray] = None
        self._slope_inv_transform = None
        
        self._load_spatial_auxiliaries()
        self._build_graph()
        self._initialized = True

    def _load_spatial_auxiliaries(self):
        """Loads waterway trees, historical points, and DEM/Slope rasters for segment risk sampling."""
        # 1. Drainage and Water bodies
        water_features = []
        for path in [DRAINAGE_GEOJSON, WATER_BODIES_GEOJSON]:
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    for feat in data.get("features", []):
                        geom = feat.get("geometry")
                        if geom:
                            water_features.append(shape(geom))
                except Exception as e:
                    print(f"[ROAD_NET] Warning loading water features from {path}: {e}")
        
        if water_features:
            self._waterway_geoms = water_features
            self._waterway_tree = STRtree(water_features)

        # 2. Historical flood evidence points
        if os.path.exists(HISTORICAL_FLOOD_GEOJSON):
            try:
                with open(HISTORICAL_FLOOD_GEOJSON, encoding="utf-8") as f:
                    flood_data = json.load(f)
                for feat in flood_data.get("features", []):
                    coords = feat.get("geometry", {}).get("coordinates", [])
                    if len(coords) >= 2:
                        self._flood_points.append((float(coords[0]), float(coords[1])))
            except Exception as e:
                print(f"[ROAD_NET] Warning loading flood points: {e}")

        # 3. DEM and Slope rasters
        if os.path.exists(DEM_RASTER):
            try:
                with rasterio.open(DEM_RASTER) as src:
                    self._dem_data = src.read(1)
                    self._dem_inv_transform = ~src.transform
            except Exception as e:
                print(f"[ROAD_NET] Warning loading DEM: {e}")

        if os.path.exists(SLOPE_RASTER):
            try:
                with rasterio.open(SLOPE_RASTER) as src:
                    self._slope_data = src.read(1)
                    self._slope_inv_transform = ~src.transform
            except Exception as e:
                print(f"[ROAD_NET] Warning loading Slope: {e}")

    def _sample_elevation(self, lon: float, lat: float) -> float:
        if self._dem_data is not None and self._dem_inv_transform is not None:
            try:
                c, r = self._dem_inv_transform @ (lon, lat)
                col, row = int(round(c)), int(round(r))
                if 0 <= row < self._dem_data.shape[0] and 0 <= col < self._dem_data.shape[1]:
                    val = float(self._dem_data[row, col])
                    if np.isfinite(val) and val > 0:
                        return val
            except Exception:
                pass
        return 525.0

    def _sample_slope(self, lon: float, lat: float) -> float:
        if self._slope_data is not None and self._slope_inv_transform is not None:
            try:
                c, r = self._slope_inv_transform @ (lon, lat)
                col, row = int(round(c)), int(round(r))
                if 0 <= row < self._slope_data.shape[0] and 0 <= col < self._slope_data.shape[1]:
                    val = float(self._slope_data[row, col])
                    if np.isfinite(val) and val >= 0:
                        return val
            except Exception:
                pass
        return 2.5

    def _sample_waterway_distance(self, lon: float, lat: float) -> float:
        if self._waterway_tree is not None and self._waterway_geoms:
            try:
                pt = Point(lon, lat)
                idx = self._waterway_tree.nearest(pt)
                nearest_geom = self._waterway_geoms[idx]
                # Planar distance approximation in meters at lat 17.4°
                dx = (nearest_geom.centroid.x - lon) * 106100.0
                dy = (nearest_geom.centroid.y - lat) * 110700.0
                return max(5.0, math.sqrt(dx**2 + dy**2))
            except Exception:
                pass
        return 350.0

    def _sample_flood_distance(self, lon: float, lat: float) -> float:
        if self._flood_points:
            min_d = 999999.0
            for flon, flat in self._flood_points:
                dx = (flon - lon) * 106100.0
                dy = (flat - lat) * 110700.0
                d = math.sqrt(dx**2 + dy**2)
                if d < min_d:
                    min_d = d
            return max(5.0, min_d)
        return 1200.0

    def _get_or_create_node(self, lon: float, lat: float) -> int:
        key = (round(lon, 6), round(lat, 6))
        if key not in self.node_map:
            node_id = len(self.node_map)
            self.node_map[key] = node_id
            utm_x, utm_y = self.transformer.transform(lon, lat)
            self.graph.add_node(node_id, lon=lon, lat=lat, x=utm_x, y=utm_y)
            self.node_coords_utm.append((utm_x, utm_y))
            self.node_ids_in_order.append(node_id)
        return self.node_map[key]

    def _build_graph(self):
        """Constructs the NetworkX directed graph from processed OSM roads."""
        if not os.path.exists(ROADS_GEOJSON):
            raise FileNotFoundError(f"Roads GeoJSON not found at: {ROADS_GEOJSON}")

        with open(ROADS_GEOJSON, encoding="utf-8") as f:
            data = json.load(f)

        features = data.get("features", [])
        for feat in features:
            geom = feat.get("geometry", {})
            if geom.get("type") != "LineString":
                continue

            coords = geom.get("coordinates", [])
            if len(coords) < 2:
                continue

            props = feat.get("properties", {})
            hw_type = props.get("highway", "residential")
            name = props.get("name") or "Unnamed Road"
            osm_id = props.get("osm_id")
            oneway = props.get("oneway") in ("yes", "1", True)

            for i in range(len(coords) - 1):
                p1_lon, p1_lat = float(coords[i][0]), float(coords[i][1])
                p2_lon, p2_lat = float(coords[i+1][0]), float(coords[i+1][1])

                u = self._get_or_create_node(p1_lon, p1_lat)
                v = self._get_or_create_node(p2_lon, p2_lat)

                if u == v:
                    continue

                ux, uy = self.graph.nodes[u]["x"], self.graph.nodes[u]["y"]
                vx, vy = self.graph.nodes[v]["x"], self.graph.nodes[v]["y"]
                length_m = max(0.5, math.sqrt((vx - ux)**2 + (vy - uy)**2))

                mid_lon = (p1_lon + p2_lon) / 2.0
                mid_lat = (p1_lat + p2_lat) / 2.0

                elev = self._sample_elevation(mid_lon, mid_lat)
                slope = self._sample_slope(mid_lon, mid_lat)
                w_dist = self._sample_waterway_distance(mid_lon, mid_lat)
                f_dist = self._sample_flood_distance(mid_lon, mid_lat)

                # Precompute baseline risk at standard 25 mm/hr rain
                base_risk = compute_geographic_risk(
                    rainfall_rate_mm_hr=25.0,
                    elevation_m=elev,
                    slope_degrees=slope,
                    distance_to_waterway_m=w_dist,
                    landcover_class=50,
                    distance_to_flood_point_m=f_dist
                )["final_risk_score"]

                edge_attrs = {
                    "length_m": round(length_m, 2),
                    "highway": hw_type,
                    "name": name,
                    "osm_id": osm_id,
                    "mid_lon": round(mid_lon, 6),
                    "mid_lat": round(mid_lat, 6),
                    "elevation_m": round(elev, 1),
                    "slope_degrees": round(slope, 1),
                    "distance_waterway_m": round(w_dist, 1),
                    "distance_flood_point_m": round(f_dist, 1),
                    "base_risk_score": base_risk,
                    "current_risk_score": base_risk,
                    "incident_penalty": 0.0,
                    "disruption_penalty": 0.0,
                    "shortest_cost": round(length_m, 2),
                    "risk_cost": round(length_m * (1.0 + 3.0 * (base_risk / 100.0)), 2),
                    "geometry": [[p1_lon, p1_lat], [p2_lon, p2_lat]]
                }

                self.graph.add_edge(u, v, **edge_attrs)
                if not oneway:
                    self.graph.add_edge(v, u, **edge_attrs)

        # Analyze connected components
        components = list(nx.weakly_connected_components(self.graph))
        if components:
            self.largest_cc_nodes = max(components, key=len)
            for idx, node_id in enumerate(self.node_ids_in_order):
                if node_id in self.largest_cc_nodes:
                    self.largest_cc_node_indices.append(node_id)
                    self.largest_cc_coords_utm.append(self.node_coords_utm[idx])

        # Build KDTree spatial indices
        if self.node_coords_utm:
            self.kdtree = cKDTree(np.array(self.node_coords_utm))
        if self.largest_cc_coords_utm:
            self.kdtree_largest_cc = cKDTree(np.array(self.largest_cc_coords_utm))

        print(f"[ROAD_NET] Initialized road network graph: {self.graph.number_of_nodes()} nodes, "
              f"{self.graph.number_of_edges()} edges. Largest CC: {len(self.largest_cc_nodes)} nodes "
              f"({len(self.largest_cc_nodes)/max(1, self.graph.number_of_nodes())*100:.1f}%).")

    def snap_to_node(self, lat: float, lon: float, must_be_in_largest_cc: bool = True) -> Tuple[int, float]:
        """Snaps an arbitrary (lat, lon) to the nearest road network node in meters."""
        utm_x, utm_y = self.transformer.transform(lon, lat)
        
        if must_be_in_largest_cc and self.kdtree_largest_cc is not None:
            dist_m, idx = self.kdtree_largest_cc.query([utm_x, utm_y])
            node_id = self.largest_cc_node_indices[idx]
            return node_id, float(dist_m)
        elif self.kdtree is not None:
            dist_m, idx = self.kdtree.query([utm_x, utm_y])
            node_id = self.node_ids_in_order[idx]
            return node_id, float(dist_m)
        else:
            raise RuntimeError("Spatial KDTree not initialized.")

    def update_edge_weights(
        self,
        db_session=None,
        rainfall_rate_mm_hr: Optional[float] = None,
        lambda_param: float = 3.0,
        incident_influence_radius_m: float = 200.0,
        incident_penalty_multiplier: float = 12.0
    ):
        """
        Dynamically updates edge weights based on:
        1. Current rainfall rate.
        2. Active flood incidents (REPORTED, UNDER_REVIEW, ASSIGNED, IN_PROGRESS).
        3. Active road disruptions (ACTIVE).
        """
        db = db_session or SessionLocal()
        close_db_after = db_session is None

        try:
            # 1. Determine rainfall rate
            if rainfall_rate_mm_hr is None:
                latest_rain = db.query(RainfallObservation).order_by(RainfallObservation.id.desc()).first()
                curr_rain = latest_rain.rainfall_mm_per_hour if latest_rain else 25.0
            else:
                curr_rain = max(0.0, float(rainfall_rate_mm_hr))

            # 2. Fetch active incidents
            active_incidents = (
                db.query(Incident)
                .filter(Incident.status.in_(["REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS"]))
                .all()
            )

            # 3. Fetch active disruptions
            active_disruptions = (
                db.query(RoadDisruption)
                .filter(RoadDisruption.status == "ACTIVE")
                .all()
            )

            incident_locs = []
            for inc in active_incidents:
                severity_weight = {
                    "CRITICAL": 2.5,
                    "HIGH": 1.8,
                    "MODERATE": 1.2,
                    "LOW": 0.6
                }.get(inc.severity, 1.0)
                incident_locs.append({
                    "lat": inc.latitude,
                    "lon": inc.longitude,
                    "weight": severity_weight,
                    "code": inc.incident_code
                })

            disruption_locs = []
            for dis in active_disruptions:
                disruption_locs.append({
                    "lat": dis.latitude,
                    "lon": dis.longitude,
                    "radius": dis.radius_meters,
                    "factor": dis.penalty_factor,
                    "code": dis.disruption_code
                })

            # Update edges
            for u, v, data in self.graph.edges(data=True):
                mid_lon = data["mid_lon"]
                mid_lat = data["mid_lat"]
                length_m = data["length_m"]

                # A. Risk Score updated with current rainfall
                risk_res = compute_geographic_risk(
                    rainfall_rate_mm_hr=curr_rain,
                    elevation_m=data["elevation_m"],
                    slope_degrees=data["slope_degrees"],
                    distance_to_waterway_m=data["distance_waterway_m"],
                    landcover_class=50,
                    distance_to_flood_point_m=data["distance_flood_point_m"]
                )
                r_score = risk_res["final_risk_score"]
                data["current_risk_score"] = r_score

                # B. Incident proximity penalty
                p_inc = 0.0
                for inc in incident_locs:
                    dx = (inc["lon"] - mid_lon) * 106100.0
                    dy = (inc["lat"] - mid_lat) * 110700.0
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist <= incident_influence_radius_m:
                        decay = 1.0 - (dist / incident_influence_radius_m)
                        p_inc += decay * inc["weight"] * incident_penalty_multiplier

                data["incident_penalty"] = round(p_inc, 2)

                # C. Road disruption penalty
                p_dis = 0.0
                for dis in disruption_locs:
                    dx = (dis["lon"] - mid_lon) * 106100.0
                    dy = (dis["lat"] - mid_lat) * 110700.0
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist <= dis["radius"]:
                        decay = 1.0 - (dist / dis["radius"])
                        p_dis += decay * dis["factor"] * 25.0

                data["disruption_penalty"] = round(p_dis, 2)

                # D. Total edge costs
                data["shortest_cost"] = length_m
                total_risk_multiplier = 1.0 + lambda_param * (r_score / 100.0) + p_inc + p_dis
                data["risk_cost"] = round(length_m * max(1.0, total_risk_multiplier), 2)

        finally:
            if close_db_after:
                db.close()

    def _format_route_result(
        self,
        node_path: List[int],
        cost_key: str,
        route_type: str,
        lambda_param: float
    ) -> Dict[str, Any]:
        """Assembles rich route payload including GeoJSON coordinates, length, risk metrics, and segments."""
        if not node_path:
            return {
                "route_type": route_type,
                "found": False,
                "error": "No route found."
            }

        coords = []
        total_length_m = 0.0
        total_weighted_risk = 0.0
        high_risk_segment_count = 0
        incident_affected_segment_count = 0
        disruption_affected_segment_count = 0
        road_names = []

        for i in range(len(node_path) - 1):
            u = node_path[i]
            v = node_path[i+1]
            data = self.graph.get_edge_data(u, v)
            if not data:
                continue

            length_m = data["length_m"]
            r_score = data.get("current_risk_score", data.get("base_risk_score", 50.0))
            inc_pen = data.get("incident_penalty", 0.0)
            dis_pen = data.get("disruption_penalty", 0.0)

            total_length_m += length_m
            total_weighted_risk += length_m * r_score

            if r_score >= 70.0:
                high_risk_segment_count += 1
            if inc_pen > 0.1:
                incident_affected_segment_count += 1
            if dis_pen > 0.1:
                disruption_affected_segment_count += 1

            r_name = data.get("name", "Unnamed Road")
            if r_name and r_name != "Unnamed Road" and (not road_names or road_names[-1] != r_name):
                road_names.append(r_name)

            edge_geom = data.get("geometry")
            if edge_geom:
                if not coords:
                    coords.append(edge_geom[0])
                coords.append(edge_geom[1])
            else:
                coords.append([self.graph.nodes[u]["lon"], self.graph.nodes[u]["lat"]])

        if not coords:
            coords = [[self.graph.nodes[n]["lon"], self.graph.nodes[n]["lat"]] for n in node_path]

        avg_risk = round(total_weighted_risk / max(0.1, total_length_m), 1)

        return {
            "route_type": route_type,
            "found": True,
            "total_distance_meters": round(total_length_m, 1),
            "total_distance_km": round(total_length_m / 1000.0, 3),
            "average_risk_score": avg_risk,
            "risk_category": "HIGH" if avg_risk >= 70.0 else ("MODERATE" if avg_risk >= 40.0 else "LOW"),
            "high_risk_segment_count": high_risk_segment_count,
            "incident_affected_segment_count": incident_affected_segment_count,
            "disruption_affected_segment_count": disruption_affected_segment_count,
            "node_count": len(node_path),
            "primary_roads_traversed": road_names[:8] if road_names else ["Local Manikonda Roads"],
            "coordinates": coords,
            "lambda_param_applied": lambda_param
        }

    def find_shortest_path(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float
    ) -> Dict[str, Any]:
        """Calculates distance-optimal shortest path using Dijkstra."""
        u_node, d_snap_orig = self.snap_to_node(origin_lat, origin_lon, must_be_in_largest_cc=True)
        v_node, d_snap_dest = self.snap_to_node(dest_lat, dest_lon, must_be_in_largest_cc=True)

        if u_node == v_node:
            return {
                "route_type": "SHORTEST",
                "found": True,
                "total_distance_meters": 0.0,
                "total_distance_km": 0.0,
                "average_risk_score": 25.0,
                "risk_category": "LOW",
                "high_risk_segment_count": 0,
                "incident_affected_segment_count": 0,
                "disruption_affected_segment_count": 0,
                "node_count": 1,
                "primary_roads_traversed": ["Origin is at destination"],
                "coordinates": [[origin_lon, origin_lat]],
                "snapping_distance_origin_m": round(d_snap_orig, 1),
                "snapping_distance_dest_m": round(d_snap_dest, 1)
            }

        try:
            path = nx.shortest_path(self.graph, source=u_node, target=v_node, weight="shortest_cost")
            res = self._format_route_result(path, "shortest_cost", "SHORTEST", lambda_param=0.0)
            res["snapping_distance_origin_m"] = round(d_snap_orig, 1)
            res["snapping_distance_dest_m"] = round(d_snap_dest, 1)
            return res
        except nx.NetworkXNoPath:
            return {
                "route_type": "SHORTEST",
                "found": False,
                "error": "No road path connects the selected origin and destination.",
                "snapping_distance_origin_m": round(d_snap_orig, 1),
                "snapping_distance_dest_m": round(d_snap_dest, 1)
            }

    def find_lowest_risk_path(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        lambda_param: float = 3.0
    ) -> Dict[str, Any]:
        """Calculates safety-optimal lowest-risk path using Dijkstra."""
        u_node, d_snap_orig = self.snap_to_node(origin_lat, origin_lon, must_be_in_largest_cc=True)
        v_node, d_snap_dest = self.snap_to_node(dest_lat, dest_lon, must_be_in_largest_cc=True)

        if u_node == v_node:
            return {
                "route_type": "LOWEST_RISK",
                "found": True,
                "total_distance_meters": 0.0,
                "total_distance_km": 0.0,
                "average_risk_score": 25.0,
                "risk_category": "LOW",
                "high_risk_segment_count": 0,
                "incident_affected_segment_count": 0,
                "disruption_affected_segment_count": 0,
                "node_count": 1,
                "primary_roads_traversed": ["Origin is at destination"],
                "coordinates": [[origin_lon, origin_lat]],
                "snapping_distance_origin_m": round(d_snap_orig, 1),
                "snapping_distance_dest_m": round(d_snap_dest, 1)
            }

        try:
            path = nx.shortest_path(self.graph, source=u_node, target=v_node, weight="risk_cost")
            res = self._format_route_result(path, "risk_cost", "LOWEST_RISK", lambda_param=lambda_param)
            res["snapping_distance_origin_m"] = round(d_snap_orig, 1)
            res["snapping_distance_dest_m"] = round(d_snap_dest, 1)
            return res
        except nx.NetworkXNoPath:
            return {
                "route_type": "LOWEST_RISK",
                "found": False,
                "error": "No viable path avoids active road disruptions.",
                "snapping_distance_origin_m": round(d_snap_orig, 1),
                "snapping_distance_dest_m": round(d_snap_dest, 1)
            }

    def compare_routes(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        lambda_param: float = 3.0
    ) -> Dict[str, Any]:
        """Calculates both shortest and lowest-risk routes and generates an explainable comparison."""
        from app.services.route_explanation_service import route_explanation_service

        shortest = self.find_shortest_path(origin_lat, origin_lon, dest_lat, dest_lon)
        lowest_risk = self.find_lowest_risk_path(origin_lat, origin_lon, dest_lat, dest_lon, lambda_param=lambda_param)
        explanation = route_explanation_service.explain_route_comparison(shortest, lowest_risk, lambda_param=lambda_param)

        return {
            "origin": {"latitude": origin_lat, "longitude": origin_lon},
            "destination": {"latitude": dest_lat, "longitude": dest_lon},
            "shortest_route": shortest,
            "lowest_risk_route": lowest_risk,
            "comparison": explanation
        }


    def get_network_summary(self) -> Dict[str, Any]:
        """Returns topological and attribute summary of the road graph."""
        hw_counts = {}
        for _, _, data in self.graph.edges(data=True):
            hw = data.get("highway", "unknown")
            hw_counts[hw] = hw_counts.get(hw, 0) + 1

        total_nodes = self.graph.number_of_nodes()
        largest_cc_size = len(self.largest_cc_nodes)

        return {
            "total_nodes": total_nodes,
            "total_directed_edges": self.graph.number_of_edges(),
            "largest_connected_component_nodes": largest_cc_size,
            "connectivity_percentage": round((largest_cc_size / max(1, total_nodes)) * 100.0, 1),
            "highway_type_distribution": hw_counts,
            "spatial_projection": "EPSG:32644 (UTM Zone 44N)",
            "storage_crs": "EPSG:4326 (WGS 84)",
            "road_features_source": "OpenStreetMap Manikonda Extract"
        }


# Singleton Instance
road_network_service = RoadNetworkService()
