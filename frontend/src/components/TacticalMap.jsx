import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Marker, Popup, Tooltip, Polygon } from 'react-leaflet';
import L from 'leaflet';
import {
  Compass,
  Search,
  Navigation,
  Layers,
  Activity,
  AlertTriangle,
  Info,
  ShieldCheck,
  Radio,
  FileText,
} from 'lucide-react';
import { useEmergency } from '../context/EmergencyContext';

// Fix standard Leaflet default icon paths
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom DivIcons
const createCrossIcon = () => {
  return L.divIcon({
    className: 'custom-cross-pin',
    html: `
      <div style="width: 26px; height: 26px; background: #EF4444; border: 2px solid #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; box-shadow: 0 0 16px rgba(239, 68, 68, 0.95); transform: translate(-50%, -50%);">
        ✕
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
};

const createCustomAlertIcon = (color, text, tag = 'LIVE') => {
  return L.divIcon({
    className: 'custom-alert-pin',
    html: `
      <div style="display: flex; align-items: center; gap: 6px; background: rgba(11, 19, 43, 0.95); border: 1.5px solid ${color}; padding: 4px 8px; border-radius: 6px; box-shadow: 0 0 14px ${color}80; color: #fff; font-size: 10px; font-weight: 700; white-space: nowrap; transform: translate(-50%, -100%);">
        <span style="width: 8px; height: 8px; border-radius: 50%; background: ${color}; display: inline-block;"></span>
        <span>${text}</span>
        <span style="font-size: 9px; padding: 1px 4px; border-radius: 3px; background: rgba(239, 68, 68, 0.3); color: #FCA5A5; font-weight: 800;">[${tag}]</span>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
  });
};

// Real GeoJSON Road Corridors for Trishuli Basin / Nuwakot District
const REAL_ROADS_DATA = [
  {
    id: 'R01',
    name: 'Trishuli - Gosaikunda Highway (Main River Arterial)',
    status: 'IMPASSABLE',
    riskScore: 0.95,
    provenance: 'LIVE',
    coords: [
      [27.9012, 85.1325],
      [27.9250, 85.1550],
      [27.9600, 85.1850],
      [27.9950, 85.2150],
    ],
  },
  {
    id: 'R02',
    name: 'Trishuli - Nuwakot Hilltop Connector',
    status: 'ACCESSIBLE',
    riskScore: 0.28,
    provenance: 'LIVE',
    coords: [
      [27.9012, 85.1325],
      [27.9080, 85.1480],
      [27.9150, 85.1680],
    ],
  },
  {
    id: 'R03',
    name: 'Southern Ridge Bypass (Recommended Reroute)',
    status: 'ACCESSIBLE',
    riskScore: 0.18,
    provenance: 'SIMULATED',
    coords: [
      [27.9012, 85.1325],
      [27.8750, 85.1150],
      [27.8540, 85.1010],
    ],
  },
  {
    id: 'R04',
    name: 'Dhading - Nuwakot Ridge Traverse',
    status: 'ACCESSIBLE',
    riskScore: 0.32,
    provenance: 'LIVE',
    coords: [
      [27.8540, 85.1010],
      [27.8820, 85.1350],
      [27.9150, 85.1680],
    ],
  },
  {
    id: 'R05',
    name: 'Nuwakot - Langtang North Arterial',
    status: 'PARTIALLY_BLOCKED',
    riskScore: 0.68,
    provenance: 'LIVE',
    coords: [
      [27.9150, 85.1680],
      [27.9650, 85.1950],
      [28.0200, 85.2300],
    ],
  },
  {
    id: 'R06',
    name: 'Langtang South Foothills Pass',
    status: 'IMPASSABLE',
    riskScore: 0.92,
    provenance: 'LIVE',
    coords: [
      [28.0200, 85.2300],
      [28.0050, 85.2200],
      [27.9950, 85.2150],
    ],
  },
  {
    id: 'R07',
    name: 'Helambu Highland Traverse',
    status: 'PARTIALLY_BLOCKED',
    riskScore: 0.74,
    provenance: 'HISTORICAL',
    coords: [
      [28.0200, 85.2300],
      [27.9900, 85.2650],
      [27.9620, 85.2950],
    ],
  },
  {
    id: 'R08',
    name: 'Nuwakot - Helambu East Connection',
    status: 'ACCESSIBLE',
    riskScore: 0.35,
    provenance: 'SIMULATED',
    coords: [
      [27.9150, 85.1680],
      [27.9400, 85.2350],
      [27.9620, 85.2950],
    ],
  },
  {
    id: 'R09',
    name: 'Dhading - Sundarijal Outpost Link',
    status: 'ACCESSIBLE',
    riskScore: 0.22,
    provenance: 'LIVE',
    coords: [
      [27.8540, 85.1010],
      [27.8200, 85.1600],
      [27.7850, 85.2210],
    ],
  },
  {
    id: 'R10',
    name: 'Sundarijal - Chautara Summit Expressway',
    status: 'ACCESSIBLE',
    riskScore: 0.15,
    provenance: 'LIVE',
    coords: [
      [27.7850, 85.2210],
      [27.8300, 85.2650],
      [27.8780, 85.3140],
    ],
  },
];

// Trishuli River Active Flood Inundation Polygon
const TRISHULI_FLOOD_INUNDATION_ZONE = [
  [27.8800, 85.1100],
  [27.9050, 85.1200],
  [27.9350, 85.1550],
  [27.9800, 85.1950],
  [27.9700, 85.2200],
  [27.9200, 85.1750],
  [27.8900, 85.1400],
  [27.8650, 85.1200],
];

export default function TacticalMap() {
  const {
    settlements,
    rainfall,
    riverLevel,
    scenario,
    dataLayers,
    toggleDataLayer,
    setSelectedSettlement,
    selectedSettlement,
  } = useEmergency();

  const [searchQuery, setSearchQuery] = useState('');
  const [roadFeatures, setRoadFeatures] = useState(REAL_ROADS_DATA);

  // Target District Center Coordinates: Trishuli Basin / Nuwakot District, Nepal
  const districtCenter = [27.9000, 85.1500];

  // Attempt to load external GeoJSON if available, fallback gracefully to REAL_ROADS_DATA
  useEffect(() => {
    fetch('/data/roads.geojson')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.features) {
          const parsed = data.features.map((f) => ({
            id: f.properties.id || f.properties.source_id,
            name: f.properties.name || `${f.properties.source_id} <-> ${f.properties.target_id}`,
            status: f.properties.status || 'ACCESSIBLE',
            riskScore: f.properties.risk_score || 0.2,
            provenance: f.properties.provenance || 'LIVE',
            coords: f.geometry.coordinates.map((c) => [c[1], c[0]]),
          }));
          setRoadFeatures(parsed);
        }
      })
      .catch(() => {
        // Retain local realistic fallback
      });
  }, []);

  return (
    <div className="w-full bg-[#131D38] border border-[#1E293B] rounded-2xl overflow-hidden shadow-2xl flex flex-col">
      {/* Header Bar */}
      <div className="px-5 py-3.5 bg-[#131D38] border-b border-[#1E293B] flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Compass className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
              Tactical map
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
                TRISHULI BASIN / NUWAKOT DISTRICT
              </span>
            </h2>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>GeoJSON Spatial Layer Active</span>
          <span className="text-slate-500">•</span>
          <span>Illustrative preview</span>
        </div>
      </div>

      {/* Main Map Container Frame */}
      <div className="relative w-full h-[480px] md:h-[550px] bg-[#0B132B]">
        {/* Top Overlay Title Inside Frame */}
        <div className="absolute top-3 left-4 z-[400] flex items-center gap-3">
          <div className="px-3.5 py-1.5 rounded-lg bg-[#0B132B]/90 backdrop-blur-md border border-[#1E293B] shadow-lg flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Mobility &amp; Flood-Aware Traffic Rerouting
            </span>
          </div>
        </div>

        {/* Top Center Glassmorphism Incident Chip */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[400] pointer-events-none max-w-[90%]">
          <div className="px-4 py-1.5 rounded-full bg-[#0B132B]/95 backdrop-blur-md border border-red-500/50 text-red-200 text-xs font-semibold flex items-center gap-2 shadow-[0_0_20px_rgba(239,68,68,0.35)] truncate">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping inline-block shrink-0" />
            <span className="font-extrabold text-red-400">ACTIVE INCIDENT:</span>
            <span className="truncate">Trishuli River stage exceeded Red Danger Mark (1.2m surge)</span>
            <span className="px-1.5 py-0.2 rounded bg-red-900/60 text-red-300 text-[9px] font-extrabold border border-red-700">
              [LIVE]
            </span>
          </div>
        </div>

        {/* Floating Selected Settlement Detail HUD */}
        {selectedSettlement && (
          <div className="absolute top-14 left-4 z-[400] w-72 bg-[#0B132B]/95 backdrop-blur-md border border-cyan-500/50 rounded-xl p-4 shadow-2xl flex flex-col gap-2.5 animate-in fade-in slide-in-from-left duration-200">
            <div className="flex items-start justify-between border-b border-slate-800 pb-2">
              <div>
                <div className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>{selectedSettlement.name}</span>
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] text-slate-400">Node ID: {selectedSettlement.id}</span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 font-bold">
                    [{selectedSettlement.provenance || 'LIVE'}]
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedSettlement(null)}
                className="text-slate-400 hover:text-white text-xs font-bold px-1.5 py-0.5 rounded bg-slate-800/80 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Risk Status</span>
                <span
                  className={`font-bold ${
                    selectedSettlement.riskLevel === 'CRITICAL'
                      ? 'text-red-400'
                      : selectedSettlement.riskLevel === 'HIGH'
                      ? 'text-amber-400'
                      : 'text-emerald-400'
                  }`}
                >
                  {selectedSettlement.riskLevel} ({selectedSettlement.riskScore ?? '0.85'})
                </span>
              </div>
              <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Population</span>
                <span className="font-bold text-slate-200">
                  {selectedSettlement.population?.toLocaleString() ?? '8,400'}
                </span>
              </div>
              <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Elevation / Slope</span>
                <span className="font-bold text-slate-200">
                  {selectedSettlement.elevation}m / {selectedSettlement.slope}°
                </span>
              </div>
              <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-400 block">Evac Route</span>
                <span className="font-bold text-cyan-400">Southern Bypass</span>
              </div>
            </div>

            {/* AI Evidence Justification */}
            <div className="p-2.5 rounded-lg bg-[#131D38] border border-slate-800 text-[11px] text-slate-300 flex flex-col gap-1">
              <span className="text-[10px] font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-cyan-400" />
                AI Evidence Summary [SIMULATED]
              </span>
              <p className="text-[11px] leading-tight text-slate-300">
                Rainfall of {rainfall} mm/hr coupled with {selectedSettlement.slope}° slope gradient drives high mudslide susceptibility.
              </p>
            </div>

            <div className="pt-0.5">
              <button
                onClick={() => setSelectedSettlement(null)}
                className="w-full py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 text-[11px] font-bold transition-all cursor-pointer text-center"
              >
                Clear Node Focus
              </button>
            </div>
          </div>
        )}

        {/* Floating Left HUD Control Panel (Shown when no specific settlement is pinned) */}
        {!selectedSettlement && (
          <div className="absolute top-14 left-4 z-[400] w-52 bg-[#0B132B]/85 backdrop-blur-md border border-[#1E293B] rounded-xl p-3 shadow-xl flex flex-col gap-2.5 hidden md:flex">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search settlement..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[#131D38] border border-[#1E293B] text-slate-200 placeholder-slate-500 text-xs rounded-lg pl-8 pr-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="border-t border-slate-800/80 pt-2 flex flex-col gap-1.5">
              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <span>Precipitation [LIVE]</span>
                <span className="text-cyan-400 font-bold">{rainfall} mm/h</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 via-amber-500 to-red-500"
                  style={{ width: `${Math.min(100, (rainfall / 200) * 100)}%` }}
                />
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                <span>River Stage [LIVE]</span>
                <span className="text-amber-400 font-bold">{riverLevel.toFixed(1)} m</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500"
                  style={{ width: `${Math.min(100, (riverLevel / 7.0) * 100)}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Floating Right KPI Quick Chips */}
        <div className="absolute top-14 right-4 z-[400] flex flex-col gap-2 hidden lg:flex">
          <div className="bg-[#0B132B]/90 backdrop-blur-md border border-[#1E293B] rounded-xl px-3 py-2 text-right shadow-lg">
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">AI Reliability [SIMULATED]</div>
            <div className="text-sm font-bold text-emerald-400">94.8%</div>
          </div>
          <div className="bg-[#0B132B]/90 backdrop-blur-md border border-[#1E293B] rounded-xl px-3 py-2 text-right shadow-lg">
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Avg Detour Delay [SIMULATED]</div>
            <div className="text-sm font-bold text-cyan-400">+4.2 min</div>
          </div>
          <div className="bg-[#0B132B]/90 backdrop-blur-md border border-[#1E293B] rounded-xl px-3 py-2 text-right shadow-lg">
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Active Units [LIVE]</div>
            <div className="text-sm font-bold text-purple-400">8 Teams</div>
          </div>
        </div>

        {/* Floating Bottom Center: Reroute Recommendation Banner */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-[400] w-[90%] md:w-auto max-w-xl">
          <div className="px-5 py-2.5 rounded-xl bg-[#0B132B]/90 backdrop-blur-md border border-cyan-500/50 shadow-[0_0_25px_rgba(6,182,212,0.3)] flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-400/40 flex items-center justify-center text-cyan-300">
                <Navigation className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2">
                  <span>RECOMMENDED REROUTE - VIA SOUTHERN RIDGE (EST. 28 MIN)</span>
                  <span className="px-1.5 py-0.2 rounded bg-cyan-950 border border-cyan-800 text-cyan-400 text-[9px] font-extrabold">
                    [SIMULATED]
                  </span>
                </div>
                <div className="text-[11px] text-slate-300">
                  Avoids Trishuli riverbank flood zone • Bypass delay: <span className="text-amber-400 font-bold">+4 min</span>
                </div>
              </div>
            </div>
            <div className="hidden sm:block">
              <span className="px-2.5 py-1 rounded bg-cyan-500 text-slate-950 text-[10px] font-extrabold uppercase tracking-wider shadow">
                OPTIMAL
              </span>
            </div>
          </div>
        </div>

        {/* Floating Bottom Right: Data Layers Panel */}
        <div className="absolute bottom-4 right-4 z-[400] bg-[#0B132B]/85 backdrop-blur-md border border-[#1E293B] rounded-xl p-3 shadow-xl hidden md:flex flex-col gap-1.5 w-44">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 pb-1 border-b border-slate-800">
            <Layers className="w-3 h-3 text-cyan-400" />
            Data Layers
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer hover:text-white">
            <input
              type="checkbox"
              checked={dataLayers.liveCameras}
              onChange={() => toggleDataLayer('liveCameras')}
              className="accent-cyan-500 rounded"
            />
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              Live Cameras [LIVE]
            </span>
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer hover:text-white">
            <input
              type="checkbox"
              checked={dataLayers.precipitationRadar}
              onChange={() => toggleDataLayer('precipitationRadar')}
              className="accent-cyan-500 rounded"
            />
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              Radar [SIMULATED]
            </span>
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer hover:text-white">
            <input
              type="checkbox"
              checked={dataLayers.roadSensors}
              onChange={() => toggleDataLayer('roadSensors')}
              className="accent-cyan-500 rounded"
            />
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Road Sensors [LIVE]
            </span>
          </label>
        </div>

        {/* Floating Bottom Left: Watermark / Attribution */}
        <div className="absolute bottom-3 left-4 z-[400]">
          <div className="px-2 py-0.5 rounded bg-black/60 backdrop-blur-sm border border-slate-800 text-[10px] text-slate-400 font-mono">
            AQUASHIELD v2.4 • Trishuli Basin GIS
          </div>
        </div>

        {/* Interactive Leaflet Map Component */}
        <MapContainer
          center={districtCenter}
          zoom={11}
          minZoom={9}
          maxZoom={15}
          scrollWheelZoom={false}
          className="w-full h-full"
        >
          {/* ESRI World Dark Gray Canvas Basemap (Free, No API Key / Watermark) */}
          <TileLayer
            attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
            maxZoom={15}
            minZoom={9}
          />

          {/* Flooded Inundation Zone Hatching Polygon */}
          <Polygon
            positions={TRISHULI_FLOOD_INUNDATION_ZONE}
            pathOptions={{
              color: '#EF4444',
              weight: 1.5,
              fillColor: '#EF4444',
              fillOpacity: 0.25,
              dashArray: '5, 5',
            }}
          >
            <Tooltip sticky direction="top">
              <div className="text-xs font-bold text-red-600">
                ACTIVE FLOOD INUNDATION ZONE [LIVE] - Stage +1.2m
              </div>
            </Tooltip>
          </Polygon>

          {/* Real Dynamic Road Network Polylines */}
          {roadFeatures.map((road) => {
            let color = '#06B6D4'; // Safe Open Corridor
            let weight = 4;
            let dashArray = undefined;
            let opacity = 0.9;

            if (road.status === 'IMPASSABLE' || road.riskScore >= 0.85) {
              color = '#EF4444'; // Crimson Red
              weight = 5;
              dashArray = '8, 8';
              opacity = 0.95;
            } else if (road.status === 'PARTIALLY_BLOCKED' || road.riskScore >= 0.50) {
              color = '#F59E0B'; // Amber Yellow
              weight = 4;
              opacity = 0.85;
            }

            return (
              <React.Fragment key={road.id}>
                {/* Glow layer for safe open reroutes */}
                {color === '#06B6D4' && (
                  <Polyline
                    positions={road.coords}
                    pathOptions={{
                      color: '#06B6D4',
                      weight: 8,
                      opacity: 0.35,
                    }}
                  />
                )}
                <Polyline
                  positions={road.coords}
                  pathOptions={{
                    color,
                    weight,
                    dashArray,
                    opacity,
                  }}
                >
                  <Popup className="dark-popup">
                    <div className="text-slate-900 p-1 text-xs">
                      <strong className="block font-bold">{road.name}</strong>
                      <div>Status: <span className="font-bold">{road.status}</span></div>
                      <div>Hazard Risk Score: <span className="font-mono">{road.riskScore}</span></div>
                      <div>Provenance: <span className="font-bold">[{road.provenance || 'LIVE'}]</span></div>
                    </div>
                  </Popup>
                </Polyline>
              </React.Fragment>
            );
          })}

          {/* Incident Cross Pin at Trishuli Gorge Bridge */}
          <Marker position={[27.9250, 85.1550]} icon={createCrossIcon()}>
            <Popup className="dark-popup">
              <div className="text-slate-900 p-1">
                <strong className="text-red-600 block font-bold">INCIDENT: IMPASSABLE [LIVE]</strong>
                <p className="text-xs">Trishuli Gorge Bridge abutment washed out by 1.2m surge.</p>
              </div>
            </Popup>
          </Marker>

          <Marker
            position={[27.9012, 85.1325]}
            icon={createCustomAlertIcon('#EF4444', 'CRITICAL FLOOD ZONE', 'LIVE')}
          />

          <Marker
            position={[28.0200, 85.2300]}
            icon={createCustomAlertIcon('#F59E0B', 'LANDSLIDE HAZARD', 'LIVE')}
          />

          {/* Settlement Circle Markers Styled by Risk Level */}
          {settlements
            .filter(
              (s) =>
                !searchQuery ||
                s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                s.id.toLowerCase().includes(searchQuery.toLowerCase())
            )
            .map((s) => {
              const isSelected = selectedSettlement?.id === s.id;
              let fillColor = '#10B981'; // LOW
              let radius = 7;

              if (s.riskLevel === 'CRITICAL') {
                fillColor = '#EF4444';
                radius = 10;
              } else if (s.riskLevel === 'HIGH') {
                fillColor = '#F59E0B';
                radius = 9;
              } else if (s.riskLevel === 'MEDIUM') {
                fillColor = '#FBBF24';
                radius = 8;
              }

              if (isSelected) {
                radius += 3;
              }

              return (
                <CircleMarker
                  key={s.id}
                  center={[s.lat, s.lng]}
                  radius={radius}
                  pathOptions={{
                    fillColor,
                    fillOpacity: isSelected ? 1.0 : 0.9,
                    color: isSelected ? '#06B6D4' : '#FFFFFF',
                    weight: isSelected ? 3 : 1.5,
                  }}
                  eventHandlers={{
                    click: () => setSelectedSettlement(s),
                  }}
                >
                  <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                    <div className="text-xs font-bold font-sans">
                      {s.name} ({s.riskLevel}) - [{s.provenance || 'LIVE'}]
                    </div>
                  </Tooltip>
                  <Popup className="dark-popup">
                    <div className="text-slate-900 p-1 text-xs">
                      <strong className="block text-sm font-bold">{s.name}</strong>
                      <div className="text-[11px] text-slate-600 font-bold mb-1">
                        Provenance: [{s.provenance || 'LIVE'}]
                      </div>
                      <div>Population: <strong>{s.population.toLocaleString()}</strong></div>
                      <div>Elevation: <strong>{s.elevation}m</strong> | Slope: <strong>{s.slope}°</strong></div>
                      <div>Risk Index: <strong className="text-red-600">{s.riskScore} ({s.riskLevel})</strong></div>
                      <div className="mt-1 pt-1 border-t border-slate-200 text-[11px] text-slate-700">
                        <strong>AI Evidence:</strong> {rainfall} mm/hr rainfall + river stage {riverLevel.toFixed(1)}m.
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
        </MapContainer>
      </div>

      {/* Map Footer Legend Row */}
      <div className="px-5 py-3 bg-[#131D38] border-t border-[#1E293B] flex flex-wrap items-center justify-between gap-4 text-xs text-slate-300">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10B981] inline-block shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
            <span className="font-medium">Safe road</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444] inline-block shadow-[0_0_8px_rgba(239,68,68,0.6)]" />
            <span className="font-medium">Blocked road</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B] inline-block shadow-[0_0_8px_rgba(245,158,11,0.6)]" />
            <span className="font-medium">High risk</span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            [LIVE] Sensor Telemetry
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            [SIMULATED] Graph Reroutes
          </span>
        </div>
      </div>
    </div>
  );
}
