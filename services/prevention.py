"""
AgniWatch India - Wildfire Prevention Intelligence Service
Implements pre-ignition risk scoring, evidence-based mitigation recommendations,
forest beat inspection routing, and prevention action tracking.

DISCLAIMER: Recommendations support forest management decision-making.
All fuel treatments and patrols must comply with State Forest Department protocols.
"""

import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np


class FirePreventionService:
    """
    Evaluates pre-ignition risk factors and generates actionable,
    evidence-based prevention measures for forest beats and compartments.
    """

    # Pre-configured Forest Beats for Tadoba-Andhari Tiger Reserve
    TADOBA_BEATS = [
        {
            "beat_id": "TATR-MOH-01",
            "beat_name": "Moharli Core Beat",
            "range": "Moharli",
            "center": [20.18, 79.32],
            "fuel_class": "Dry Teak & Bamboo Forest",
            "dominant_species": "Tectona grandis, Dendrocalamus strictus",
            "historical_fire_frequency": "High (3 fires in 5 years)",
            "proximity_to_settlements_km": 2.4,
            "vulnerability_reason": "Dense bamboo understory with intense summer tourism traffic."
        },
        {
            "beat_id": "TATR-CHM-02",
            "beat_name": "Chimur Peripheral Beat",
            "range": "Chimur",
            "center": [20.35, 79.24],
            "fuel_class": "Grasslands & Savannah Woodland",
            "dominant_species": "Heteropogon contortus, Butea monosperma",
            "historical_fire_frequency": "Very High (Annual fires during Mahua season)",
            "proximity_to_settlements_km": 1.1,
            "vulnerability_reason": "Abuts agricultural fields; frequent non-timber forest produce collection."
        },
        {
            "beat_id": "TATR-KOL-03",
            "beat_name": "Kolsa Deep Forest Beat",
            "range": "Kolsa",
            "center": [20.12, 79.45],
            "fuel_class": "Moist Deciduous Mixed Woodland",
            "dominant_species": "Terminalia tomentosa, Madhuca longifolia",
            "historical_fire_frequency": "Moderate (1 fire in 5 years)",
            "proximity_to_settlements_km": 6.8,
            "vulnerability_reason": "Remote rugged terrain; limited road access for mechanized fire response."
        },
        {
            "beat_id": "TATR-NAV-04",
            "beat_name": "Navegaon Buffer Beat",
            "range": "Navegaon",
            "center": [20.42, 79.38],
            "fuel_class": "Dry Thorn & Scrubland",
            "dominant_species": "Acacia catechu, Ziziphus mauritiana",
            "historical_fire_frequency": "High (2 fires in 3 years)",
            "proximity_to_settlements_km": 0.8,
            "vulnerability_reason": "High grazing pressure and cattle movement across forest fringe."
        }
    ]

    @staticmethod
    def calculate_prevention_priority_score(
        fuel_class: str,
        ndmi: Optional[float],
        temp_c: Optional[float],
        rh_pct: Optional[float],
        wind_kmh: Optional[float],
        slope_deg: float = 8.0,
        historical_freq: str = "High",
        proximity_km: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculates Pre-Ignition Prevention Priority Score (0 - 100).
        Strictly evaluates conditions favorable to ignition before any fire occurs.
        """
        # 1. Fuel combustibility factor (0 - 25 pts)
        fuel_scores = {
            "Grasslands & Savannah Woodland": 24.0,
            "Dry Thorn & Scrubland": 21.0,
            "Dry Teak & Bamboo Forest": 19.0,
            "Moist Deciduous Mixed Woodland": 11.0,
            "Non-Burnable (Water/Bare Ground)": 0.0
        }
        f_pts = fuel_scores.get(fuel_class, 15.0)

        # 2. Moisture desiccation factor (0 - 25 pts)
        # NDMI scale: low NDMI (< 0.05) indicates severely dry leaf litter
        if ndmi is not None:
            m_norm = np.clip((0.30 - ndmi) / 0.50, 0.0, 1.0)
            m_pts = float(m_norm * 25.0)
        else:
            m_pts = 14.0  # Moderate default assumption when sensor unavailable

        # 3. Fire Weather dryness (0 - 25 pts)
        # High temperature (> 38C) + Low RH (< 25%)
        temp = temp_c or 36.0
        rh = rh_pct or 30.0
        w_norm = np.clip((temp - 20.0) / 25.0, 0.0, 1.0) * 0.5 + np.clip((70.0 - rh) / 60.0, 0.0, 1.0) * 0.5
        w_pts = float(w_norm * 25.0)

        # 4. Proximity & Historic Vulnerability (0 - 25 pts)
        hist_scores = {"Very High": 15.0, "High": 11.0, "Moderate": 7.0, "Low": 3.0}
        h_pts = hist_scores.get(historical_freq, 8.0)
        
        # Closer to human activity / fringe (< 2km) = higher human ignition risk
        prox_pts = 10.0 if proximity_km <= 1.5 else (6.0 if proximity_km <= 3.5 else 2.0)
        v_pts = h_pts + prox_pts

        total_score = round(f_pts + m_pts + w_pts + v_pts, 1)
        total_score = float(np.clip(total_score, 0.0, 100.0))

        # Categorization
        if total_score >= 75.0:
            tier = "Critical Prevention Priority"
            color = "#dc2626"
            badge = "🔴 Critical"
        elif total_score >= 55.0:
            tier = "High Prevention Priority"
            color = "#ea580c"
            badge = "🟠 High"
        elif total_score >= 35.0:
            tier = "Moderate Prevention Priority"
            color = "#f59e0b"
            badge = "🟡 Moderate"
        else:
            tier = "Low Prevention Priority"
            color = "#10b981"
            badge = "🟢 Low"

        return {
            "prevention_score": total_score,
            "tier": tier,
            "color": color,
            "badge": badge,
            "factors": {
                "fuel_combustibility_pts": round(f_pts, 1),
                "canopy_desiccation_pts": round(m_pts, 1),
                "weather_dryness_pts": round(w_pts, 1),
                "vulnerability_human_pts": round(v_pts, 1)
            },
            "data_classification": "MODEL-DERIVED"
        }

    @classmethod
    def generate_beat_recommendations(
        cls,
        beat_info: Dict[str, Any],
        prevention_result: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generates actionable, evidence-based recommendations tied directly to observed conditions.
        """
        score = prevention_result["prevention_score"]
        fuel = beat_info.get("fuel_class", "")
        range_name = beat_info.get("range", "Core")
        wind_spd = weather_data.get("wind_speed_kmh", 15.0) or 15.0
        temp = weather_data.get("temperature_c", 35.0) or 35.0

        recs = []

        # 1. Fireline & Fuel break inspection
        if "Bamboo" in fuel or "Grassland" in fuel:
            recs.append({
                "action_type": "Fuel Break Clearance",
                "priority": "High" if score >= 60 else "Medium",
                "recommendation": f"Inspect and sweep combustible teak leaf litter and dry bamboo foliage along compartment boundaries in {range_name}.",
                "evidence": f"Fuel type is {fuel}; dry season leaf-fall creates continuous fine fuel beds susceptible to rapid surface flame.",
                "protocol_note": "Ensure clearing strictly follows Maharashtra Forest Department manual fire line maintenance guidelines."
            })

        # 2. Patrol frequency escalation
        if score >= 70 or temp >= 38.0:
            recs.append({
                "action_type": "Patrol Schedule Escalation",
                "priority": "Critical",
                "recommendation": f"Increase foot and motorcycle patrols between 12:00 and 16:30 IST across {beat_info['beat_name']}.",
                "evidence": f"Extreme heat ({temp:.1f}°C) and low relative humidity coincide with peak solar radiation and Mahua collection hours.",
                "protocol_note": "Equip beat guards with wireless handsets, GPS loggers, and pressurized water knapsacks."
            })
        elif score >= 50:
            recs.append({
                "action_type": "Regular Patrol Inspection",
                "priority": "Medium",
                "recommendation": f"Maintain twice-daily monitoring along boundary trails in {beat_info['beat_name']}.",
                "evidence": f"Moderate fire risk score of {score:.0f} requires sustained surveillance.",
                "protocol_note": "Coordinate with peripheral Village Eco-Development Committees (EDCs)."
            })

        # 3. High wind containment precaution
        if wind_spd >= 20.0:
            recs.append({
                "action_type": "Wind Hazard Alert",
                "priority": "High",
                "recommendation": f"Position mobile water tanker at key forest road junction near {beat_info['beat_name']}.",
                "evidence": f"Gusty winds ({wind_spd:.1f} km/h) dramatically increase potential fire spread rate and ember spotting distance.",
                "protocol_note": "Ensure access route bridges and culverts are unobstructed for quick response."
            })

        # 4. Community awareness advisory
        if beat_info.get("proximity_to_settlements_km", 5.0) <= 2.0:
            recs.append({
                "action_type": "Community Advisory",
                "priority": "Medium",
                "recommendation": "Conduct awareness outreach with local villagers regarding safe Mahua flower and tendu leaf harvesting practices.",
                "evidence": f"Beat is within {beat_info.get('proximity_to_settlements_km')} km of habitations, where controlled clearing by fire must be prevented.",
                "protocol_note": "Promote clean-sweeping methods instead of lighting ground fires under trees."
            })

        return recs

    @classmethod
    def evaluate_all_beats(
        cls,
        weather_data: Dict[str, Any],
        ndmi: Optional[float]
    ) -> List[Dict[str, Any]]:
        """Evaluates all registered beats and sorts them by prevention priority."""
        evaluated = []
        for beat in cls.TADOBA_BEATS:
            res = cls.calculate_prevention_priority_score(
                fuel_class=beat["fuel_class"],
                ndmi=ndmi,
                temp_c=weather_data.get("temperature_c"),
                rh_pct=weather_data.get("humidity_pct"),
                wind_kmh=weather_data.get("wind_speed_kmh"),
                historical_freq=beat.get("historical_fire_frequency", "Moderate"),
                proximity_km=beat.get("proximity_to_settlements_km", 2.5)
            )
            recs = cls.generate_beat_recommendations(beat, res, weather_data)

            evaluated.append({
                **beat,
                "prevention_score": res["prevention_score"],
                "tier": res["tier"],
                "color": res["color"],
                "badge": res["badge"],
                "factors": res["factors"],
                "recommendations": recs
            })

        # Sort highest priority first
        evaluated.sort(key=lambda x: x["prevention_score"], reverse=True)
        return evaluated
