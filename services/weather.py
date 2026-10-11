"""
AgniWatch India - OpenWeatherMap Meteorological Service
Queries live meteorological data from OpenWeatherMap Current Weather API.
Corrects wind vector orientations (FROM vs TOWARD) and provides robust missing-data handling.
"""

import time
import datetime
from typing import Dict, Any, Optional, Tuple
import requests


class WeatherClient:
    """Client for retrieving surface weather observations from OpenWeatherMap."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = (api_key or "").strip()

    def is_configured(self) -> bool:
        """Checks if a valid API key is present."""
        return bool(self.api_key and self.api_key != "your_openweathermap_api_key_here")

    def get_current_weather(
        self,
        lat: float,
        lon: float,
        location_name: str = "Tadoba-Andhari Core",
        timeout: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieves current weather observation for given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            location_name: Friendly name for metadata
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing parsed meteorological parameters and metadata.
        """
        # Validate coordinates
        lat = float(lat)
        lon = float(lon)

        # Fallback if unconfigured
        if not self.is_configured():
            return self._generate_demo_weather(lat, lon, location_name, reason="No OPENWEATHERMAP_API_KEY configured")

        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=timeout)
            
            if resp.status_code == 200:
                data = resp.json()
                return self._parse_owm_response(data, lat, lon, location_name, is_demo=False)
            
            elif resp.status_code == 401:
                return self._generate_demo_weather(
                    lat, lon, location_name, 
                    reason="Invalid OpenWeatherMap API key (HTTP 401 Unauthorized)"
                )
            elif resp.status_code == 429:
                return self._generate_demo_weather(
                    lat, lon, location_name, 
                    reason="OpenWeatherMap rate limit reached (HTTP 429)"
                )
            else:
                return self._generate_demo_weather(
                    lat, lon, location_name, 
                    reason=f"OpenWeatherMap HTTP {resp.status_code}: {resp.reason}"
                )

        except requests.exceptions.RequestException as e:
            return self._generate_demo_weather(
                lat, lon, location_name, 
                reason=f"Network connection failed: {str(e)}"
            )

    def _parse_owm_response(
        self,
        data: Dict[str, Any],
        lat: float,
        lon: float,
        location_name: str,
        is_demo: bool = False,
        demo_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Parses OpenWeatherMap JSON into standardized meteorological structure."""
        main = data.get("main", {})
        wind = data.get("wind", {})
        clouds = data.get("clouds", {})
        rain = data.get("rain", {})
        weather_list = data.get("weather", [{}])
        weather_desc = weather_list[0].get("description", "Clear").title() if weather_list else "Unknown"

        # Observation timestamp
        dt_unix = data.get("dt")
        if dt_unix:
            obs_dt_utc = datetime.datetime.fromtimestamp(dt_unix, tz=datetime.timezone.utc)
            obs_dt_ist = obs_dt_utc + datetime.timedelta(hours=5, minutes=30)
            obs_time_str = obs_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST")
            # Staleness check (flag if older than 3 hours)
            age_hours = (datetime.datetime.now(datetime.timezone.utc) - obs_dt_utc).total_seconds() / 3600.0
            is_stale = age_hours > 3.0
        else:
            obs_time_str = "Unavailable"
            is_stale = False
            age_hours = 0.0

        # Wind direction handling:
        # Meteorological wind deg is the direction FROM which wind blows (0=North, 90=East, 180=South, 270=West).
        # Direction TOWARD which wind blows: (deg + 180) % 360
        wind_deg_from = wind.get("deg")
        if wind_deg_from is not None:
            wind_deg_from = float(wind_deg_from) % 360.0
            wind_deg_toward = (wind_deg_from + 180.0) % 360.0
            wind_cardinal = self._degrees_to_cardinal(wind_deg_from)
        else:
            wind_deg_toward = None
            wind_cardinal = "N/A"

        # Wind speeds
        wind_speed_ms = wind.get("speed")
        wind_speed_kmh = round(wind_speed_ms * 3.6, 1) if wind_speed_ms is not None else None
        
        gust_ms = wind.get("gust")
        gust_kmh = round(gust_ms * 3.6, 1) if gust_ms is not None else None

        # Rainfall
        rain_1h = rain.get("1h") if isinstance(rain, dict) else None
        rain_3h = rain.get("3h") if isinstance(rain, dict) else None

        # Visibility
        visibility_m = data.get("visibility")

        return {
            "is_demo": is_demo,
            "demo_reason": demo_reason,
            "location_name": location_name,
            "latitude": lat,
            "longitude": lon,
            "observation_time_ist": obs_time_str,
            "is_stale": is_stale,
            "age_hours": round(age_hours, 1),
            "condition": weather_desc,
            
            # Primary Meteorological Variables (None if unavailable)
            "temperature_c": main.get("temp"),
            "temp_min_c": main.get("temp_min"),
            "temp_max_c": main.get("temp_max"),
            "humidity_pct": main.get("humidity"),
            "pressure_hpa": main.get("pressure"),
            
            # Wind Fields
            "wind_speed_ms": wind_speed_ms,
            "wind_speed_kmh": wind_speed_kmh,
            "wind_gust_kmh": gust_kmh,
            "wind_deg_from": wind_deg_from,       # Meteorological: where wind comes from
            "wind_deg_toward": wind_deg_toward,   # Vector: where wind is blowing toward
            "wind_cardinal": wind_cardinal,
            
            # Additional Sensors
            "cloud_cover_pct": clouds.get("all"),
            "rain_1h_mm": rain_1h,
            "rain_3h_mm": rain_3h,
            "visibility_m": visibility_m,
            "source": "OpenWeatherMap API" if not is_demo else "Synthetic Meteorological Demonstration"
        }

    def _generate_demo_weather(
        self,
        lat: float,
        lon: float,
        location_name: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Generates realistic dry-season meteorological conditions for Indian central deciduous forests (e.g., Tadoba).
        """
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
        
        # Tadoba typical fire weather in pre-monsoon summer:
        # High heat (38-42°C), Low RH (18-30%), Gusty NW/W wind
        wind_from = 305.0  # From NW (305°)
        wind_toward = (wind_from + 180.0) % 360.0  # Toward SE (125°)

        return {
            "is_demo": True,
            "demo_reason": reason,
            "location_name": location_name,
            "latitude": lat,
            "longitude": lon,
            "observation_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST") + " (Simulated)",
            "is_stale": False,
            "age_hours": 0.0,
            "condition": "Dry & Sunny (Typical Fire Season)",
            "temperature_c": 39.4,
            "temp_min_c": 28.5,
            "temp_max_c": 41.2,
            "humidity_pct": 22.0,
            "pressure_hpa": 1008.0,
            "wind_speed_ms": 5.2,
            "wind_speed_kmh": 18.7,
            "wind_gust_kmh": 28.4,
            "wind_deg_from": wind_from,
            "wind_deg_toward": wind_toward,
            "wind_cardinal": "NW",
            "cloud_cover_pct": 12.0,
            "rain_1h_mm": None,
            "rain_3h_mm": None,
            "visibility_m": 8000,
            "source": "Synthetic Meteorological Demonstration (OpenWeatherMap unauthenticated)"
        }

    @staticmethod
    def _degrees_to_cardinal(deg: float) -> str:
        """Converts meteorological degrees to 16-point cardinal compass string."""
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        ix = int((deg + 11.25) / 22.5) % 16
        return dirs[ix]
