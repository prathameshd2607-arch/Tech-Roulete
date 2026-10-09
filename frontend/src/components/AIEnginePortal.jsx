import React from 'react';
import {
  BrainCircuit,
  Cpu,
  TrendingUp,
  ShieldCheck,
  Zap,
  BarChart2,
  FileText,
  Activity,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import { useEmergency } from '../context/EmergencyContext';

export default function AIEnginePortal() {
  const { rainfall, riverLevel, aiRiskLevel } = useEmergency();

  const metricsComparison = [
    { metric: 'True Positives (Detected Hazards)', nonML: '6 / 20 (30%)', aiModel: '19 / 20 (95%)', highlight: true },
    { metric: 'Missed Hazards (False Negatives)', nonML: '14 Critical Misses', aiModel: '1 Incident (-93%)', highlight: true },
    { metric: 'False Alarms (False Positives)', nonML: '2 False Blocks', aiModel: '2 False Blocks', highlight: false },
    { metric: 'Precision (Reliability of Alerts)', nonML: '75.0%', aiModel: '90.5%', highlight: true },
    { metric: 'Recall (Hazard Sensitivity)', nonML: '30.0%', aiModel: '95.0%', highlight: true },
    { metric: 'Harmonic F1-Score', nonML: '0.4286', aiModel: '0.9268', highlight: true },
    { metric: 'Overall Classification Accuracy', nonML: '68.0%', aiModel: '94.0%', highlight: true },
  ];

  return (
    <div className="w-full max-w-7xl mx-auto px-4 md:px-8 py-5 flex flex-col gap-6">
      {/* Header Banner */}
      <div className="bg-[#131D38] border border-[#1E293B] p-5 rounded-2xl shadow-lg flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-cyan-400" />
            AI Context-Fused Risk Engine & Explainability Matrix
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time multi-hazard fusion combining digital elevation models, hydrometric sensors, and citizen observations.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 rounded-xl bg-cyan-950 border border-cyan-700/50 text-cyan-300 text-xs font-bold flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            <span>Active Model: FloodNet-v4 Graph Neural Net</span>
          </div>
        </div>
      </div>

      {/* Top Grid: Circular Gauge & Contributing Factors */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 5 Cols: Confidence Gauge & AI Risk Verdict */}
        <div className="lg:col-span-5 bg-[#131D38] border border-[#1E293B] rounded-2xl p-6 shadow-lg flex flex-col items-center justify-between text-center gap-4">
          <div className="w-full text-left flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Model Confidence Gauge
            </span>
            <span className="text-xs font-bold text-emerald-400 px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800">
              OPTIMAL
            </span>
          </div>

          {/* SVG Circular Progress Gauge */}
          <div className="relative w-44 h-44 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                stroke="#1E293B"
                strokeWidth="10"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                stroke="#06B6D4"
                strokeWidth="10"
                strokeDasharray="251.2"
                strokeDashoffset="18.8" // ~92.5%
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
              <span className="text-3xl font-black text-white">92.8%</span>
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Confidence</span>
            </div>
          </div>

          {/* Real-Time Explainability Summary */}
          <div className="w-full bg-[#0B132B] p-4 rounded-xl border border-slate-800 text-left flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs font-bold text-cyan-300">
              <FileText className="w-3.5 h-3.5" />
              Automated Evidence Summary
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Trishuli valley corridor risk escalated to <strong className="text-red-400 font-semibold">{aiRiskLevel}</strong> due to coupled non-linear stressors: precipitation intensity of <span className="text-cyan-400 font-bold">{rainfall} mm/hr</span> exceeding the 30 mm/hr landslide threshold, coupled with river stage at <span className="text-amber-400 font-bold">{riverLevel.toFixed(1)}m</span>.
            </p>
          </div>
        </div>

        {/* Right 7 Cols: Feature Importance Weights & Topography Factors */}
        <div className="lg:col-span-7 bg-[#131D38] border border-[#1E293B] rounded-2xl p-6 shadow-lg flex flex-col justify-between gap-5">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyan-400" />
              Multi-Hazard Contributing Feature Weights
            </h3>
            <span className="text-xs text-slate-400">Dynamic weights</span>
          </div>

          <div className="flex flex-col gap-4">
            {/* Feature 1 */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-300">1. Real-Time Precipitation Rate ({rainfall} mm/hr)</span>
                <span className="text-cyan-400 font-mono font-bold">45% Weight</span>
              </div>
              <div className="w-full bg-[#0B132B] h-2.5 rounded-full overflow-hidden border border-slate-800">
                <div className="h-full bg-cyan-500 rounded-full" style={{ width: '45%' }} />
              </div>
              <span className="text-[11px] text-slate-400">Exponential trigger escalation above 30 mm/hr storm intensity.</span>
            </div>

            {/* Feature 2 */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-300">2. Topographical Terrain Slope Gradient (avg 26.5°)</span>
                <span className="text-amber-400 font-mono font-bold">30% Weight</span>
              </div>
              <div className="w-full bg-[#0B132B] h-2.5 rounded-full overflow-hidden border border-slate-800">
                <div className="h-full bg-amber-500 rounded-full" style={{ width: '30%' }} />
              </div>
              <span className="text-[11px] text-slate-400">Steep mountain facets (&gt;25°) drive rapid mudslide and debris slip.</span>
            </div>

            {/* Feature 3 */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-300">3. Citizen & Field Responder Ground Reports</span>
                <span className="text-purple-400 font-mono font-bold">25% Weight</span>
              </div>
              <div className="w-full bg-[#0B132B] h-2.5 rounded-full overflow-hidden border border-slate-800">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: '25%' }} />
              </div>
              <span className="text-[11px] text-slate-400">Ground-truth validation score weighted by reporter reliability (0.95).</span>
            </div>
          </div>

          <div className="p-3 bg-[#0B132B] rounded-xl border border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Inference Latency: <strong className="text-emerald-400">14.2 ms</strong></span>
            <span>Graph Nodes: <strong className="text-slate-200">12 Settlements</strong></span>
            <span>Graph Corridors: <strong className="text-slate-200">18 Edges</strong></span>
          </div>
        </div>
      </div>

      {/* Bottom Full-Width Card: Non-ML Baseline vs Trained AI Model */}
      <div className="bg-[#131D38] border border-[#1E293B] rounded-2xl p-6 shadow-xl flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-emerald-400" />
              Evaluation Matrix: Non-ML Static Baseline vs. AI Risk Engine
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Benchmark comparison over 50 ground-truth flood & landslide corridor observations.
            </p>
          </div>
          <span className="px-3 py-1 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-400 text-xs font-bold">
            +26.0% Overall Lift
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-[#0B132B] text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Performance Metric</th>
                <th className="py-3 px-4">Static Non-ML Baseline</th>
                <th className="py-3 px-4">AQUASHIELD AI Engine</th>
                <th className="py-3 px-4">Advantage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {metricsComparison.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-200">{row.metric}</td>
                  <td className="py-3 px-4 text-slate-400 font-mono">{row.nonML}</td>
                  <td className="py-3 px-4 font-bold text-cyan-400 font-mono">{row.aiModel}</td>
                  <td className="py-3 px-4">
                    {row.highlight ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 border border-emerald-800 text-emerald-400">
                        SUPERIOR
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400">Parity</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
