"""
AgniWatch India - Export & Situation Report Service
Generates incident monitoring reports, CSV data downloads, and printable markdown summaries.
"""

import io
import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


def generate_detections_csv(df_hotspots: pd.DataFrame) -> str:
    """Exports active hotspot detections to CSV string."""
    if df_hotspots.empty:
        return "latitude,longitude,acq_datetime_ist,satellite,instrument,brightness_k,frp_mw,confidence,detection_status\n"

    # Select standard clean columns for export
    cols_map = {
        "latitude": "Latitude",
        "longitude": "Longitude",
        "acq_datetime_ist": "Observation_Time_IST",
        "satellite": "Satellite_Sensor",
        "instrument": "Instrument",
        "brightness": "Brightness_Kelvin",
        "frp": "Fire_Radiative_Power_MW",
        "confidence_label": "Confidence_Level",
        "daynight": "Day_Night",
        "detection_status": "Verification_Status"
    }

    export_df = pd.DataFrame()
    for col, new_name in cols_map.items():
        if col in df_hotspots.columns:
            export_df[new_name] = df_hotspots[col]

    return export_df.to_csv(index=False)


def generate_risk_grid_csv(cells: List[Dict[str, Any]]) -> str:
    """Exports fire risk grid analysis to CSV string."""
    if not cells:
        return "cell_id,latitude_center,longitude_center,score,category,temp_c,humidity_pct,ndmi,soil_moisture\n"

    rows = []
    for c in cells:
        rows.append({
            "Cell_ID": c["cell_id"],
            "Latitude_Center": round(c["center"][0], 5),
            "Longitude_Center": round(c["center"][1], 5),
            "Risk_Score_0_100": c["score"],
            "Risk_Tier": c["category"],
            "Temperature_C": c.get("temp_c"),
            "Relative_Humidity_Pct": c.get("humidity_pct"),
            "NDMI_Canopy_Moisture": c.get("ndmi"),
            "Soil_Moisture_m3_m3": c.get("soil_moisture"),
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def generate_situation_report_markdown(
    area_meta: Dict[str, Any],
    weather_data: Dict[str, Any],
    hotspots_df: pd.DataFrame,
    risk_summary: Dict[str, Any],
    satellite_data: Dict[str, Any],
    simulation_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Builds an executive markdown wildfire situation report for command briefings.
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
    report_ts = now_ist.strftime("%d-%b-%Y %H:%M:%S IST")

    area_name = area_meta.get("name", "Study Area")
    state = area_meta.get("state", "India")
    district = area_meta.get("district", "N/A")
    ecosystem = area_meta.get("ecosystem", "Deciduous Forest")

    hotspot_count = len(hotspots_df)
    max_frp = hotspots_df["frp"].max() if not hotspots_df.empty and "frp" in hotspots_df.columns else 0.0

    temp = weather_data.get("temperature_c", "N/A")
    rh = weather_data.get("humidity_pct", "N/A")
    wind_kmh = weather_data.get("wind_speed_kmh", "N/A")
    wind_card = weather_data.get("wind_cardinal", "N/A")
    wind_from = weather_data.get("wind_deg_from", "N/A")
    wind_toward = weather_data.get("wind_deg_toward", "N/A")

    risk_score = risk_summary.get("score", "N/A")
    risk_cat = risk_summary.get("category", "N/A")
    high_cells_pct = risk_summary.get("high_risk_cells_pct", "N/A")

    s2_ndvi = satellite_data.get("mean_ndvi", "N/A")
    s2_ndmi = satellite_data.get("mean_ndmi", "N/A")

    sim_text = "No active spread simulation computed."
    if simulation_data and simulation_data.get("final_step"):
        f = simulation_data["final_step"]
        p = simulation_data["parameters"]
        sim_text = (
            f"- **Hypothetical Spread Duration:** {p.get('max_duration_hours')} hours\n"
            f"- **Projected Burn Area:** {f.get('area_ha')} hectares ({f.get('area_km2')} km²)\n"
            f"- **Projected Perimeter:** {f.get('perimeter_km')} km\n"
            f"- **Forward Rate of Spread:** {f.get('head_rate_kmh')} km/h ({f.get('head_rate_m_min')} m/min)\n"
            f"- **Estimated Flame Length:** {f.get('flame_length_m')} m\n"
            f"- **Containment Difficulty:** {f.get('containment_difficulty')}"
        )

    md = f"""# 🇮🇳 AgniWatch India — Wildfire Situation Briefing
**Target Area:** {area_name} ({district}, {state})  
**Report Generated:** {report_ts}  
**Classification:** OPERATIONAL AWARENESS & MONITORING (PRELIMINARY)

---

## 1. Executive Summary
- **Current Fire Risk Index:** **{risk_score} / 100 ({risk_cat})**
- **Satellite Detections Pending Ground Verification:** **{hotspot_count}**
- **Peak Fire Radiative Power (FRP):** **{max_frp} MW**
- **High / Extreme Risk Grid Coverage:** **{high_cells_pct}%** of reserve extent

---

## 2. Surface Meteorology & Fire Weather
- **Temperature:** {temp} °C
- **Relative Humidity:** {rh} %
- **Surface Wind:** {wind_kmh} km/h from **{wind_card} ({wind_from}°)**, blowing toward **{wind_toward}°**
- **Weather Source:** {weather_data.get('source', 'OpenWeatherMap')}
- **Observation Timestamp:** {weather_data.get('observation_time_ist', 'Recent')}

> *Note: Wind direction indicates origin; propagation vector travels 180° opposite downwind.*

---

## 3. Satellite Remote Sensing & Canopy Hydration
- **Vegetation Greenness (Sentinel-2 NDVI):** {s2_ndvi}
- **Canopy Moisture Index (Sentinel-2 NDMI):** {s2_ndmi} *(Lower values indicate desiccated forest litter)*
- **Ecosystem Classification:** {ecosystem}
- **Satellite Status:** {satellite_data.get('collection', 'Sentinel-2 Harmonized')}

---

## 4. Hypothetical Spread Projection
{sim_text}

---

## 5. Methodological Disclaimers
1. **Thermal Hotspots:** Satellite detections indicate radiometric thermal anomalies, not confirmed wildfires. Detections require field beat verification by forest guards.
2. **Fire Risk Model:** Transparent heuristic scoring model based on weighted meteorological and spectral factors. Not an empirically calibrated probability.
3. **Spread Simulator:** Simplified Huygens elliptical directional propagation model designed for scenario planning and resource deployment exercises.

---
*AgniWatch India Wildfire Intelligence Platform — Developed for Forest Protection & Disaster Management.*
"""
    return md
