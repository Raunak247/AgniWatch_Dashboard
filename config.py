"""
AgniWatch India - Configuration, Environment & Server-Side Credentials
Professional Wildfire Intelligence, Risk Analytics & Prevention Platform
"""

import os
from typing import Dict, List, Tuple, Any
from dotenv import load_dotenv

# Try importing streamlit to check st.secrets for deployed administrator keys
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Load local .env from project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()


def get_server_credential(key_name: str, default: str = "") -> str:
    """
    Retrieves server-side administrator credentials.
    Priority:
    1. Streamlit secrets (st.secrets) - for deployed server environments
    2. Environment variables (.env or os.environ)
    3. Default empty string
    
    CRITICAL SECURITY RULE:
    Credentials are configured ONCE by the administrator on the server.
    Authorized users of the deployed application automatically inherit them.
    Raw keys are never sent to browser code, reports, or public exports.
    """
    # 1. Check Streamlit secrets
    if HAS_STREAMLIT:
        try:
            if hasattr(st, "secrets") and key_name in st.secrets:
                val = st.secrets[key_name]
                if val and str(val).strip() and not str(val).startswith("your_"):
                    return str(val).strip()
        except Exception:
            pass

    # 2. Check environment variables
    env_val = os.getenv(key_name, default)
    if env_val and str(env_val).strip() and not str(env_val).startswith("your_"):
        return str(env_val).strip()

    return default


# Server-Side Administrator Credentials
NASA_FIRMS_MAP_KEY: str = get_server_credential("NASA_FIRMS_MAP_KEY", "")
OPENWEATHERMAP_API_KEY: str = get_server_credential("OPENWEATHERMAP_API_KEY", "")
EARTH_ENGINE_PROJECT: str = get_server_credential("EARTH_ENGINE_PROJECT", "")

# App Metadata
APP_NAME: str = "AgniWatch India"
APP_SUBTITLE: str = "Wildfire Intelligence, Risk Analytics, Simulation & Prevention System"
APP_VERSION: str = "2.0.0-ENTERPRISE"

# Standard Data Classification Labels (Required throughout UI and exports)
DATA_CLASSIFICATIONS = {
    "OBSERVED": {"badge": "🔵 Observed", "color": "#0284c7", "desc": "Direct sensor measurement from satellite or surface station."},
    "SATELLITE_DERIVED": {"badge": "🟣 Satellite-Derived", "color": "#7c3aed", "desc": "Computed from spectral reflectance bands (Sentinel-2 NDVI, NDMI, NBR)."},
    "MODEL_DERIVED": {"badge": "🟠 Model-Derived", "color": "#ea580c", "desc": "Calculated via documented equations (Rothermel spread, multi-factor risk)."},
    "ESTIMATED": {"badge": "🟡 Estimated", "color": "#f59e0b", "desc": "Inferred from regional proxies or seasonal historical benchmarks."},
    "SIMULATED": {"badge": "🔴 Simulated", "color": "#dc2626", "desc": "Hypothetical scenario output for emergency preparedness."},
    "UNAVAILABLE": {"badge": "⚪ Unavailable", "color": "#64748b", "desc": "Sensor pass missing or credentials not configured. Never fabricated."}
}

# Supported Indian Study Areas and Tiger Reserves
STUDY_AREAS: Dict[str, dict] = {
    "Tadoba-Andhari Tiger Reserve (Maharashtra) [Default]": {
        "id": "tadoba",
        "name": "Tadoba-Andhari Tiger Reserve",
        "state": "Maharashtra",
        "district": "Chandrapur",
        "center": [20.21, 79.30],
        "zoom": 11,
        "bbox": [79.15, 20.05, 79.55, 20.45],
        "area_sq_km": 625.4,
        "ecosystem": "Tropical Dry Deciduous (Teak, Bamboo, Ain, Mahua)",
        "fire_season": "February - May (Peak: March-April)",
        "verified_boundary": True
    },
    "Kanha Tiger Reserve (Madhya Pradesh)": {
        "id": "kanha",
        "name": "Kanha Tiger Reserve",
        "state": "Madhya Pradesh",
        "district": "Mandla / Balaghat",
        "center": [22.28, 80.61],
        "zoom": 11,
        "bbox": [80.35, 22.10, 80.95, 22.50],
        "area_sq_km": 940.0,
        "ecosystem": "Moist & Dry Deciduous Sal & Grasslands",
        "fire_season": "February - May",
        "verified_boundary": True
    },
    "Bandipur Tiger Reserve (Karnataka)": {
        "id": "bandipur",
        "name": "Bandipur Tiger Reserve",
        "state": "Karnataka",
        "district": "Chamarajanagar",
        "center": [11.66, 76.63],
        "zoom": 11,
        "bbox": [76.40, 11.50, 76.85, 11.85],
        "area_sq_km": 874.0,
        "ecosystem": "Dry Deciduous Scrub & Teak Woodland",
        "fire_season": "January - April",
        "verified_boundary": True
    },
    "Jim Corbett National Park (Uttarakhand)": {
        "id": "corbett",
        "name": "Jim Corbett National Park",
        "state": "Uttarakhand",
        "district": "Nainital / Pauri Garhwal",
        "center": [29.53, 78.96],
        "zoom": 11,
        "bbox": [78.75, 29.35, 79.20, 29.75],
        "area_sq_km": 520.8,
        "ecosystem": "Sub-Himalayan Sal, Mixed Deciduous, Pine",
        "fire_season": "March - June",
        "verified_boundary": True
    },
    "Similipal Tiger Reserve (Odisha)": {
        "id": "similipal",
        "name": "Similipal Tiger Reserve",
        "state": "Odisha",
        "district": "Mayurbhanj",
        "center": [21.78, 86.35],
        "zoom": 10,
        "bbox": [86.10, 21.50, 86.65, 22.10],
        "area_sq_km": 2750.0,
        "ecosystem": "Dense Sal Forest & Semi-Evergreen",
        "fire_season": "February - May",
        "verified_boundary": True
    },
    "India National Overview": {
        "id": "india_overview",
        "name": "India National Extent",
        "state": "All India",
        "district": "National",
        "center": [21.50, 78.96],
        "zoom": 5,
        "bbox": [68.0, 8.0, 97.0, 37.0],
        "area_sq_km": 3287263.0,
        "ecosystem": "Diverse Terrestrial Biomes",
        "fire_season": "Annual Fire Season (Peak Feb-May)",
        "verified_boundary": False
    }
}

# NASA FIRMS Sources
FIRMS_SOURCES = [
    ("VIIRS_NOAA20_NRT", "VIIRS (NOAA-20 / JPSS-1) 375m - High Resolution NRT"),
    ("VIIRS_SNPP_NRT", "VIIRS (Suomi NPP) 375m - High Resolution NRT"),
    ("VIIRS_NOAA21_NRT", "VIIRS (NOAA-21 / JPSS-2) 375m - High Resolution NRT"),
    ("MODIS_NRT", "MODIS (Terra & Aqua) 1km - Standard NRT"),
]

# Baseline Risk Scoring Weights (Defaults)
DEFAULT_RISK_WEIGHTS = {
    "temperature": 0.25,
    "humidity": 0.25,
    "wind_speed": 0.20,
    "vegetation_dryness": 0.15,
    "soil_moisture": 0.15,
}

# Fuel Models for Indian Forest Biomes
FUEL_MODELS = {
    "Dry Teak & Bamboo Forest": {
        "base_spread_rate_m_min": 7.5,
        "flame_length_m": 2.2,
        "intensity_factor": 1.4,
        "description": "High leaf litter, combustible bamboo culms in summer dry season."
    },
    "Moist Deciduous Mixed Woodland": {
        "base_spread_rate_m_min": 3.8,
        "flame_length_m": 1.2,
        "intensity_factor": 0.9,
        "description": "Moderate surface litter, higher canopy humidity retention."
    },
    "Dry Thorn & Scrubland": {
        "base_spread_rate_m_min": 12.0,
        "flame_length_m": 2.8,
        "intensity_factor": 1.6,
        "description": "Dense thorny bushes, rapid flaming front with wind sensitivity."
    },
    "Grasslands & Savannah Woodland": {
        "base_spread_rate_m_min": 18.5,
        "flame_length_m": 3.4,
        "intensity_factor": 1.8,
        "description": "Fine cured fuels, very fast head-fire spread."
    },
    "Non-Burnable (Water/Bare Ground)": {
        "base_spread_rate_m_min": 0.0,
        "flame_length_m": 0.0,
        "intensity_factor": 0.0,
        "description": "Water bodies, rivers, paved corridors, bare rock (firebreak barrier)."
    }
}
