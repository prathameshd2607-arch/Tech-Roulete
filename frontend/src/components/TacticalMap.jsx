import React, { useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Marker, Popup, Tooltip, Polygon } from 'react-leaflet';
import L from 'leaflet';
import {
  AlertTriangle,
  Radio,
  Camera,
  Layers,
  Search,
  Navigation,
  CheckCircle2,
  Sliders,
  Maximize2,
  Compass,
  XCircle,
  Clock,
  ShieldAlert,
} from 'lucide-react';
import { useEmergency } from '../context/EmergencyContext';

// Fix standard Leaflet default icon paths if needed
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Create custom colored DivIcons
const createCustomIcon = (color, label, iconType = 'pin') => {
  return L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="display: flex; align-items: center; gap: 6px; background: rgba(11, 19, 43, 0.9); border: 1px solid ${color}; padding: 4px 8px; border-radius: 6px; box-shadow: 0 0 12px ${color}80; color: #fff; font-size: 10px; font-weight: 700; white-space: nowrap; transform: translate(-50%, -100%);">
        <span style="width: 8px; height: 8px; border-radius: 50%; background: ${color}; display: inline-block;"></span>
        ${label}
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
  });
};

const createCrossIcon = () => {
  return L.divIcon({
    className: 'custom-cross-pin',
    html: `
      <div style="width: 24px; height: 24px; background: #EF4444; border: 2px solid #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; box-shadow: 0 0 15px rgba(239, 68, 68, 0.9); transform: translate(-50%, -50%);">
        ✕
      </div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
};

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

  // Map center at realistic valley corridor
  const mapCenter = [27.865, 85.32];

  // Primary Blocked Road Coordinates (Trishuli - Nuwakot arterial)
  const blockedRouteCoordinates = [
    [27.8021, 85.1432],
    [27.8450, 85.2200],
    [27.8745, 85.2850],
    [27.9150, 85.3800],
  ];

  // Blocked flood zone polygon
  const floodZonePolygon = [
    [27.8200, 85.1800],
    [27.8700, 85.2600],
    [27.8900, 85.3200],
    [27.8500, 85.3400],
    [27.8100, 85.2400],
  ];

  // Safe Recommended Reroute (Cyan Glowing Route via Southern Ridge)
  const recommendedRerouteCoordinates = [
    [27.8021, 85.1432],
    [27.7650, 85.2100],
    [27.7500, 85.3200],
    [27.7800, 85.4400],
    [27.8310, 85.5780],
    [27.9150, 85.3800],
  ];

  // Secondary Safe Connection
  const alternateRouteCoordinates = [
    [27.8745, 85.0214],
    [27.9150, 85.1670],
    [27.9850, 85.3120],
    [27.9950, 85.2150],
  ];

  // Network background arterial roads
  const backgroundArterials = [
    [[27.7650, 85.4210], [27.8310, 85.5780]],
    [[27.8310, 85.5780], [27.9620, 85.4950]],
    [[27.7780, 85.7140], [27.7920, 85.8950]],
    [[27.8745, 85.0214], [27.8021, 85.1432]],
    [[27.9620, 85.4950], [27.9850, 85.3120]],
  ];

  return (
    <div className="w-full bg-[#131D38] border border-[#1E293B] rounded-2xl overflow-hidden shadow-2xl flex flex-col">
      {/* Header Bar */}
      <div className="px-5 py-3.5 bg-[#131D38] border-b border-[#1E293B] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Compass className="w-4 h-4" />
          </div>
          <h2 className="text-base font-bold text-white tracking-wide">
            Tactical map
          </h2>
        </div>
        <span className="text-xs text-slate-400 font-medium">
          Illustrative preview
        </span>
      </div>

      {/* Main Map Container Frame */}
      <div className="relative w-full h-[480px] md:h-[540px] bg-[#0B132B]">
        {/* Top Overlay Title Inside Frame */}
        <div className="absolute top-3 left-4 z-[400] flex items-center gap-3">
          <div className="px-3.5 py-1.5 rounded-lg bg-[#0B132B]/85 backdrop-blur-md border border-[#1E293B] shadow-lg flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Mobility & Flood-Aware Traffic Rerouting
            </span>
          </div>
        </div>

        {/* Top Center Glassmorphism Incident Chip */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[400] pointer-events-none">
          <div className="px-4 py-1.5 rounded-full bg-[#0B132B]/90 backdrop-blur-md border border-red-500/40 text-red-200 text-xs font-semibold flex items-center gap-2 shadow-[0_0_20px_rgba(239,68,68,0.3)]">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping inline-block" />
            <span className="font-bold text-red-400">ACTIVE INCIDENTS:</span>
            <span>Multiple road closures due to heavy rainfall ({rainfall} mm/hr)</span>
          </div>
        </div>

          {/* Floating Selected Settlement Detail HUD */}
          {selectedSettlement && (
            <div className="absolute top-14 left-4 z-[400] w-64 bg-[#0B132B]/95 backdrop-blur-md border border-cyan-500/40 rounded-xl p-3.5 shadow-2xl flex flex-col gap-2.5 animate-in fade-in slide-in-from-left duration-200">
              <div className="flex items-start justify-between border-b border-slate-800 pb-2">
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <span>{selectedSettlement.name}</span>
                  </div>
                  <span className="text-[10px] text-slate-400">Node ID: {selectedSettlement.id}</span>
                </div>
                <button
                  onClick={() => setSelectedSettlement(null)}
                  className="text-slate-400 hover:text-white text-xs font-bold px-1.5 py-0.5 rounded bg-slate-800/80"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Risk Status</span>
                  <span className={`font-bold ${
                    selectedSettlement.riskLevel === 'CRITICAL' ? 'text-red-400' :
                    selectedSettlement.riskLevel === 'HIGH' ? 'text-amber-400' : 'text-emerald-400'
                  }`}>
                    {selectedSettlement.riskLevel} ({selectedSettlement.riskScore ?? '0.85'})
                  </span>
                </div>
                <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Population</span>
                  <span className="font-bold text-slate-200">{selectedSettlement.population?.toLocaleString() ?? '8,400'}</span>
                </div>
                <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Elevation / Slope</span>
                  <span className="font-bold text-slate-200">{selectedSettlement.elevation}m / {selectedSettlement.slope}°</span>
                </div>
                <div className="bg-[#131D38] p-2 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Evac Route</span>
                  <span className="font-bold text-cyan-400">Bypass Open</span>
                </div>
              </div>

              <div className="pt-1">
                <button
                  onClick={() => setSelectedSettlement(null)}
                  className="w-full py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 text-[11px] font-bold transition-all cursor-pointer text-center"
                >
                  Focus Tactical Corridor
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
                  placeholder="Search settlement/node..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-[#131D38] border border-[#1E293B] text-slate-200 placeholder-slate-500 text-xs rounded-lg pl-8 pr-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="border-t border-slate-800/80 pt-2 flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>Precipitation</span>
                  <span className="text-cyan-400 font-bold">{rainfall} mm/h</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 via-amber-500 to-red-500"
                    style={{ width: `${Math.min(100, (rainfall / 200) * 100)}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  <span>River Gauge Stage</span>
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
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">AI Reliability</div>
            <div className="text-sm font-bold text-emerald-400">94.8%</div>
          </div>
          <div className="bg-[#0B132B]/90 backdrop-blur-md border border-[#1E293B] rounded-xl px-3 py-2 text-right shadow-lg">
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Avg Detour Delay</div>
            <div className="text-sm font-bold text-cyan-400">+4.2 min</div>
          </div>
          <div className="bg-[#0B132B]/90 backdrop-blur-md border border-[#1E293B] rounded-xl px-3 py-2 text-right shadow-lg">
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Active Responders</div>
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
                <div className="text-xs font-bold text-cyan-300 uppercase tracking-wider">
                  Recommended Reroute - Flood Aware
                </div>
                <div className="text-[11px] text-slate-300">
                  Est. Travel Time: <span className="text-white font-bold">28 Min</span> (<span className="text-amber-400 font-bold">+4 Min Delay</span> via Southern Ridge Bypass)
                </div>
              </div>
            </div>
            <div className="hidden sm:block">
              <span className="px-2.5 py-1 rounded bg-cyan-500 text-slate-950 text-[10px] font-extrabold uppercase tracking-wider">
                Optimal
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
              Live Cameras
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
              Precipitation Radar
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
              Road Sensors
            </span>
          </label>
        </div>

        {/* Floating Bottom Left: Watermark / Attribution */}
        <div className="absolute bottom-3 left-4 z-[400]">
          <div className="px-2 py-0.5 rounded bg-black/60 backdrop-blur-sm border border-slate-800 text-[10px] text-slate-400 font-mono">
            AQUASHIELD v2.4 • Tactical GIS
          </div>
        </div>

        {/* Interactive Leaflet Map Component */}
        <MapContainer
          center={mapCenter}
          zoom={11}
          scrollWheelZoom={false}
          className="w-full h-full"
        >
          {/* ESRI World Dark Gray Canvas Basemap (Free, No API Key / Watermark) */}
          <TileLayer
            attribution="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
            maxZoom={16}
          />

          {/* Background Arterial Network */}
          {backgroundArterials.map((coords, idx) => (
            <Polyline
              key={`bg-${idx}`}
              positions={coords}
              pathOptions={{
                color: '#334155',
                weight: 2,
                opacity: 0.7,
              }}
            />
          ))}

          {/* Flooded Inundation Zone Hatching */}
          <Polygon
            positions={floodZonePolygon}
            pathOptions={{
              color: '#EF4444',
              weight: 1,
              fillColor: '#EF4444',
              fillOpacity: 0.18,
              dashArray: '4, 6',
            }}
          />

          {/* Red Blocked Road Corridor */}
          <Polyline
            positions={blockedRouteCoordinates}
            pathOptions={{
              color: '#EF4444',
              weight: 6,
              opacity: 0.9,
              dashArray: '8, 8',
            }}
          />

          {/* Cyan Glow Layer for Recommended Reroute */}
          <Polyline
            positions={recommendedRerouteCoordinates}
            pathOptions={{
              color: '#06B6D4',
              weight: 8,
              opacity: 0.35,
            }}
          />
          {/* Main Solid Cyan Line for Recommended Reroute */}
          <Polyline
            positions={recommendedRerouteCoordinates}
            pathOptions={{
              color: '#06B6D4',
              weight: 4,
              opacity: 0.95,
            }}
          />

          {/* Alternate Magenta Corridor */}
          <Polyline
            positions={alternateRouteCoordinates}
            pathOptions={{
              color: '#F59E0B',
              weight: 3,
              opacity: 0.85,
            }}
          />

          {/* Flood Alert Pins / Markers */}
          <Marker
            position={[27.8745, 85.2850]}
            icon={createCrossIcon()}
          >
            <Popup className="dark-popup">
              <div className="text-slate-900 p-1">
                <strong className="text-red-600 block font-bold">INCIDENT ALERT: UNPASSABLE</strong>
                <p className="text-xs">Trishuli Gorge Bridge abutment submerged under 1.5m flood stage.</p>
              </div>
            </Popup>
          </Marker>

          <Marker
            position={[27.8450, 85.2200]}
            icon={createCustomIcon('#EF4444', 'FLOOD ALERT - UNPASSABLE')}
          />

          <Marker
            position={[27.9150, 85.3800]}
            icon={createCustomIcon('#F59E0B', 'FLOOD ALERT - RISK AWARE')}
          />

          {/* Settlement Circle Markers */}
          {settlements
            .filter((s) =>
              !searchQuery ||
              s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              s.id.toLowerCase().includes(searchQuery.toLowerCase())
            )
            .map((s) => {
              const isSelected = selectedSettlement?.id === s.id;
              let fillColor = '#10B981';
              let radius = 6;
              if (s.riskLevel === 'CRITICAL') {
                fillColor = '#EF4444';
                radius = 9;
              } else if (s.riskLevel === 'HIGH') {
                fillColor = '#F59E0B';
                radius = 8;
              } else if (s.riskLevel === 'MEDIUM') {
                fillColor = '#FBBF24';
                radius = 7;
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
                    fillOpacity: isSelected ? 1.0 : 0.88,
                    color: isSelected ? '#06B6D4' : '#FFFFFF',
                    weight: isSelected ? 3 : 1.5,
                  }}
                  eventHandlers={{
                    click: () => setSelectedSettlement(s),
                  }}
                >
                  <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                    <div className="text-xs font-bold font-sans">
                      {s.name} ({s.riskLevel}) - Pop: {s.population.toLocaleString()}
                    </div>
                  </Tooltip>
                </CircleMarker>
              );
            })}
        </MapContainer>
      </div>

      {/* Map Footer Legend Row matching target screenshot */}
      <div className="px-5 py-3 bg-[#131D38] border-t border-[#1E293B] flex items-center gap-6 text-xs text-slate-300">
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
    </div>
  );
}
