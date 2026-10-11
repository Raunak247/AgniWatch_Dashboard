"""
AgniWatch India - Top Metric Cards and Status Banners
Renders high-visibility KPI cards, data freshness indicators, and API status badges.
"""

from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd


def render_header(
    area_name: str,
    firms_status: Dict[str, Any],
    weather_status: Dict[str, Any],
    ee_status: Dict[str, Any],
):
    """Renders the top command-center banner and live connection badges."""
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
                <span style="font-size: 2.2rem;">🔥</span>
                <div>
                    <h1 style="margin: 0; padding: 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.5px;">
                        AgniWatch India
                    </h1>
                    <div style="color: #64748b; font-size: 0.92rem; font-weight: 500;">
                        Wildfire Intelligence & Spread Simulation System • <b>{area_name}</b>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        # API Status Pills
        f_badge = "🟢 FIRMS Live" if not firms_status.get("is_demo") else "🟡 FIRMS Demo"
        w_badge = "🟢 Weather Live" if not weather_status.get("is_demo") else "🟡 Weather Demo"
        ee_badge = "🟢 GEE Online" if ee_status.get("authenticated") else "⚪ GEE Offline"

        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
                <span style="background: {'#dcfce7' if not firms_status.get('is_demo') else '#fef9c3'}; 
                             color: {'#166534' if not firms_status.get('is_demo') else '#854d0e'}; 
                             padding: 4px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; border: 1px solid {'#bbf7d0' if not firms_status.get('is_demo') else '#fef08a'};">
                    {f_badge}
                </span>
                <span style="background: {'#dcfce7' if not weather_status.get('is_demo') else '#fef9c3'}; 
                             color: {'#166534' if not weather_status.get('is_demo') else '#854d0e'}; 
                             padding: 4px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; border: 1px solid {'#bbf7d0' if not weather_status.get('is_demo') else '#fef08a'};">
                    {w_badge}
                </span>
                <span style="background: {'#dcfce7' if ee_status.get('authenticated') else '#f1f5f9'}; 
                             color: {'#166534' if ee_status.get('authenticated') else '#475569'}; 
                             padding: 4px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; border: 1px solid {'#bbf7d0' if ee_status.get('authenticated') else '#e2e8f0'};">
                    {ee_badge}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_metric_row(
    hotspots_df: pd.DataFrame,
    weather_data: Dict[str, Any],
    risk_summary: Dict[str, Any],
    satellite_data: Dict[str, Any],
):
    """Renders the 5 primary tactical KPI metric cards."""
    col1, col2, col3, col4, col5 = st.columns(5)

    num_detections = len(hotspots_df)
    max_frp = round(hotspots_df["frp"].max(), 1) if not hotspots_df.empty and "frp" in hotspots_df.columns else 0.0

    temp = weather_data.get("temperature_c")
    temp_str = f"{temp:.1f} °C" if temp is not None else "N/A"

    rh = weather_data.get("humidity_pct")
    rh_str = f"{rh:.0f}%" if rh is not None else "N/A"

    wind_speed = weather_data.get("wind_speed_kmh")
    wind_card = weather_data.get("wind_cardinal", "")
    wind_str = f"{wind_speed:.1f} km/h {wind_card}" if wind_speed is not None else "N/A"

    risk_score = risk_summary.get("score", 0.0)
    risk_cat = risk_summary.get("category", "Low")
    risk_color = risk_summary.get("color", "#2ecc71")

    mean_ndmi = satellite_data.get("mean_ndmi")
    ndmi_str = f"{mean_ndmi:.3f}" if mean_ndmi is not None else "N/A"

    with col1:
        st.markdown(
            f"""
            <div style="background: #ffffff; padding: 14px 16px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.78rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Satellite Hotspots</div>
                <div style="font-size: 1.7rem; font-weight: 800; color: {'#dc2626' if num_detections > 5 else '#0f172a'}; margin-top: 2px;">
                    {num_detections}
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8;">Pending ground verification</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: #ffffff; padding: 14px 16px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.78rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Peak Radiative Power</div>
                <div style="font-size: 1.7rem; font-weight: 800; color: #ea580c; margin-top: 2px;">
                    {max_frp} <span style="font-size: 0.95rem; font-weight: 600;">MW</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8;">Fire Radiative Power (VIIRS/MODIS)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background: #ffffff; padding: 14px 16px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.78rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Fire Weather</div>
                <div style="font-size: 1.45rem; font-weight: 800; color: #0f172a; margin-top: 2px;">
                    {temp_str} <span style="font-size: 0.95rem; font-weight: 600; color: #64748b;">| {rh_str}</span>
                </div>
                <div style="font-size: 0.75rem; color: #475569; font-weight: 500;">Wind: {wind_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="background: #ffffff; padding: 14px 16px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.78rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Fire Risk Index</div>
                <div style="font-size: 1.7rem; font-weight: 800; color: {risk_color}; margin-top: 2px;">
                    {risk_score:.0f}<span style="font-size: 0.9rem; font-weight: 500; color: #94a3b8;"> / 100</span>
                </div>
                <div style="font-size: 0.75rem; font-weight: 600; color: {risk_color};">{risk_cat}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div style="background: #ffffff; padding: 14px 16px; border-radius: 10px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.78rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Canopy Moisture (NDMI)</div>
                <div style="font-size: 1.7rem; font-weight: 800; color: #0284c7; margin-top: 2px;">
                    {ndmi_str}
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8;">Sentinel-2 Spectral Index</div>
            </div>
            """,
            unsafe_allow_html=True
        )
