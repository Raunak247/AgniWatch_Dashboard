"""
Unit tests for AgniWatch India Fire Prevention Service
Validates pre-ignition risk scoring, factor bounds, and evidence-based recommendations.
"""

import pytest
from services.prevention import FirePreventionService


def test_prevention_score_calculation():
    res = FirePreventionService.calculate_prevention_priority_score(
        fuel_class="Grasslands & Savannah Woodland",
        ndmi=-0.15,  # Very dry canopy
        temp_c=42.0,
        rh_pct=15.0,
        wind_kmh=25.0,
        historical_freq="Very High",
        proximity_km=1.0
    )
    
    assert res["prevention_score"] >= 75.0
    assert res["tier"] == "Critical Prevention Priority"
    assert "factors" in res
    assert res["factors"]["fuel_combustibility_pts"] > 20.0


def test_fuel_class_combustibility_comparison():
    res_grass = FirePreventionService.calculate_prevention_priority_score(
        fuel_class="Grasslands & Savannah Woodland", ndmi=0.1, temp_c=35.0, rh_pct=30.0, wind_kmh=15.0
    )
    res_moist = FirePreventionService.calculate_prevention_priority_score(
        fuel_class="Moist Deciduous Mixed Woodland", ndmi=0.1, temp_c=35.0, rh_pct=30.0, wind_kmh=15.0
    )
    res_water = FirePreventionService.calculate_prevention_priority_score(
        fuel_class="Non-Burnable (Water/Bare Ground)", ndmi=0.1, temp_c=35.0, rh_pct=30.0, wind_kmh=15.0
    )

    assert res_grass["factors"]["fuel_combustibility_pts"] > res_moist["factors"]["fuel_combustibility_pts"]
    assert res_water["factors"]["fuel_combustibility_pts"] == 0.0


def test_beat_evaluation_and_recommendations():
    weather = {"temperature_c": 40.0, "humidity_pct": 20.0, "wind_speed_kmh": 22.0}
    beats = FirePreventionService.evaluate_all_beats(weather, ndmi=0.04)
    
    assert len(beats) == 4
    # Highest priority beat must be first (sorted descending)
    assert beats[0]["prevention_score"] >= beats[-1]["prevention_score"]
    
    # Each beat must have recommendations with evidence
    for b in beats:
        assert len(b["recommendations"]) > 0
        assert "evidence" in b["recommendations"][0]
        assert "protocol_note" in b["recommendations"][0]
