"""
Unit tests for Land Cover & Dynamic Vegetation Classification Service
"""

import pytest
from services.landcover import (
    SUPPORTED_REGIONS,
    LAND_COVER_CLASSES,
    get_landcover_features,
    filter_landcover
)


def test_supported_regions_structure():
    assert "tadoba" in SUPPORTED_REGIONS
    assert "all_india" in SUPPORTED_REGIONS
    tadoba = SUPPORTED_REGIONS["tadoba"]
    assert len(tadoba["center"]) == 2
    assert len(tadoba["bbox"]) == 4
    assert tadoba["area_sqkm"] > 0


def test_landcover_classes_definitions():
    expected_classes = [
        "dense_forest", "other_forest", "dry_forest", "grassland",
        "scrub", "agriculture", "bare_land", "built_up", "water"
    ]
    for c in expected_classes:
        assert c in LAND_COVER_CLASSES
        assert LAND_COVER_CLASSES[c]["color"].startswith("#")
        assert "name" in LAND_COVER_CLASSES[c]


def test_get_landcover_features_tadoba():
    features = get_landcover_features("tadoba")
    assert len(features) >= 7
    class_ids = [f["properties"]["class_id"] for f in features]
    assert "dense_forest" in class_ids
    assert "dry_forest" in class_ids
    assert "water" in class_ids


def test_filter_landcover_dynamic_selection():
    # 1. Filter only water
    res_water = filter_landcover("tadoba", selected_classes=["water"])
    assert res_water["total_features"] >= 1
    for f in res_water["features"]:
        assert f["properties"]["class_id"] == "water"

    # 2. Filter forest and grassland
    res_multi = filter_landcover("tadoba", selected_classes=["dense_forest", "grassland"])
    for f in res_multi["features"]:
        assert f["properties"]["class_id"] in ["dense_forest", "grassland"]

    # 3. Clear all produces intentional empty state
    res_empty = filter_landcover("tadoba", selected_classes=[])
    assert res_empty["total_features"] == 0
    assert len(res_empty["features"]) == 0


def test_dry_forest_condition_separation():
    # Dry forest should only be included if NDMI <= threshold
    res_strict = filter_landcover("tadoba", selected_classes=["dry_forest"], ndmi_dryness_threshold=0.01)
    # If threshold is very low, fewer or zero dry forest features pass
    res_lenient = filter_landcover("tadoba", selected_classes=["dry_forest"], ndmi_dryness_threshold=0.15)
    assert len(res_lenient["features"]) >= len(res_strict["features"])
