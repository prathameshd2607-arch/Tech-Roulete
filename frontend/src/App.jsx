import React from 'react';
import Header from './components/Header';
import CommandDashboard from './components/CommandDashboard';
import GISAdminPortal from './components/GISAdminPortal';
import AIEnginePortal from './components/AIEnginePortal';
import ResponderCenter from './components/ResponderCenter';
import { useEmergency } from './context/EmergencyContext';

function MainContent() {
  const { currentRole } = useEmergency();

  return (
    <main className="flex-1 w-full pb-10">
      {currentRole === 'Command' && <CommandDashboard />}
      {currentRole === 'GIS Admin' && <GISAdminPortal />}
      {currentRole === 'AI Engine' && <AIEnginePortal />}
      {currentRole === 'Responder' && <ResponderCenter />}
    </main>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-[#0B132B] text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      <Header />
      <MainContent />
    </div>
  );
}
