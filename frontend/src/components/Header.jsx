import React from 'react';
import { Waves, Shield, Activity } from 'lucide-react';
import { useEmergency } from '../context/EmergencyContext';

export default function Header() {
  const { currentRole, setCurrentRole } = useEmergency();

  const roles = [
    { id: 'GIS Admin', label: 'GIS Admin' },
    { id: 'AI Engine', label: 'AI Engine' },
    { id: 'Responder', label: 'Responder' },
    { id: 'Command', label: 'Command' },
  ];

  return (
    <header className="w-full bg-[#0B132B]/90 backdrop-blur-md border-b border-[#1E293B] px-4 md:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4 sticky top-0 z-50">
      {/* Left: Logo & Branding */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
          <Waves className="w-5 h-5 stroke-[2.5]" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-wider text-white font-sans">
              AQUASHIELD
            </h1>
          </div>
          <p className="text-xs text-slate-400 font-medium">
            Flood Intelligence & Response
          </p>
        </div>
      </div>

      {/* Center: Role Switcher Tabs */}
      <div className="bg-[#131D38] p-1 rounded-full border border-[#1E293B] flex items-center gap-1 shadow-inner">
        {roles.map((role) => {
          const isActive = currentRole === role.id;
          return (
            <button
              key={role.id}
              onClick={() => setCurrentRole(role.id)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer ${
                isActive
                  ? 'bg-[#06B6D4] text-white shadow-[0_0_12px_rgba(6,182,212,0.5)]'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              {role.label}
            </button>
          );
        })}
      </div>

      {/* Right: Simulation Status Badge */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-700/50 text-emerald-400 text-xs font-bold tracking-wider shadow-[0_0_10px_rgba(16,185,129,0.2)]">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
          <span>SIMULATION</span>
        </div>
      </div>
    </header>
  );
}
