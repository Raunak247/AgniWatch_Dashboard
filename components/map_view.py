"""
AgniWatch India - Professional GIS Operations Map Component
Builds a high-performance, multi-layered Folium operations map with independent controls for:
- Basemaps: Satellite (Esri), Topo (OpenTopoMap), Streets (OSM)
- Thermal Hotspots: VIIRS/MODIS detections with FRP and confidence
- Land Cover & Vegetation: Forest classes, grasslands, water bodies, Sentinel-2 NDVI/NDMI
- Environmental: Weather stations, wind propagation vectors, SMAP soil moisture
- Intelligence: Fire-risk grid, prevention priority beats, simulation perimeters
"""

import math
from typing import Dict, Any, List, Optional
import folium
from folium import plugins
import pandas as pd


# Synthetic verified land-cover / vegetation zones for Tadoba Demonstration
TADOBA_VEGETATION_ZONES = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Central Dense Teak-Bamboo Forest",
                "class": "Dense Forest (Canopy > 60%)",
                "dominant": "Tectona grandis & Dendrocalamus strictus",
                "fuel_type": "Dry Teak & Bamboo Forest",
                "combustibility": "High during dry leaf-fall (March-May)"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [79.25, 20.18], [79.24, 20.32], [79.40, 20.35],
                    [79.44, 20.22], [79.35, 20.15], [79.25, 20.18]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Western Grasslands & Savannah Woodland",
                "class": "Open Grassland & Savannah",
                "dominant": "Heteropogon contortus, Themeda quadrivalvis",
                "fuel_type": "Grasslands & Savannah Woodland",
                "combustibility": "Very High fine fuel ignition rate"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [79.16, 20.25], [79.18, 20.38], [79.24, 20.32],
                    [79.22, 20.20], [79.16, 20.25]
                ]]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Tadoba Lake & Wetland Waterbody",
                "class": "Water Body / Non-Burnable",
                "dominant": "Open fresh water reservoir",
                "fuel_type": "Non-Burnable Surface (Natural Firebreak)",
                "combustibility": "Zero (Firebreak barrier)"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [79.30, 20.23], [79.29, 20.26], [79.33, 20.26],
                    [79.34, 20.24], [79.30, 20.23]
                ]]
            }
        }
    ]
}


def render_interactive_map(
    center: List[float],
    zoom: int,
    boundary_geojson: Optional[Dict[str, Any]] = None,
    hotspots_df: Optional[pd.DataFrame] = None,
    weather_data: Optional[Dict[str, Any]] = None,
    risk_cells: Optional[List[Dict[str, Any]]] = None,
    prevention_beats: Optional[List[Dict[str, Any]]] = None,
    simulation_result: Optional[Dict[str, Any]] = None,
    selected_sim_step: Optional[int] = None,
    tile_url_ndvi: Optional[str] = None,
    tile_url_ndmi: Optional[str] = None,
) -> folium.Map:
    """Constructs the master operations Folium GIS map."""
    lat, lon = center

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
    )

    # 1. BASEMAPS
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery, Maxar, Earthstar Geographics",
        name="🛰️ Satellite Imagery (Esri High-Res)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="Map data: © OpenStreetMap contributors, SRTM | Map style: © OpenTopoMap (CC-BY-SA)",
        name="🏔️ Topography & Terrain (OpenTopoMap)",
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="🗺️ Base Streets & Boundaries (OSM)",
        overlay=False,
        control=True
    ).add_to(m)

    # 2. VEGETATION & LAND COVER LAYERS
    fg_veg = folium.FeatureGroup(name="🌿 Vegetation & Land Cover Classes", show=True)
    def style_veg(feature):
        f_class = feature["properties"].get("class", "")
        if "Dense Forest" in f_class:
            return {"fillColor": "#15803d", "color": "#166534", "weight": 1.5, "fillOpacity": 0.25}
        elif "Grassland" in f_class:
            return {"fillColor": "#eab308", "color": "#ca8a04", "weight": 1.5, "fillOpacity": 0.25}
        elif "Water" in f_class:
            return {"fillColor": "#0284c7", "color": "#0369a1", "weight": 2.0, "fillOpacity": 0.50}
        return {"fillColor": "#64748b", "color": "#475569", "weight": 1.0, "fillOpacity": 0.20}

    folium.GeoJson(
        TADOBA_VEGETATION_ZONES,
        name="Vegetation Zones",
        style_function=style_veg,
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "class", "dominant", "fuel_type", "combustibility"],
            aliases=["Ecosystem:", "Class:", "Species:", "Fuel Model:", "Fire Risk:"],
            localize=True
        )
    ).add_to(fg_veg)
    fg_veg.add_to(m)

    # 3. RESERVE BOUNDARY
    if boundary_geojson:
        fg_boundary = folium.FeatureGroup(name="🛡️ Protected Reserve Boundary", show=True)
        folium.GeoJson(
            boundary_geojson,
            name="Reserve Extents",
            style_function=lambda feature: {
                "fillColor": "#16a34a",
                "color": "#22c55e",
                "weight": 2.5,
                "fillOpacity": 0.05,
                "dashArray": "6, 4"
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["name", "category", "state"],
                aliases=["Area:", "Status:", "State:"],
                localize=True
            )
        ).add_to(fg_boundary)
        fg_boundary.add_to(m)

    # 4. SATELLITE INDICES OVERLAYS (GEE tiles if available)
    if tile_url_ndvi:
        folium.TileLayer(
            tiles=tile_url_ndvi,
            attr="Google Earth Engine Sentinel-2 NDVI",
            name="🌱 Sentinel-2 NDVI (Vegetation Greenness)",
            overlay=True,
            opacity=0.65,
            show=False
        ).add_to(m)

    if tile_url_ndmi:
        folium.TileLayer(
            tiles=tile_url_ndmi,
            attr="Google Earth Engine Sentinel-2 NDMI",
            name="💧 Sentinel-2 NDMI (Canopy Moisture)",
            overlay=True,
            opacity=0.65,
            show=False
        ).add_to(m)

    # 5. FIRE RISK GRID OVERLAY
    if risk_cells:
        fg_risk = folium.FeatureGroup(name="🔥 Composite Fire Risk Grid (0-100)", show=True)
        for cell in risk_cells:
            bounds = cell["bounds"]
            score = cell["score"]
            cat = cell["category"]
            color = cell["color"]
            cid = cell["cell_id"]
            
            tooltip_html = f"""
            <b>[MODEL-DERIVED] Risk Grid Cell {cid}</b><br>
            <b>Fire Risk Score:</b> {score:.0f} / 100 ({cat})<br>
            <b>Micro-Air Temp:</b> {cell.get('temp_c')} °C<br>
            <b>Relative Humidity:</b> {cell.get('humidity_pct')}%<br>
            <b>Canopy Dryness (NDMI):</b> {cell.get('ndmi')}
            """

            folium.Rectangle(
                bounds=bounds,
                color=color,
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.28,
                tooltip=tooltip_html
            ).add_to(fg_risk)
        fg_risk.add_to(m)

    # 6. PREVENTION PRIORITY BEATS
    if prevention_beats:
        fg_prev = folium.FeatureGroup(name="📍 Prevention Priority Beats & Patrols", show=True)
        for beat in prevention_beats:
            b_lat, b_lon = beat["center"]
            b_score = beat["prevention_score"]
            b_color = beat["color"]
            b_name = beat["beat_name"]
            b_tier = beat["tier"]

            p_popup = f"""
            <div style="font-family: sans-serif; font-size: 12px; width: 240px;">
                <h4 style="margin: 0 0 6px 0; color: {b_color};">🚨 {b_name}</h4>
                <b>Prevention Priority Score:</b> <b>{b_score:.0f} / 100</b><br>
                <b>Priority Tier:</b> {b_tier}<br>
                <b>Fuel Type:</b> {beat.get('fuel_class')}<br>
                <b>Vulnerability:</b> {beat.get('vulnerability_reason')}<br>
                <b>Proximity to Village:</b> {beat.get('proximity_to_settlements_km')} km<br>
                <hr style="margin: 6px 0;">
                <b>Top Preventive Action:</b> {beat['recommendations'][0]['recommendation'] if beat.get('recommendations') else 'Patrol inspection'}
            </div>
            """

            folium.Marker(
                location=[b_lat, b_lon],
                icon=folium.Icon(color="darkpurple" if b_score >= 70 else "orange", icon="shield", prefix="fa"),
                popup=folium.Popup(p_popup, max_width=270),
                tooltip=f"Prevention Beat: {b_name} ({b_score:.0f} pts - {b_tier})"
            ).add_to(fg_prev)
        fg_prev.add_to(m)

    # 7. SENSITIVE ASSETS / INFRASTRUCTURE
    fg_assets = folium.FeatureGroup(name="🏛️ Sensitive Landmarks & Habitats", show=True)
    assets_list = [
        {"name": "Moharli Village & Tourism Gate", "coords": [20.175, 79.330], "type": "Habitation Fringe"},
        {"name": "Tadoba Lake Core Ecological Zone", "coords": [20.242, 79.315], "type": "Breeding Habitat"},
        {"name": "Kolsa Forest Rest House & Staff Beat", "coords": [20.130, 79.442], "type": "Forest Station"},
        {"name": "Chimur Range Peripheral Village", "coords": [20.362, 79.235], "type": "Fringe Village"},
    ]
    for ast in assets_list:
        folium.CircleMarker(
            location=ast["coords"],
            radius=6,
            color="#2563eb",
            fill=True,
            fill_color="#3b82f6",
            fill_opacity=0.9,
            tooltip=f"Sensitive Asset: {ast['name']} ({ast['type']})"
        ).add_to(fg_assets)
    fg_assets.add_to(m)

    # 8. NASA FIRMS THERMAL HOTSPOTS
    if hotspots_df is not None and not hotspots_df.empty:
        fg_hotspots = folium.FeatureGroup(name="🛰️ NASA FIRMS Thermal Hotspots", show=True)
        conf_colors = {"High": "#dc2626", "Nominal": "#ea580c", "Low": "#eab308", "Unknown": "#94a3b8"}

        for _, row in hotspots_df.iterrows():
            h_lat = float(row["latitude"])
            h_lon = float(row["longitude"])
            frp = float(row.get("frp", 10.0) or 10.0)
            conf = str(row.get("confidence_label", "Nominal"))
            marker_color = conf_colors.get(conf, "#ea580c")
            marker_radius = max(5, min(15, int(math.sqrt(frp) * 2.2)))

            dt_ist_str = str(row.get("acq_datetime_ist", "Recent"))
            if dt_ist_str.endswith("+00:00"):
                dt_ist_str = dt_ist_str[:-6]

            popup_html = f"""
            <div style="font-family: sans-serif; font-size: 12px; width: 240px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color: {marker_color}; font-weight: 700; font-size: 13px;">🛰️ Thermal Anomaly</span>
                    <span style="font-size:10px; background:#f1f5f9; padding:2px 6px; border-radius:4px;">OBSERVED</span>
                </div>
                <hr style="margin: 4px 0 6px 0;">
                <b>Verification Status:</b> <span style="color:#d97706; font-weight:600;">Pending Field Recon</span><br>
                <b>Observation Time (IST):</b> {dt_ist_str}<br>
                <b>Satellite Sensor:</b> {row.get('satellite', 'VIIRS')} ({row.get('instrument', 'VIIRS')})<br>
                <b>Brightness Temp:</b> {row.get('brightness', 'N/A')} K<br>
                <b>Fire Radiative Power:</b> <b style="color:#ea580c;">{frp:.1f} MW</b><br>
                <b>Detection Confidence:</b> <b>{conf}</b><br>
                <b>Coordinates:</b> {h_lat:.4f}° N, {h_lon:.4f}° E<br>
                <div style="margin-top: 6px; font-size: 10px; color: #64748b;">
                    NASA FIRMS Near-Real-Time Feed
                </div>
            </div>
            """

            folium.CircleMarker(
                location=[h_lat, h_lon],
                radius=marker_radius,
                color="#ffffff",
                weight=1.8,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.88,
                popup=folium.Popup(popup_html, max_width=270),
                tooltip=f"Thermal Anomaly: {frp:.1f} MW ({conf} Confidence)"
            ).add_to(fg_hotspots)

        fg_hotspots.add_to(m)

    # 9. SURFACE WEATHER & PROPAGATION ARROW
    if weather_data:
        fg_weather = folium.FeatureGroup(name="🌤️ Weather Station & Spread Heading Vector", show=True)
        w_lat = weather_data.get("latitude", lat)
        w_lon = weather_data.get("longitude", lon)
        temp = weather_data.get("temperature_c", "N/A")
        rh = weather_data.get("humidity_pct", "N/A")
        wind_speed = float(weather_data.get("wind_speed_kmh", 0.0) or 0.0)
        wind_card = weather_data.get("wind_cardinal", "")
        wind_from = float(weather_data.get("wind_deg_from", 0.0) or 0.0)
        wind_toward = float(weather_data.get("wind_deg_toward", 180.0) or 180.0)

        station_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 230px;">
            <h4 style="margin: 0 0 6px 0; color: #0284c7;">🌤️ Surface Weather Observation</h4>
            <b>Station:</b> {weather_data.get('location_name', 'Reserve Core')}<br>
            <b>Observation:</b> {weather_data.get('observation_time_ist', 'Recent')}<br>
            <b>Air Temperature:</b> {temp} °C<br>
            <b>Relative Humidity:</b> {rh}%<br>
            <b>Wind Speed:</b> {wind_speed:.1f} km/h (Gusts: {weather_data.get('wind_gust_kmh', 'N/A')} km/h)<br>
            <b>Origin (FROM):</b> {wind_card} ({wind_from:.0f}°)<br>
            <b>Spread Heading (TOWARD):</b> <b style="color:#dc2626;">{wind_toward:.0f}°</b><br>
            <b>Precipitation (1h):</b> {weather_data.get('rain_1h_mm') or '0.0 mm'}
        </div>
        """

        folium.Marker(
            location=[w_lat, w_lon],
            icon=folium.Icon(color="blue", icon="cloud", prefix="fa"),
            popup=folium.Popup(station_html, max_width=260),
            tooltip=f"Surface Weather: {temp}°C, Wind {wind_speed:.1f} km/h from {wind_card}"
        ).add_to(fg_weather)

        # Draw Downwind Propagation Arrow
        vector_len_deg = max(0.02, min(0.065, (wind_speed / 40.0) * 0.055))
        rad_toward = math.radians(wind_toward)
        arrow_lat = w_lat + vector_len_deg * math.cos(rad_toward)
        arrow_lon = w_lon + (vector_len_deg * math.sin(rad_toward)) / math.cos(math.radians(w_lat))

        folium.PolyLine(
            locations=[[w_lat, w_lon], [arrow_lat, arrow_lon]],
            color="#0284c7",
            weight=4.0,
            opacity=0.9,
            tooltip=f"Downwind Fire Spread Heading Vector ({wind_toward:.0f}°)"
        ).add_to(fg_weather)

        folium.CircleMarker(
            location=[arrow_lat, arrow_lon],
            radius=5,
            color="#0284c7",
            fill=True,
            fill_color="#0284c7",
            fill_opacity=1.0,
            tooltip=f"Spread Tip ({wind_toward:.0f}°)"
        ).add_to(fg_weather)

        fg_weather.add_to(m)

    # 10. FIRE SPREAD SIMULATION PERIMETERS
    if simulation_result and "steps" in simulation_result:
        fg_sim = folium.FeatureGroup(name="🔥 Hypothetical Fire Spread Perimeters", show=True)
        ign = simulation_result["ignition"]
        ign_lat = ign["latitude"]
        ign_lon = ign["longitude"]

        folium.Marker(
            location=[ign_lat, ign_lon],
            icon=folium.Icon(color="red", icon="fire", prefix="fa"),
            tooltip="Hypothetical Ignition Point"
        ).add_to(fg_sim)

        steps = simulation_result["steps"]
        step_colors = ["#fef08a", "#fde047", "#facc15", "#fbbf24", "#f59e0b", "#f97316", "#ea580c", "#dc2626", "#b91c1c"]

        for idx, step in enumerate(steps):
            if step["elapsed_hours"] == 0:
                continue

            is_active_step = (selected_sim_step is None) or (step["step_index"] == selected_sim_step)
            poly_coords = step["polygon"]
            
            c_idx = min(len(step_colors) - 1, idx)
            line_color = step_colors[c_idx]
            fill_op = 0.25 if is_active_step else 0.08
            line_wt = 3.5 if is_active_step else 1.5

            sim_tooltip = f"""
            <b>[SIMULATED] HYPOTHETICAL FIRE PERIMETER</b><br>
            <b>Elapsed Time:</b> T+{step['elapsed_hours']} Hours<br>
            <b>Burned Area:</b> {step['area_ha']} ha ({step['area_km2']} km²)<br>
            <b>Perimeter:</b> {step['perimeter_km']} km<br>
            <b>Forward Head Speed:</b> {step['head_rate_kmh']} km/h ({step['head_rate_m_min']} m/min)<br>
            <b>Flame Length:</b> {step['flame_length_m']} m<br>
            <b>Containment Rating:</b> {step['containment_difficulty']}
            """

            folium.Polygon(
                locations=poly_coords,
                color=line_color,
                weight=line_wt,
                fill=True,
                fill_color=line_color,
                fill_opacity=fill_op,
                tooltip=sim_tooltip
            ).add_to(fg_sim)

        fg_sim.add_to(m)

    # Master Layer Control
    folium.LayerControl(position="topright", collapsed=True).add_to(m)

    # MiniMap for Orientation
    plugins.MiniMap(toggle_display=True, position="bottomright").add_to(m)

    return m
