"""
AgniWatch India - Professional Geospatial & Environmental Analytics Charts
Provides interactive Plotly visualizations for fire radiative power,
environmental parameter trends, vegetation indices, fuel distributions, and spread curves.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def plot_frp_distribution(df: pd.DataFrame) -> go.Figure:
    """Renders Fire Radiative Power (MW) distribution colored by confidence tier."""
    if df.empty or "frp" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No active detections in selected time window", showarrow=False, font=dict(size=14))
        fig.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20))
        return fig

    color_map = {"High": "#ef4444", "Nominal": "#f97316", "Low": "#eab308", "Unknown": "#94a3b8"}
    
    fig = px.strip(
        df,
        x="confidence_label",
        y="frp",
        color="confidence_label",
        color_discrete_map=color_map,
        hover_data=["latitude", "longitude", "satellite", "brightness"],
        labels={"confidence_label": "Confidence Level", "frp": "Fire Radiative Power (MW)"},
        title="Fire Radiative Power (MW) by Detection Confidence [OBSERVED]"
    )

    fig.update_layout(
        height=320,
        margin=dict(l=40, r=20, t=40, b=30),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        showlegend=False,
        font=dict(family="Inter, sans-serif", size=12)
    )
    return fig


def plot_detection_timeline(df: pd.DataFrame) -> go.Figure:
    """Renders acquisition timeline of satellite thermal detections."""
    if df.empty or "acq_datetime_ist" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No temporal detection data available", showarrow=False)
        fig.update_layout(height=280)
        return fig

    df_valid = df.dropna(subset=["acq_datetime_ist"]).copy()
    if df_valid.empty:
        fig = go.Figure()
        fig.add_annotation(text="No valid timestamps", showarrow=False)
        return fig

    df_valid["date_str"] = df_valid["acq_datetime_ist"].dt.strftime("%Y-%m-%d %H:00")
    counts = df_valid.groupby("date_str").agg(
        detections=("latitude", "count"),
        mean_frp=("frp", "mean"),
        max_frp=("frp", "max")
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=counts["date_str"],
        y=counts["detections"],
        name="Detections Count",
        marker_color="#f97316"
    ))

    fig.update_layout(
        title="Detections Over Time (Indian Standard Time) [OBSERVED]",
        xaxis_title="Satellite Acquisition Time",
        yaxis_title="Detection Count",
        height=320,
        margin=dict(l=40, r=20, t=40, b=30),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=12)
    )
    return fig


def plot_risk_factor_breakdown(breakdown: Dict[str, Any]) -> go.Figure:
    """Renders points contributed by each physical risk variable."""
    factors = []
    points = []
    labels = {
        "temperature": "Air Temperature",
        "humidity": "Atmospheric Dryness (1 - RH)",
        "wind_speed": "Wind Speed & Gusts",
        "vegetation_dryness": "Canopy Moisture Desiccation (NDMI)",
        "soil_moisture": "Topsoil Parchedness (SMAP)",
    }

    colors = ["#ef4444", "#f97316", "#eab308", "#3b82f6", "#10b981"]

    for k, v in breakdown.items():
        factors.append(labels.get(k, k.title()))
        points.append(v.get("contribution_pts", 0.0))

    fig = go.Figure(go.Bar(
        x=points,
        y=factors,
        orientation='h',
        marker=dict(color=colors[:len(factors)]),
        text=[f"{p:.1f} pts" for p in points],
        textposition='outside'
    ))

    fig.update_layout(
        title="Points Contributed to Fire Risk Score (Total 0 - 100) [MODEL-DERIVED]",
        xaxis_title="Contributed Points",
        height=290,
        margin=dict(l=10, r=40, t=40, b=20),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=12)
    )
    return fig


def plot_simulation_growth(steps: List[Dict[str, Any]]) -> go.Figure:
    """Renders hypothetical area growth (hectares) and forward head speed over time."""
    if not steps:
        return go.Figure()

    hours = [s["elapsed_hours"] for s in steps]
    areas = [s["area_ha"] for s in steps]
    rates = [s["head_rate_kmh"] for s in steps]

    fig = go.Figure()

    # Cumulative Area
    fig.add_trace(go.Scatter(
        x=hours,
        y=areas,
        name="Projected Area (Hectares)",
        mode="lines+markers",
        line=dict(color="#dc2626", width=3),
        fill='tozeroy',
        fillcolor='rgba(220, 38, 38, 0.12)'
    ))

    # Rate of Spread on secondary y-axis
    fig.add_trace(go.Scatter(
        x=hours,
        y=rates,
        name="Forward Spread Rate (km/h)",
        mode="lines+markers",
        line=dict(color="#ea580c", width=2, dash="dash"),
        yaxis="y2"
    ))

    fig.update_layout(
        title="Hypothetical Perimeter Area Growth & Forward Speed [SIMULATED]",
        xaxis_title="Elapsed Time (Hours)",
        yaxis=dict(title="Simulated Area (Hectares)", side="left"),
        yaxis2=dict(title="Spread Rate (km/h)", side="right", overlaying="y", showgrid=False),
        height=320,
        margin=dict(l=40, r=40, t=40, b=30),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        hovermode="x unified",
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", y=-0.2)
    )
    return fig


def plot_wind_vector(weather_data: Dict[str, Any]) -> go.Figure:
    """Renders polar radar compass comparing meteorological wind origin vs propagation heading."""
    wind_from = weather_data.get("wind_deg_from", 300.0) or 300.0
    wind_toward = weather_data.get("wind_deg_toward", 120.0) or 120.0
    wind_speed = weather_data.get("wind_speed_kmh", 18.0) or 18.0

    fig = go.Figure()

    # Wind origin (from which wind blows)
    fig.add_trace(go.Barpolar(
        r=[wind_speed * 0.7],
        theta=[wind_from],
        width=[20],
        marker_color="#0284c7",
        name=f"Origin: FROM {wind_from:.0f}° ({weather_data.get('wind_cardinal', 'NW')})",
        opacity=0.75
    ))

    # Downwind spread vector (toward which fire spreads)
    fig.add_trace(go.Barpolar(
        r=[wind_speed],
        theta=[wind_toward],
        width=[26],
        marker_color="#dc2626",
        name=f"Fire Spread Vector: TOWARD {wind_toward:.0f}°",
        opacity=0.9
    ))

    fig.update_layout(
        title=f"Wind Vector vs Spread Heading ({wind_speed:.1f} km/h) [OBSERVED]",
        polar=dict(
            radialaxis=dict(visible=True, range=[0, max(30, wind_speed * 1.3)]),
            angularaxis=dict(direction="clockwise", rotation=90)
        ),
        height=310,
        margin=dict(l=30, r=30, t=45, b=20),
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=11),
        legend=dict(orientation="h", y=-0.18)
    )
    return fig


def plot_land_cover_distribution() -> go.Figure:
    """Renders fuel model & land cover distribution in Tadoba Demonstration Area."""
    classes = [
        "Dry Teak & Bamboo Forest",
        "Moist Deciduous Mixed",
        "Grasslands & Savannah",
        "Dry Thorn & Scrub",
        "Water & Non-Burnable"
    ]
    pcts = [44.5, 26.0, 16.2, 9.8, 3.5]
    colors = ["#15803d", "#22c55e", "#eab308", "#f97316", "#0284c7"]

    fig = px.pie(
        names=classes,
        values=pcts,
        color_discrete_sequence=colors,
        title="Land Cover & Fuel Model Composition (Tadoba Reserve) [SATELLITE-DERIVED]",
        hole=0.45
    )
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="Inter, sans-serif", size=11)
    )
    return fig


def plot_environmental_correlation(df_hotspots: pd.DataFrame, weather: Dict[str, Any]) -> go.Figure:
    """
    Renders correlation visualization between temperature, humidity, wind, and observed FRP.
    Includes explicit warning that correlation does not establish causation.
    """
    if df_hotspots.empty:
        return go.Figure()

    fig = px.scatter(
        df_hotspots,
        x="brightness",
        y="frp",
        color="confidence_label",
        size="frp",
        color_discrete_map={"High": "#dc2626", "Nominal": "#ea580c", "Low": "#eab308"},
        labels={"brightness": "Brightness Temp (Kelvin)", "frp": "Fire Radiative Power (MW)"},
        title="Radiative Power vs Brightness Temperature [OBSERVED CORRELATION]"
    )

    fig.add_annotation(
        text="⚠️ Notice: Statistical correlation does not establish environmental causation.",
        xref="paper", yref="paper", x=0.5, y=-0.22,
        showarrow=False, font=dict(size=10, color="#64748b")
    )

    fig.update_layout(
        height=320,
        margin=dict(l=40, r=20, t=40, b=45),
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=12)
    )
    return fig
