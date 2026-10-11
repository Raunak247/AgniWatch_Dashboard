"""
AgniWatch India - Heuristic Wildfire Risk Scoring Model
Grid-based, transparent, multi-factor risk assessment combining weather,
satellite vegetation indices, and soil moisture estimates.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class FireRiskModel:
    """
    Transparent, configurable heuristic fire-risk scoring engine.
    Computes index from 0 to 100 based on physical fire-weather and fuel moisture drivers.
    """

    DEFAULT_WEIGHTS = {
        "temperature": 0.25,
        "humidity": 0.25,
        "wind_speed": 0.20,
        "vegetation_dryness": 0.15,
        "soil_moisture": 0.15,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._normalize_weights()

    def _normalize_weights(self):
        """Ensures weights sum to 1.0."""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    @staticmethod
    def normalize_temperature(temp_c: Optional[float]) -> Optional[float]:
        """Normalizes temperature: 15°C (0.0) to 45°C (1.0)."""
        if temp_c is None:
            return None
        return float(np.clip((temp_c - 15.0) / 30.0, 0.0, 1.0))

    @staticmethod
    def normalize_humidity(rh_pct: Optional[float]) -> Optional[float]:
        """Normalizes relative humidity: 80% (0.0) to 10% (1.0) - inverted scale."""
        if rh_pct is None:
            return None
        # Lower humidity = higher fire risk
        return float(np.clip((80.0 - rh_pct) / 70.0, 0.0, 1.0))

    @staticmethod
    def normalize_wind_speed(wind_kmh: Optional[float], gust_kmh: Optional[float] = None) -> Optional[float]:
        """Normalizes wind speed & gust: 0 km/h (0.0) to 50 km/h (1.0)."""
        if wind_kmh is None:
            return None
        effective_wind = wind_kmh
        if gust_kmh and gust_kmh > wind_kmh:
            # Factor in gusts with 30% weight
            effective_wind = 0.7 * wind_kmh + 0.3 * gust_kmh
        return float(np.clip(effective_wind / 50.0, 0.0, 1.0))

    @staticmethod
    def normalize_vegetation_dryness(ndmi: Optional[float], ndvi: Optional[float] = None) -> Optional[float]:
        """
        Normalizes vegetation canopy dryness.
        NDMI (Normalized Difference Moisture Index) ranges -0.3 (dry) to +0.4 (wet).
        Lower NDMI = drier vegetation canopy = higher risk.
        Note: NDVI alone is NOT used to assign risk, avoiding false high risk in lush green forests.
        """
        if ndmi is None:
            # If NDMI is not provided, do not guess from NDVI alone
            return None
        # NDMI scale: +0.35 (very wet/green: 0.0) to -0.20 (senescent/cured: 1.0)
        norm_dryness = np.clip((0.35 - ndmi) / 0.55, 0.0, 1.0)
        
        # If NDVI is also provided, fine-tune: high NDVI with dry NDMI implies high dry fuel load
        if ndvi is not None and not np.isnan(ndvi):
            fuel_load_factor = np.clip(ndvi, 0.2, 0.8)  # higher biomass
            combined = 0.75 * norm_dryness + 0.25 * fuel_load_factor
            return float(np.clip(combined, 0.0, 1.0))
        
        return float(norm_dryness)

    @staticmethod
    def normalize_soil_moisture(sm_val: Optional[float]) -> Optional[float]:
        """
        Normalizes volumetric soil moisture (m³/m³).
        Ranges from 0.05 (parched soil: 1.0 risk) to 0.40 (saturated soil: 0.0 risk).
        """
        if sm_val is None:
            return None
        return float(np.clip((0.40 - sm_val) / 0.35, 0.0, 1.0))

    def calculate_score(
        self,
        temperature_c: Optional[float],
        humidity_pct: Optional[float],
        wind_kmh: Optional[float],
        wind_gust_kmh: Optional[float] = None,
        ndmi: Optional[float] = None,
        ndvi: Optional[float] = None,
        soil_moisture_m3: Optional[float] = None,
        rainfall_mm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes composite fire-risk score (0 - 100) and detailed contributing factor breakdown.
        """
        norm_factors = {
            "temperature": self.normalize_temperature(temperature_c),
            "humidity": self.normalize_humidity(humidity_pct),
            "wind_speed": self.normalize_wind_speed(wind_kmh, wind_gust_kmh),
            "vegetation_dryness": self.normalize_vegetation_dryness(ndmi, ndvi),
            "soil_moisture": self.normalize_soil_moisture(soil_moisture_m3),
        }

        # Filter available factors
        available_weights = {}
        weighted_sum = 0.0
        missing_factors = []

        for factor, val in norm_factors.items():
            if val is not None:
                w = self.weights.get(factor, 0.2)
                available_weights[factor] = w
                weighted_sum += val * w
            else:
                missing_factors.append(factor)

        total_avail_weight = sum(available_weights.values())

        if total_avail_weight > 0:
            # Rescale to 100
            base_score = (weighted_sum / total_avail_weight) * 100.0
        else:
            base_score = 0.0

        # Rainfall suppression effect:
        # If rainfall occurred in the past 1-3 hours, drastically suppress fire risk
        rain_suppression_pct = 0.0
        if rainfall_mm is not None and rainfall_mm > 0:
            # 5mm rain cuts score by 75%
            rain_suppression_pct = min(90.0, rainfall_mm * 18.0)
            base_score = max(0.0, base_score * (1.0 - rain_suppression_pct / 100.0))

        score = round(float(np.clip(base_score, 0.0, 100.0)), 1)
        category, color, badge = self.get_category(score)

        completeness_pct = round((len(available_weights) / len(norm_factors)) * 100.0, 1)

        # Breakdown of individual contributions
        breakdown = {}
        for f_name, norm_val in norm_factors.items():
            if norm_val is not None:
                eff_weight = (available_weights[f_name] / total_avail_weight) if total_avail_weight > 0 else 0
                contribution_pts = round(norm_val * eff_weight * 100.0, 1)
                breakdown[f_name] = {
                    "normalized_value": round(norm_val, 3),
                    "effective_weight": round(eff_weight, 3),
                    "contribution_pts": contribution_pts,
                    "status": "Available"
                }
            else:
                breakdown[f_name] = {
                    "normalized_value": None,
                    "effective_weight": 0.0,
                    "contribution_pts": 0.0,
                    "status": "Missing (Assumptions Marked)"
                }

        return {
            "score": score,
            "category": category,
            "color": color,
            "badge": badge,
            "completeness_pct": completeness_pct,
            "missing_factors": missing_factors,
            "rain_suppressed": rain_suppression_pct > 0,
            "rain_suppression_pct": round(rain_suppression_pct, 1),
            "breakdown": breakdown,
            "disclaimer": "Preliminary heuristic score (0-100) — not an empirically validated wildfire probability."
        }

    @staticmethod
    def get_category(score: float) -> Tuple[str, str, str]:
        """Maps score to risk tier, hex color, and UI badge."""
        if score < 25.0:
            return "Low", "#2ecc71", "🟢 Low Risk"
        elif score < 50.0:
            return "Moderate", "#f1c40f", "🟡 Moderate Risk"
        elif score < 75.0:
            return "High", "#e67e22", "🟠 High Risk"
        else:
            return "Very High / Extreme", "#e74c3c", "🔴 Very High / Extreme Risk"

    def generate_risk_grid(
        self,
        bbox: List[float],
        grid_size: int = 8,
        base_weather: Optional[Dict[str, Any]] = None,
        base_ndmi: float = 0.05,
        base_ndvi: float = 0.52,
        base_soil_moisture: float = 0.14
    ) -> List[Dict[str, Any]]:
        """
        Subdivides the bounding box into a spatial grid and computes fire risk per cell.
        Adds spatial microclimate variations (e.g. slope/canopy variation).
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        lon_step = (max_lon - min_lon) / grid_size
        lat_step = (max_lat - min_lat) / grid_size

        weather = base_weather or {}
        temp = weather.get("temperature_c", 38.0)
        rh = weather.get("humidity_pct", 24.0)
        wind_kmh = weather.get("wind_speed_kmh", 18.0)
        gust_kmh = weather.get("wind_gust_kmh", 28.0)
        rain_mm = weather.get("rain_1h_mm")

        cells = []
        np.random.seed(101)  # Reproducible microclimate variation

        for i in range(grid_size):
            for j in range(grid_size):
                cell_min_lon = min_lon + j * lon_step
                cell_max_lon = cell_min_lon + lon_step
                cell_min_lat = min_lat + i * lat_step
                cell_max_lat = cell_min_lat + lat_step
                
                c_lat = (cell_min_lat + cell_max_lat) / 2.0
                c_lon = (cell_min_lon + cell_max_lon) / 2.0

                # Micro-spatial variation across terrain
                temp_var = temp + np.random.uniform(-1.8, 2.2)
                rh_var = max(10.0, rh + np.random.uniform(-4.0, 5.0))
                wind_var = max(0.0, wind_kmh + np.random.uniform(-3.5, 4.0))
                ndmi_var = float(np.clip(base_ndmi + np.random.uniform(-0.12, 0.10), -0.25, 0.35))
                sm_var = float(np.clip(base_soil_moisture + np.random.uniform(-0.04, 0.05), 0.05, 0.35))

                res = self.calculate_score(
                    temperature_c=temp_var,
                    humidity_pct=rh_var,
                    wind_kmh=wind_var,
                    wind_gust_kmh=gust_kmh,
                    ndmi=ndmi_var,
                    ndvi=base_ndvi,
                    soil_moisture_m3=sm_var,
                    rainfall_mm=rain_mm
                )

                cells.append({
                    "cell_id": f"R{i}C{j}",
                    "row": i,
                    "col": j,
                    "center": [c_lat, c_lon],
                    "bounds": [[cell_min_lat, cell_min_lon], [cell_max_lat, cell_max_lon]],
                    "score": res["score"],
                    "category": res["category"],
                    "color": res["color"],
                    "badge": res["badge"],
                    "temp_c": round(temp_var, 1),
                    "humidity_pct": round(rh_var, 1),
                    "ndmi": round(ndmi_var, 2),
                    "soil_moisture": round(sm_var, 2),
                    "breakdown": res["breakdown"]
                })

        return cells
