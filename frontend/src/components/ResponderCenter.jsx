import React, { useState } from 'react';
import {
  Users,
  Send,
  Navigation,
  CheckCircle2,
  AlertTriangle,
  Clock,
  MapPin,
  FilePlus,
  Shield,
  Truck,
  Flame,
  Radio,
} from 'lucide-react';
import { useEmergency } from '../context/EmergencyContext';
import TacticalMap from './TacticalMap';

export default function ResponderCenter() {
  const { settlements, addReport, reports } = useEmergency();

  const [dispatchedMissions, setDispatchedMissions] = useState({
    'S01': true,
    'S04': false,
    'S06': false,
    'S10': false,
  });

  const [showReportModal, setShowReportModal] = useState(false);
  const [reportText, setReportText] = useState('');
  const [reportLocation, setReportLocation] = useState('Trishuli Valley Route S01 <-> S10');
  const [reportType, setReportType] = useState('BRIDGE_COLLAPSE');
  const [toastMessage, setToastMessage] = useState('');

  const handleDispatch = (settlementId) => {
    setDispatchedMissions((prev) => ({
      ...prev,
      [settlementId]: true,
    }));
    setToastMessage(`Rescue Unit Alpha dispatched to Settlement ${settlementId}! ETA: 24 mins.`);
    setTimeout(() => setToastMessage(''), 4000);
  };

  const handleReportSubmit = (e) => {
    e.preventDefault();
    if (!reportText.trim()) return;

    addReport({
      location: reportLocation,
      type: reportType,
      text: reportText,
      reliability: 0.99,
    });

    setReportText('');
    setShowReportModal(false);
    setToastMessage('Field ground observation ingested! Graph edges updated and rerouting calculated.');
    setTimeout(() => setToastMessage(''), 4000);
  };

  // Prioritize critical & high risk settlements for task dispatch
  const priorityTasks = settlements.filter(s => s.riskLevel === 'CRITICAL' || s.riskLevel === 'HIGH').slice(0, 4);

  return (
    <div className="w-full max-w-7xl mx-auto px-4 md:px-8 py-5 flex flex-col gap-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-20 right-6 z-50 bg-emerald-950 border border-emerald-500/60 text-emerald-200 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 animate-bounce">
          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          <span className="text-xs font-bold">{toastMessage}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-[#131D38] border border-[#1E293B] p-5 rounded-2xl shadow-lg flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Truck className="w-5 h-5 text-cyan-400" />
            Field Responder Action & Evacuation Dispatch Center
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Coordinate rapid rescue sorties, ingest ground observations, and navigate through verified open corridors.
          </p>
        </div>

        <button
          onClick={() => setShowReportModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-all cursor-pointer"
        >
          <FilePlus className="w-4 h-4" />
          Submit Ground Report
        </button>
      </div>

      {/* Main Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 5 Columns: Priority Dispatch Task Cards */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-400" />
              High-Priority Evacuation Targets
            </h3>
            <span className="text-xs text-slate-400 font-medium">
              {priorityTasks.length} Action Items
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {priorityTasks.map((task) => {
              const isDispatched = dispatchedMissions[task.id];
              return (
                <div
                  key={task.id}
                  className="bg-[#131D38] border border-[#1E293B] hover:border-slate-700 rounded-2xl p-4 shadow-lg flex flex-col gap-3 transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-sm font-bold text-white flex items-center gap-2">
                        <span>{task.name}</span>
                        {task.isolated && (
                          <span className="px-2 py-0.5 rounded bg-red-950/80 border border-red-700 text-[10px] font-bold text-red-300">
                            ISOLATED
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                        <span>Pop: <strong className="text-slate-200">{task.population.toLocaleString()}</strong></span>
                        <span>Elev: <strong className="text-slate-200">{task.elevation}m</strong></span>
                        <span>Risk: <strong className="text-red-400 font-mono">{task.riskScore}</strong></span>
                      </div>
                    </div>

                    <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase bg-red-500/20 text-red-300 border border-red-500/40">
                      {task.riskLevel}
                    </span>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-cyan-400" />
                      <span>ETA: <strong className="text-slate-200">28 min</strong> via Southern Ridge</span>
                    </div>

                    {isDispatched ? (
                      <span className="px-3 py-1.5 rounded-xl bg-emerald-950 border border-emerald-600/60 text-emerald-300 text-xs font-bold flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        Unit Dispatched
                      </span>
                    ) : (
                      <button
                        onClick={() => handleDispatch(task.id)}
                        className="px-3.5 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold shadow-md transition-all cursor-pointer flex items-center gap-1"
                      >
                        <Send className="w-3 h-3" />
                        Dispatch Team
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Recent Field Observation Feed */}
          <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-4 shadow-lg flex flex-col gap-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-amber-400" />
              Live Field Reports Feed ({reports.length})
            </h4>
            <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
              {reports.map((rep) => (
                <div key={rep.id} className="p-2.5 bg-[#0B132B] rounded-xl border border-slate-800 flex flex-col gap-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-bold text-slate-200">{rep.location}</span>
                    <span className="text-[10px] text-slate-400">{rep.time}</span>
                  </div>
                  <p className="text-xs text-slate-300">{rep.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 7 Columns: Tactical Navigation Map */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <TacticalMap />
        </div>
      </div>

      {/* Submit Ground Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-6 w-full max-w-lg shadow-2xl flex flex-col gap-4 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FilePlus className="w-5 h-5 text-cyan-400" />
                Submit Ground Observation Report
              </h3>
              <button
                onClick={() => setShowReportModal(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleReportSubmit} className="flex flex-col gap-3.5 text-xs">
              <div>
                <label className="text-slate-300 font-semibold block mb-1">Observed Corridor / Settlement</label>
                <select
                  value={reportLocation}
                  onChange={(e) => setReportLocation(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="Trishuli Valley Route S01 <-> S10">Trishuli Gorge Highway (S01 &lt;-&gt; S10)</option>
                  <option value="Dhading Ridge Pass S02 <-> S03">Dhading Ridge Pass (S02 &lt;-&gt; S03)</option>
                  <option value="Melamchi Basin Low Bridge S05">Melamchi River Basin (S05)</option>
                  <option value="Langtang South Foothills S04">Langtang Foothills (S04)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Hazard Classification</label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="BRIDGE_COLLAPSE">Bridge Collapse / Abutment Washout</option>
                  <option value="LANDSLIDE">Major Landslide &amp; Boulder Fall</option>
                  <option value="FLASH_FLOOD">Torrential Flash Flood / Inundation</option>
                  <option value="MUDSLIDE">Mudslide Single-Lane Passable</option>
                </select>
              </div>

              <div>
                <label className="text-slate-300 font-semibold block mb-1">Field Situation Report</label>
                <textarea
                  rows={3}
                  placeholder="Describe road blockage depth, impassable conditions, or casualties..."
                  value={reportText}
                  onChange={(e) => setReportText(e.target.value)}
                  required
                  className="w-full bg-[#0B132B] border border-slate-800 rounded-xl p-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReportModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold shadow-[0_0_15px_rgba(6,182,212,0.4)] cursor-pointer"
                >
                  Submit &amp; Mutate Graph
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
