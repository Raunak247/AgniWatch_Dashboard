"""
AgniWatch India — Wildfire Intelligence, Risk Analytics, Simulation & Prevention Platform
Main Streamlit Application
"""

import os
import datetime
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
import numpy as np
from streamlit_folium import st_folium

import config
from services.boundaries import (
    get_boundary_geojson,
    parse_custom_geojson,
    bbox_to_geojson_polygon
)
from services.firms import FirmsClient
from services.weather import WeatherClient
from services.earth_engine import EarthEngineService
from services.risk_model import FireRiskModel
from services.simulation import FireSpreadSimulator, compare_scenarios
from services.prevention import FirePreventionService
from services.incident_service import IncidentManager
from services.export_service import (
    generate_detections_csv,
    generate_risk_grid_csv,
    generate_situation_report_markdown
)
from components.metrics import render_header, render_metric_row
from components.charts import (
    plot_frp_distribution,
    plot_detection_timeline,
    plot_risk_factor_breakdown,
    plot_simulation_growth,
    plot_wind_vector,
    plot_land_cover_distribution,
    plot_environmental_correlation
)
from components.map_view import render_interactive_map

# ==============================================================================
# Page Configuration
# ==============================================================================
st.set_page_config(
    page_title="AgniWatch India — Wildfire Intelligence Platform",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Professional Geospatial Operations Command Center
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .stRadio > div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        gap: 12px;
        background: #f8fafc;
        padding: 6px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    .stRadio > div[role="radiogroup"] > label {
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .classification-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# Session State Initialization
# ==============================================================================
# Server-side administrator credentials (inherited automatically by all users)
if "server_firms_key" not in st.session_state:
    st.session_state.server_firms_key = config.NASA_FIRMS_MAP_KEY
if "server_owm_key" not in st.session_state:
    st.session_state.server_owm_key = config.OPENWEATHERMAP_API_KEY
if "server_gee_project" not in st.session_state:
    st.session_state.server_gee_project = config.EARTH_ENGINE_PROJECT

if "selected_area_name" not in st.session_state:
    st.session_state.selected_area_name = "Tadoba-Andhari Tiger Reserve (Maharashtra) [Default]"
if "firms_source" not in st.session_state:
    st.session_state.firms_source = "VIIRS_NOAA20_NRT"
if "day_range" not in st.session_state:
    st.session_state.day_range = 3

if "risk_weights" not in st.session_state:
    st.session_state.risk_weights = config.DEFAULT_RISK_WEIGHTS.copy()

if "incident_manager" not in st.session_state:
    st.session_state.incident_manager = IncidentManager()

if "action_tracker" not in st.session_state:
    st.session_state.action_tracker = [
        {"id": "ACT-01", "beat": "Moharli Core", "action": "Clear dry teak leaf litter on road firebreaks", "status": "In Progress", "officer": "Range Forest Officer Moharli"},
        {"id": "ACT-02", "beat": "Chimur Peripheral", "action": "Awareness patrol for Mahua flower harvesters", "status": "Completed", "officer": "Beat Guard Chimur"},
        {"id": "ACT-03", "beat": "Kolsa Deep", "action": "Water bowser readiness & access route check", "status": "Pending", "officer": "Beat Guard Kolsa"}
    ]

if "ignition_coords" not in st.session_state:
    st.session_state.ignition_coords = [20.21, 79.30]
if "sim_fuel_type" not in st.session_state:
    st.session_state.sim_fuel_type = "Dry Teak & Bamboo Forest"
if "sim_wind_speed" not in st.session_state:
    st.session_state.sim_wind_speed = 18.0
if "sim_wind_from" not in st.session_state:
    st.session_state.sim_wind_from = 300.0
if "sim_slope_deg" not in st.session_state:
    st.session_state.sim_slope_deg = 6.0
if "sim_duration_hours" not in st.session_state:
    st.session_state.sim_duration_hours = 8.0

if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False


# ==============================================================================
# Sidebar Navigation & Operational Settings
# ==============================================================================
with st.sidebar:
    st.markdown("### 🛰️ AgniWatch Operations")
    
    # Study Area Selector
    area_options = list(config.STUDY_AREAS.keys()) + ["Custom Coordinates / Upload GeoJSON"]
    selected_area = st.selectbox(
        "Study Area / Protected Reserve",
        options=area_options,
        index=0,
        help="Select a monitored tiger reserve or provide custom geospatial boundaries."
    )
    st.session_state.selected_area_name = selected_area

    if selected_area == "Custom Coordinates / Upload GeoJSON":
        st.markdown("##### 📍 Custom Bounding Box")
        c1, c2 = st.columns(2)
        with c1:
            min_lon = st.number_input("Min Lon (W)", value=79.15, format="%.4f")
            min_lat = st.number_input("Min Lat (S)", value=20.05, format="%.4f")
        with c2:
            max_lon = st.number_input("Max Lon (E)", value=79.55, format="%.4f")
            max_lat = st.number_input("Max Lat (N)", value=20.45, format="%.4f")
        st.session_state.custom_bbox = [min_lon, min_lat, max_lon, max_lat]
        
        uploaded_file = st.file_uploader("Upload Boundary GeoJSON", type=["geojson", "json"])
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8")
            ok, parsed_geo, msg = parse_custom_geojson(content)
            if ok:
                st.session_state.custom_geojson = parsed_geo
                st.success("Custom boundary loaded!")

    st.markdown("---")
    st.markdown("##### 📡 Satellite Sensor Feeds")
    firms_src = st.selectbox(
        "NASA FIRMS Sensor Feed",
        options=[src[0] for src in config.FIRMS_SOURCES],
        format_func=lambda x: dict(config.FIRMS_SOURCES).get(x, x),
        index=0
    )
    st.session_state.firms_source = firms_src

    day_rng = st.slider("Lookback Window (Days)", 1, 10, st.session_state.day_range)
    st.session_state.day_range = day_rng

    if st.button("🔄 Refresh Data Feeds", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("##### ⚙️ Administrator Configuration")
    st.caption("Server API keys are active. Authorized users use these services automatically.")
    with st.expander("Admin Key Status", expanded=False):
        firms_configured = bool(st.session_state.server_firms_key and not st.session_state.server_firms_key.startswith("your_"))
        owm_configured = bool(st.session_state.server_owm_key and not st.session_state.server_owm_key.startswith("your_"))
        gee_configured = bool(st.session_state.server_gee_project and not st.session_state.server_gee_project.startswith("your_"))

        st.write(f"- NASA FIRMS: {'🟢 Active' if firms_configured else '⚪ Demo Mode'}")
        st.write(f"- OpenWeatherMap: {'🟢 Active' if owm_configured else '⚪ Demo Mode'}")
        st.write(f"- Earth Engine: {'🟢 Active' if gee_configured else '⚪ Demo Mode'}")

        admin_pin = st.text_input("Enter Admin PIN to update keys", type="password")
        if admin_pin == "2026":
            st.session_state.admin_unlocked = True
            st.success("Admin mode unlocked!")
            new_f_key = st.text_input("NASA_FIRMS_MAP_KEY", value=st.session_state.server_firms_key)
            new_w_key = st.text_input("OPENWEATHERMAP_API_KEY", value=st.session_state.server_owm_key)
            new_gee = st.text_input("EARTH_ENGINE_PROJECT", value=st.session_state.server_gee_project)
            if st.button("Save Server Keys"):
                st.session_state.server_firms_key = new_f_key
                st.session_state.server_owm_key = new_w_key
                st.session_state.server_gee_project = new_gee
                st.cache_data.clear()
                st.success("Server keys updated! Reloading...")
                st.rerun()


# ==============================================================================
# Resolve Study Area Extents
# ==============================================================================
if selected_area in config.STUDY_AREAS:
    area_meta = config.STUDY_AREAS[selected_area]
    bbox = area_meta["bbox"]
    center = area_meta["center"]
    zoom = area_meta["zoom"]
    boundary_geojson = get_boundary_geojson(area_meta["id"])
else:
    bbox = getattr(st.session_state, "custom_bbox", [79.15, 20.05, 79.55, 20.45])
    center = [(bbox[1] + bbox[3]) / 2.0, (bbox[0] + bbox[2]) / 2.0]
    zoom = 11
    boundary_geojson = getattr(st.session_state, "custom_geojson", None) or bbox_to_geojson_polygon(bbox, "Custom Study Area")
    area_meta = {
        "id": "custom", "name": "Custom Study Area", "state": "Custom Region",
        "district": "User Selected", "center": center, "zoom": zoom, "bbox": bbox,
        "area_sq_km": 500.0, "ecosystem": "Tropical Deciduous / Mixed Woodland",
        "verified_boundary": False
    }


# ==============================================================================
# Data Services Pipeline
# ==============================================================================
@st.cache_data(ttl=300)
def load_firms_data(key: str, bbox: List[float], source: str, day_range: int):
    client = FirmsClient(map_key=key)
    return client.fetch_hotspots(bbox=bbox, source=source, day_range=day_range)

@st.cache_data(ttl=300)
def load_weather_data(key: str, lat: float, lon: float, name: str):
    client = WeatherClient(api_key=key)
    return client.get_current_weather(lat=lat, lon=lon, location_name=name)

@st.cache_data(ttl=600)
def load_earth_engine_data(project_id: str, bbox: List[float]):
    ee_service = EarthEngineService(project_id=project_id)
    return ee_service.get_status(), ee_service.get_sentinel2_indices(bbox=bbox), ee_service.get_smap_soil_moisture(bbox=bbox)

# Retrieve Data
hotspots_df, firms_meta = load_firms_data(st.session_state.server_firms_key, bbox, st.session_state.firms_source, st.session_state.day_range)
weather_data = load_weather_data(st.session_state.server_owm_key, center[0], center[1], area_meta["name"])
ee_status, s2_data, smap_data = load_earth_engine_data(st.session_state.server_gee_project, bbox)

# Sync Hotspots with Incident Management Workspace
st.session_state.incident_manager.sync_from_firms_dataframe(hotspots_df)

# Evaluate Risk Model
risk_model = FireRiskModel(weights=st.session_state.risk_weights)
risk_summary = risk_model.calculate_score(
    temperature_c=weather_data.get("temperature_c"),
    humidity_pct=weather_data.get("humidity_pct"),
    wind_kmh=weather_data.get("wind_speed_kmh"),
    wind_gust_kmh=weather_data.get("wind_gust_kmh"),
    ndmi=s2_data.get("mean_ndmi"),
    ndvi=s2_data.get("mean_ndvi"),
    soil_moisture_m3=smap_data.get("surface_soil_moisture_m3_m3"),
    rainfall_mm=weather_data.get("rain_1h_mm")
)
risk_cells = risk_model.generate_risk_grid(
    bbox=bbox, grid_size=8, base_weather=weather_data,
    base_ndmi=s2_data.get("mean_ndmi", 0.06), base_ndvi=s2_data.get("mean_ndvi", 0.48),
    base_soil_moisture=smap_data.get("surface_soil_moisture_m3_m3", 0.13)
)
high_risk_cells = [c for c in risk_cells if c["score"] >= 50.0]
risk_summary["high_risk_cells_pct"] = round((len(high_risk_cells) / len(risk_cells)) * 100.0, 1) if risk_cells else 0.0

# Evaluate Prevention Priority System
prevention_beats = FirePreventionService.evaluate_all_beats(weather_data, ndmi=s2_data.get("mean_ndmi"))

# Run Rothermel-Huygens Simulation
simulator = FireSpreadSimulator(
    ignition_lat=st.session_state.ignition_coords[0],
    ignition_lon=st.session_state.ignition_coords[1],
    wind_speed_kmh=st.session_state.sim_wind_speed,
    wind_from_deg=st.session_state.sim_wind_from,
    fuel_type=st.session_state.sim_fuel_type,
    slope_deg=st.session_state.sim_slope_deg,
    max_duration_hours=st.session_state.sim_duration_hours
)
simulation_results = simulator.run_simulation()


# ==============================================================================
# Header & Navigation
# ==============================================================================
render_header(area_meta["name"], firms_meta, weather_data, ee_status)
render_metric_row(hotspots_df, weather_data, risk_summary, s2_data)

# Five Professional Master Sections
nav_section = st.radio(
    "Navigation Sections",
    options=[
        "🛡️ Command Center",
        "🗺️ Live Operations Map",
        "📊 Environmental Intelligence",
        "⚡ Fire Simulation Lab",
        "📋 Incidents & Prevention"
    ],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# SECTION 1: COMMAND CENTER
# ==============================================================================
if nav_section == "🛡️ Command Center":
    st.markdown("### 🛡️ Tactical Command Center Overview")
    
    col_c1, col_c2 = st.columns([7, 3])
    
    with col_c1:
        st.markdown("##### 🚨 High-Priority Thermal Incidents Awaiting Field Verification")
        incidents_df = st.session_state.incident_manager.get_incidents_dataframe()
        if not incidents_df.empty:
            high_priority = incidents_df[incidents_df["priority"] == "High"]
            if not high_priority.empty:
                st.dataframe(
                    high_priority[["incident_id", "observation_time_ist", "frp_mw", "confidence", "review_status", "priority", "beat_notes"]],
                    use_container_width=True,
                    height=200
                )
            else:
                st.info("No high-priority unverified thermal hotspots in the active window.")
        else:
            st.info("Zero active satellite detections in selected area.")

        st.markdown("##### 📍 Recommended Action Priority Areas for Immediate Inspection")
        c_p1, c_p2 = st.columns(2)
        top_beats = prevention_beats[:2]
        with c_p1:
            st.markdown(
                f"""
                <div style="background: #ffffff; padding: 14px; border-radius: 8px; border-left: 4px solid {top_beats[0]['color']}; border: 1px solid #e2e8f0;">
                    <div style="font-weight: 700; font-size: 1rem;">{top_beats[0]['beat_name']} ({top_beats[0]['range']} Range)</div>
                    <div style="color: {top_beats[0]['color']}; font-weight: 600; font-size: 0.85rem; margin-bottom: 6px;">
                        Prevention Score: {top_beats[0]['prevention_score']:.0f} / 100 • {top_beats[0]['tier']}
                    </div>
                    <div style="font-size: 0.82rem; color: #475569;">
                        <b>Top Action:</b> {top_beats[0]['recommendations'][0]['recommendation']}<br>
                        <b>Evidence:</b> {top_beats[0]['recommendations'][0]['evidence']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c_p2:
            st.markdown(
                f"""
                <div style="background: #ffffff; padding: 14px; border-radius: 8px; border-left: 4px solid {top_beats[1]['color']}; border: 1px solid #e2e8f0;">
                    <div style="font-weight: 700; font-size: 1rem;">{top_beats[1]['beat_name']} ({top_beats[1]['range']} Range)</div>
                    <div style="color: {top_beats[1]['color']}; font-weight: 600; font-size: 0.85rem; margin-bottom: 6px;">
                        Prevention Score: {top_beats[1]['prevention_score']:.0f} / 100 • {top_beats[1]['tier']}
                    </div>
                    <div style="font-size: 0.82rem; color: #475569;">
                        <b>Top Action:</b> {top_beats[1]['recommendations'][0]['recommendation']}<br>
                        <b>Evidence:</b> {top_beats[1]['recommendations'][0]['evidence']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with col_c2:
        st.markdown("##### 📡 Environmental Freshness & API Status")
        st.markdown(
            f"""
            <div style="background: #f8fafc; padding: 14px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 0.85rem; line-height: 1.6;">
                <b>NASA FIRMS Status:</b> <span class="classification-tag" style="background:#e0f2fe; color:#0369a1;">{firms_meta.get('status')}</span><br>
                <b>Detection Count:</b> {len(hotspots_df)} active hotspots<br>
                <b>Observation Timestamp:</b> {weather_data.get('observation_time_ist')}<br>
                <b>Weather Source:</b> {weather_data.get('source')}<br>
                <b>Google Earth Engine:</b> {'🟢 Authenticated Live' if ee_status.get('authenticated') else '⚪ Benchmark Mode'}<br>
                <b>Soil Moisture Context:</b> SMAP L4 ({smap_data.get('spatial_resolution')})<br>
                <b>Data Staleness:</b> {'🔴 Stale (>3h)' if weather_data.get('is_stale') else '🟢 Fresh Live'}
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.plotly_chart(plot_wind_vector(weather_data), use_container_width=True)


# ==============================================================================
# SECTION 2: LIVE OPERATIONS MAP
# ==============================================================================
elif nav_section == "🗺️ Live Operations Map":
    st.markdown("### 🗺️ Live Fire & Environmental GIS Operations Map")
    
    col_map_view, col_map_ctrl = st.columns([7, 3])
    
    with col_map_view:
        m = render_interactive_map(
            center=center,
            zoom=zoom,
            boundary_geojson=boundary_geojson,
            hotspots_df=hotspots_df,
            weather_data=weather_data,
            risk_cells=risk_cells,
            prevention_beats=prevention_beats,
            simulation_result=simulation_results,
            tile_url_ndvi=s2_data.get("tile_url_ndvi"),
            tile_url_ndmi=s2_data.get("tile_url_ndmi"),
        )
        st_data = st_folium(m, width="100%", height=650, returned_objects=["last_clicked"])

        if st_data and st_data.get("last_clicked"):
            c_lat = round(st_data["last_clicked"]["lat"], 4)
            c_lon = round(st_data["last_clicked"]["lng"], 4)
            st.info(f"📍 Map clicked at: **{c_lat}° N, {c_lon}° E**.")
            if st.button("Set as Simulation Ignition Scenario"):
                st.session_state.ignition_coords = [c_lat, c_lon]
                st.success(f"Ignition set to [{c_lat}, {c_lon}]! Open 'Fire Simulation Lab' to run.")

    with col_map_ctrl:
        st.markdown("##### 🔍 GIS Layer Inspector")
        st.markdown(
            """
            - 🛰️ **Satellite Imagery (Esri):** Native high-resolution surface view.
            - 🏔️ **Topography (OpenTopoMap):** Elevation contours & terrain aspect.
            - 🌿 **Vegetation Zones:** Teak-bamboo forest, grasslands, and firebreak water bodies.
            - 🔴/🟠 **FIRMS Hotspots:** Scaled by Fire Radiative Power (MW).
            - 🟦 **Weather Vector Arrow:** Points **TOWARD** downwind spread heading.
            - 🟨/🟧/🟥 **Risk Grid:** Heuristic microclimate risk cells (0–100).
            - 🛡️ **Prevention Beats:** High-priority inspection routes.
            - ⭕ **Simulation Perimeters:** Hypothetical fire growth contours.
            """
        )
        st.markdown("---")
        st.markdown("##### 🔬 Data Integrity Standards")
        st.markdown(
            """
            <div style="font-size: 0.78rem; line-height: 1.5; color: #475569;">
                <b>• OBSERVED:</b> Direct satellite or weather station measurements.<br>
                <b>• SATELLITE-DERIVED:</b> Spectral reflectance indices (NDVI/NDMI/NBR).<br>
                <b>• MODEL-DERIVED:</b> Rothermel spread equations & risk scores.<br>
                <b>• SIMULATED:</b> Hypothetical fire perimeters.<br>
                <i>Never confuse simulated contours with confirmed satellite detections!</i>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==============================================================================
# SECTION 3: ENVIRONMENTAL INTELLIGENCE & ANALYTICS
# ==============================================================================
elif nav_section == "📊 Environmental Intelligence":
    st.markdown("### 📊 Environmental Intelligence & Geospatial Analytics")
    
    tab_a1, tab_a2, tab_a3 = st.tabs(["📈 Thermal Hotspot Trends", "🌿 Vegetation & Fuel Analytics", "🌦️ Meteorology & Correlations"])
    
    with tab_a1:
        c_tr1, c_tr2 = st.columns(2)
        with c_tr1:
            st.plotly_chart(plot_detection_timeline(hotspots_df), use_container_width=True)
        with c_tr2:
            st.plotly_chart(plot_frp_distribution(hotspots_df), use_container_width=True)

    with tab_a2:
        c_vg1, c_vg2 = st.columns(2)
        with c_vg1:
            st.plotly_chart(plot_land_cover_distribution(), use_container_width=True)
        with c_vg2:
            st.plotly_chart(plot_risk_factor_breakdown(risk_summary["breakdown"]), use_container_width=True)
            st.markdown(
                f"""
                <div style="background:#f8fafc; padding:10px; border-radius:6px; font-size:0.85rem;">
                    <b>Mean Sentinel-2 NDVI:</b> {s2_data.get('mean_ndvi'):.3f} (Photosynthetic Biomass)<br>
                    <b>Mean Sentinel-2 NDMI:</b> {s2_data.get('mean_ndmi'):.3f} (Canopy Liquid Moisture)<br>
                    <b>Surface Soil Moisture (SMAP 9km):</b> {smap_data.get('surface_soil_moisture_m3_m3')} m³/m³
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_a3:
        c_cr1, c_cr2 = st.columns(2)
        with c_cr1:
            st.plotly_chart(plot_environmental_correlation(hotspots_df, weather_data), use_container_width=True)
        with c_cr2:
            st.markdown("##### 🗓️ Central India Fire Season Climatology")
            st.markdown(
                """
                - **Seasonality:** High fire danger peaks between **late February and early May**.
                - **Driving Factors:** Pre-monsoon heatwaves (>40°C), rapid desiccation of bamboo clumps, and agricultural/harvest residue burning.
                - **Resolution Caution:** Coarse SMAP soil moisture (9 km) represents regional hydrological deficit, not high-resolution dead fuel litter moisture.
                """
            )


# ==============================================================================
# SECTION 4: FIRE SIMULATION LABORATORY
# ==============================================================================
elif nav_section == "⚡ Fire Simulation Lab":
    st.markdown("### ⚡ Rothermel-Huygens Wildfire Spread Simulation Laboratory")
    st.markdown(
        """
        <div style="background: #fff7ed; padding: 10px 14px; border-radius: 6px; border-left: 4px solid #ea580c; margin-bottom: 12px; font-size: 0.88rem;">
            ⚠️ <b>HYPOTHETICAL SIMULATION — NOT AN OPERATIONAL GUARANTEE:</b><br>
            Directional perimeter model combining Rothermel surface spread rate physics with Huygens elliptical propagation.
            Used for emergency scenario evaluation, containment line planning, and exposed asset assessment.
        </div>
        """,
        unsafe_allow_html=True
    )

    col_sim_in, col_sim_out = st.columns([4, 6])

    with col_sim_in:
        st.markdown("##### 🕹️ Scenario Configuration")
        st.write(f"**Ignition Point:** {st.session_state.ignition_coords[0]:.4f}° N, {st.session_state.ignition_coords[1]:.4f}° E")
        
        fuel_choice = st.selectbox(
            "Fuel Model",
            options=list(FireSpreadSimulator.FUEL_MODELS.keys()),
            index=list(FireSpreadSimulator.FUEL_MODELS.keys()).index(st.session_state.sim_fuel_type) if st.session_state.sim_fuel_type in FireSpreadSimulator.FUEL_MODELS else 2
        )
        st.session_state.sim_fuel_type = fuel_choice

        w_spd = st.slider("Wind Speed (km/h)", 0.0, 50.0, float(st.session_state.sim_wind_speed), 1.0)
        st.session_state.sim_wind_speed = w_spd

        w_dir = st.slider("Wind Origin (FROM deg)", 0.0, 360.0, float(st.session_state.sim_wind_from), 15.0)
        st.session_state.sim_wind_from = w_dir

        slope = st.slider("Terrain Slope (degrees)", 0.0, 35.0, float(st.session_state.sim_slope_deg), 1.0)
        st.session_state.sim_slope_deg = slope

        dur = st.slider("Simulation Duration (Hours)", 1.0, 18.0, float(st.session_state.sim_duration_hours), 1.0)
        st.session_state.sim_duration_hours = dur

        st.markdown("##### ⏱️ Time-Step Inspector")
        step_select = st.slider(
            "Inspect Step",
            0, len(simulation_results["steps"]) - 1,
            min(4, len(simulation_results["steps"]) - 1),
            format="T+%d h"
        )
        cur_step = simulation_results["steps"][step_select]

    with col_sim_out:
        st.markdown(f"##### 📊 Simulated Perimeter State at T+{cur_step['elapsed_hours']:.0f} Hours")
        m_s1, m_s2, m_s3 = st.columns(3)
        with m_s1:
            st.metric("Projected Burned Area", f"{cur_step['area_ha']} ha", f"{cur_step['area_km2']} km²")
        with m_s2:
            st.metric("Perimeter Length", f"{cur_step['perimeter_km']} km")
        with m_s3:
            st.metric("Forward Head Speed", f"{cur_step['head_rate_kmh']} km/h", f"{cur_step['head_rate_m_min']} m/min")

        m_s4, m_s5 = st.columns(2)
        with m_s4:
            st.metric("Flame Length", f"{cur_step['flame_length_m']} m")
        with m_s5:
            st.metric("Fireline Intensity", f"{cur_step.get('fireline_intensity_kw_m', 0)} kW/m", cur_step["containment_difficulty"])

        st.plotly_chart(plot_simulation_growth(simulation_results["steps"]), use_container_width=True)

        # Exposed Assets Alert
        if simulation_results.get("exposed_assets_summary"):
            st.error("🚨 **POTENTIALLY EXPOSED ASSETS DETECTED IN SIMULATION PERIMETER:**")
            for ast in simulation_results["exposed_assets_summary"]:
                st.markdown(f"- ⚠️ **{ast['asset_name']}** ({ast['asset_type']}) — Potential contact at $T+{ast['impact_time_hours']:.0f}h$")

    st.markdown("---")
    st.markdown("##### 🔄 Alternative Scenario Comparison")
    with st.expander("Compare with Alternative Meteorological & Fuel Scenarios", expanded=False):
        c_sc1, c_sc2 = st.columns(2)
        with c_sc1:
            alt_wind = st.slider("Alternative Wind Speed (km/h)", 0.0, 50.0, min(45.0, w_spd * 1.5))
        with c_sc2:
            alt_fuel = st.selectbox("Alternative Fuel Class", options=list(FireSpreadSimulator.FUEL_MODELS.keys()), index=0)
            cmp = compare_scenarios(simulator, {"scenario_name": "High Wind / Alternate Fuel", "wind_speed_kmh": alt_wind, "fuel_type": alt_fuel})
            c_data = cmp["comparison"]
            st.metric("Area Impact Difference", f"{c_data['area_difference_ha']} ha", f"{c_data['area_change_pct']}% change")


# ==============================================================================
# SECTION 5: INCIDENTS, PREVENTION & REPORTS
# ==============================================================================
elif nav_section == "📋 Incidents & Prevention":
    st.markdown("### 📋 Incident Management, Prevention Planning & Executive Reports")
    
    tab_p1, tab_p2, tab_p3 = st.tabs(["🚨 Incident Review Workspace", "🛡️ Prevention Action Tracker", "📄 Reports & Data Exports"])
    
    # Tab 1: Incidents Workspace
    with tab_p1:
        st.markdown("##### 🔍 Satellite Detection Lifecycle Management")
        inc_df = st.session_state.incident_manager.get_incidents_dataframe()
        
        if not inc_df.empty:
            c_f1, c_f2 = st.columns([3, 7])
            with c_f1:
                st.markdown("###### Update Verification Status")
                selected_inc = st.selectbox("Select Incident ID", options=inc_df["incident_id"].tolist())
                new_status = st.selectbox("Status", options=IncidentManager.VALID_STATUSES)
                reviewer = st.text_input("Reviewing Officer", value="Forest Beat Officer")
                notes = st.text_area("Field Beat Notes", value="Ground reconnaissance completed.")
                if st.button("Submit Verification Record"):
                    st.session_state.incident_manager.update_incident_status(selected_inc, new_status, reviewer, notes)
                    st.success(f"Updated {selected_inc} to {new_status}!")
                    st.rerun()

            with c_f2:
                st.dataframe(
                    inc_df[["incident_id", "observation_time_ist", "frp_mw", "confidence", "review_status", "verified_by", "beat_notes"]],
                    use_container_width=True,
                    height=280
                )
        else:
            st.info("No incidents currently logged.")

    # Tab 2: Prevention Action Tracker
    with tab_p2:
        st.markdown("##### 🛡️ Beat-Level Prevention Measures & Recommendations")
        for beat in prevention_beats:
            with st.expander(f"{beat['badge']} {beat['beat_name']} — Priority Score: {beat['prevention_score']:.0f}/100", expanded=False):
                st.write(f"**Dominant Fuel:** {beat['fuel_class']}")
                st.write(f"**Historic Frequency:** {beat['historical_fire_frequency']}")
                st.write(f"**Vulnerability Reason:** {beat['vulnerability_reason']}")
                st.markdown("###### Actionable Recommendations:")
                for r in beat["recommendations"]:
                    st.markdown(f"- **[{r['action_type']}]** {r['recommendation']}")
                    st.caption(f"Evidence: {r['evidence']} | Protocol: {r['protocol_note']}")

        st.markdown("---")
        st.markdown("##### 📝 Active Prevention Action Tracker")
        st.dataframe(pd.DataFrame(st.session_state.action_tracker), use_container_width=True)

    # Tab 3: Reports & Exports
    with tab_p3:
        st.markdown("##### 📄 Executive Situation Briefing & Incident Exports")
        
        rep_md = generate_situation_report_markdown(
            area_meta=area_meta,
            weather_data=weather_data,
            hotspots_df=hotspots_df,
            risk_summary=risk_summary,
            satellite_data=s2_data,
            simulation_data=simulation_results
        )

        c_exp1, c_exp2, c_exp3, c_exp4 = st.columns(4)
        with c_exp1:
            st.download_button(
                "📥 Briefing (.md)",
                data=rep_md,
                file_name=f"AgniWatch_Briefing_{area_meta['id']}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with c_exp2:
            st.download_button(
                "📥 Hotspots (.csv)",
                data=generate_detections_csv(hotspots_df),
                file_name=f"AgniWatch_Hotspots_{area_meta['id']}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c_exp3:
            st.download_button(
                "📥 Risk Grid (.csv)",
                data=generate_risk_grid_csv(risk_cells),
                file_name=f"AgniWatch_RiskGrid_{area_meta['id']}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c_exp4:
            st.download_button(
                "📥 Incidents (.csv)",
                data=st.session_state.incident_manager.export_incidents_csv(),
                file_name=f"AgniWatch_Incidents_{area_meta['id']}.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("##### Briefing Document Preview")
        st.markdown(rep_md)
