"""
AgniWatch India - Incident Management & Verification Service
Tracks satellite hotspot detections through the full operational lifecycle:
Unreviewed -> Under Review -> Confirmed Wildfire / False Alarm -> Resolved.
Provides audit history, beat-level notes, and verified incident exports.
"""

import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


class IncidentManager:
    """Manages active fire incident records, verification workflow, and review logs."""

    VALID_STATUSES = [
        "Unreviewed",
        "Under Review",
        "Confirmed Wildfire",
        "False Alarm / Agricultural",
        "Resolved / Extinguished"
    ]

    def __init__(self):
        # In-memory incident registry
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def sync_from_firms_dataframe(self, df_hotspots: pd.DataFrame):
        """
        Populates or updates the incident registry from newly retrieved FIRMS detections.
        Preserves existing human review notes and status updates.
        """
        if df_hotspots.empty:
            return

        for idx, row in df_hotspots.iterrows():
            lat = round(float(row["latitude"]), 4)
            lon = round(float(row["longitude"]), 4)
            acq_dt = str(row.get("acq_datetime_ist", "N/A"))
            frp = float(row.get("frp", 10.0) or 10.0)
            conf = str(row.get("confidence_label", "Nominal"))
            sensor = str(row.get("satellite", "VIIRS"))

            # Deterministic incident ID based on location and time
            dt_tag = acq_dt.replace(" ", "T").replace(":", "").replace("-", "")[:13]
            inc_id = f"INC-{lat:.3f}N-{lon:.3f}E-{dt_tag}"

            if inc_id not in self.incidents:
                # Priority scoring based on FRP and Confidence
                base_priority = "High" if (frp >= 35.0 or conf == "High") else ("Medium" if frp >= 15.0 else "Low")

                self.incidents[inc_id] = {
                    "incident_id": inc_id,
                    "latitude": lat,
                    "longitude": lon,
                    "observation_time_ist": acq_dt,
                    "sensor": sensor,
                    "brightness_k": float(row.get("brightness", 330.0) or 330.0),
                    "frp_mw": frp,
                    "confidence": conf,
                    "daynight": str(row.get("daynight", "D")),
                    "review_status": "Unreviewed",
                    "priority": base_priority,
                    "verified_by": None,
                    "review_timestamp": None,
                    "beat_notes": "Pending ground reconnaissance by forest beat staff.",
                    "data_classification": "OBSERVED (Pending Verification)"
                }

    def update_incident_status(
        self,
        incident_id: str,
        new_status: str,
        officer_name: str,
        notes: str
    ) -> bool:
        """Updates the verification status and attaches reviewer audit logs."""
        if incident_id not in self.incidents or new_status not in self.VALID_STATUSES:
            return False

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        self.incidents[incident_id]["review_status"] = new_status
        self.incidents[incident_id]["verified_by"] = officer_name
        self.incidents[incident_id]["review_timestamp"] = now_str
        self.incidents[incident_id]["beat_notes"] = notes
        return True

    def get_incidents_dataframe(self) -> pd.DataFrame:
        """Returns all incidents as a structured Pandas DataFrame."""
        if not self.incidents:
            return pd.DataFrame()
        return pd.DataFrame(list(self.incidents.values()))

    def export_incidents_csv(self) -> str:
        """Exports the incidents registry with full verification history to CSV string."""
        df = self.get_incidents_dataframe()
        if df.empty:
            return "incident_id,latitude,longitude,observation_time_ist,frp_mw,confidence,review_status,verified_by,beat_notes\n"
        return df.to_csv(index=False)
