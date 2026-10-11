"""
AgniWatch India - NASA FIRMS Active Fire / Hotspot Integration Service
Retrieves, parses, and validates thermal anomaly detections from NASA FIRMS Area CSV API.
Gracefully falls back to high-fidelity simulated detections if API credentials are not provided.
"""

import io
import time
import datetime
from typing import Dict, Any, List, Optional, Tuple
import requests
import pandas as pd
import numpy as np


# Standard NASA FIRMS CSV columns expected
EXPECTED_COLUMNS = [
    "latitude", "longitude", "brightness", "scan", "track", 
    "acq_date", "acq_time", "satellite", "instrument", 
    "confidence", "version", "bright_t31", "frp", "daynight"
]

class FirmsClient:
    """Client for querying NASA FIRMS Near Real-Time Active Fire CSV API."""

    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    def __init__(self, map_key: Optional[str] = None):
        self.map_key = (map_key or "").strip()

    def is_configured(self) -> bool:
        """Checks if a non-placeholder MAP_KEY is set."""
        return bool(self.map_key and self.map_key != "your_nasa_firms_map_key_here")

    def fetch_hotspots(
        self,
        bbox: List[float],
        source: str = "VIIRS_NOAA20_NRT",
        day_range: int = 3,
        timeout: int = 15
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Fetches hotspots within a bounding box from NASA FIRMS Area API.
        
        Args:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            source: Satellite source (e.g., VIIRS_NOAA20_NRT, MODIS_NRT)
            day_range: Integer lookback in days (1 to 10)
            timeout: HTTP request timeout in seconds
            
        Returns:
            Tuple[pd.DataFrame, Dict[str, Any]]: (Hotspots DataFrame, metadata dict)
        """
        # Validate day_range
        day_range = max(1, min(10, int(day_range)))

        # Format area parameter: min_lon,min_lat,max_lon,max_lat
        min_lon, min_lat, max_lon, max_lat = [round(float(c), 4) for c in bbox]
        area_str = f"{min_lon},{min_lat},{max_lon},{max_lat}"

        metadata = {
            "source": source,
            "bbox": [min_lon, min_lat, max_lon, max_lat],
            "day_range": day_range,
            "retrieval_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "is_demo": False,
            "error": None,
            "total_detections": 0,
            "status": "UNCONFIGURED"
        }

        # If key is missing, return demo data
        if not self.is_configured():
            metadata["is_demo"] = True
            metadata["status"] = "DEMO_FALLBACK (No NASA_FIRMS_MAP_KEY configured)"
            df_demo = self._generate_demo_detections(bbox, source, day_range)
            metadata["total_detections"] = len(df_demo)
            return df_demo, metadata

        # Construct request URL
        url = f"{self.BASE_URL}/{self.map_key}/{source}/{area_str}/{day_range}"
        
        try:
            headers = {"User-Agent": "AgniWatch-India/1.0 (Wildfire-Monitoring-Research)"}
            response = requests.get(url, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                raw_text = response.text.strip()
                
                # Check if API returned an error message in text body
                if "Invalid MAP_KEY" in raw_text or "Error" in raw_text and len(raw_text) < 200:
                    metadata["is_demo"] = True
                    metadata["error"] = f"FIRMS API Error: {raw_text}"
                    metadata["status"] = "API_ERROR_FALLBACK"
                    df_demo = self._generate_demo_detections(bbox, source, day_range)
                    metadata["total_detections"] = len(df_demo)
                    return df_demo, metadata
                
                # Empty CSV or header-only response
                if not raw_text or len(raw_text.splitlines()) <= 1:
                    metadata["status"] = "LIVE_SUCCESS (Zero Hotspots Detected)"
                    return self._empty_dataframe(), metadata
                
                # Parse CSV
                df = pd.read_csv(io.StringIO(raw_text))
                df = self._standardize_and_clean_dataframe(df, source)
                metadata["status"] = "LIVE_SUCCESS"
                metadata["total_detections"] = len(df)
                return df, metadata

            elif response.status_code == 403:
                metadata["is_demo"] = True
                metadata["error"] = "HTTP 403: Forbidden - Invalid or expired NASA FIRMS MAP_KEY"
                metadata["status"] = "AUTH_FAILED_FALLBACK"
                df_demo = self._generate_demo_detections(bbox, source, day_range)
                metadata["total_detections"] = len(df_demo)
                return df_demo, metadata

            elif response.status_code == 429:
                metadata["is_demo"] = True
                metadata["error"] = "HTTP 429: NASA FIRMS Rate limit reached. Using fallback demo."
                metadata["status"] = "RATE_LIMIT_FALLBACK"
                df_demo = self._generate_demo_detections(bbox, source, day_range)
                metadata["total_detections"] = len(df_demo)
                return df_demo, metadata

            else:
                metadata["is_demo"] = True
                metadata["error"] = f"HTTP {response.status_code}: {response.reason}"
                metadata["status"] = "HTTP_ERROR_FALLBACK"
                df_demo = self._generate_demo_detections(bbox, source, day_range)
                metadata["total_detections"] = len(df_demo)
                return df_demo, metadata

        except requests.exceptions.RequestException as e:
            metadata["is_demo"] = True
            metadata["error"] = f"Network Connection Error: {str(e)}"
            metadata["status"] = "NETWORK_ERROR_FALLBACK"
            df_demo = self._generate_demo_detections(bbox, source, day_range)
            metadata["total_detections"] = len(df_demo)
            return df_demo, metadata

    def _empty_dataframe(self) -> pd.DataFrame:
        """Returns empty DataFrame with standard columns."""
        df = pd.DataFrame(columns=EXPECTED_COLUMNS + ["acq_datetime_utc", "acq_datetime_ist", "confidence_label"])
        return df

    def _standardize_and_clean_dataframe(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Cleans, type-casts, and enriches FIRMS DataFrame."""
        if df.empty:
            return self._empty_dataframe()

        # Lowercase column names
        df.columns = [c.strip().lower() for c in df.columns]

        # Numeric conversions
        for col in ["latitude", "longitude", "brightness", "scan", "track", "frp"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "bright_t31" in df.columns:
            df["bright_t31"] = pd.to_numeric(df["bright_t31"], errors="coerce")
        else:
            df["bright_t31"] = np.nan

        # Handle acquisition date & time
        if "acq_date" in df.columns and "acq_time" in df.columns:
            # acq_time is often int like 430 or 1520 -> format to HH:MM
            def format_time(t):
                try:
                    s = f"{int(t):04d}"
                    return f"{s[:2]}:{s[2:]}:00"
                except Exception:
                    return "00:00:00"

            time_strings = df["acq_time"].apply(format_time)
            dt_series = pd.to_datetime(
                df["acq_date"].astype(str) + " " + time_strings,
                errors="coerce",
                utc=True
            )
            df["acq_datetime_utc"] = dt_series
            # Indian Standard Time (UTC + 5:30)
            df["acq_datetime_ist"] = dt_series + pd.Timedelta(hours=5, minutes=30)
        else:
            df["acq_datetime_utc"] = pd.NaT
            df["acq_datetime_ist"] = pd.NaT

        # Standardize confidence label
        # VIIRS uses 'l' (low), 'n' (nominal), 'h' (high)
        # MODIS uses 0-100 numeric confidence
        def standardize_conf(row):
            conf = row.get("confidence")
            if pd.isna(conf):
                return "Unknown"
            conf_str = str(conf).strip().lower()
            if conf_str in ["h", "high"]:
                return "High"
            elif conf_str in ["n", "nominal"]:
                return "Nominal"
            elif conf_str in ["l", "low"]:
                return "Low"
            try:
                val = float(conf)
                if val >= 80:
                    return "High"
                elif val >= 50:
                    return "Nominal"
                else:
                    return "Low"
            except ValueError:
                return str(conf)

        df["confidence_label"] = df.apply(standardize_conf, axis=1)

        # Ensure satellite / instrument
        if "satellite" not in df.columns:
            df["satellite"] = "VIIRS/MODIS"
        if "instrument" not in df.columns:
            df["instrument"] = "VIIRS"

        # Explicit scientific warning column
        df["detection_status"] = "Satellite detection pending ground verification"

        return df

    def _generate_demo_detections(
        self,
        bbox: List[float],
        source: str,
        day_range: int
    ) -> pd.DataFrame:
        """
        Generates realistic demonstrative thermal anomaly detections for Tadoba/selected study area.
        Clearly marked as demonstrative data.
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Center coordinates
        c_lat = (min_lat + max_lat) / 2.0
        c_lon = (min_lon + max_lon) / 2.0
        lat_span = (max_lat - min_lat) * 0.5
        lon_span = (max_lon - min_lon) * 0.5

        np.random.seed(42)  # Deterministic seed for reproducible testing
        num_hotspots = 14

        lats = np.clip(c_lat + np.random.normal(0, lat_span * 0.35, num_hotspots), min_lat + 0.02, max_lat - 0.02)
        lons = np.clip(c_lon + np.random.normal(0, lon_span * 0.35, num_hotspots), min_lon + 0.02, max_lon - 0.02)
        
        # Brightness temp (Kelvin): typical fire hotspots range 310K - 380K
        brightness = np.round(np.random.uniform(315.0, 368.5, num_hotspots), 1)
        bright_t31 = np.round(brightness - np.random.uniform(15.0, 35.0, num_hotspots), 1)
        
        # Fire Radiative Power (MW): 5 - 120 MW
        frp = np.round(np.random.exponential(18.0, num_hotspots) + 4.5, 1)
        
        # Timestamps over recent days
        now = datetime.datetime.now(datetime.timezone.utc)
        acq_dates = []
        acq_times = []
        acq_utcs = []
        acq_ists = []
        
        for i in range(num_hotspots):
            hours_ago = np.random.uniform(2, day_range * 24)
            dt = now - datetime.timedelta(hours=hours_ago)
            acq_dates.append(dt.strftime("%Y-%m-%d"))
            acq_times.append(int(dt.strftime("%H%M")))
            acq_utcs.append(dt)
            acq_ists.append(dt + datetime.timedelta(hours=5, minutes=30))

        confidence_labels = np.random.choice(["High", "Nominal", "Low"], size=num_hotspots, p=[0.45, 0.45, 0.10])
        daynight = np.random.choice(["D", "N"], size=num_hotspots, p=[0.7, 0.3])

        df = pd.DataFrame({
            "latitude": lats,
            "longitude": lons,
            "brightness": brightness,
            "scan": [0.38] * num_hotspots,
            "track": [0.37] * num_hotspots,
            "acq_date": acq_dates,
            "acq_time": acq_times,
            "satellite": ["NOAA-20 (Simulated)" if "NOAA20" in source else "Suomi-NPP (Simulated)"] * num_hotspots,
            "instrument": ["VIIRS"] * num_hotspots,
            "confidence": confidence_labels,
            "version": ["2.0NRT-DEMO"] * num_hotspots,
            "bright_t31": bright_t31,
            "frp": frp,
            "daynight": daynight,
            "acq_datetime_utc": acq_utcs,
            "acq_datetime_ist": acq_ists,
            "confidence_label": confidence_labels,
            "detection_status": "DEMO SATELLITE DETECTION (Unverified)",
            "is_simulated": [True] * num_hotspots
        })

        return df
