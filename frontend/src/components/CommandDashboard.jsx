import React from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  Radio,
  BarChart3,
  List,
  ChevronRight,
  TrendingUp,
  Flame,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import { useEmergency } from '../context/EmergencyContext';
import TacticalMap from './TacticalMap';

export default function CommandDashboard() {
  const {
    settlements,
    criticalSettlementsCount,
    atRiskSettlementsCount,
    roadsBlockedCount,
    routesAffectedCount,
    reportsCount,
    aiRiskLevel,
    setSelectedSettlement,
  } = useEmergency();

  // Top 3 Priority Settlements for the bottom panel list
  const prioritySettlements = settlements.slice(0, 3);

  return (
    <div className="flex flex-col gap-5 w-full max-w-7xl mx-auto px-4 md:px-8 py-5">
      {/* 1. Top Metrics Grid (4 Equal Cards in a Row) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Settlements at risk */}
        <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div className="text-xs font-semibold text-slate-400">
            Settlements at risk
          </div>
          <div className="my-2">
            <span className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              {atRiskSettlementsCount}
            </span>
          </div>
          <div className="text-xs font-bold text-[#EF4444]">
            {criticalSettlementsCount} critical
          </div>
        </div>

        {/* Card 2: Roads blocked */}
        <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div className="text-xs font-semibold text-slate-400">
            Roads blocked
          </div>
          <div className="my-2">
            <span className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              {roadsBlockedCount}
            </span>
          </div>
          <div className="text-xs font-bold text-[#F59E0B]">
            {routesAffectedCount} routes affected
          </div>
        </div>

        {/* Card 3: Reports received */}
        <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div className="text-xs font-semibold text-slate-400">
            Reports received
          </div>
          <div className="my-2">
            <span className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              {reportsCount}
            </span>
          </div>
          <div className="text-xs font-bold text-[#06B6D4]">
            Demo dataset
          </div>
        </div>

        {/* Card 4: AI risk level */}
        <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-all">
          <div className="text-xs font-semibold text-slate-400">
            AI risk level
          </div>
          <div className="my-2">
            <span
              className={`text-3xl md:text-4xl font-extrabold tracking-tight ${
                aiRiskLevel === 'CRITICAL' || aiRiskLevel === 'HIGH'
                  ? 'text-[#EF4444]'
                  : aiRiskLevel === 'MEDIUM'
                  ? 'text-[#F59E0B]'
                  : 'text-[#10B981]'
              }`}
            >
              {aiRiskLevel}
            </span>
          </div>
          <div className="text-xs font-medium text-slate-400">
            Illustrative result
          </div>
        </div>
      </div>

      {/* 2. Tactical Map Panel */}
      <TacticalMap />

      {/* 3. Priority Settlements Panel */}
      <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl overflow-hidden shadow-xl">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-[#1E293B] flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <List className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-bold text-white tracking-wide">
            Priority settlements
          </h3>
        </div>

        {/* Settlement Items List */}
        <div className="divide-y divide-[#1E293B]">
          {prioritySettlements.map((settlement, index) => {
            const isSelected = selectedSettlement?.id === settlement.id;
            let badgeColorClass = 'text-[#FBBF24]';
            if (settlement.riskLevel === 'CRITICAL') {
              badgeColorClass = 'text-[#EF4444] font-bold';
            } else if (settlement.riskLevel === 'HIGH') {
              badgeColorClass = 'text-[#F59E0B] font-bold';
            }

            return (
              <div
                key={settlement.id}
                onClick={() => setSelectedSettlement(isSelected ? null : settlement)}
                className={`px-5 py-3.5 flex items-center justify-between transition-all cursor-pointer group ${
                  isSelected ? 'bg-cyan-950/40 border-l-4 border-l-[#06B6D4]' : 'hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-bold ${isSelected ? 'text-cyan-400' : 'text-slate-400'}`}>
                    {index + 1}.
                  </span>
                  <div>
                    <span className={`text-sm font-semibold transition-colors ${isSelected ? 'text-cyan-300 font-bold' : 'text-slate-200 group-hover:text-white'}`}>
                      {settlement.shortName || settlement.name}
                    </span>
                    <span className="text-xs text-slate-400 ml-2 hidden sm:inline">
                      (Pop: {settlement.population.toLocaleString()}, Elev: {settlement.elevation}m)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1.5">
                  <span className={`text-xs uppercase tracking-wider font-extrabold ${badgeColorClass}`}>
                    {settlement.riskLevel}
                  </span>
                  <ChevronRight className={`w-4 h-4 ${badgeColorClass} group-hover:translate-x-0.5 transition-transform`} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
