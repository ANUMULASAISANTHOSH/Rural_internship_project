"""
AQUILA — Command-Centre Operational Dashboard
Streamlit-based interface for Urban Flood Intelligence & Emergency Response.
"""

import os
import sys
from datetime import datetime
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.db.database import SessionLocal
from app.db.models import Incident, Resource, RainfallObservation, AuditHistory, IncidentAssignment, RoadDisruption
from app.db.seed import init_db
from app.services.geo_service import get_layer
from app.services.risk_engine import compute_geographic_risk, DEFAULT_WEIGHTS
from app.services.resource_service import recommend_resource_for_incident, assign_resource_to_incident
from app.services.scenario_service import scenario_manager
from app.services.road_network_service import road_network_service
from app.services.accessibility_service import accessibility_service
from app.services.route_explanation_service import route_explanation_service
from app.services.scenario_comparison_service import scenario_comparison_service
from app.services.uncertainty_service import uncertainty_service
from app.services.vulnerability_service import vulnerability_service
from app.services.response_priority_service import response_priority_service

# Page Configuration
st.set_page_config(
    page_title="AQUILA — Flood Command Centre",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
init_db(seed_resources=True)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 5px solid #0d6efd;
        margin-bottom: 10px;
    }
    .badge-observed { background-color: #28a745; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-simulated { background-color: #6f42c1; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-historical { background-color: #fd7e14; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-seeded { background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar: Controls & Configuration
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🌊 AQUILA Platform")
st.sidebar.markdown("**Urban Flood Intelligence & Response**")
st.sidebar.caption("Pilot Catchment: Manikonda, Hyderabad (55.63 km²)")
st.sidebar.markdown("---")

nav = st.sidebar.radio(
    "Navigation Mode",
    ["Command Overview", "Interactive Map", "Incident Management", "Flood-Aware Routing", "Scenario Intelligence & Analytics", "Scenario Simulator", "Audit Trail"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Risk Weight Parameters")
w_rain = st.sidebar.slider("Rainfall Weight (P)", 0.0, 1.0, 0.40, 0.05)
w_terrain = st.sidebar.slider("Terrain Weight (T)", 0.0, 1.0, 0.20, 0.05)
w_drain = st.sidebar.slider("Drainage Proximity (D)", 0.0, 1.0, 0.20, 0.05)
w_land = st.sidebar.slider("Land Cover (L)", 0.0, 1.0, 0.10, 0.05)
w_hist = st.sidebar.slider("Historical Flood (H)", 0.0, 1.0, 0.10, 0.05)

active_weights = {
    "rainfall": w_rain,
    "terrain": w_terrain,
    "drainage": w_drain,
    "landcover": w_land,
    "historical": w_hist
}

# ─────────────────────────────────────────────────────────────────────────────
# Global Database Helper
# ─────────────────────────────────────────────────────────────────────────────
db = SessionLocal()

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 1: Command Overview
# ─────────────────────────────────────────────────────────────────────────────
if nav == "Command Overview":
    st.header("🎛️ Operational Command Overview — Manikonda Pilot")

    # Fetch live stats
    total_inc = db.query(Incident).count()
    active_inc = db.query(Incident).filter(Incident.status.in_(["REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS"])).count()
    resolved_inc = db.query(Incident).filter(Incident.status == "RESOLVED").count()
    avail_res = db.query(Resource).filter(Resource.availability_status == "AVAILABLE").count()
    total_res = db.query(Resource).count()

    latest_rain = db.query(RainfallObservation).order_by(RainfallObservation.id.desc()).first()
    rain_rate = latest_rain.rainfall_mm_per_hour if latest_rain else 0.0
    rain_prov = latest_rain.source_type if latest_rain else "HISTORICAL"

    # Compute risk
    risk_data = compute_geographic_risk(rainfall_rate_mm_hr=rain_rate, custom_weights=active_weights)
    risk_score = risk_data["final_risk_score"]
    risk_cat = risk_data["risk_category"]

    # Top KPI Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Active Incidents", f"{active_inc} / {total_inc}", delta="Active Flood Events")
    c2.metric("Available Resources", f"{avail_res} / {total_res}", delta="Emergency Fleet")
    c3.metric("Current Rainfall", f"{rain_rate:.1f} mm/hr", delta=f"Tag: {rain_prov}")
    c4.metric("Geographic Risk Index", f"{risk_score} / 100", delta=f"Rating: {risk_cat}")
    c5.metric("Simulation Status", "ACTIVE" if scenario_manager.is_active else "IDLE")

    st.markdown("---")

    # Risk Index Breakdown Gauge & Chart
    r_col1, r_col2 = st.columns([1, 1])

    with r_col1:
        st.subheader("🎯 Geographic Risk Gauge")
        cat_colors = {"LOW": "#28a745", "MODERATE": "#fd7e14", "HIGH": "#dc3545"}
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Catchment Risk: {risk_cat}"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': cat_colors.get(risk_cat, "#0d6efd")},
                'steps': [
                    {'range': [0, 40], 'color': "rgba(40, 167, 69, 0.2)"},
                    {'range': [40, 70], 'color': "rgba(253, 126, 20, 0.2)"},
                    {'range': [70, 100], 'color': "rgba(220, 53, 69, 0.2)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70.0
                }
            }
        ))
        gauge_fig.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(gauge_fig, use_container_width=True)

    with r_col2:
        st.subheader("📊 Risk Component Factor Breakdown")
        cb = risk_data["component_breakdown"]
        labels = ["Rainfall (P)", "Terrain (T)", "Drainage (D)", "Land Cover (L)", "Historical (H)"]
        scores = [cb["rainfall_score"], cb["terrain_score"], cb["drainage_score"], cb["landcover_score"], cb["historical_score"]]
        
        comp_fig = go.Figure(go.Bar(
            x=scores,
            y=labels,
            orientation='h',
            marker=dict(color=['#0d6efd', '#20c997', '#0dcaf0', '#ffc107', '#fd7e14'])
        ))
        comp_fig.update_layout(
            xaxis=dict(range=[0, 100], title="Normalized Score (0-100)"),
            height=260,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(comp_fig, use_container_width=True)

    # Active Incidents Summary Table
    st.subheader("🚨 Active Incidents Queue")
    incidents = db.query(Incident).filter(Incident.status != "RESOLVED").all()
    if incidents:
        inc_df = pd.DataFrame([{
            "Code": inc.incident_code,
            "Title": inc.title,
            "Type": inc.incident_type,
            "Severity": inc.severity,
            "Status": inc.status,
            "Provenance": inc.source_type,
            "Coordinates": f"{inc.latitude:.4f}, {inc.longitude:.4f}"
        } for inc in incidents])
        st.dataframe(inc_df, use_container_width=True)
    else:
        st.info("No active flood incidents reported at this time.")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 2: Interactive Map
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "Interactive Map":
    st.header("🗺️ Interactive Flood Intelligence Map — Manikonda")
    st.caption("Explore verified Phase 2 layers, critical infrastructure, water bodies, and active incidents.")

    # Layer selection toggles
    t1, t2, t3, t4, t5, t6, t7 = st.columns(7)
    show_bbox = t1.checkbox("Study Area", value=True)
    show_roads = t2.checkbox("Arterial Roads", value=True)
    show_water = t3.checkbox("Water Bodies", value=True)
    show_drain = t4.checkbox("Drainage Nalas", value=True)
    show_infra = t5.checkbox("Facilities", value=True)
    show_sensors = t6.checkbox("Monitoring Stations", value=True)
    show_floods = t7.checkbox("Historical Floods", value=True)

    # Folium Map Centered at Manikonda
    m = folium.Map(location=[17.3925, 78.3825], zoom_start=13, tiles="cartodbpositron")

    # 1. Study Area BBOX
    if show_bbox:
        bbox_geo = get_layer("study_area_bbox")
        folium.GeoJson(
            bbox_geo,
            name="Study Area Bounding Box",
            style_function=lambda x: {
                "fillColor": "#3388ff", "color": "#3388ff", "weight": 2, "fillOpacity": 0.05
            }
        ).add_to(m)

    # 1b. Arterial Road Network (Filtered to primary, secondary, tertiary, motorway, trunk)
    if show_roads:
        roads_geo = get_layer("roads")
        arterial_features = [
            f for f in roads_geo.get("features", [])
            if f.get("properties", {}).get("highway") in ("motorway", "primary", "secondary", "tertiary", "trunk")
        ]
        arterial_fc = {
            "type": "FeatureCollection",
            "features": arterial_features
        }
        folium.GeoJson(
            arterial_fc,
            name="Arterial Roads",
            style_function=lambda x: {
                "color": "#6c757d", "weight": 2.0, "opacity": 0.7
            },
            tooltip=folium.GeoJsonTooltip(fields=["name", "highway"], aliases=["Road:", "Class:"])
        ).add_to(m)

    # 2. Water Bodies
    if show_water:
        water_geo = get_layer("water_bodies")
        folium.GeoJson(
            water_geo,
            name="Water Bodies",
            style_function=lambda x: {
                "fillColor": "#0077be", "color": "#005580", "weight": 1.5, "fillOpacity": 0.4
            },
            tooltip=folium.GeoJsonTooltip(fields=["name", "water"], aliases=["Name:", "Type:"])
        ).add_to(m)

    # 3. Drainage Nalas
    if show_drain:
        drain_geo = get_layer("drainage")
        folium.GeoJson(
            drain_geo,
            name="Drainage Channels",
            style_function=lambda x: {
                "color": "#17a2b8", "weight": 3, "opacity": 0.8
            },
            tooltip=folium.GeoJsonTooltip(fields=["name", "waterway"], aliases=["Channel:", "Waterway:"])
        ).add_to(m)

    # 4. Critical Infrastructure
    if show_infra:
        infra_geo = get_layer("infrastructure")
        for feat in infra_geo.get("features", []):
            coords = feat["geometry"]["coordinates"]
            props = feat["properties"]
            amenity = props.get("amenity", "facility")
            color = "red" if amenity == "hospital" else ("orange" if amenity == "fire_station" else "blue")
            folium.CircleMarker(
                location=[coords[1], coords[0]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.8,
                popup=f"<b>{props.get('name')}</b><br>Type: {amenity}<br>Tag: OSM_UNVERIFIED"
            ).add_to(m)

    # 5. Monitoring Stations
    if show_sensors:
        sensors_geo = get_layer("monitoring_locations")
        for feat in sensors_geo.get("features", []):
            coords = feat["geometry"]["coordinates"]
            props = feat["properties"]
            prov = props.get("provenance", "OBSERVED")
            color = "green" if prov == "OBSERVED" else ("purple" if prov == "SIMULATED" else "cadetblue")
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.Icon(color=color, icon="tint", prefix="fa"),
                popup=f"<b>{props.get('name')}</b><br>ID: {props.get('location_id')}<br>Status: {props.get('verification_status')}<br>Provenance: {prov}"
            ).add_to(m)

    # 6. Historical Flood Points
    if show_floods:
        floods_geo = get_layer("historical_flood_points")
        for feat in floods_geo.get("features", []):
            coords = feat["geometry"]["coordinates"]
            props = feat["properties"]
            folium.Marker(
                location=[coords[1], coords[0]],
                icon=folium.Icon(color="darkred", icon="exclamation-triangle", prefix="fa"),
                popup=f"<b>{props.get('location_name')}</b><br>Oct 2020 Depth: {props.get('observed_water_depth_m')}m<br>Cause: {props.get('inundation_cause')}<br>Tag: HISTORICAL"
            ).add_to(m)

    # 7. Current Active Incidents
    active_incidents = db.query(Incident).filter(Incident.status != "RESOLVED").all()
    for inc in active_incidents:
        sev_color = "red" if inc.severity in ("CRITICAL", "HIGH") else ("orange" if inc.severity == "MODERATE" else "green")
        folium.Marker(
            location=[inc.latitude, inc.longitude],
            icon=folium.Icon(color=sev_color, icon="bullhorn", prefix="fa"),
            popup=f"<b>{inc.incident_code}: {inc.title}</b><br>Severity: {inc.severity}<br>Status: {inc.status}<br>Type: {inc.incident_type}<br>Tag: {inc.source_type}"
        ).add_to(m)

    # Render Map
    st_folium(m, width="100%", height=550)

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 3: Incident Management & Resource Dispatch
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "Incident Management":
    st.header("🚨 Incident Management & Emergency Dispatch")

    tab1, tab2, tab3 = st.tabs(["Active Incidents Queue", "Create New Incident", "Emergency Fleet Status"])

    with tab1:
        st.subheader("📋 Active Incident Log")
        all_incidents = db.query(Incident).order_by(Incident.id.desc()).all()

        if all_incidents:
            col_sel, col_act = st.columns([1, 1])
            with col_sel:
                inc_options = {f"{inc.incident_code} — {inc.title} ({inc.status})": inc.id for inc in all_incidents}
                selected_label = st.selectbox("Select Incident to Manage", list(inc_options.keys()))
                selected_id = inc_options[selected_label]
                selected_inc = db.query(Incident).filter(Incident.id == selected_id).first()

                st.markdown(f"""
                **Code:** `{selected_inc.incident_code}`  
                **Title:** {selected_inc.title}  
                **Type:** `{selected_inc.incident_type}` | **Severity:** `{selected_inc.severity}`  
                **Status:** `{selected_inc.status}` | **Provenance:** `{selected_inc.source_type}`  
                **Coordinates:** `[{selected_inc.latitude:.4f}, {selected_inc.longitude:.4f}]`  
                **Description:** {selected_inc.description or 'None provided.'}
                """)

            with col_act:
                st.markdown("#### ⚡ Operator Actions")
                new_status = st.selectbox(
                    "Update Status",
                    ["REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"],
                    index=["REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"].index(selected_inc.status)
                )
                if st.button("Apply Status Change"):
                    old = selected_inc.status
                    selected_inc.status = new_status
                    if new_status == "RESOLVED":
                        # Release assigned resources
                        asgs = db.query(IncidentAssignment).filter(IncidentAssignment.incident_id == selected_inc.id).all()
                        for a in asgs:
                            a.assignment_status = "COMPLETED"
                            res = db.query(Resource).filter(Resource.id == a.resource_id).first()
                            if res:
                                res.availability_status = "AVAILABLE"

                    audit = AuditHistory(
                        entity_type="INCIDENT",
                        entity_id=selected_inc.incident_code,
                        action="STATUS_UPDATED",
                        details=f"Operator transitioned status from {old} to {new_status}.",
                        timestamp=datetime.utcnow()
                    )
                    db.add(audit)
                    db.commit()
                    st.success(f"Updated status of {selected_inc.incident_code} to {new_status}!")
                    st.rerun()

                st.markdown("---")
                st.markdown("#### 🚒 Emergency Resource Recommendation")
                if st.button("🎯 Find Nearest Compatible Resource"):
                    rec = recommend_resource_for_incident(db, selected_inc.id)
                    if rec:
                        st.info(f"""
                        **Recommended Resource:** `{rec['resource_code']}` — {rec['resource_name']}  
                        **Type:** `{rec['resource_type']}` | **Capability:** `{rec['capability']}`  
                        **Haversine Distance:** **{rec['distance_km']} km**  
                        **Assignment Status:** `RECOMMENDED`
                        """)
                        if st.button("✅ Approve & Deploy Resource"):
                            assign_resource_to_incident(db, selected_inc.id, rec["resource_id"])
                            st.success(f"Resource {rec['resource_code']} successfully deployed to {selected_inc.incident_code}!")
                            st.rerun()
                    else:
                        st.warning("No compatible available emergency resources found within the deployment perimeter.")

        else:
            st.info("No incidents currently registered.")

    with tab2:
        st.subheader("➕ Create New Flood Incident")
        with st.form("create_incident_form"):
            f_title = st.text_input("Incident Title", "Puppalaguda Main Road Waterlogging")
            f_desc = st.text_area("Description / Field Report", "Standing water depth approx 0.35m. Vehicles bottlenecked.")
            col_t1, col_t2 = st.columns(2)
            f_type = col_t1.selectbox("Incident Type", ["WATERLOGGING", "ROAD_SEVERANCE", "CELLAR_FLOODING", "DRAIN_OVERFLOW", "STRUCTURAL_HAZARD"])
            f_sev = col_t2.selectbox("Severity", ["LOW", "MODERATE", "HIGH", "CRITICAL"], index=1)
            
            col_c1, col_c2 = st.columns(2)
            f_lat = col_c1.number_input("Latitude", value=17.4015, format="%.5f")
            f_lon = col_c2.number_input("Longitude", value=78.3750, format="%.5f")
            f_prov = st.selectbox("Provenance Tag", ["REPORTED", "SIMULATED"], index=0)

            submitted = st.form_submit_button("Register Incident")
            if submitted:
                inc_count = db.query(Incident).count() + 1
                new_code = f"INC-2026-{inc_count:04d}"
                new_inc = Incident(
                    incident_code=new_code,
                    title=f_title,
                    description=f_desc,
                    latitude=f_lat,
                    longitude=f_lon,
                    incident_type=f_type,
                    severity=f_sev,
                    status="REPORTED",
                    source_type=f_prov,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_inc)
                db.commit()

                # Audit log
                audit = AuditHistory(
                    entity_type="INCIDENT",
                    entity_id=new_code,
                    action="CREATED",
                    details=f"Registered incident {new_code}: '{f_title}' ({f_sev}, {f_type}) at [{f_lat}, {f_lon}]. Provenance: {f_prov}.",
                    timestamp=datetime.utcnow()
                )
                db.add(audit)
                db.commit()
                st.success(f"Incident {new_code} registered successfully!")
                st.rerun()

    with tab3:
        st.subheader("🚒 Emergency Fleet & Resource Registry")
        resources = db.query(Resource).all()
        res_df = pd.DataFrame([{
            "Code": r.resource_code,
            "Name": r.resource_name,
            "Type": r.resource_type,
            "Capability": r.capability,
            "Status": r.availability_status,
            "Location": f"{r.latitude:.4f}, {r.longitude:.4f}"
        } for r in resources])
        st.dataframe(res_df, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 4: Flood-Aware Routing & Safe Accessibility (Phase 4)
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "Flood-Aware Routing":
    st.header("🧭 Flood-Aware Routing, Safe Accessibility & Navigation")
    st.markdown("**Dual-Cost Dynamic Pathfinding & Explainable Route Recommendation**")
    st.caption("Calculates distance-optimal shortest paths and safety-optimal lowest-risk paths across Manikonda's 6,659 OSM road segments, penalizing active flood incidents, road disruptions, and low-lying depression corridors.")

    # Preset locations dictionary
    PRESET_ORIGINS = {
        "Alkapur Township Sector 1 (17.3912°N, 78.3845°E)": (17.3912, 78.3845),
        "Puppalaguda Junction (17.4015°N, 78.3750°E)": (17.4015, 78.3750),
        "Manikonda Municipal Office (17.3980°N, 78.3880°E)": (17.3980, 78.3880),
        "Lanco Hills Road (17.4120°N, 78.3790°E)": (17.4120, 78.3790),
        "Neknampur Lake Spillway (17.3895°N, 78.3855°E)": (17.3895, 78.3855),
        "Custom Coordinates": None
    }

    PRESET_DESTS = {
        "Shobha Hospital, Manikonda (17.3980°N, 78.3920°E)": (17.3980, 78.3920),
        "Prolife Hospital (17.4005°N, 78.3895°E)": (17.4005, 78.3895),
        "Puppalaguda Fire Station (17.4060°N, 78.3760°E)": (17.4060, 78.3760),
        "Manikonda Central Junction (17.3990°N, 78.3840°E)": (17.3990, 78.3840),
        "Khajaguda Hills Junction (17.4160°N, 78.3700°E)": (17.4160, 78.3700),
        "Custom Coordinates": None
    }

    # Session state for routing
    if "route_data" not in st.session_state:
        st.session_state.route_data = None

    c_orig, c_dest, c_param = st.columns([1.5, 1.5, 1.0])
    with c_orig:
        sel_orig = st.selectbox("🚩 Select Origin", list(PRESET_ORIGINS.keys()), index=0)
        if sel_orig == "Custom Coordinates":
            o_lat = st.number_input("Origin Lat", 17.20, 17.60, 17.3912, format="%.5f")
            o_lon = st.number_input("Origin Lon", 78.20, 78.60, 78.3845, format="%.5f")
        else:
            o_lat, o_lon = PRESET_ORIGINS[sel_orig]

    with c_dest:
        sel_dest = st.selectbox("🏁 Select Destination", list(PRESET_DESTS.keys()), index=0)
        if sel_dest == "Custom Coordinates":
            d_lat = st.number_input("Dest Lat", 17.20, 17.60, 17.3980, format="%.5f")
            d_lon = st.number_input("Dest Lon", 78.20, 78.60, 78.3920, format="%.5f")
        else:
            d_lat, d_lon = PRESET_DESTS[sel_dest]

    with c_param:
        lambda_val = st.slider("⚖️ Risk Multiplier (λ)", 0.0, 10.0, 3.0, 0.5,
                               help="Higher values force routing to make longer detours to avoid flood risk and incident zones.")
        st.caption("λ = 0: Pure distance\nλ >= 3: Strong risk avoidance")

    btn_col1, btn_col2, _ = st.columns([1.5, 1.5, 3.0])
    if btn_col1.button("🚀 Compute Route Alternatives", use_container_width=True):
        with st.spinner("Analyzing road network and computing flood-aware routes..."):
            road_network_service.update_edge_weights(db_session=db, lambda_param=lambda_val)
            comp = road_network_service.compare_routes(o_lat, o_lon, d_lat, d_lon, lambda_param=lambda_val)
            st.session_state.route_data = comp

    if btn_col2.button("🔄 Clear Route", use_container_width=True):
        st.session_state.route_data = None
        st.rerun()

    st.markdown("---")

    # If route computed, display comparison metrics and explanation
    if st.session_state.route_data:
        rdata = st.session_state.route_data
        short_r = rdata["shortest_route"]
        risk_r = rdata["lowest_risk_route"]
        comp = rdata["comparison"]

        if short_r.get("found") and risk_r.get("found"):
            # Metric Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Shortest Distance", f"{short_r['total_distance_km']:.2f} km", f"{short_r['total_distance_meters']:.0f} m")
            
            d_delta = comp["distance_delta_pct"]
            m2.metric("Lowest-Risk Distance", f"{risk_r['total_distance_km']:.2f} km",
                      f"+{d_delta:.1f}% Detour" if d_delta > 0 else "Optimal Direct")
            
            r_reduc = comp["risk_reduction_pct"]
            m3.metric("Risk Reduction", f"{comp['lowest_risk_average_risk']:.1f} / 100",
                      f"-{r_reduc:.1f}% Hazard" if r_reduc > 0 else "Baseline Risk")

            hazards_avoided = comp["avoided_incident_segments"] + comp["avoided_disruption_segments"]
            m4.metric("Hazards Avoided", f"{hazards_avoided} Zones",
                      f"{comp['avoided_high_risk_segments']} High-Risk Segments")

            # Explanation Callout Box
            pref = comp["preferred_route"]
            pref_color = "#9d4edd" if pref == "LOWEST_RISK" else "#00b4d8"
            st.markdown(f"""
            <div style="background-color: #f1f3f5; border-left: 6px solid {pref_color}; padding: 14px; border-radius: 6px; margin: 12px 0;">
                <h4 style="margin: 0 0 6px 0; color: #212529;">💡 Route Decision Support: <b>{pref.replace('_', ' ')} PREFERRED</b></h4>
                <p style="margin: 0; font-size: 14px; color: #343a40;">{comp['explanation_summary']}</p>
                <small style="display: block; margin-top: 6px; color: #6c757d;">⚠️ <i>{comp['scientific_disclaimer']}</i></small>
            </div>
            """, unsafe_allow_html=True)

            # Map Visualization
            st.subheader("🗺️ Dual-Route Geographic Comparison Map")
            
            # Center on route midpoint
            mid_lat = (o_lat + d_lat) / 2.0
            mid_lon = (o_lon + d_lon) / 2.0
            route_map = folium.Map(location=[mid_lat, mid_lon], zoom_start=14, tiles="CartoDB positron")

            # Add Shortest Route (Cyan Line)
            if short_r["coordinates"]:
                folium.PolyLine(
                    locations=[[c[1], c[0]] for c in short_r["coordinates"]],
                    color="#00b4d8",
                    weight=5,
                    opacity=0.85,
                    tooltip=f"Shortest Route: {short_r['total_distance_km']:.2f} km (Risk {short_r['average_risk_score']:.1f}/100)"
                ).add_to(route_map)

            # Add Lowest-Risk Route (Purple Line)
            if risk_r["coordinates"]:
                folium.PolyLine(
                    locations=[[c[1], c[0]] for c in risk_r["coordinates"]],
                    color="#7209b7",
                    weight=5,
                    opacity=0.9,
                    dash_array="8, 8",
                    tooltip=f"Lowest-Risk Route: {risk_r['total_distance_km']:.2f} km (Risk {risk_r['average_risk_score']:.1f}/100)"
                ).add_to(route_map)

            # Origin & Destination Markers
            folium.Marker(
                [o_lat, o_lon],
                popup=f"<b>Origin:</b> {sel_orig}",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(route_map)

            folium.Marker(
                [d_lat, d_lon],
                popup=f"<b>Destination:</b> {sel_dest}",
                icon=folium.Icon(color="red", icon="stop")
            ).add_to(route_map)

            # Overlay Active Incidents
            active_incs = db.query(Incident).filter(Incident.status.in_(["REPORTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS"])).all()
            for inc in active_incs:
                folium.CircleMarker(
                    [inc.latitude, inc.longitude],
                    radius=8,
                    color="#d90429",
                    fill=True,
                    fill_color="#d90429",
                    fill_opacity=0.7,
                    popup=f"<b>Incident:</b> {inc.incident_code}<br>{inc.title}<br><b>Severity:</b> {inc.severity}"
                ).add_to(route_map)

            # Overlay Active Road Disruptions
            active_disruptions = db.query(RoadDisruption).filter(RoadDisruption.status == "ACTIVE").all()
            for dis in active_disruptions:
                folium.Circle(
                    [dis.latitude, dis.longitude],
                    radius=dis.radius_meters,
                    color="#ff6b35",
                    fill=True,
                    fill_color="#ff6b35",
                    fill_opacity=0.4,
                    popup=f"<b>Road Disruption:</b> {dis.disruption_code}<br>{dis.title}"
                ).add_to(route_map)

            # Render map
            st_folium(route_map, width="100%", height=450)
            st.caption("🔷 <b>Cyan Line:</b> Shortest Route (Distance-Optimal) | 🟣 <b>Purple Dashed:</b> Lowest-Risk Route (Safety-Optimal) | 🔴 <b>Red Dots:</b> Active Incidents | 🟠 <b>Orange Rings:</b> Road Disruptions", unsafe_allow_html=True)

        else:
            st.error("No traversable route found connecting the origin and destination. Check if the road network is severed by disruptions.")

    # ─────────────────────────────────────────────────────────────────────────
    # Accessible Critical Facilities Section
    # ─────────────────────────────────────────────────────────────────────────
    st.subheader("🏥 Accessible Emergency & Medical Facilities")
    st.caption("Evaluates road-network driving distances from the selected origin to mapped medical infrastructure, tagging unverified crowdsource data.")

    fac_col1, fac_col2 = st.columns([2, 4])
    with fac_col1:
        f_cat = st.selectbox("Facility Filter", ["hospital", "clinic", "pharmacy", "medical", "all"], index=0)
    with fac_col2:
        st.write("")
        st.write("")
        check_fac_btn = st.button("🔍 Find Nearest Accessible Facilities", use_container_width=True)

    if check_fac_btn or st.session_state.route_data:
        fac_results = accessibility_service.find_accessible_facilities(o_lat, o_lon, facility_category=f_cat, max_results=5)
        if fac_results["facilities"]:
            fac_table = []
            for f in fac_results["facilities"]:
                fac_table.append({
                    "Facility Name": f["facility_name"],
                    "Category": f["facility_category"].title(),
                    "Straight-Line (km)": f"{f['straight_line_distance_km']:.2f}",
                    "Driving Distance (km)": f"{f['road_network_distance_km']:.2f}" if f['road_network_distance_km'] else "Severed",
                    "Route Risk (0-100)": f"{f['route_average_risk_score']:.1f}" if f['route_average_risk_score'] is not None else "N/A",
                    "Accessibility Status": f["accessibility_status"],
                    "Provenance": f["verification_status"]
                })
            st.dataframe(pd.DataFrame(fac_table), use_container_width=True)
            st.caption("ℹ️ Facilities are sourced from OpenStreetMap and classified `OSM_UNVERIFIED`. Driving routes avoid active flood incidents.")
        else:
            st.info("No critical facilities found matching the criteria within search radius.")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 5: Scenario Intelligence & Decision Support (Phase 5)
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "Scenario Intelligence & Analytics":
    st.header("🧠 Scenario Intelligence, Uncertainty & Decision Support")
    st.markdown("**Multi-Scenario Impact Synthesis, Algorithmic Sensitivity & Response Prioritization**")
    st.caption("Pilot Catchment: Manikonda, Hyderabad | Academic Decision-Support System")

    ana_tab1, ana_tab2, ana_tab3, ana_tab4 = st.tabs([
        "📊 Multi-Scenario Comparison",
        "🎯 Uncertainty & Sensitivity",
        "🏥 Infrastructure Vulnerability & Historical Consistency",
        "🚨 Response Priority Queue"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: Multi-Scenario Comparison
    # -------------------------------------------------------------------------
    with ana_tab1:
        st.subheader("Multi-Scenario Impact Matrix")
        st.caption("Compares baseline dry conditions against moderate rain, cloudburst peak, weir overflow surcharge, and arterial road severance.")

        comp_data = scenario_comparison_service.compare_all_scenarios()
        matrix = comp_data["comparison_matrix"]
        matrix_df = pd.DataFrame(matrix)

        # Highlight KPIs
        dry_row = next(r for r in matrix if r["scenario_id"] == "SCEN-DRY-000")
        storm_row = next(r for r in matrix if r["scenario_id"] == "SCEN-HVY-002")
        disr_row = next(r for r in matrix if r["scenario_id"] == "SCEN-DISR-004")

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Baseline Dry Risk", f"{dry_row['mean_catchment_risk']:.1f} / 100", delta="0.0 mm/hr Rain")
        kpi2.metric("Heavy Storm Peak Risk", f"{storm_row['mean_catchment_risk']:.1f} / 100", delta=f"+{storm_row['delta_risk_score']:.1f} pts ({storm_row['risk_pct_increase']:.0f}%)")
        kpi3.metric("Severed Corridor Risk", f"{disr_row['mean_catchment_risk']:.1f} / 100", delta=f"{disr_row['inaccessible_road_segments']} Severed Edges")
        kpi4.metric("Peak Dewatering Demand", f"{disr_row['dewatering_pumps_needed']} Pumps", delta=f"{disr_row['rescue_boats_needed']} Rescue Boats")

        st.markdown("---")

        # Comparative Visualization
        sc_names = [r["scenario_name"] for r in matrix]
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            x=sc_names,
            y=[r["mean_catchment_risk"] for r in matrix],
            name="Mean Catchment Risk (0-100)",
            marker_color="#0d6efd"
        ))
        fig_comp.add_trace(go.Bar(
            x=sc_names,
            y=[round(r["high_risk_edges"] / 483.91, 1) for r in matrix],
            name="High-Risk Road Segments (%)",
            marker_color="#dc3545"
        ))
        fig_comp.update_layout(
            title="Scenario Comparison: Mean Risk vs High-Risk Road Segments (%)",
            barmode="group",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Detailed Comparison Table
        display_cols = [
            "scenario_id", "scenario_name", "rainfall_rate_mm_hr", "mean_catchment_risk",
            "risk_category", "delta_risk_score", "high_risk_edges", "inaccessible_road_segments",
            "facilities_at_risk", "dewatering_pumps_needed", "rescue_boats_needed"
        ]
        table_view = matrix_df[display_cols].rename(columns={
            "scenario_id": "ID",
            "scenario_name": "Scenario Description",
            "rainfall_rate_mm_hr": "Rain (mm/h)",
            "mean_catchment_risk": "Mean Risk",
            "risk_category": "Category",
            "delta_risk_score": "Δ Risk",
            "high_risk_edges": "High-Risk Roads",
            "inaccessible_road_segments": "Severed Roads",
            "facilities_at_risk": "At-Risk Facilities",
            "dewatering_pumps_needed": "Pumps Req.",
            "rescue_boats_needed": "Boats Req."
        })
        st.dataframe(table_view, use_container_width=True)
        st.caption(f"ℹ️ {comp_data['disclaimer']}")

    # -------------------------------------------------------------------------
    # TAB 2: Uncertainty & Sensitivity Analysis
    # -------------------------------------------------------------------------
    with ana_tab2:
        st.subheader("Algorithmic Uncertainty & OAT Sensitivity Analysis")
        st.caption("One-At-a-Time (OAT) parameter perturbation evaluates mathematical robustness and elasticity of the 5-factor risk engine.")

        pert_col1, pert_col2 = st.columns([1, 3])
        with pert_col1:
            pert_pct = st.slider("Perturbation Fraction", 0.05, 0.40, 0.20, 0.05, help="Fraction to perturb each component weight (±%).")
        with pert_col2:
            st.info("💡 **Defensible Engineering Note**: Sensitivity analysis evaluates local mathematical gradient elasticity. It does not fabricate unverified empirical confidence bounds.")

        sens_report = uncertainty_service.analyze_weight_sensitivity(perturbation_fraction=pert_pct)
        sens_df = pd.DataFrame(sens_report["factor_sensitivities"])

        c_sens1, c_sens2 = st.columns([3, 2])
        with c_sens1:
            st.markdown(f"**Factor Weight Sensitivity Ranking (Base Risk: {sens_report['base_risk_score']:.1f})**")
            st.dataframe(sens_df[[
                "factor", "base_weight", "perturbed_weight_up", "perturbed_weight_down",
                "risk_at_up", "risk_at_down", "risk_swing", "pct_swing", "elasticity"
            ]].rename(columns={
                "factor": "Factor",
                "base_weight": "Base Weight",
                "perturbed_weight_up": "Weight (+)",
                "perturbed_weight_down": "Weight (-)",
                "risk_at_up": "Risk (+)",
                "risk_at_down": "Risk (-)",
                "risk_swing": "Swing ΔR",
                "pct_swing": "% Swing",
                "elasticity": "Elasticity"
            }), use_container_width=True)

        with c_sens2:
            fig_sens = go.Figure(go.Bar(
                x=sens_df["risk_swing"],
                y=sens_df["factor"],
                orientation="h",
                marker_color="#198754"
            ))
            fig_sens.update_layout(
                title=f"Factor Risk Swing (±{int(pert_pct*100)}% Perturbation)",
                xaxis_title="Risk Swing ΔR (points)",
                yaxis=dict(autorange="reversed"),
                height=260,
                margin=dict(l=10, r=10, t=35, b=20)
            )
            st.plotly_chart(fig_sens, use_container_width=True)

        st.markdown("---")

        # Non-Linear Rainfall Sweep & Missing Layers
        sub_c1, sub_c2 = st.columns(2)
        with sub_c1:
            st.markdown("**Precipitation Non-Linear Response Curve (0 to 120 mm/hr)**")
            sweep_data = uncertainty_service.analyze_rainfall_sweep()
            sweep_df = pd.DataFrame(sweep_data["sweep_curve"])
            fig_sweep = go.Figure()
            fig_sweep.add_trace(go.Scatter(
                x=sweep_df["rainfall_rate_mm_hr"],
                y=sweep_df["final_risk_score"],
                mode="lines+markers",
                name="Geographic Risk Score",
                line=dict(color="#fd7e14", width=3)
            ))
            fig_sweep.add_hline(y=40.0, line_dash="dash", line_color="orange", annotation_text="Moderate Threshold (40)")
            fig_sweep.add_hline(y=70.0, line_dash="dash", line_color="red", annotation_text="High Risk Threshold (70)")
            fig_sweep.update_layout(
                title="Rainfall Intensity vs Catchment Risk Curve",
                xaxis_title="Rainfall Rate (mm/hr)",
                yaxis_title="Risk Index (0-100)",
                height=300,
                margin=dict(l=20, r=20, t=35, b=20)
            )
            st.plotly_chart(fig_sweep, use_container_width=True)

        with sub_c2:
            st.markdown("**Missing Layer Degradation & Renormalization**")
            missing_report = uncertainty_service.analyze_missing_layer_impact()
            miss_df = pd.DataFrame(missing_report["layer_omission_impacts"])
            st.dataframe(miss_df[[
                "missing_layer", "resulting_risk_score", "resulting_risk_category", "delta_from_full_model"
            ]].rename(columns={
                "missing_layer": "Omitted Layer",
                "resulting_risk_score": "Risk Score",
                "resulting_risk_category": "Category",
                "delta_from_full_model": "Δ vs Full Model"
            }), use_container_width=True)
            st.caption(f"Full Model Benchmark: {missing_report['full_model_risk_score']:.1f} ({missing_report['full_model_risk_category']}). {missing_report['conclusion']}")

        # Routing Lambda Sensitivity
        st.markdown("**Routing Risk Aversion Multiplier (λ) Trade-off**")
        lambda_report = uncertainty_service.analyze_routing_lambda_sensitivity()
        lam_df = pd.DataFrame(lambda_report["lambda_evaluations"])
        st.dataframe(lam_df[[
            "lambda_param", "distance_km", "detour_pct", "average_risk", "risk_reduction_pct", "route_classification"
        ]].rename(columns={
            "lambda_param": "λ Multiplier",
            "distance_km": "Distance (km)",
            "detour_pct": "Detour (+%)",
            "average_risk": "Avg Route Risk",
            "risk_reduction_pct": "Risk Reduction (%)",
            "route_classification": "Operational Profile"
        }), use_container_width=True)
        st.caption(f"💡 {lambda_report['recommendation_rationale']}")

    # -------------------------------------------------------------------------
    # TAB 3: Infrastructure Vulnerability & Historical Consistency
    # -------------------------------------------------------------------------
    with ana_tab3:
        st.subheader("Critical Infrastructure Vulnerability Index (V)")
        st.caption("Multi-criteria vulnerability scoring across all 65 critical facilities in Manikonda:")
        st.latex(r"V = 0.35 R_{\text{geo}} + 0.25 S_{\text{flood\_prox}} + 0.20 S_{\text{drain\_prox}} + 0.20 S_{\text{access\_risk}}")

        vf_c1, vf_c2 = st.columns([1, 2])
        with vf_c1:
            fac_filter = st.selectbox("Filter by Category", ["all", "hospital", "clinic", "pharmacy", "school"], index=0)
        with vf_c2:
            sim_rain = st.slider("Simulation Rainfall for Assessment (mm/hr)", 0.0, 100.0, 25.0, 5.0)

        vuln_res = vulnerability_service.rank_facilities_vulnerability(rainfall_rate_mm_hr=sim_rain, category_filter=fac_filter)
        dist = vuln_res["vulnerability_distribution"]

        v_kpi1, v_kpi2, v_kpi3, v_kpi4 = st.columns(4)
        v_kpi1.metric("🔴 Critical Vulnerability", f"{dist['CRITICAL']} Facilities", delta="V ≥ 70")
        v_kpi2.metric("🟠 High Vulnerability", f"{dist['HIGH']} Facilities", delta="50 ≤ V < 70")
        v_kpi3.metric("🟡 Moderate Vulnerability", f"{dist['MODERATE']} Facilities", delta="30 ≤ V < 50")
        v_kpi4.metric("🟢 Low Vulnerability", f"{dist['LOW']} Facilities", delta="V < 30")

        # Ranked Table
        fac_rows = []
        for f in vuln_res["ranked_facilities"]:
            fac_rows.append({
                "Name": f["name"],
                "Category": f["category"].title(),
                "Vulnerability (V)": f["vulnerability_score"],
                "Rating": f["vulnerability_category"],
                "Geo Risk": f["component_scores"]["geographic_risk_r_geo"],
                "Flood Prox Score": f["component_scores"]["historical_flood_prox_score"],
                "Drain Prox Score": f["component_scores"]["drainage_prox_score"],
                "Access Score": f["component_scores"]["access_route_risk_score"],
                "Elevation (m)": f["spatial_context"]["elevation_m"],
                "Drain Dist (m)": f["spatial_context"]["distance_to_waterway_m"],
                "Adjacent Road": f["spatial_context"]["adjacent_road_type"],
                "Provenance": f["verification_status"]
            })
        st.dataframe(pd.DataFrame(fac_rows), use_container_width=True)
        st.caption("ℹ️ All facility assets are sourced from OpenStreetMap and classified `OSM_UNVERIFIED`. Not an official structural engineering certificate.")

        st.markdown("---")

        # Historical Evidence Consistency Card (Feature F)
        st.subheader("🏛️ Historical Flood Evidence Spatial Consistency Benchmark (October 2020)")
        st.caption("Validates the model's spatial risk estimates against the 5 documented October 2020 flood evidence locations.")

        hist_res = vulnerability_service.evaluate_historical_evidence_consistency(rainfall_rate_mm_hr=sim_rain)
        
        hc1, hc2 = st.columns([1, 3])
        with hc1:
            st.metric("Spatial Agreement", f"{hist_res['spatial_agreement_percentage']:.0f}%", delta=f"{hist_res['consistent_hotspots_count']}/{hist_res['total_historical_points_evaluated']} Hotspots Consistent")
        with hc2:
            st.success(f"**Consistency Validation**: {hist_res['disclosure']}")

        hist_table = []
        for h in hist_res["hotspots"]:
            hist_table.append({
                "Hotspot ID": h["incident_id"],
                "Location Name": h["location_name"],
                "Observed Depth (m)": f"{h['observed_water_depth_m']:.2f} m",
                "Inundation Cause": h["inundation_cause"],
                "Infrastructure Impact": h["infrastructure_impact"],
                "Model Risk Score": f"{h['model_risk_score']:.1f}",
                "Model Category": h["model_risk_category"],
                "Agreement": h["spatial_consistency"],
                "Nearby Facilities (<750m)": len(h["nearby_critical_facilities_750m"])
            })
        st.dataframe(pd.DataFrame(hist_table), use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 4: Emergency Response Priority Queue
    # -------------------------------------------------------------------------
    with ana_tab4:
        st.subheader("🚨 Incident Response Priority Engine")
        st.caption("Multi-criteria human-in-the-loop priority queue for active flood incidents:")
        st.latex(r"P = 0.30 S_{\text{severity}} + 0.25 R_{\text{geo}} + 0.20 S_{\text{med\_prox}} + 0.15 S_{\text{road\_tier}} + 0.10 S_{\text{age}}")

        st.warning("🛡️ **Operational Governance Rule**: Priority rankings and candidate resource allocations are algorithmic decision aids. Physical or virtual dispatch requires explicit human operator confirmation.")

        p_data = response_priority_service.evaluate_incident_priorities(db)
        ranked_inc = p_data["ranked_incidents"]

        if ranked_inc:
            for item in ranked_inc:
                badge_color = "#dc3545" if item["priority_level"] == "P1_IMMEDIATE" else ("#fd7e14" if item["priority_level"] == "P2_URGENT" else "#ffc107")
                
                with st.expander(f"Rank #{item['priority_rank']} | {item['priority_level']} (Score: {item['priority_score']:.1f}) — {item['title']}", expanded=item['priority_rank'] <= 2):
                    col_p1, col_p2 = st.columns([3, 2])
                    with col_p1:
                        st.markdown(f"**Incident Code:** `{item['incident_code']}` | **Type:** {item['incident_type']} | **Severity:** {item['severity']}")
                        st.markdown(f"**Explainable Justification:** {item['explainable_justification']}")
                        st.markdown(f"**Nearest Medical Facility:** {item['spatial_details']['nearest_medical_facility']} ({item['spatial_details']['medical_distance_m']:.0f}m away)")
                        st.markdown(f"**Road Tier:** {item['spatial_details']['road_classification'].title()} Arterial | **Time Active:** {item['spatial_details']['minutes_open']:.1f} minutes")
                    
                    with col_p2:
                        st.markdown("**Sub-Score Breakdown (0-100)**")
                        st.progress(int(item["sub_scores"]["severity_score"]), text=f"Severity (30%): {item['sub_scores']['severity_score']:.0f}")
                        st.progress(int(item["sub_scores"]["geographic_risk_score"]), text=f"Local Risk (25%): {item['sub_scores']['geographic_risk_score']:.0f}")
                        st.progress(int(item["sub_scores"]["medical_proximity_score"]), text=f"Med Prox (20%): {item['sub_scores']['medical_proximity_score']:.0f}")
                        st.progress(int(item["sub_scores"]["road_tier_score"]), text=f"Road Tier (15%): {item['sub_scores']['road_tier_score']:.0f}")
                        st.progress(int(item["sub_scores"]["age_escalation_score"]), text=f"Age Escalation (10%): {item['sub_scores']['age_escalation_score']:.0f}")

                        if item["candidate_resource"]:
                            cand = item["candidate_resource"]
                            st.info(f"🎯 **Candidate Resource**: {cand['resource_name']} ({cand['resource_code']}) — {cand['distance_km']:.2f} km away")
                        else:
                            st.warning("⚠️ No compatible available resource currently unassigned.")

                    # Action buttons
                    btn_col1, btn_col2 = st.columns([1, 3])
                    with btn_col1:
                        if st.button(f"✅ Authorize Dispatch", key=f"auth_{item['incident_id']}"):
                            st.success(f"Operator authorized dispatch for {item['incident_code']}. Confirm assignment in Incident Management.")
        else:
            st.info("No active flood incidents currently pending in the database. Use 'Incident Management' to register a new incident or run the 'Scenario Simulator'.")


# ─────────────────────────────────────────────────────────────────────────────
# VIEW 6: Scenario Simulator (MANI-HEAVY-001)
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "Scenario Simulator":
    st.header("⚡ Scenario Simulator: MANI-HEAVY-001")
    st.markdown("**Controlled 120 mm / 3-Hour Synthetic Heavy Rainfall Demonstration**")
    st.caption("Advances through 15-minute storm time steps, dynamically recalculating the geographic risk index and injecting deterministic simulated incidents.")

    s_status = scenario_manager.get_status()

    # Scenario Controls
    ctrl_c1, ctrl_c2, ctrl_c3 = st.columns(3)
    if ctrl_c1.button("▶️ Start / Restart Scenario", use_container_width=True):
        scenario_manager.start_scenario(db)
        st.success("Scenario started at T=0 minutes!")
        st.rerun()

    if ctrl_c2.button("⏩ Advance 15-Minute Step", use_container_width=True, disabled=not scenario_manager.is_active or s_status["is_completed"]):
        res = scenario_manager.advance_step(db)
        st.rerun()

    if ctrl_c3.button("🔄 Reset Scenario (Purge SIMULATED Data)", use_container_width=True):
        res = scenario_manager.reset_scenario(db)
        st.warning(f"Reset complete. Deleted {res['deleted_simulated_incidents']} simulated incidents and {res['deleted_simulated_rainfall_records']} simulated rainfall observations. Real/historical records preserved.")
        st.rerun()

    st.markdown("---")

    # Scenario Status Cards
    curr_min = s_status["current_time_minutes"]
    curr_rate = s_status["current_rainfall_rate_mm_hr"]
    curr_cum = s_status["cumulative_depth_mm"]
    step_num = s_status["current_step"]
    tot_steps = s_status["total_steps"]

    s_risk = compute_geographic_risk(rainfall_rate_mm_hr=curr_rate, custom_weights=active_weights)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Simulation Timeline", f"T = {curr_min} min", f"Step {step_num + 1} of {tot_steps}")
    m2.metric("Rainfall Intensity", f"{curr_rate:.1f} mm/hr", "Simulated Rate")
    m3.metric("Cumulative Depth", f"{curr_cum:.1f} mm", "Scenario Total")
    m4.metric("Dynamic Risk Score", f"{s_risk['final_risk_score']} / 100", f"Category: {s_risk['risk_category']}")

    # Hyetograph Chart with Current Step Highlight
    if scenario_manager.steps:
        steps_df = pd.DataFrame(scenario_manager.steps)
        bar_colors = ["#dc3545" if i == step_num else "#0d6efd" for i in range(len(steps_df))]
        
        hyeto_fig = go.Figure(go.Bar(
            x=[f"T={t}m" for t in steps_df["time_minutes"]],
            y=steps_df["rainfall_rate_mm_hr"],
            marker_color=bar_colors,
            text=[f"{r:.0f} mm/h" for r in steps_df["rainfall_rate_mm_hr"]],
            textposition="auto"
        ))
        hyeto_fig.update_layout(
            title="Chicago Synthetic Design Storm Hyetograph (Red = Current Active Step)",
            xaxis_title="Simulation Time",
            yaxis_title="Rainfall Intensity (mm/hr)",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(hyeto_fig, use_container_width=True)

    # Simulated Incidents generated during scenario
    st.subheader("🚨 Injected Scenario Incidents")
    sim_incidents = db.query(Incident).filter(Incident.source_type == "SIMULATED").all()
    if sim_incidents:
        sim_df = pd.DataFrame([{
            "Code": i.incident_code,
            "Title": i.title,
            "Severity": i.severity,
            "Status": i.status,
            "Type": i.incident_type,
            "Coordinates": f"{i.latitude:.4f}, {i.longitude:.4f}"
        } for i in sim_incidents])
        st.dataframe(sim_df, use_container_width=True)
        st.caption("ℹ️ These incidents are tagged as `SIMULATED` and will be safely purged when the scenario is reset.")
    else:
        st.info("No simulated incidents generated yet. Advance to Step 3 (T=45 min, Peak 70 mm/hr) to observe deterministic incident triggering.")

# ─────────────────────────────────────────────────────────────────────────────
# VIEW 5: Audit Trail
# ─────────────────────────────────────────────────────────────────────────────
elif nav == "Audit Trail":
    st.header("📜 Operational Audit Log & Provenance Trail")
    st.caption("Operational append-only log of incident registrations, status transitions, dispatch approvals, and simulation events.")

    audit_records = db.query(AuditHistory).order_by(AuditHistory.id.desc()).limit(100).all()
    if audit_records:
        audit_df = pd.DataFrame([{
            "Timestamp (UTC)": a.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Entity": a.entity_type,
            "ID": a.entity_id,
            "Action": a.action,
            "Details": a.details
        } for a in audit_records])
        st.dataframe(audit_df, use_container_width=True)
    else:
        st.info("Audit log is currently empty.")

db.close()

