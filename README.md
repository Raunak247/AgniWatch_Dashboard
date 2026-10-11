# 🇮🇳 AgniWatch India — Enterprise Wildfire Intelligence & Simulation Platform

**AgniWatch India** is a full-stack, enterprise-grade geospatial intelligence and wildfire decision-support platform engineered for Indian forest ecosystems, with **Tadoba–Andhari Tiger Reserve (Maharashtra)** configured as the default demonstration area.

The platform covers the complete operational wildfire lifecycle:  
**Observe → Detect → Verify → Assess Risk → Predict Scenarios → Prevent → Respond → Evaluate**

---

## 🌟 Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │    External Space & Weather Telemetry   │
                      │  • NASA FIRMS (VIIRS NOAA-20 / MODIS)  │
                      │  • OpenWeatherMap Micro-Climate API    │
                      │  • Sentinel-2 / Landsat NDVI Baselines │
                      └──────────────────┬─────────────────────┘
                                         │  (Server-Side API Ingestion)
                                         ▼
                      ┌────────────────────────────────────────┐
                      │      FastAPI Backend Engine (Port 8000)│
                      │  • Multi-Factor 2D Risk Matrix         │
                      │  • Rothermel-Huygens Spread Physics    │
                      │  • Beat Patrol Prevention Scoring      │
                      │  • Incident Triage & Verification Logs │
                      │  • Zero-Client Credential Resolution   │
                      └──────────────────┬─────────────────────┘
                                         │  REST API / CORS
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
┌──────────────────────────────────────┐   ┌──────────────────────────────────────┐
│ Vite + React 19 Frontend (Port 5173) │   │ Streamlit Operations UI (Port 8501)  │
│ • Tailwind CSS v4 Dark Theme         │   │ • Interactive Folium GIS Map         │
│ • Leaflet GIS (Esri Satellite & Dark)│   │ • Plotly Analytics Charts            │
│ • Recharts Telemetry Visualizations  │   │ • One-Click Markdown Situation Brief │
│ • 7-Section Mission Console          │   └──────────────────────────────────────┘
└──────────────────────────────────────┘
```

---

## 🔑 1. Administrator Server-Side API Security

* **Configured Once by the Admin:** Credentials are saved on the server in `.env` or Streamlit secrets.
* **Zero Client-Side Key Prompts:** All authorized users accessing the deployed React dashboard or Streamlit app automatically inherit live satellite and weather feeds **without entering any API keys**.
* **Zero Client Exposure:** Raw keys are never leaked to client bundles, browser network inspection, logs, or exported reports.
* **Automatic Fallbacks:** If an external API is temporarily unavailable, the system displays clean diagnostics without fabricating fake observations.

### Environment Configuration (`D:\agniwatch-india\.env`)
Set your own API credentials locally. Do not commit `.env` or real API keys.
```env
NASA_FIRMS_MAP_KEY=your_nasa_firms_map_key
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
EARTH_ENGINE_PROJECT=your_google_cloud_project_id
```

---

## 🖥️ 2. Core Functional Modules

### 1. 🛡️ Command Center
* **Live Telemetry KPIs:** Active thermal hotspots, new detections in lookback window, peak observed Fire Radiative Power (MW), ambient temperature, relative humidity, and canopy moisture indices.
* **Priority Incident Queue:** Thermal hotspots ranked by radiative intensity and proximity to core tiger breeding habitats, marked as *Pending Ground Verification*.
* **Prevention Guidance:** Real-time top beat-level mitigation actions tied directly to atmospheric dryness and fine fuel loads.
* **Telemetry Diagnostics:** Live status pills indicating sensor feed status and observation latency.

### 2. 🗺️ Tactical GIS Map
* **Dual Base Maps (100% Free, Zero Watermarks, No Map Keys Needed):**
  * **Esri World Imagery (Satellite):** High-resolution forest canopies, terrain elevation, and water bodies.
  * **Esri World Dark Canvas:** Clean, high-contrast dark GIS backdrop for night patrols and tactical command.
* **Interactive Overlays:**
  * **Thermal Hotspots:** Scaled by Fire Radiative Power (MW) and colored by confidence (High = Red, Nominal = Orange).
  * **Risk Grid Cells:** 2D cellular risk matrix computed from temperature, relative humidity, wind gusts, and fuel moisture deficit.
  * **Wind Propagation Vector:** Interactive propagation arrow oriented toward the direction **TOWARD** which the wind pushes embers ($\text{origin FROM} + 180^\circ$).
  * **Rothermel Spread Perimeters:** Concentric 1-hour, 2-hour, and 3-hour projected burn boundaries.
  * **Conservation Assets:** Tadoba-Andhari Tiger Reserve boundary polygons and ranger patrol beat centers.

### 3. 📊 Environmental Intelligence
* **Micro-Climate Telemetry:** Live temperature, relative humidity, wind speed, gust velocity, atmospheric pressure, and cloud cover.
* **10-Hour Equilibrium Dead Fuel Moisture:** Calculated via temperature-humidity deficit:
  $$m_f \approx \frac{RH}{100} \times \left(1 + \frac{30 - T}{50}\right)$$
* **FRP Energy Trajectory:** Historical and real-time Fire Radiative Power trends.

### 4. ⚡ Rothermel-Huygens Fire Simulation Lab
* **Physics-Based Spread Engine:**
  $$R_{\text{head}} = R_0 \times (1 + \phi_w + \phi_s) \times \text{fuel\_dryness\_factor}$$
  * $\phi_w = c \cdot U^B$: Wind multiplier based on midflame wind velocity.
  * $\phi_s = 5.275 \times (\tan \theta)^2$: Slope multiplier based on terrain inclination angle $\theta$.
  * Length-to-width ratio: $L/B = 1 + 0.125 \times U_{\text{km/h}}$.
* **Fuel Models Supported:**
  * *Dry Teak & Bamboo Forest* (High fuel bed depth)
  * *Grasslands & Savannah* (Fast-spreading light fuels)
  * *Dry Thorn & Scrub* (High heat output, moderate rate of spread)
  * *Moist Deciduous* (Slow ignition threshold)
  * *Non-Burnable Water/Rock* (Natural barrier)
* **Real-Time Simulation Controls:** Interactive sliders for duration (1h–6h), wind speed override, slope angle, and ignition coordinates with automated asset exposure detection.

### 5. 📋 Incident Triage & Beat Patrol Prevention
* **Incident Lifecycle:** Tracks satellite thermal detections through `Unreviewed` $\rightarrow$ `Under Review` $\rightarrow$ `Confirmed Wildfire` $\rightarrow$ `False Alarm` $\rightarrow$ `Resolved`.
* **Beat Patrol Guidance:** Generates priority patrol routes (e.g., *Moharli Core Sector*, *Kolsa Southern Buffer*), firebreak clearance tasks, and water bowser staging coordinates.
* **Export Engine:** Instant export of situation reports to **GeoJSON**, **CSV**, **JSON**, and printable situation briefs.

---

## 📁 3. Project Structure

```
D:\agniwatch-india\
├── api.py                      # FastAPI REST API exposing all telemetry & simulation models
├── app.py                      # Streamlit 5-section enterprise operations dashboard
├── config.py                   # Configuration, server-side credential resolution & presets
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation & setup guide
├── conftest.py                 # Pytest configuration
├── .env                        # Server-side API credentials (configured by Admin)
├── .env.example                # Local environment variables template
├── services/
│   ├── boundaries.py           # Reserve boundary GeoJSONs & custom area parser
│   ├── firms.py                # NASA FIRMS Area API client & CSV parser
│   ├── weather.py              # OpenWeatherMap client & wind vector orientation
│   ├── earth_engine.py         # Google Earth Engine Sentinel-2 & SMAP processor
│   ├── risk_model.py           # Heuristic multi-factor risk scoring engine
│   ├── simulation.py           # Rothermel-Huygens simulation & asset exposure
│   ├── prevention.py           # Pre-ignition prevention scoring & recommendations
│   ├── incident_service.py     # Incident lifecycle management & audit logging
│   └── export_service.py       # Executive briefings & CSV export service
├── components/
│   ├── map_view.py             # Folium GIS operations map
│   ├── metrics.py              # Header badges & KPI metric cards
│   └── charts.py               # Plotly charts (FRP, trends, fuel models)
├── frontend/                   # Modern Vite + React 19 Dashboard
│   ├── package.json            # React, Tailwind CSS v4, Leaflet, Recharts, Lucide
│   ├── vite.config.ts          # Vite configuration with automatic /api proxy
│   ├── index.html              # HTML entry point
│   ├── src/
│   │   ├── App.tsx             # 7-section mission console with live telemetry
│   │   ├── main.tsx            # React application mount
│   │   └── components/
│   │       └── MapComponent.tsx# High-performance Leaflet GIS map with Esri tiles
│   └── dist/                   # Production build assets
└── tests/
    ├── test_prevention.py      # Unit tests for prevention scoring & beat recommendations
    ├── test_incident_service.py# Unit tests for incident lifecycle & status updates
    ├── test_simulation.py      # Unit tests for Rothermel spread, fuels & assets
    ├── test_risk_model.py      # Unit tests for normalization, weights & rain suppression
    └── test_services.py        # Unit tests for FIRMS & weather client fallbacks
```

---

## 🚀 4. How to Run the Platform

### Terminal 1: Backend API (FastAPI)
```powershell
Set-Location -Path "D:\agniwatch-india"
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```
* **API Endpoint:** `http://localhost:8000`
* **Swagger API Documentation:** `http://localhost:8000/docs`

### Terminal 2: Frontend Dashboard (Vite + React)
```powershell
Set-Location -Path "D:\agniwatch-india\frontend"
npx vite --host 127.0.0.1 --port 5173
```
* **Web Application:** `http://localhost:5173`

### Terminal 3 (Optional): Streamlit Dashboard
```powershell
Set-Location -Path "D:\agniwatch-india"
streamlit run app.py --server.port 8501
```
* **Streamlit Application:** `http://localhost:8501`

---

## 🧪 5. Automated Verification & Testing

Execute the test suite at any time from PowerShell:
```powershell
Set-Location -Path "D:\agniwatch-india"
$env:PYTHONPATH="D:\agniwatch-india"
python -m pytest -v tests
```
*(All 19 unit tests execute with 100% pass rate covering risk scoring, Rothermel physics, asset exposure, incident triage, and API resilience).*

---

## 🔌 6. Integration with Other React Applications

To embed or integrate AgniWatch into an existing React project (e.g. `Thermotwin_By_Team_Wavenex`):

### Option A: Iframe / Microfrontend Route
```jsx
export default function WildfireView() {
  return (
    <iframe
      src="http://localhost:5173"
      title="AgniWatch India Wildfire Intelligence"
      className="w-full h-screen border-none"
    />
  );
}
```

### Option B: Native Component Import
1. Copy `D:\agniwatch-india\frontend\src\components\MapComponent.tsx` into your project's components folder.
2. Ensure `leaflet`, `@types/leaflet`, `lucide-react`, and `recharts` are installed.
3. Connect your component to the backend at `http://localhost:8000/api/*`.
