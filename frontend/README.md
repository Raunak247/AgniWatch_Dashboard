# AgniWatch India — Enterprise Wildfire Intelligence Dashboard (React + Vite)

A modern, high-performance geospatial command center built with **React 19**, **Vite**, **Tailwind CSS v4**, **Leaflet GIS**, and **Recharts**.

## 🌟 Key Features
- **Live NASA FIRMS Hotspot Telemetry**: Real-time thermal anomaly ingestion from VIIRS and MODIS with confidence thresholds and FRP (Fire Radiative Power) scaling.
- **Micro-climate Meteorological Tracking**: Live OpenWeatherMap data with wind vectors (converting meteorological "FROM" heading to propagation "TOWARD" bearing).
- **Rothermel Fire Spread Simulation Lab**: Physics-based elliptical fire front modeling taking into account slope, wind velocity, fuel moisture, and ignition duration.
- **Cellular Risk Intelligence Grid**: 2D geospatial matrix synthesizing weather severity, drought indices, fuel dryness, and detection density.
- **Triage & Beat Patrol Guidance**: Actionable patrol beats and early intervention protocols for forest rangers and district responders.
- **One-Click Intelligence Reports**: Export incident logs, risk summaries, and simulated perimeters to JSON / CSV / Print Briefs.

## 🚀 Running the Frontend
```bash
cd D:\agniwatch-india\frontend
npm run dev -- --host 0.0.0.0 --port 5173
```
Accessible at: `http://localhost:5173`

## 🔌 API Proxy & Backend
The frontend is configured via `vite.config.ts` to automatically proxy all `/api/*` calls to the FastAPI backend running at `http://localhost:8000`.

## 📦 Production Build
```bash
npm run build
```
Builds optimized static assets into `D:\agniwatch-india\frontend\dist`.
