# 🔌 AgniWatch India — Integration & External Machine Deployment Guide

This package is completely self-contained, pre-configured with active API credentials in `.env`, and ready to run on any machine or integrate into any React / Next.js / Web platform.

---

## 🚀 Part 1: Running on Any Person's Machine (Zero Setup Friction)

### Prerequisites
* **Python 3.10+** (Required)
* **Node.js 18+** (Optional — only needed for live frontend modification; the production web app is already pre-compiled in `frontend/dist/`!)

### Quick 2-Step Launch:
1. **Step 1:** Double-click `setup.bat`  
   *(Installs all Python and NPM packages automatically).*
2. **Step 2:** Double-click `start.bat`  
   *(Launches the backend, launches the frontend, and opens `http://localhost:5173` automatically).*

### Or Run via Terminal:
```bash
# Terminal 1: Backend
pip install -r requirements.txt
python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: Frontend (Live Dev)
cd frontend
npm install
npm run dev
```

---

## 🔑 Part 2: API Credentials

Configure your own API credentials in a local `.env` file. Do not commit real credentials:

```env
NASA_FIRMS_MAP_KEY=your_nasa_firms_map_key
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
EARTH_ENGINE_PROJECT=your_google_cloud_project_id
```

* Provide keys through local environment configuration or the deployment platform's secret manager.
* Never commit real keys to source control.

---

## 🧩 Part 3: How to Integrate into Another Website / Project

### Option A: Iframe / Microfrontend Route (Fastest — 1 Minute)
Drop this directly into any React / Vue / HTML project:

```jsx
// WildfireDashboard.jsx
import React from 'react';

export default function WildfireDashboard() {
  return (
    <div style={{ width: '100%', height: '100vh', background: '#020617' }}>
      <iframe
        src="http://localhost:5173"
        title="AgniWatch India Wildfire Intelligence"
        style={{ width: '100%', height: '100%', border: 'none' }}
      />
    </div>
  );
}
```

---

### Option B: Native React Component Integration
To import the GIS Tactical Map directly into your existing project (e.g. `Thermotwin_By_Team_Wavenex`):

1. Copy `frontend/src/components/MapComponent.tsx` into your project's `components/` directory.
2. Install Leaflet:
   ```bash
   npm install leaflet @types/leaflet
   ```
3. Use the component in your React code:
   ```tsx
   import { MapComponent } from './components/MapComponent';

   <MapComponent
     center={[20.21, 79.30]}
     zoom={11}
     hotspots={hotspotsList}
     weather={weatherData}
     riskCells={riskGrid}
     simulationResult={simData}
     selectedStep={1}
     landcoverFeatures={landcoverFeatures}
     landcoverOpacity={0.55}
     activeLayers={{
       satellite: true,
       labels: true,
       landcover: true,
       hotspots: true,
       riskGrid: true,
       weather: true,
       simulation: true,
       assets: true
     }}
   />
   ```

---

### Option C: Pure Python Single-Port Mode (No Node.js Required!)
Because `frontend/dist/` is pre-compiled, the FastAPI backend in `api.py` automatically mounts the production frontend at the root:

```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000/`** — both the React Dashboard and the REST API run simultaneously from a single Python port!
