"""
Unit tests for AgniWatch India Fire Spread Simulator
Validates Rothermel surface spread rate calculations, flame intensity,
Huygens elliptical expansion, and exposed asset detection.
"""

import pytest
from services.simulation import FireSpreadSimulator, compare_scenarios


def test_rothermel_spread_rate_by_fuel_type():
    # Grassland should spread faster than moist deciduous
    sim_grass = FireSpreadSimulator(20.21, 79.30, fuel_type="Grasslands & Savannah Woodland", wind_speed_kmh=15.0)
    rate_grass = sim_grass.calculate_rothermel_spread_rate()

    sim_moist = FireSpreadSimulator(20.21, 79.30, fuel_type="Moist Deciduous Mixed Woodland", wind_speed_kmh=15.0)
    rate_moist = sim_moist.calculate_rothermel_spread_rate()

    assert rate_grass["head_rate_kmh"] > rate_moist["head_rate_kmh"]

    # Non-burnable should have zero spread
    sim_water = FireSpreadSimulator(20.21, 79.30, fuel_type="Non-Burnable (Water/Bare Ground)", wind_speed_kmh=15.0)
    rate_water = sim_water.calculate_rothermel_spread_rate()
    assert rate_water["head_rate_kmh"] == 0.0
    assert rate_water["flame_length_m"] == 0.0


def test_simulation_perimeter_growth():
    sim = FireSpreadSimulator(
        ignition_lat=20.21,
        ignition_lon=79.30,
        wind_speed_kmh=15.0,
        wind_from_deg=270.0,
        fuel_type="Dry Teak & Bamboo Forest",
        time_step_hours=1.0,
        max_duration_hours=4.0
    )
    result = sim.run_simulation()
    steps = result["steps"]
    
    assert len(steps) == 5  # T=0, 1, 2, 3, 4
    
    for i in range(1, len(steps)):
        assert steps[i]["area_ha"] > steps[i-1]["area_ha"]
        assert steps[i]["perimeter_km"] > steps[i-1]["perimeter_km"]

    final_step = result["final_step"]
    assert len(final_step["polygon"]) > 10
    assert final_step["head_rate_kmh"] > 0
    assert final_step["flame_length_m"] > 0


def test_wind_influence_on_spread_heading():
    # Wind FROM 0 deg (North) -> wind travels TOWARD 180 deg (South)
    sim = FireSpreadSimulator(
        ignition_lat=20.21,
        ignition_lon=79.30,
        wind_speed_kmh=20.0,
        wind_from_deg=0.0
    )
    assert sim.wind_toward_deg == 180.0
    
    poly = sim.generate_perimeter_polygon(elapsed_hours=2.0)
    min_lat = min(pt[0] for pt in poly)
    assert min_lat < sim.ignition_lat


def test_scenario_comparison():
    base_sim = FireSpreadSimulator(
        ignition_lat=20.21,
        ignition_lon=79.30,
        wind_speed_kmh=10.0,
        time_step_hours=2.0,
        max_duration_hours=6.0
    )
    
    alt_params = {
        "scenario_name": "Strong Gale Wind",
        "wind_speed_kmh": 30.0
    }
    
    cmp = compare_scenarios(base_sim, alt_params)
    assert cmp["comparison"]["alt_final_area_ha"] > cmp["comparison"]["baseline_final_area_ha"]
    assert cmp["comparison"]["area_change_pct"] > 0
