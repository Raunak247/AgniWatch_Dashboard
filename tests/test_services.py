"""
Unit tests for AgniWatch India FIRMS and Weather services
Validates CSV parsing, mock fallback generation, and meteorological wind conversions.
"""

import pytest
import pandas as pd
from services.firms import FirmsClient
from services.weather import WeatherClient


def test_firms_client_unconfigured_fallback():
    client = FirmsClient(map_key="")
    assert not client.is_configured()
    
    bbox = [79.15, 20.05, 79.55, 20.45]
    df, meta = client.fetch_hotspots(bbox=bbox, source="VIIRS_NOAA20_NRT", day_range=3)
    
    assert meta["is_demo"] is True
    assert len(df) > 0
    assert "latitude" in df.columns
    assert "frp" in df.columns
    assert "confidence_label" in df.columns
    assert "detection_status" in df.columns
    # Ensure detections lie within bounding box
    assert df["latitude"].min() >= bbox[1] - 0.05
    assert df["latitude"].max() <= bbox[3] + 0.05


def test_firms_standardize_dataframe():
    client = FirmsClient(map_key="test_key")
    raw_df = pd.DataFrame({
        "latitude": ["20.21", "20.25"],
        "longitude": ["79.30", "79.35"],
        "brightness": ["330.5", "345.0"],
        "scan": ["0.4", "0.4"],
        "track": ["0.4", "0.4"],
        "acq_date": ["2026-03-15", "2026-03-15"],
        "acq_time": [430, 1420],
        "satellite": ["N", "N"],
        "instrument": ["VIIRS", "VIIRS"],
        "confidence": ["n", "h"],
        "version": ["2.0NRT", "2.0NRT"],
        "bright_t31": ["295.0", "300.2"],
        "frp": ["14.2", "42.8"],
        "daynight": ["D", "D"]
    })
    
    cleaned = client._standardize_and_clean_dataframe(raw_df, source="VIIRS_NOAA20_NRT")
    assert cleaned["confidence_label"].tolist() == ["Nominal", "High"]
    assert cleaned["frp"].iloc[1] == 42.8
    assert pd.api.types.is_datetime64_any_dtype(cleaned["acq_datetime_utc"])


def test_weather_client_unconfigured_fallback():
    client = WeatherClient(api_key="")
    assert not client.is_configured()
    
    w = client.get_current_weather(lat=20.21, lon=79.30)
    assert w["is_demo"] is True
    assert w["temperature_c"] > 30.0
    assert w["humidity_pct"] < 35.0
    # Wind conversion: NW (305 deg) blows toward SE (125 deg)
    assert w["wind_deg_from"] == 305.0
    assert w["wind_deg_toward"] == 125.0
    assert w["wind_cardinal"] == "NW"


def test_weather_cardinal_conversion():
    assert WeatherClient._degrees_to_cardinal(0) == "N"
    assert WeatherClient._degrees_to_cardinal(90) == "E"
    assert WeatherClient._degrees_to_cardinal(180) == "S"
    assert WeatherClient._degrees_to_cardinal(270) == "W"
    assert WeatherClient._degrees_to_cardinal(315) == "NW"
