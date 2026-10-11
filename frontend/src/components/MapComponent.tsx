import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

export interface LandCoverFeature {
  type: string;
  properties: {
    id: string;
    name: string;
    class_id: string;
    class_name: string;
    color: string;
    description: string;
    default_fuel: string;
    area_sqkm: number;
    canopy_density_pct?: number;
    dryness_status?: string;
    ndmi?: number;
    ndvi?: number;
  };
  geometry: {
    type: string;
    coordinates: any;
  };
}

interface MapComponentProps {
  center: [number, number];
  zoom: number;
  hotspots: any[];
  weather: any;
  riskCells: any[];
  simulationResult: any;
  selectedStep: number;
  landcoverFeatures: LandCoverFeature[];
  landcoverOpacity: number;
  onMapClick?: (lat: number, lon: number) => void;
  onFeatureSelect?: (feature: any) => void;
  activeLayers: {
    satellite: boolean;
    landcover: boolean;
    hotspots: boolean;
    riskGrid: boolean;
    weather: boolean;
    simulation: boolean;
    assets: boolean;
  };
}

export const MapComponent: React.FC<MapComponentProps> = ({
  center,
  zoom,
  hotspots,
  weather,
  riskCells,
  simulationResult,
  selectedStep,
  landcoverFeatures,
  landcoverOpacity,
  onMapClick,
  onFeatureSelect,
  activeLayers
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersRef = useRef<{ [key: string]: L.LayerGroup }>({});

  // ---------------------------------------------------------------------------
  // Initialize Leaflet Map (With strict container cleanup)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Destroy any existing leaflet instance on container
    if (mapInstanceRef.current) {
      try {
        mapInstanceRef.current.remove();
      } catch (e) {
        console.warn('Map cleanup warning:', e);
      }
      mapInstanceRef.current = null;
    }

    const containerEl = mapContainerRef.current as any;
    if (containerEl._leaflet_id) {
      delete containerEl._leaflet_id;
    }

    const map = L.map(mapContainerRef.current, {
      center: center && center.length === 2 ? center : [20.21, 79.30],
      zoom: zoom || 11,
      zoomControl: false,
      attributionControl: false
    });

    // Add zoom control at bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Add scale bar
    L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);

    // Base Layers (Free, No Key, No Watermark)
    const satLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 18 }
    );

    const darkLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 18 }
    );

    // Reference Labels & Boundaries (Cities, States, Districts, Highways)
    const satLabelsLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 18, zIndex: 400 }
    );

    const darkLabelsLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 18, zIndex: 400 }
    );

    // Initial base layer based on activeLayers.satellite
    const showLabels = activeLayers.labels !== false;
    if (activeLayers.satellite) {
      satLayer.addTo(map);
      if (showLabels) satLabelsLayer.addTo(map);
    } else {
      darkLayer.addTo(map);
      if (showLabels) darkLabelsLayer.addTo(map);
    }

    // Map Click Listener
    map.on('click', (e: L.LeafletMouseEvent) => {
      if (onMapClick && e && e.latlng) {
        onMapClick(Number(e.latlng.lat.toFixed(4)), Number(e.latlng.lng.toFixed(4)));
      }
    });

    // Register Layer Groups
    layersRef.current.baseSat = satLayer as any;
    layersRef.current.baseDark = darkLayer as any;
    layersRef.current.labelsSat = satLabelsLayer as any;
    layersRef.current.labelsDark = darkLabelsLayer as any;
    layersRef.current.landcover = L.layerGroup().addTo(map);
    layersRef.current.riskGrid = L.layerGroup().addTo(map);
    layersRef.current.simulation = L.layerGroup().addTo(map);
    layersRef.current.assets = L.layerGroup().addTo(map);
    layersRef.current.weather = L.layerGroup().addTo(map);
    layersRef.current.hotspots = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('Map cleanup error:', e);
        }
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Smooth Camera Pan/Zoom when Region Center Changes
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !center || center.length !== 2) return;
    try {
      map.flyTo(center, zoom || 11, {
        duration: 1.2,
        easeLinearity: 0.25
      });
    } catch (e) {
      console.warn('flyTo error:', e);
    }
  }, [center?.[0], center?.[1], zoom]);

  // ---------------------------------------------------------------------------
  // Base Layer & Labels Toggle (Satellite vs Dark Canvas + Boundaries & Places)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !layersRef.current.baseSat || !layersRef.current.baseDark) return;

    try {
      const showLabels = activeLayers.labels !== false;

      if (activeLayers.satellite) {
        map.addLayer(layersRef.current.baseSat as any);
        map.removeLayer(layersRef.current.baseDark as any);

        if (showLabels && layersRef.current.labelsSat) {
          map.addLayer(layersRef.current.labelsSat as any);
        } else if (layersRef.current.labelsSat) {
          map.removeLayer(layersRef.current.labelsSat as any);
        }
        if (layersRef.current.labelsDark) {
          map.removeLayer(layersRef.current.labelsDark as any);
        }
      } else {
        map.addLayer(layersRef.current.baseDark as any);
        map.removeLayer(layersRef.current.baseSat as any);

        if (showLabels && layersRef.current.labelsDark) {
          map.addLayer(layersRef.current.labelsDark as any);
        } else if (layersRef.current.labelsDark) {
          map.removeLayer(layersRef.current.labelsDark as any);
        }
        if (layersRef.current.labelsSat) {
          map.removeLayer(layersRef.current.labelsSat as any);
        }
      }
    } catch (e) {
      console.warn('Base layer switch warning:', e);
    }
  }, [activeLayers.satellite, activeLayers.labels]);

  // ---------------------------------------------------------------------------
  // Dynamic Land Cover & Vegetation Layer
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const group = layersRef.current.landcover;
    if (!group) return;
    group.clearLayers();

    if (!activeLayers.landcover || !Array.isArray(landcoverFeatures) || landcoverFeatures.length === 0) return;

    landcoverFeatures.forEach((feat) => {
      try {
        if (!feat || !feat.geometry || !feat.geometry.coordinates) return;
        const props = feat.properties || {};
        const rawCoords = feat.geometry.coordinates;

        // Extract outer ring coordinates safely
        let ring = rawCoords;
        if (Array.isArray(rawCoords[0]) && Array.isArray(rawCoords[0][0])) {
          ring = rawCoords[0];
        }
        if (!Array.isArray(ring) || ring.length < 3) return;

        const latLngs = ring
          .filter((c: any) => Array.isArray(c) && c.length >= 2)
          .map((c: any) => [c[1], c[0]] as [number, number]);

        if (latLngs.length < 3) return;

        const color = props.color || '#15803d';
        const polygon = L.polygon(latLngs, {
          color: color,
          weight: 1.8,
          opacity: 0.9,
          fillColor: color,
          fillOpacity: Math.min(0.85, Math.max(0.15, landcoverOpacity || 0.5))
        });

        // Hover glow styling
        polygon.on('mouseover', (e) => {
          const layer = e.target;
          layer.setStyle({
            weight: 3.5,
            color: '#ffffff',
            fillOpacity: Math.min(0.95, (landcoverOpacity || 0.5) + 0.25)
          });
        });

        polygon.on('mouseout', (e) => {
          const layer = e.target;
          layer.setStyle({
            weight: 1.8,
            color: color,
            fillOpacity: Math.min(0.85, Math.max(0.15, landcoverOpacity || 0.5))
          });
        });

        // Click to inspect
        polygon.on('click', (e) => {
          L.DomEvent.stopPropagation(e);
          if (onFeatureSelect) {
            onFeatureSelect({ type: 'landcover', data: props });
          }
        });

        // Tooltip
        polygon.bindTooltip(
          `<div style="font-weight: 700; color: ${color};">${props.class_name || 'Vegetation'}</div>` +
          `<div style="color: #cbd5e1; font-size: 11px;">${props.name || ''}</div>` +
          `<div style="color: #94a3b8; font-size: 10px;">Area: <b>${props.area_sqkm || 0} km²</b></div>`,
          { sticky: true }
        );

        group.addLayer(polygon);
      } catch (err) {
        console.warn('Error rendering landcover feature:', err);
      }
    });
  }, [landcoverFeatures, activeLayers.landcover, landcoverOpacity]);

  // ---------------------------------------------------------------------------
  // Animated Pulsating Fire Hotspots Layer
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const group = layersRef.current.hotspots;
    if (!group) return;
    group.clearLayers();

    if (!activeLayers.hotspots || !Array.isArray(hotspots) || hotspots.length === 0) return;

    hotspots.forEach((h: any) => {
      try {
        if (!h || typeof h.latitude !== 'number' || typeof h.longitude !== 'number') return;
        const frp = Number(h.frp || h.frp_mw || 10);
        const conf = h.confidence_label || h.confidence || 'Nominal';
        const sizePx = Math.max(22, Math.min(48, Math.round(18 + Math.sqrt(frp) * 4.5)));
        const color = conf === 'High' ? '#ef4444' : conf === 'Nominal' ? '#f97316' : '#eab308';

        const pulseHtml = `
          <div class="fire-marker-pulse" style="width: ${sizePx}px; height: ${sizePx}px; background: ${color}33; border: 2px solid ${color};">
            <div style="width: ${Math.round(sizePx * 0.45)}px; height: ${Math.round(sizePx * 0.45)}px; border-radius: 50%; background: ${color}; box-shadow: 0 0 10px ${color};"></div>
            <span style="position: absolute; bottom: -14px; font-size: 9px; font-weight: 800; color: #fff; background: rgba(0,0,0,0.75); padding: 1px 4px; border-radius: 4px; white-space: nowrap; border: 1px solid ${color};">
              ${frp.toFixed(0)} MW
            </span>
          </div>
        `;

        const customIcon = L.divIcon({
          className: 'custom-fire-marker',
          html: pulseHtml,
          iconSize: [sizePx, sizePx],
          iconAnchor: [sizePx / 2, sizePx / 2]
        });

        const marker = L.marker([h.latitude, h.longitude], { icon: customIcon });

        const popupHtml = `
          <div style="font-family: sans-serif; font-size: 12px; color: #f1f5f9; min-width: 220px; line-height: 1.5;">
            <div style="font-weight: 800; color: ${color}; font-size: 13px; margin-bottom: 6px;">
              🔥 Thermal Anomaly Hotspot
            </div>
            <div style="background: rgba(255,255,255,0.06); padding: 6px 8px; border-radius: 6px; margin-bottom: 6px;">
              <div><b>Fire Radiative Power:</b> <span style="color: #fb923c; font-weight: 700;">${frp.toFixed(1)} MW</span></div>
              <div><b>Confidence:</b> <span style="color: ${color}; font-weight: 700;">${conf}</span></div>
              <div><b>Sensor:</b> ${h.satellite || 'VIIRS'}</div>
              <div><b>Time:</b> ${h.acq_datetime_ist || h.observation_time_ist || 'Recent'}</div>
            </div>
            <div style="font-size: 10px; color: #94a3b8;">
              Coords: ${h.latitude.toFixed(4)}°N, ${h.longitude.toFixed(4)}°E
            </div>
          </div>
        `;

        marker.bindPopup(popupHtml);
        marker.on('click', () => {
          if (onFeatureSelect) {
            onFeatureSelect({ type: 'hotspot', data: h });
          }
        });

        group.addLayer(marker);
      } catch (err) {
        console.warn('Error rendering hotspot:', err);
      }
    });
  }, [hotspots, activeLayers.hotspots]);

  // ---------------------------------------------------------------------------
  // Weather & Animated Downwind Propagation Vector
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const group = layersRef.current.weather;
    if (!group) return;
    group.clearLayers();

    if (!activeLayers.weather || !weather) return;

    try {
      const wLat = weather.latitude || center[0] || 20.21;
      const wLon = weather.longitude || center[1] || 79.30;
      const temp = weather.temperature_c ?? 26.6;
      const windSpeed = weather.wind_speed_kmh ?? 18.0;
      const windToward = weather.wind_deg_toward ?? 120.0;
      const windCard = weather.wind_cardinal || 'NE';

      const stationHtml = `
        <div style="width: 28px; height: 28px; border-radius: 50%; background: rgba(2, 132, 199, 0.25); border: 2px solid #38bdf8; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px #0284c7;">
          <div style="width: 10px; height: 10px; border-radius: 50%; background: #38bdf8;"></div>
        </div>
      `;

      const stationIcon = L.divIcon({
        html: stationHtml,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const stationMarker = L.marker([wLat, wLon], { icon: stationIcon });
      stationMarker.bindTooltip(
        `<b>Weather Station:</b> ${temp}°C<br/>Wind ${windSpeed} km/h from ${windCard}`,
        { sticky: true }
      );
      group.addLayer(stationMarker);

      // Downwind vector
      const lenDeg = Math.max(0.04, Math.min(0.12, (windSpeed / 30.0) * 0.08));
      const radToward = (windToward * Math.PI) / 180.0;
      const arrowLat = wLat + lenDeg * Math.cos(radToward);
      const arrowLon = wLon + (lenDeg * Math.sin(radToward)) / Math.cos((wLat * Math.PI) / 180.0);

      const vectorLine = L.polyline([[wLat, wLon], [arrowLat, arrowLon]], {
        color: '#38bdf8',
        weight: 4,
        dashArray: '8, 6',
        opacity: 0.95
      });

      vectorLine.bindTooltip(`🔥 Flame Spread Propagation (${windToward.toFixed(0)}° Toward)`, { sticky: true });
      group.addLayer(vectorLine);

      const tipMarker = L.circleMarker([arrowLat, arrowLon], {
        radius: 6,
        fillColor: '#38bdf8',
        color: '#ffffff',
        weight: 2,
        fillOpacity: 1
      });
      group.addLayer(tipMarker);
    } catch (err) {
      console.warn('Error rendering weather vector:', err);
    }
  }, [weather, activeLayers.weather, center]);

  // ---------------------------------------------------------------------------
  // 2D Risk Grid Cells Overlay
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const group = layersRef.current.riskGrid;
    if (!group) return;
    group.clearLayers();

    if (!activeLayers.riskGrid || !Array.isArray(riskCells) || riskCells.length === 0) return;

    riskCells.forEach((c: any) => {
      try {
        if (!c || !c.bounds) return;
        const b = c.bounds;
        const bounds: [[number, number], [number, number]] = [
          [b.south, b.west],
          [b.north, b.east]
        ];
        const score = c.risk_score || 50;
        const tier = c.risk_tier || 'Moderate';
        const color = c.color || (score >= 70 ? '#ef4444' : score >= 50 ? '#f97316' : score >= 30 ? '#eab308' : '#22c55e');

        const rect = L.rectangle(bounds, {
          color: color,
          weight: 1,
          opacity: 0.6,
          fillColor: color,
          fillOpacity: 0.28
        });

        rect.bindTooltip(`Risk Cell: <b>${score.toFixed(0)}/100 (${tier})</b>`, { sticky: true });
        group.addLayer(rect);
      } catch (err) {
        console.warn('Error rendering risk cell:', err);
      }
    });
  }, [riskCells, activeLayers.riskGrid]);

  // ---------------------------------------------------------------------------
  // Rothermel Fire Spread Simulation Isochrones
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const group = layersRef.current.simulation;
    if (!group) return;
    group.clearLayers();

    if (!activeLayers.simulation || !simulationResult || !Array.isArray(simulationResult.steps)) return;

    const colors = ['#f43f5e', '#ef4444', '#f97316', '#fb923c', '#fbbf24', '#facc15', '#a855f7'];

    simulationResult.steps.forEach((step: any, idx: number) => {
      try {
        if (idx > selectedStep || idx === 0) return;
        const poly = step.polygon as [number, number][];
        if (!poly || poly.length < 3) return;

        const isCurrent = idx === selectedStep;
        const color = colors[idx % colors.length];

        const polygon = L.polygon(poly, {
          color: color,
          weight: isCurrent ? 3.5 : 2,
          dashArray: isCurrent ? undefined : '5, 5',
          opacity: 0.95,
          fillColor: color,
          fillOpacity: isCurrent ? 0.42 : 0.18
        });

        polygon.bindTooltip(
          `<b>T+${step.elapsed_hours}h Front:</b> Area ${step.area_ha} ha`,
          { sticky: true }
        );

        group.addLayer(polygon);
      } catch (err) {
        console.warn('Error rendering sim step:', err);
      }
    });

    if (simulationResult.ignition && typeof simulationResult.ignition.latitude === 'number') {
      try {
        const ig = simulationResult.ignition;
        const ignitionIcon = L.divIcon({
          html: `
            <div style="width: 26px; height: 26px; border-radius: 50%; background: #ef4444; border: 3px solid #ffffff; box-shadow: 0 0 16px #ef4444; display: flex; align-items: center; justify-content: center; font-size: 14px;">
              🔥
            </div>
          `,
          iconSize: [26, 26],
          iconAnchor: [13, 13]
        });

        const igMarker = L.marker([ig.latitude, ig.longitude], { icon: ignitionIcon });
        igMarker.bindTooltip(`<b>Hypothetical Ignition Point</b>`, { sticky: true });
        group.addLayer(igMarker);
      } catch (err) {
        console.warn('Error rendering ignition point:', err);
      }
    }
  }, [simulationResult, selectedStep, activeLayers.simulation]);

  return (
    <div className="relative w-full h-full min-h-[460px] rounded-xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-950">
      <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: '460px' }} />
    </div>
  );
};

export default MapComponent;
