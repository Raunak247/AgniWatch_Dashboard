"""
AgniWatch India - Land Cover & Vegetation Classification Service
Provides geographically aligned land-cover polygons across India and detailed forest reserves.
Follows Forest Survey of India (FSI) & Copernicus Global Land Cover classification standards.
Separates static land cover from dynamic vegetation condition (NDVI, NDMI, NBR).
"""

from typing import Dict, Any, List, Optional

# Supported Land Cover Classes with standard visualization hex colors
LAND_COVER_CLASSES = {
    "dense_forest": {
        "id": "dense_forest",
        "name": "Dense Forest",
        "color": "#15803d",  # Dark green
        "description": "Very Dense & Moderately Dense Forest (Canopy Density > 40%)",
        "default_fuel": "Dense Teak & Bamboo Forest",
        "base_ndmi": 0.32,
        "base_ndvi": 0.76
    },
    "other_forest": {
        "id": "other_forest",
        "name": "Other Forest Cover",
        "color": "#4ade80",  # Medium green
        "description": "Open Forest & Mixed Woodland (Canopy Density 10–40%)",
        "default_fuel": "Moist Deciduous Mixed Woodland",
        "base_ndmi": 0.22,
        "base_ndvi": 0.58
    },
    "dry_forest": {
        "id": "dry_forest",
        "name": "Dry / Moisture-Stressed Forest",
        "color": "#a16207",  # Brown
        "description": "Desiccated Deciduous Forest with high leaf-litter accumulation (NDMI < 0.10)",
        "default_fuel": "Dry Teak & Bamboo Forest",
        "base_ndmi": 0.04,
        "base_ndvi": 0.44
    },
    "grassland": {
        "id": "grassland",
        "name": "Grassland & Savannah",
        "color": "#eab308",  # Yellow
        "description": "Tall perennial grasses, meadows, and savannah woodland with fine fuels",
        "default_fuel": "Grasslands & Savannah Woodland",
        "base_ndmi": 0.08,
        "base_ndvi": 0.35
    },
    "scrub": {
        "id": "scrub",
        "name": "Scrub & Shrubland",
        "color": "#ea580c",  # Orange-brown
        "description": "Dry thorny scrub, degraded forest edges, and coppice re-growth",
        "default_fuel": "Dry Thorn & Scrubland",
        "base_ndmi": 0.05,
        "base_ndvi": 0.28
    },
    "agriculture": {
        "id": "agriculture",
        "name": "Agricultural Land",
        "color": "#d97706",  # Tan / Gold
        "description": "Cropland, fallow agricultural fields, and agro-forestry parcels",
        "default_fuel": "Light Agricultural Crop Residue",
        "base_ndmi": 0.12,
        "base_ndvi": 0.42
    },
    "bare_land": {
        "id": "bare_land",
        "name": "Bare Soil & Rocky Outcrops",
        "color": "#94a3b8",  # Grey
        "description": "Exposed bedrock, escarpments, river sandbanks, and fallow ground",
        "default_fuel": "Non-Burnable Mineral Soil",
        "base_ndmi": -0.05,
        "base_ndvi": 0.10
    },
    "built_up": {
        "id": "built_up",
        "name": "Built-up & Human Settlements",
        "color": "#475569",  # Dark neutral slate
        "description": "Forest fringe villages, ranger posts, tourism complexes, and roads",
        "default_fuel": "Urban / Structural Fuel",
        "base_ndmi": -0.10,
        "base_ndvi": 0.12
    },
    "water": {
        "id": "water",
        "name": "Water Bodies",
        "color": "#0284c7",  # Blue
        "description": "Perennial lakes, reservoir impoundments, perennial rivers, and tanks",
        "default_fuel": "Non-Burnable Water Barrier",
        "base_ndmi": 0.70,
        "base_ndvi": -0.20
    }
}

# Supported Indian Regions for Wildfire Intelligence
SUPPORTED_REGIONS = {
    "tadoba": {
        "id": "tadoba",
        "name": "Tadoba-Andhari Tiger Reserve (Maharashtra)",
        "short_name": "Tadoba (MH)",
        "state": "Maharashtra",
        "center": [20.21, 79.30],
        "zoom": 11,
        "bbox": [79.15, 20.05, 79.55, 20.45],
        "description": "Dry deciduous teak, dense bamboo brakes, and tiger core habitat in Chandrapur district.",
        "area_sqkm": 1727.6,
        "baseline_ndmi": 0.06,
        "baseline_ndvi": 0.48
    },
    "bandhavgarh": {
        "id": "bandhavgarh",
        "name": "Bandhavgarh Tiger Reserve (Madhya Pradesh)",
        "short_name": "Bandhavgarh (MP)",
        "state": "Madhya Pradesh",
        "center": [23.70, 81.03],
        "zoom": 11,
        "bbox": [80.85, 23.55, 81.25, 23.85],
        "description": "Sal and mixed deciduous forest, steep sandstone hill ranges, and Charno meadows.",
        "area_sqkm": 1536.0,
        "baseline_ndmi": 0.11,
        "baseline_ndvi": 0.54
    },
    "corbett": {
        "id": "corbett",
        "name": "Jim Corbett National Park (Uttarakhand)",
        "short_name": "Jim Corbett (UK)",
        "state": "Uttarakhand",
        "center": [29.53, 78.77],
        "zoom": 11,
        "bbox": [78.60, 29.40, 79.05, 29.70],
        "description": "Sub-Himalayan belt, moist sal forest, Ramganga river valley, and chaurs grasslands.",
        "area_sqkm": 1288.3,
        "baseline_ndmi": 0.18,
        "baseline_ndvi": 0.62
    },
    "similipal": {
        "id": "similipal",
        "name": "Similipal Tiger Reserve (Odisha)",
        "short_name": "Similipal (OD)",
        "state": "Odisha",
        "center": [21.85, 86.35],
        "zoom": 11,
        "bbox": [86.15, 21.60, 86.60, 22.10],
        "description": "Vast undulating plateau, dense semi-evergreen and moist deciduous sal forest.",
        "area_sqkm": 2750.0,
        "baseline_ndmi": 0.22,
        "baseline_ndvi": 0.65
    },
    "kaziranga": {
        "id": "kaziranga",
        "name": "Kaziranga National Park (Assam)",
        "short_name": "Kaziranga (AS)",
        "state": "Assam",
        "center": [26.58, 93.17],
        "zoom": 11,
        "bbox": [92.95, 26.45, 93.45, 26.75],
        "description": "Brahmaputra alluvial floodplain, tall elephant grass, and wetland beels.",
        "area_sqkm": 884.0,
        "baseline_ndmi": 0.38,
        "baseline_ndvi": 0.71
    },
    "western_ghats": {
        "id": "western_ghats",
        "name": "Western Ghats - Wayanad / Nilgiris Belt",
        "short_name": "Western Ghats",
        "state": "Kerala / Karnataka / Tamil Nadu",
        "center": [11.68, 76.13],
        "zoom": 10,
        "bbox": [75.80, 11.40, 76.50, 12.00],
        "description": "Montane evergreen rainforests, moist deciduous slopes, and shola grassland complex.",
        "area_sqkm": 3400.0,
        "baseline_ndmi": 0.34,
        "baseline_ndvi": 0.74
    },
    "all_india": {
        "id": "all_india",
        "name": "All-India National Wildfire Overview",
        "short_name": "All-India Overview",
        "state": "National Overview",
        "center": [22.50, 79.50],
        "zoom": 5,
        "bbox": [68.00, 8.00, 97.00, 36.00],
        "description": "National multi-sensor synoptic overview across major Indian forest and bioclimatic zones.",
        "area_sqkm": 3287263.0,
        "baseline_ndmi": 0.14,
        "baseline_ndvi": 0.52
    }
}


def _create_feature(feature_id: str, name: str, class_id: str, coords: List[List[float]], props: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to structure clean GeoJSON features."""
    class_meta = LAND_COVER_CLASSES[class_id]
    properties = {
        "id": feature_id,
        "name": name,
        "class_id": class_id,
        "class_name": class_meta["name"],
        "color": class_meta["color"],
        "description": class_meta["description"],
        "default_fuel": class_meta["default_fuel"],
        "base_ndmi": class_meta["base_ndmi"],
        "base_ndvi": class_meta["base_ndvi"],
        **props
    }
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    }


def get_landcover_features(region_id: str = "tadoba") -> List[Dict[str, Any]]:
    """Returns authoritative land-cover polygons for the selected region."""
    features = []

    if region_id == "tadoba":
        # 1. Tadoba Core Dense Teak & Bamboo Forest (Very Dense / Dense Canopy)
        features.append(_create_feature(
            "tadoba_core_dense",
            "Moharli-Tadoba Core Teak & Bamboo Canopy",
            "dense_forest",
            [
                [79.24, 20.18], [79.28, 20.26], [79.36, 20.30], [79.42, 20.28],
                [79.40, 20.19], [79.33, 20.15], [79.24, 20.18]
            ],
            {"area_sqkm": 184.2, "canopy_density_pct": 74, "dryness_status": "Moderately Hydrated", "ndmi": 0.28, "ndvi": 0.72}
        ))

        # 2. Chimur-Buffer Dry Deciduous Forest (Moisture-Stressed, High Fire Risk)
        features.append(_create_feature(
            "tadoba_chimur_dry_forest",
            "Chimur North Buffer Dry Deciduous Zone",
            "dry_forest",
            [
                [79.18, 20.32], [79.23, 20.42], [79.33, 20.44], [79.35, 20.35],
                [79.28, 20.30], [79.18, 20.32]
            ],
            {"area_sqkm": 132.8, "canopy_density_pct": 46, "dryness_status": "Severe Moisture Stress", "ndmi": 0.04, "ndvi": 0.42}
        ))

        # 3. Kolsa Southern Mixed Open Forest
        features.append(_create_feature(
            "tadoba_kolsa_other_forest",
            "Kolsa Range Mixed Open Woodland",
            "other_forest",
            [
                [79.34, 20.08], [79.38, 20.16], [79.48, 20.18], [79.52, 20.10],
                [79.45, 20.06], [79.34, 20.08]
            ],
            {"area_sqkm": 148.5, "canopy_density_pct": 32, "dryness_status": "Moderate Dryness", "ndmi": 0.16, "ndvi": 0.54}
        ))

        # 4. Erai Grassland Corridor & Meadow Clearing
        features.append(_create_feature(
            "tadoba_erai_grassland",
            "Erai Valley Perennial Meadow & Savannah",
            "grassland",
            [
                [79.20, 20.21], [79.24, 20.24], [79.25, 20.18], [79.21, 20.15],
                [79.20, 20.21]
            ],
            {"area_sqkm": 42.1, "canopy_density_pct": 12, "dryness_status": "Cured Grass Fine Fuel", "ndmi": 0.07, "ndvi": 0.36}
        ))

        # 5. Southern Scrub & Thorn Edges
        features.append(_create_feature(
            "tadoba_south_scrub",
            "Chandrapur Fringe Degraded Scrubland",
            "scrub",
            [
                [79.38, 20.04], [79.44, 20.08], [79.50, 20.06], [79.46, 20.02],
                [79.38, 20.04]
            ],
            {"area_sqkm": 36.4, "canopy_density_pct": 8, "dryness_status": "High Combustibility", "ndmi": 0.03, "ndvi": 0.25}
        ))

        # 6. Taluka Agricultural Fringe (Paddy & Cotton Fields)
        features.append(_create_feature(
            "tadoba_peripheral_agri",
            "Bhadravati-Chimur Agro-Ecosystem Fringe",
            "agriculture",
            [
                [79.14, 20.10], [79.18, 20.25], [79.16, 20.38], [79.12, 20.34],
                [79.11, 20.18], [79.14, 20.10]
            ],
            {"area_sqkm": 210.4, "canopy_density_pct": 4, "dryness_status": "Crop Residue Burn Season", "ndmi": 0.11, "ndvi": 0.40}
        ))

        # 7. Tadoba Lake & Erai Reservoir (Natural Firebreaks)
        features.append(_create_feature(
            "tadoba_lake_water",
            "Tadoba Lake & Erai Backwaters Barrier",
            "water",
            [
                [79.29, 20.22], [79.32, 20.25], [79.34, 20.23], [79.31, 20.20],
                [79.29, 20.22]
            ],
            {"area_sqkm": 18.6, "canopy_density_pct": 0, "dryness_status": "Non-Burnable Water Body", "ndmi": 0.74, "ndvi": -0.22}
        ))

        # 8. Human Settlements & Beat Headquarters (Moharli & Kolara Gates)
        features.append(_create_feature(
            "tadoba_settlements",
            "Moharli-Kolara Gate Infrastructure Zone",
            "built_up",
            [
                [79.31, 20.16], [79.33, 20.18], [79.35, 20.17], [79.33, 20.15],
                [79.31, 20.16]
            ],
            {"area_sqkm": 8.5, "canopy_density_pct": 5, "dryness_status": "Asset Protection Priority", "ndmi": -0.08, "ndvi": 0.14}
        ))

        # 9. Rocky Escarpment & Mineral Outcrop
        features.append(_create_feature(
            "tadoba_rocky_ridge",
            "Andhari Ridge Sandstone Escarpment",
            "bare_land",
            [
                [79.43, 20.24], [79.46, 20.26], [79.48, 20.22], [79.44, 20.21],
                [79.43, 20.24]
            ],
            {"area_sqkm": 14.2, "canopy_density_pct": 2, "dryness_status": "Thermal Radiant Rock Shelf", "ndmi": -0.04, "ndvi": 0.08}
        ))

    elif region_id == "bandhavgarh":
        # Bandhavgarh Core Sal Forest
        features.append(_create_feature(
            "bandhavgarh_sal_forest",
            "Tala-Magdhi Core Moist Sal Canopy",
            "dense_forest",
            [
                [80.95, 23.65], [81.04, 23.75], [81.15, 23.72], [81.12, 23.60],
                [80.95, 23.65]
            ],
            {"area_sqkm": 240.5, "canopy_density_pct": 78, "dryness_status": "Moist Sal Canopy", "ndmi": 0.29, "ndvi": 0.75}
        ))
        # Dry Mixed Forest Ridge
        features.append(_create_feature(
            "bandhavgarh_dry_ridge",
            "Khitauli North Dry Deciduous Ridge",
            "dry_forest",
            [
                [80.90, 23.72], [80.98, 23.82], [81.08, 23.80], [80.90, 23.72]
            ],
            {"area_sqkm": 110.2, "canopy_density_pct": 42, "dryness_status": "High Leaf Litter", "ndmi": 0.06, "ndvi": 0.45}
        ))
        # Charno Grasslands
        features.append(_create_feature(
            "bandhavgarh_charno_grass",
            "Charno Valley Meadows",
            "grassland",
            [
                [81.02, 23.67], [81.06, 23.70], [81.08, 23.66], [81.02, 23.67]
            ],
            {"area_sqkm": 35.8, "canopy_density_pct": 10, "dryness_status": "Dry Meadow Grass", "ndmi": 0.08, "ndvi": 0.38}
        ))
        # Charanganga River Stream
        features.append(_create_feature(
            "bandhavgarh_water",
            "Charanganga River Basin Barrier",
            "water",
            [
                [81.00, 23.66], [81.04, 23.72], [81.05, 23.71], [81.00, 23.66]
            ],
            {"area_sqkm": 12.4, "canopy_density_pct": 0, "dryness_status": "Perennial River", "ndmi": 0.65, "ndvi": -0.18}
        ))

    elif region_id == "corbett":
        # Dhikala Sal Forest
        features.append(_create_feature(
            "corbett_sal_canopy",
            "Dhikala Foothill Sal Canopy",
            "dense_forest",
            [
                [78.70, 29.50], [78.82, 29.62], [78.95, 29.58], [78.85, 29.45],
                [78.70, 29.50]
            ],
            {"area_sqkm": 310.0, "canopy_density_pct": 82, "dryness_status": "Sub-Himalayan Sal", "ndmi": 0.31, "ndvi": 0.77}
        ))
        # Chaurs Grasslands
        features.append(_create_feature(
            "corbett_chaurs_grass",
            "Ramganga Chaurs Grassland Corridor",
            "grassland",
            [
                [78.74, 29.52], [78.80, 29.56], [78.83, 29.51], [78.74, 29.52]
            ],
            {"area_sqkm": 48.0, "canopy_density_pct": 14, "dryness_status": "Riverine Chaurs", "ndmi": 0.12, "ndvi": 0.44}
        ))
        # Ramganga Reservoir
        features.append(_create_feature(
            "corbett_ramganga_water",
            "Ramganga Lake Reservoir",
            "water",
            [
                [78.72, 29.55], [78.78, 29.60], [78.82, 29.57], [78.75, 29.53],
                [78.72, 29.55]
            ],
            {"area_sqkm": 38.5, "canopy_density_pct": 0, "dryness_status": "Major Water Body Barrier", "ndmi": 0.78, "ndvi": -0.25}
        ))

    elif region_id == "similipal":
        # Similipal Dense Moist Forest
        features.append(_create_feature(
            "similipal_core_forest",
            "Central Similipal Dense Semi-Evergreen",
            "dense_forest",
            [
                [86.25, 21.75], [86.35, 21.95], [86.52, 21.92], [86.48, 21.70],
                [86.25, 21.75]
            ],
            {"area_sqkm": 540.0, "canopy_density_pct": 84, "dryness_status": "Moist Plateau Forest", "ndmi": 0.35, "ndvi": 0.79}
        ))
        # Dry Peripheral Sal
        features.append(_create_feature(
            "similipal_dry_fringe",
            "Baripada Fringe Dry Deciduous Slope",
            "dry_forest",
            [
                [86.45, 21.65], [86.55, 21.80], [86.58, 21.72], [86.45, 21.65]
            ],
            {"area_sqkm": 160.0, "canopy_density_pct": 48, "dryness_status": "Elevated Fire Susceptibility", "ndmi": 0.08, "ndvi": 0.49}
        ))

    elif region_id == "kaziranga":
        # Kaziranga Tall Grasslands
        features.append(_create_feature(
            "kaziranga_elephant_grass",
            "Central Alluvial Tall Elephant Grass",
            "grassland",
            [
                [93.05, 26.54], [93.20, 26.62], [93.35, 26.58], [93.18, 26.50],
                [93.05, 26.54]
            ],
            {"area_sqkm": 320.0, "canopy_density_pct": 18, "dryness_status": "Post-Monsoon Dried Cane", "ndmi": 0.22, "ndvi": 0.58}
        ))
        # Brahmaputra River & Wet Beels
        features.append(_create_feature(
            "kaziranga_water_beels",
            "Brahmaputra Channel & Wet Beels",
            "water",
            [
                [93.00, 26.62], [93.30, 26.72], [93.42, 26.66], [93.15, 26.58],
                [93.00, 26.62]
            ],
            {"area_sqkm": 190.0, "canopy_density_pct": 0, "dryness_status": "Wetland Flood Barrier", "ndmi": 0.82, "ndvi": -0.28}
        ))

    elif region_id == "western_ghats":
        # Evergreen Wet Canopy
        features.append(_create_feature(
            "wg_evergreen_canopy",
            "Wayanad-Nilgiris Montane Evergreen",
            "dense_forest",
            [
                [76.00, 11.55], [76.15, 11.85], [76.40, 11.80], [76.32, 11.50],
                [76.00, 11.55]
            ],
            {"area_sqkm": 680.0, "canopy_density_pct": 88, "dryness_status": "Moist Evergreen Canopy", "ndmi": 0.42, "ndvi": 0.82}
        ))
        # Shola Grasslands
        features.append(_create_feature(
            "wg_shola_grass",
            "High Altitude Shola Grasslands",
            "grassland",
            [
                [76.25, 11.68], [76.35, 11.75], [76.38, 11.65], [76.25, 11.68]
            ],
            {"area_sqkm": 72.0, "canopy_density_pct": 12, "dryness_status": "Dry Winter Grasses", "ndmi": 0.14, "ndvi": 0.46}
        ))

    elif region_id == "all_india":
        # National Overview Belts
        # 1. Western Ghats Belt
        features.append(_create_feature(
            "india_western_ghats_forest",
            "Western Ghats Montane Forest Arc",
            "dense_forest",
            [
                [73.5, 10.0], [74.0, 15.0], [74.5, 18.0], [75.2, 15.5], [76.5, 11.0], [75.5, 9.5], [73.5, 10.0]
            ],
            {"area_sqkm": 160000.0, "canopy_density_pct": 80, "dryness_status": "Humid / Moist", "ndmi": 0.36, "ndvi": 0.78}
        ))
        # 2. Central Indian Deciduous Belt (High Wildfire Susceptibility)
        features.append(_create_feature(
            "india_central_dry_forest",
            "Central Indian Dry Deciduous Belt (Satpura-Vindhya-Tadoba)",
            "dry_forest",
            [
                [77.0, 21.0], [78.5, 23.5], [82.5, 23.8], [84.0, 21.5], [81.0, 19.5], [78.0, 20.0], [77.0, 21.0]
            ],
            {"area_sqkm": 320000.0, "canopy_density_pct": 52, "dryness_status": "Peak Summer Desiccation Zone", "ndmi": 0.07, "ndvi": 0.48}
        ))
        # 3. Himalayan Sub-Alpine & Terai Arc
        features.append(_create_feature(
            "india_himalayan_sal_forest",
            "Himalayan Sal & Pine Forest Corridor",
            "dense_forest",
            [
                [76.0, 31.5], [79.0, 29.8], [84.0, 27.5], [88.5, 26.8], [88.0, 27.8], [80.5, 30.5], [76.0, 31.5]
            ],
            {"area_sqkm": 180000.0, "canopy_density_pct": 72, "dryness_status": "Seasonal Pine Needle Dryness", "ndmi": 0.24, "ndvi": 0.68}
        ))
        # 4. Deccan & Thar Scrubland
        features.append(_create_feature(
            "india_deccan_scrub",
            "Deccan Plateau & Semi-Arid Scrub Belt",
            "scrub",
            [
                [72.0, 24.0], [75.0, 26.0], [77.5, 24.5], [76.0, 18.0], [74.0, 17.0], [72.0, 24.0]
            ],
            {"area_sqkm": 420000.0, "canopy_density_pct": 14, "dryness_status": "Low Moisture Arid Scrub", "ndmi": 0.03, "ndvi": 0.26}
        ))
        # 5. Indo-Gangetic Agricultural Plains
        features.append(_create_feature(
            "india_gangetic_agri",
            "Indo-Gangetic Fertile Cropland Belt",
            "agriculture",
            [
                [75.0, 29.5], [80.0, 28.0], [86.0, 25.5], [88.0, 23.5], [83.0, 24.5], [77.0, 27.5], [75.0, 29.5]
            ],
            {"area_sqkm": 580000.0, "canopy_density_pct": 6, "dryness_status": "Agricultural Cycles", "ndmi": 0.14, "ndvi": 0.48}
        ))
        # 6. Terai & Banni Savannah Grasslands
        features.append(_create_feature(
            "india_savannah_grass",
            "Terai & Deccan Grassland Savannas",
            "grassland",
            [
                [69.0, 23.5], [71.5, 24.2], [72.0, 23.2], [69.5, 22.8], [69.0, 23.5]
            ],
            {"area_sqkm": 85000.0, "canopy_density_pct": 10, "dryness_status": "Cured Grass Beds", "ndmi": 0.06, "ndvi": 0.32}
        ))
        # 7. Major River Basins (Ganga, Godavari, Brahmaputra)
        features.append(_create_feature(
            "india_major_water_basins",
            "Major River Basins & Coastal Backwaters",
            "water",
            [
                [88.0, 22.0], [89.5, 23.0], [90.5, 22.2], [88.8, 21.5], [88.0, 22.0]
            ],
            {"area_sqkm": 45000.0, "canopy_density_pct": 0, "dryness_status": "Perennial Water", "ndmi": 0.85, "ndvi": -0.30}
        ))

    return features


def filter_landcover(
    region_id: str = "tadoba",
    selected_classes: Optional[List[str]] = None,
    ndmi_dryness_threshold: float = 0.10
) -> Dict[str, Any]:
    """
    Filters land cover based on selected class identifiers.
    Implements dynamic separation between land-cover class and dryness condition.
    """
    all_features = get_landcover_features(region_id)
    region_info = SUPPORTED_REGIONS.get(region_id, SUPPORTED_REGIONS["tadoba"])

    if not selected_classes:
        # Empty filter state
        filtered = []
    else:
        filtered = []
        for feat in all_features:
            c_id = feat["properties"]["class_id"]
            
            # Special dynamic logic: if user specifically asked for dry_forest, check NDMI threshold
            if c_id == "dry_forest":
                feat_ndmi = feat["properties"].get("ndmi", 0.05)
                if "dry_forest" in selected_classes and feat_ndmi <= ndmi_dryness_threshold:
                    filtered.append(feat)
            elif c_id in selected_classes:
                filtered.append(feat)

    # Compute area statistics for active visible classes
    stats = {}
    total_visible_sqkm = 0.0
    for feat in filtered:
        c_name = feat["properties"]["class_name"]
        area = feat["properties"].get("area_sqkm", 0.0)
        stats[c_name] = stats.get(c_name, 0.0) + area
        total_visible_sqkm += area

    return {
        "type": "FeatureCollection",
        "region": region_info,
        "selected_classes": selected_classes or [],
        "total_features": len(filtered),
        "total_visible_area_sqkm": round(total_visible_sqkm, 1),
        "class_breakdown": {k: round(v, 1) for k, v in stats.items()},
        "features": filtered
    }
