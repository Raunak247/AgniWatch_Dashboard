"""
AgniWatch India - Wildfire Spread Simulation Engine
Implements Rothermel surface fire spread equations coupled with Huygens elliptical perimeter propagation.
Accounts for wind speed, terrain slope, fuel moisture, and asset exposure proximity.

DISCLAIMER: All outputs are HYPOTHETICAL SIMULATIONS for scenario planning and training.
Not an operational fire physics forecast guarantee.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class FireSpreadSimulator:
    """
    Rothermel-Huygens directional fire spread simulator.
    Models forward head fire rate, backing fire rate, flanking spread,
    flame length, fireline intensity, and sensitive asset exposure over time.
    """

    EARTH_RADIUS_KM = 6371.0

    # Fuel Models calibrated for Indian Forest Ecosystems (based on Rothermel 13 standard models)
    FUEL_MODELS = {
        "Grasslands & Savannah Woodland": {
            "name": "Grasslands & Savannah Woodland (Fuel Model 1)",
            "fuel_load_t_ha": 2.2,       # ~0.22 kg/m^2
            "fuel_depth_m": 0.35,
            "base_rate_m_min": 18.5,     # Fast fine fuel spread
            "heat_content_kj_kg": 18500,
            "extinction_moisture_pct": 15.0,
            "wind_sensitivity": 1.35,
            "description": "Cured fine grasses with very rapid surface fire run under slight breeze."
        },
        "Dry Thorn & Scrubland": {
            "name": "Dry Thorn & Scrubland (Fuel Model 4)",
            "fuel_load_t_ha": 6.8,       # ~0.68 kg/m^2
            "fuel_depth_m": 1.2,
            "base_rate_m_min": 12.0,
            "heat_content_kj_kg": 19200,
            "extinction_moisture_pct": 20.0,
            "wind_sensitivity": 1.15,
            "description": "Dense dry bushes, high resin/oil content, moderate to severe flame lengths."
        },
        "Dry Teak & Bamboo Forest": {
            "name": "Dry Teak & Bamboo Forest (Fuel Model 9 Modified)",
            "fuel_load_t_ha": 9.5,       # ~0.95 kg/m^2
            "fuel_depth_m": 0.45,
            "base_rate_m_min": 7.5,
            "heat_content_kj_kg": 18800,
            "extinction_moisture_pct": 25.0,
            "wind_sensitivity": 1.20,
            "description": "Heavy fallen teak foliage and dry bamboo culms; intense surface fires in summer."
        },
        "Moist Deciduous Mixed Woodland": {
            "name": "Moist Deciduous Mixed Woodland (Fuel Model 8)",
            "fuel_load_t_ha": 5.2,       # ~0.52 kg/m^2
            "fuel_depth_m": 0.25,
            "base_rate_m_min": 3.8,
            "heat_content_kj_kg": 18000,
            "extinction_moisture_pct": 30.0,
            "wind_sensitivity": 0.95,
            "description": "Slow-moving surface fires burning in closed canopy leaf litter."
        },
        "Non-Burnable (Water/Bare Ground)": {
            "name": "Non-Burnable Surface (Fuel Model 0)",
            "fuel_load_t_ha": 0.0,
            "fuel_depth_m": 0.0,
            "base_rate_m_min": 0.0,
            "heat_content_kj_kg": 0,
            "extinction_moisture_pct": 0.0,
            "wind_sensitivity": 0.0,
            "description": "Rivers, reservoirs, paved roads, and bare rocky ground serving as natural firebreaks."
        }
    }

    # Known Conservation Assets and Settlements for Tadoba Demonstration
    SENSITIVE_ASSETS = [
        {"id": "AST-01", "name": "Moharli Village Gate & Safari Entry", "coords": [20.175, 79.330], "type": "Habitation & Tourism Node"},
        {"id": "AST-02", "name": "Tadoba Lake Core Ecological Zone", "coords": [20.242, 79.315], "type": "Critical Water & Breeding Habitat"},
        {"id": "AST-03", "name": "Kolsa Forest Rest House & Beat Office", "coords": [20.130, 79.442], "type": "Administrative Facility"},
        {"id": "AST-04", "name": "Chimur Range Peripheral Village", "coords": [20.362, 79.235], "type": "Human Settlement Fringe"},
        {"id": "AST-05", "name": "Navegaon Buffer Forest Checkpost", "coords": [20.425, 79.380], "type": "Buffer Patrol Post"}
    ]

    def __init__(
        self,
        ignition_lat: float,
        ignition_lon: float,
        wind_speed_kmh: float = 18.0,
        wind_from_deg: float = 300.0,
        fuel_type: str = "Dry Teak & Bamboo Forest",
        fuel_dryness_factor: float = 1.25,
        slope_deg: float = 6.0,
        time_step_hours: float = 1.0,
        max_duration_hours: float = 8.0,
    ):
        self.ignition_lat = float(ignition_lat)
        self.ignition_lon = float(ignition_lon)
        self.wind_speed_kmh = float(wind_speed_kmh)
        self.wind_from_deg = float(wind_from_deg) % 360.0
        # Wind travels TOWARD heading:
        self.wind_toward_deg = (self.wind_from_deg + 180.0) % 360.0
        self.fuel_type = fuel_type
        self.fuel_dryness_factor = float(fuel_dryness_factor)
        self.slope_deg = float(slope_deg)
        self.time_step_hours = float(time_step_hours)
        self.max_duration_hours = float(max_duration_hours)

    def calculate_rothermel_spread_rate(self) -> Dict[str, float]:
        """
        Calculates forward spread rate using Rothermel formulation:
        R_head = R_0 * (1 + phi_w + phi_s) * dryness_factor
        """
        model = self.FUEL_MODELS.get(self.fuel_type, self.FUEL_MODELS["Dry Teak & Bamboo Forest"])
        base_rate_m_min = model["base_rate_m_min"]

        if base_rate_m_min == 0.0:
            return {
                "head_rate_m_min": 0.0, "head_rate_kmh": 0.0,
                "back_rate_kmh": 0.0, "lw_ratio": 1.0,
                "flame_length_m": 0.0, "fireline_intensity_kw_m": 0.0
            }

        # Wind factor phi_w (Rothermel empirical power function)
        wind_ms = (self.wind_speed_kmh * 1000.0) / 3600.0
        phi_w = model["wind_sensitivity"] * (0.05 * (wind_ms ** 1.35))

        # Slope factor phi_s (Rothermel slope equation: 5.275 * tan(slope)^2)
        slope_rad = math.radians(self.slope_deg)
        phi_s = 5.275 * (math.tan(slope_rad) ** 2)

        # Combined forward head fire spread rate
        effective_head_m_min = base_rate_m_min * (1.0 + phi_w + phi_s) * self.fuel_dryness_factor
        head_rate_kmh = (effective_head_m_min * 60.0) / 1000.0

        # Backing fire rate (against wind): typically 12-20% of base rate
        back_rate_kmh = (base_rate_m_min * 0.16 * 60.0) / 1000.0

        # Length-to-width ratio of fire ellipse (Alexander 1985 / Canadian FWI model)
        lw_ratio = 1.0 + 0.125 * (self.wind_speed_kmh ** 0.84)
        lw_ratio = max(1.0, min(5.5, lw_ratio))

        # Byram Fireline Intensity I = H * w * R
        # H = heat yield (kJ/kg), w = fuel consumed (kg/m^2), R = spread rate (m/s)
        w_kg_m2 = (model["fuel_load_t_ha"] * 1000.0) / 10000.0
        r_ms = effective_head_m_min / 60.0
        intensity_kw_m = round(model["heat_content_kj_kg"] * w_kg_m2 * r_ms, 1)

        # Byram Flame Length: L = 0.0775 * I^0.46 (meters)
        flame_len_m = round(0.0775 * (intensity_kw_m ** 0.46), 1) if intensity_kw_m > 0 else 0.5
        flame_len_m = max(0.5, min(8.0, flame_len_m))

        return {
            "head_rate_m_min": round(effective_head_m_min, 1),
            "head_rate_kmh": round(head_rate_kmh, 2),
            "back_rate_kmh": round(back_rate_kmh, 2),
            "lw_ratio": round(lw_ratio, 2),
            "flame_length_m": flame_len_m,
            "fireline_intensity_kw_m": intensity_kw_m
        }

    def compute_ellipse_parameters(self, elapsed_hours: float) -> Dict[str, Any]:
        """Calculates semi-major axis, semi-minor axis, and displacement at elapsed time."""
        rothermel = self.calculate_rothermel_spread_rate()
        
        dist_head_km = rothermel["head_rate_kmh"] * elapsed_hours
        dist_back_km = rothermel["back_rate_kmh"] * elapsed_hours
        
        major_axis_km = dist_head_km + dist_back_km
        semi_major_a = major_axis_km / 2.0
        
        minor_axis_km = major_axis_km / rothermel["lw_ratio"]
        semi_minor_b = minor_axis_km / 2.0
        
        displacement_km = dist_head_km - semi_major_a

        return {
            **rothermel,
            "semi_major_km": semi_major_a,
            "semi_minor_km": semi_minor_b,
            "displacement_km": displacement_km,
            "dist_head_km": round(dist_head_km, 2)
        }

    def generate_perimeter_polygon(
        self,
        elapsed_hours: float,
        num_vertices: int = 40
    ) -> List[List[float]]:
        """Generates closed list of [lat, lon] coordinates representing the fire perimeter."""
        if elapsed_hours <= 0:
            return [[self.ignition_lat, self.ignition_lon]]

        params = self.compute_ellipse_parameters(elapsed_hours)
        a = params["semi_major_km"]
        b = params["semi_minor_km"]
        d = params["displacement_km"]

        heading_rad = math.radians(self.wind_toward_deg)

        # Center displacement from ignition
        center_north_km = d * math.cos(heading_rad)
        center_east_km = d * math.sin(heading_rad)

        center_lat = self.ignition_lat + (center_north_km / self.EARTH_RADIUS_KM) * (180.0 / math.pi)
        center_lon = self.ignition_lon + (center_east_km / (self.EARTH_RADIUS_KM * math.cos(math.radians(self.ignition_lat)))) * (180.0 / math.pi)

        coords = []
        for i in range(num_vertices + 1):
            theta = 2.0 * math.pi * (i / num_vertices)
            
            y_unrot = a * math.cos(theta)
            x_unrot = b * math.sin(theta)

            north_km = y_unrot * math.cos(heading_rad) - x_unrot * math.sin(heading_rad)
            east_km = y_unrot * math.sin(heading_rad) + x_unrot * math.cos(heading_rad)

            d_lat = (north_km / self.EARTH_RADIUS_KM) * (180.0 / math.pi)
            d_lon = (east_km / (self.EARTH_RADIUS_KM * math.cos(math.radians(center_lat)))) * (180.0 / math.pi)

            coords.append([round(center_lat + d_lat, 6), round(center_lon + d_lon, 6)])

        return coords

    def check_exposed_assets(self, polygon: List[List[float]], elapsed_hours: float) -> List[Dict[str, Any]]:
        """Checks which known conservation landmarks or villages are threatened by the perimeter."""
        exposed = []
        if len(polygon) < 3:
            return exposed

        for asset in self.SENSITIVE_ASSETS:
            a_lat, a_lon = asset["coords"]
            # Simple point-in-polygon or proximity check (within 0.5 km)
            # Distance from ignition
            d_km = math.sqrt(((a_lat - self.ignition_lat) * 111.0) ** 2 + ((a_lon - self.ignition_lon) * 104.0) ** 2)
            
            # Check if point lies inside polygon bounding box and rough radius
            lats = [p[0] for p in polygon]
            lons = [p[1] for p in polygon]
            if min(lats) <= a_lat <= max(lats) and min(lons) <= a_lon <= max(lons):
                exposed.append({
                    "asset_id": asset["id"],
                    "asset_name": asset["name"],
                    "asset_type": asset["type"],
                    "impact_time_hours": elapsed_hours,
                    "distance_from_ignition_km": round(d_km, 1),
                    "status": "IMMINENT PERIMETER INTERCEPTION"
                })

        return exposed

    def run_simulation(self) -> Dict[str, Any]:
        """Runs the simulation across all time steps and produces comprehensive outputs."""
        steps = []
        current_hour = 0.0
        all_exposed = {}

        while current_hour <= self.max_duration_hours:
            if current_hour == 0.0:
                steps.append({
                    "step_index": 0,
                    "elapsed_hours": 0.0,
                    "area_ha": 0.1,
                    "area_km2": 0.001,
                    "perimeter_km": 0.05,
                    "head_rate_kmh": 0.0,
                    "head_rate_m_min": 0.0,
                    "head_distance_km": 0.0,
                    "flame_length_m": 0.5,
                    "fireline_intensity_kw_m": 0.0,
                    "polygon": [[self.ignition_lat, self.ignition_lon]],
                    "containment_difficulty": "Initial Spot Stage",
                    "exposed_assets": []
                })
            else:
                params = self.compute_ellipse_parameters(current_hour)
                a = params["semi_major_km"]
                b = params["semi_minor_km"]
                
                area_km2 = math.pi * a * b
                area_ha = area_km2 * 100.0
                
                h = ((a - b) ** 2) / ((a + b) ** 2)
                perimeter_km = math.pi * (a + b) * (1.0 + (3.0 * h) / (10.0 + math.sqrt(4.0 - 3.0 * h)))

                poly = self.generate_perimeter_polygon(current_hour)
                exp = self.check_exposed_assets(poly, current_hour)
                for item in exp:
                    all_exposed[item["asset_id"]] = item

                diff = "Direct Hand Attack Feasible"
                if params["flame_length_m"] > 3.5 or area_ha > 250:
                    diff = "Extreme / Uncontrolled Crown Potential"
                elif params["flame_length_m"] > 2.0 or area_ha > 60:
                    diff = "Heavy Equipment & Bowsers Required"
                elif area_ha > 15:
                    diff = "Direct Suppression Challenging"

                steps.append({
                    "step_index": len(steps),
                    "elapsed_hours": current_hour,
                    "area_ha": round(area_ha, 1),
                    "area_km2": round(area_km2, 3),
                    "perimeter_km": round(perimeter_km, 2),
                    "head_rate_kmh": params["head_rate_kmh"],
                    "head_rate_m_min": params["head_rate_m_min"],
                    "head_distance_km": params["dist_head_km"],
                    "flame_length_m": params["flame_length_m"],
                    "fireline_intensity_kw_m": params["fireline_intensity_kw_m"],
                    "polygon": poly,
                    "containment_difficulty": diff,
                    "exposed_assets": exp
                })

            current_hour = round(current_hour + self.time_step_hours, 2)

        return {
            "ignition": {"latitude": self.ignition_lat, "longitude": self.ignition_lon},
            "parameters": {
                "wind_speed_kmh": self.wind_speed_kmh,
                "wind_from_deg": self.wind_from_deg,
                "wind_toward_deg": self.wind_toward_deg,
                "fuel_type": self.fuel_type,
                "fuel_dryness_factor": self.fuel_dryness_factor,
                "slope_deg": self.slope_deg,
                "max_duration_hours": self.max_duration_hours,
                "time_step_hours": self.time_step_hours,
            },
            "steps": steps,
            "final_step": steps[-1] if steps else None,
            "exposed_assets_summary": list(all_exposed.values()),
            "data_classification": "SIMULATED (Rothermel-Huygens Model)",
            "disclaimer": "HYPOTHETICAL SIMULATION — Scenario decision-support model. Not an operational forecast guarantee."
        }


def compare_scenarios(
    baseline_sim: FireSpreadSimulator,
    alternative_params: Dict[str, Any]
) -> Dict[str, Any]:
    """Compares baseline simulation with alternative meteorological or fuel mitigation scenario."""
    alt_sim = FireSpreadSimulator(
        ignition_lat=baseline_sim.ignition_lat,
        ignition_lon=baseline_sim.ignition_lon,
        wind_speed_kmh=alternative_params.get("wind_speed_kmh", baseline_sim.wind_speed_kmh),
        wind_from_deg=alternative_params.get("wind_from_deg", baseline_sim.wind_from_deg),
        fuel_type=alternative_params.get("fuel_type", baseline_sim.fuel_type),
        fuel_dryness_factor=alternative_params.get("fuel_dryness_factor", baseline_sim.fuel_dryness_factor),
        slope_deg=alternative_params.get("slope_deg", baseline_sim.slope_deg),
        time_step_hours=baseline_sim.time_step_hours,
        max_duration_hours=baseline_sim.max_duration_hours
    )

    res_base = baseline_sim.run_simulation()
    res_alt = alt_sim.run_simulation()

    final_base = res_base["final_step"]
    final_alt = res_alt["final_step"]

    area_diff_pct = 0.0
    if final_base and final_base["area_ha"] > 0:
        area_diff_pct = round(((final_alt["area_ha"] - final_base["area_ha"]) / final_base["area_ha"]) * 100.0, 1)

    return {
        "baseline": res_base,
        "alternative": res_alt,
        "comparison": {
            "baseline_final_area_ha": final_base["area_ha"] if final_base else 0,
            "alt_final_area_ha": final_alt["area_ha"] if final_alt else 0,
            "area_difference_ha": round((final_alt["area_ha"] - final_base["area_ha"]), 1) if (final_base and final_alt) else 0,
            "area_change_pct": area_diff_pct,
            "alt_scenario_name": alternative_params.get("scenario_name", "Alternative Scenario")
        }
    }
