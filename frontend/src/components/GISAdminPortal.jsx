import React, { useState } from 'react';
import {
  Sliders,
  CloudRain,
  Waves,
  RefreshCw,
  Database,
  UploadCloud,
  CheckCircle2,
  AlertOctagon,
  Sparkles,
  Layers,
} from 'lucide-react';
import { useEmergency } from '../context/EmergencyContext';

export default function GISAdminPortal() {
  const {
    rainfall,
    setRainfall,
    riverLevel,
    setRiverLevel,
    scenario,
    applyScenario,
    baselineThreshold,
    setBaselineThreshold,
    resetAll,
    settlements,
  } = useEmergency();

  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleBulkUpload = () => {
    setUploadSuccess(true);
    setTimeout(() => setUploadSuccess(false), 3000);
  };

  const sampleLogs = [
    { id: 'LOG-0941', tag: 'LIVE', time: '14:52:10', source: 'Trishuli RG-01', event: 'Water stage crossed 4.8m trigger mark', value: '4.82m' },
    { id: 'LOG-0940', tag: 'SIMULATED', time: '14:51:45', source: 'Rain Gauge S04', event: 'Precipitation surge detected', value: `${rainfall} mm/hr` },
    { id: 'LOG-0939', tag: 'LIVE', time: '14:50:22', source: 'Field Unit Bravo', event: 'Landslide observation verified', value: 'IMPASSABLE' },
    { id: 'LOG-0938', tag: 'HISTORICAL', time: '2024-08-14', source: 'Disaster Archive', event: 'Monsoon flash flood recurrence benchmark', value: 'Severity 4' },
    { id: 'LOG-0937', tag: 'SIMULATED', time: '14:48:00', source: 'Hydrology Engine', event: 'Runoff coefficient recalculated', value: '0.84' },
  ];

  return (
    <div className="w-full max-w-7xl mx-auto px-4 md:px-8 py-5 flex flex-col gap-6">
      {/* Portal Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-[#131D38] border border-[#1E293B] p-5 rounded-2xl shadow-lg">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400" />
            GIS Administration & Simulation Control Portal
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure real-time meteorological parameters, test disaster scenarios, and manage telemetry feeds.
          </p>
        </div>
        <button
          onClick={resetAll}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-all cursor-pointer shadow"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reset Baseline
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 6 Columns: Interactive Sliders & Scenarios */}
        <div className="lg:col-span-6 flex flex-col gap-5">
          {/* Real-Time Telemetry Sliders */}
          <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col gap-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <CloudRain className="w-4 h-4 text-cyan-400" />
              Dynamic Environmental Sliders
            </h3>

            {/* Rainfall Slider */}
            <div className="flex flex-col gap-2 bg-[#0B132B] p-4 rounded-xl border border-slate-800">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-300">Rainfall Intensity</span>
                <span className="font-mono text-base font-bold text-cyan-400">
                  {rainfall} mm/hr
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="200"
                value={rainfall}
                onChange={(e) => setRainfall(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>0 mm/hr (Clear)</span>
                <span>50 (Moderate)</span>
                <span>100 (Severe Storm)</span>
                <span>200 (Torrential)</span>
              </div>
            </div>

            {/* River Stage Slider */}
            <div className="flex flex-col gap-2 bg-[#0B132B] p-4 rounded-xl border border-slate-800">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-300">Trishuli / Melamchi River Gauge Level</span>
                <span className="font-mono text-base font-bold text-amber-400">
                  {riverLevel.toFixed(1)} meters
                </span>
              </div>
              <input
                type="range"
                min="1.0"
                max="7.0"
                step="0.1"
                value={riverLevel}
                onChange={(e) => setRiverLevel(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>1.0m (Low)</span>
                <span>4.0m (Warning Mark)</span>
                <span>5.5m (Red Flood Stage)</span>
                <span>7.0m (Catastrophic)</span>
              </div>
            </div>

            {/* Baseline Trigger Configuration */}
            <div className="flex flex-col gap-2 bg-[#0B132B] p-4 rounded-xl border border-slate-800">
              <div className="flex justify-between items-center text-xs">
                <div>
                  <span className="font-semibold text-slate-300 block">Non-ML Rule Threshold</span>
                  <span className="text-[11px] text-slate-400">Static rule-based trigger ceiling</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    value={baselineThreshold}
                    onChange={(e) => setBaselineThreshold(Number(e.target.value))}
                    className="w-16 bg-[#131D38] border border-[#1E293B] text-center text-xs font-bold text-slate-200 rounded-lg py-1 focus:outline-none focus:border-cyan-500"
                  />
                  <span className="text-xs text-slate-400">mm/h</span>
                </div>
              </div>
            </div>
          </div>

          {/* Scenario Presets */}
          <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col gap-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              Scenario Ingestion Presets
            </h3>
            <p className="text-xs text-slate-400">
              Trigger system-wide multi-hazard emergency simulations with predefined conditions:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
              <button
                onClick={() => applyScenario('HEAVY_RAIN')}
                className={`px-3 py-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer flex flex-col items-center gap-1 ${
                  scenario === 'HEAVY_RAIN'
                    ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.3)]'
                    : 'bg-[#0B132B] border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <span>Heavy Rainfall</span>
                <span className="text-[10px] text-slate-400 font-normal">135 mm/hr Storm</span>
              </button>

              <button
                onClick={() => applyScenario('ROAD_BLOCK')}
                className={`px-3 py-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer flex flex-col items-center gap-1 ${
                  scenario === 'ROAD_BLOCK'
                    ? 'bg-amber-500/20 border-amber-500 text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.3)]'
                    : 'bg-[#0B132B] border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <span>Road Blockage</span>
                <span className="text-[10px] text-slate-400 font-normal">Bridge Abutment Slip</span>
              </button>

              <button
                onClick={() => applyScenario('EXTREME_FLOOD')}
                className={`px-3 py-2.5 rounded-xl border text-xs font-bold transition-all cursor-pointer flex flex-col items-center gap-1 ${
                  scenario === 'EXTREME_FLOOD'
                    ? 'bg-red-500/20 border-red-500 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.3)]'
                    : 'bg-[#0B132B] border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <span>Extreme Flood</span>
                <span className="text-[10px] text-slate-400 font-normal">185 mm/hr & 6.4m</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right 6 Columns: Data Stream Ingestion & Provenance Logs */}
        <div className="lg:col-span-6 flex flex-col gap-5">
          {/* Data Feeds & Bulk Ingest */}
          <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-400" />
                Data Ingestion & Provenance
              </h3>
              <button
                onClick={handleBulkUpload}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/30 rounded-lg text-xs font-bold transition-all cursor-pointer"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                Upload Dataset
              </button>
            </div>

            {uploadSuccess && (
              <div className="px-3 py-2 bg-emerald-950/80 border border-emerald-600/50 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Bulk GIS telemetry dataset (500 records) ingested and provenance tagged as [SIMULATED].</span>
              </div>
            )}

            <div className="overflow-x-auto mt-2">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-[#0B132B] text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Log ID</th>
                    <th className="py-2.5 px-3">Provenance</th>
                    <th className="py-2.5 px-3">Source</th>
                    <th className="py-2.5 px-3">Telemetry Event</th>
                    <th className="py-2.5 px-3">Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {sampleLogs.map((log) => {
                    let tagStyle = 'bg-cyan-950 border-cyan-800 text-cyan-400';
                    if (log.tag === 'LIVE') tagStyle = 'bg-emerald-950 border-emerald-800 text-emerald-400 font-bold';
                    if (log.tag === 'HISTORICAL') tagStyle = 'bg-purple-950 border-purple-800 text-purple-400';

                    return (
                      <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">{log.id}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] border ${tagStyle}`}>
                            [{log.tag}]
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-medium text-slate-200">{log.source}</td>
                        <td className="py-2.5 px-3 text-slate-400">{log.event}</td>
                        <td className="py-2.5 px-3 font-bold text-white">{log.value}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Regional Settlements GIS Overview */}
          <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col gap-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Connected District Nodes ({settlements.length})
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {settlements.map((s) => (
                <div key={s.id} className="p-2.5 rounded-xl bg-[#0B132B] border border-slate-800 flex flex-col justify-between">
                  <div className="text-xs font-bold text-slate-200 truncate">{s.name}</div>
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
                    <span>{s.elevation}m</span>
                    <span className={s.riskLevel === 'CRITICAL' ? 'text-red-400 font-bold' : s.riskLevel === 'HIGH' ? 'text-amber-400' : 'text-emerald-400'}>
                      {s.riskScore}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
