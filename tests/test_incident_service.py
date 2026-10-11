"""
Unit tests for AgniWatch India Incident Management Service
Validates incident synchronization, status updates, and audit logging.
"""

import pytest
import pandas as pd
from services.incident_service import IncidentManager


def test_incident_sync_and_status_update():
    mgr = IncidentManager()
    
    mock_df = pd.DataFrame([{
        "latitude": 20.215,
        "longitude": 79.312,
        "acq_datetime_ist": "2026-03-25 14:30:00 IST",
        "frp": 48.5,
        "confidence_label": "High",
        "satellite": "VIIRS (NOAA-20)",
        "brightness": 352.0,
        "daynight": "D"
    }])
    
    mgr.sync_from_firms_dataframe(mock_df)
    incidents = mgr.get_incidents_dataframe()
    
    assert len(incidents) == 1
    inc_id = incidents.iloc[0]["incident_id"]
    assert incidents.iloc[0]["priority"] == "High"
    assert incidents.iloc[0]["review_status"] == "Unreviewed"

    # Update verification status
    updated = mgr.update_incident_status(
        incident_id=inc_id,
        new_status="Confirmed Wildfire",
        officer_name="Beat Guard R. Sharma",
        notes="Active ground fire confirmed in teak compartment 14."
    )
    assert updated is True
    
    updated_inc = mgr.incidents[inc_id]
    assert updated_inc["review_status"] == "Confirmed Wildfire"
    assert updated_inc["verified_by"] == "Beat Guard R. Sharma"

    csv_data = mgr.export_incidents_csv()
    assert "Confirmed Wildfire" in csv_data
