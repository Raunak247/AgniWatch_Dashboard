"""
Unit tests for AgniWatch India Fire Risk Model
Validates normalization bounds, weight rebalancing, missing-data handling, and rain suppression.
"""

import pytest
from services.risk_model import FireRiskModel


def test_temperature_normalization():
    # 15°C -> 0.0, 45°C -> 1.0, 30°C -> 0.5
    assert FireRiskModel.normalize_temperature(15.0) == 0.0
    assert FireRiskModel.normalize_temperature(45.0) == 1.0
    assert round(FireRiskModel.normalize_temperature(30.0), 2) == 0.5
    # Clamping
    assert FireRiskModel.normalize_temperature(10.0) == 0.0
    assert FireRiskModel.normalize_temperature(55.0) == 1.0
    assert FireRiskModel.normalize_temperature(None) is None


def test_humidity_normalization():
    # 80% RH -> 0.0 (wet), 10% RH -> 1.0 (bone dry)
    assert FireRiskModel.normalize_humidity(80.0) == 0.0
    assert FireRiskModel.normalize_humidity(10.0) == 1.0
    assert round(FireRiskModel.normalize_humidity(45.0), 2) == 0.5
    assert FireRiskModel.normalize_humidity(None) is None


def test_wind_normalization():
    assert FireRiskModel.normalize_wind_speed(0.0) == 0.0
    assert FireRiskModel.normalize_wind_speed(50.0) == 1.0
    assert FireRiskModel.normalize_wind_speed(25.0) == 0.5
    # Gust influence
    norm_gust = FireRiskModel.normalize_wind_speed(20.0, gust_kmh=40.0)
    norm_no_gust = FireRiskModel.normalize_wind_speed(20.0, gust_kmh=20.0)
    assert norm_gust > norm_no_gust


def test_vegetation_dryness_does_not_use_ndvi_alone():
    # If NDMI is missing, NDVI alone must NOT assign risk
    assert FireRiskModel.normalize_vegetation_dryness(ndmi=None, ndvi=0.8) is None
    # When NDMI is present (e.g. -0.2 dry), it computes dryness
    assert FireRiskModel.normalize_vegetation_dryness(ndmi=-0.2) == 1.0
    assert FireRiskModel.normalize_vegetation_dryness(ndmi=0.35) == 0.0


def test_missing_data_rescaling():
    model = FireRiskModel()
    # Provide only temp (45C -> 1.0) and humidity (10% -> 1.0)
    res = model.calculate_score(temperature_c=45.0, humidity_pct=10.0, wind_kmh=None)
    # Score should still be 100 because both available normalized inputs are 1.0
    assert res["score"] == 100.0
    assert res["category"] == "Very High / Extreme"
    # Completeness should reflect only 2 out of 5 factors available
    assert res["completeness_pct"] == 40.0
    assert "wind_speed" in res["missing_factors"]


def test_rain_suppression():
    model = FireRiskModel()
    # High risk conditions
    dry_res = model.calculate_score(temperature_c=42.0, humidity_pct=15.0, wind_kmh=25.0)
    # Same conditions but with 5mm rainfall
    wet_res = model.calculate_score(temperature_c=42.0, humidity_pct=15.0, wind_kmh=25.0, rainfall_mm=5.0)
    assert wet_res["score"] < dry_res["score"]
    assert wet_res["rain_suppressed"] is True


def test_grid_generation():
    model = FireRiskModel()
    bbox = [79.15, 20.05, 79.55, 20.45]
    grid = model.generate_risk_grid(bbox, grid_size=4)
    assert len(grid) == 16  # 4x4
    first_cell = grid[0]
    assert "cell_id" in first_cell
    assert "bounds" in first_cell
    assert 0 <= first_cell["score"] <= 100
