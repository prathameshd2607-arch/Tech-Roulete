import React, { createContext, useContext, useState, useMemo, useEffect } from 'react';

const EmergencyContext = createContext();

const API_BASE_URL = 'http://localhost:8000';

// Initial Realistic Settlements Data (Trishuli Basin / Nuwakot District, Nepal)
const INITIAL_SETTLEMENTS = [
  { id: 'S01', name: 'Settlement A (Trishuli Valley)', shortName: 'Settlement A', lat: 27.9012, lng: 85.1325, population: 12500, elevation: 620, slope: 8.5, baseRisk: 0.88, provenance: 'LIVE' },
  { id: 'S02', name: 'Settlement B (Dhading Ridge)', shortName: 'Settlement B', lat: 27.8540, lng: 85.1010, population: 8400, elevation: 1420, slope: 18.2, baseRisk: 0.65, provenance: 'LIVE' },
  { id: 'S03', name: 'Settlement C (Nuwakot Hilltop)', shortName: 'Settlement C', lat: 27.9150, lng: 85.1680, population: 6200, elevation: 1780, slope: 24.0, baseRisk: 0.52, provenance: 'SIMULATED' },
  { id: 'S04', name: 'Settlement D (Langtang Foothills)', shortName: 'Settlement D', lat: 28.0200, lng: 85.2300, population: 3100, elevation: 2850, slope: 38.5, baseRisk: 0.94, provenance: 'LIVE' },
  { id: 'S05', name: 'Settlement E (Melamchi Basin)', shortName: 'Settlement E', lat: 27.8310, lng: 85.3780, population: 7800, elevation: 890, slope: 12.0, baseRisk: 0.45, provenance: 'HISTORICAL' },
  { id: 'S06', name: 'Settlement F (Helambu Highland)', shortName: 'Settlement F', lat: 27.9620, lng: 85.2950, population: 2400, elevation: 3120, slope: 41.2, baseRisk: 0.91, provenance: 'SIMULATED' },
  { id: 'S07', name: 'Settlement G (Sundarijal Outpost)', shortName: 'Settlement G', lat: 27.7850, lng: 85.2210, population: 4500, elevation: 1550, slope: 19.8, baseRisk: 0.38, provenance: 'LIVE' },
  { id: 'S08', name: 'Settlement H (Chautara Summit)', shortName: 'Settlement H', lat: 27.8780, lng: 85.3140, population: 9200, elevation: 1620, slope: 22.4, baseRisk: 0.42, provenance: 'HISTORICAL' },
  { id: 'S09', name: 'Settlement I (Bahrabise Gorge)', shortName: 'Settlement I', lat: 27.7920, lng: 85.1950, population: 5600, elevation: 980, slope: 33.0, baseRisk: 0.85, provenance: 'SIMULATED' },
  { id: 'S10', name: 'Settlement J (Gosaikunda Pass Junction)', shortName: 'Settlement J', lat: 27.9950, lng: 85.2150, population: 1200, elevation: 3190, slope: 39.7, baseRisk: 0.96, provenance: 'LIVE' },
  { id: 'S11', name: 'Settlement K (Devighat Confluence)', shortName: 'Settlement K', lat: 27.8720, lng: 85.1220, population: 3800, elevation: 580, slope: 6.2, baseRisk: 0.72, provenance: 'LIVE' },
  { id: 'S12', name: 'Settlement L (Battar Highland)', shortName: 'Settlement L', lat: 27.8920, lng: 85.1550, population: 4900, elevation: 950, slope: 14.5, baseRisk: 0.58, provenance: 'SIMULATED' },
];

const INITIAL_REPORTS = [
  { id: 'REP-01', location: 'Trishuli Bridge corridor', type: 'ROAD_WASHOUT', text: 'Bridge approach submerged under 1.2m rushing floodwater.', time: '3 min ago', reliability: 0.98, status: 'VERIFIED', provenance: 'LIVE' },
  { id: 'REP-02', location: 'Dhading-Nuwakot Ridge Pass', type: 'LANDSLIDE', text: 'Active boulder fall and slope slip covering uphill lanes.', time: '11 min ago', reliability: 0.92, status: 'VERIFIED', provenance: 'LIVE' },
  { id: 'REP-03', location: 'Melamchi Low Bridge', type: 'FLASH_FLOOD', text: 'River stage surpassed red danger mark. Culvert cracking.', time: '24 min ago', reliability: 0.89, status: 'MONITORING', provenance: 'HISTORICAL' },
  { id: 'REP-04', location: 'Langtang South Access Road', type: 'MUDSLIDE', text: 'Tree collapse and mud flow on highway single-lane passable.', time: '40 min ago', reliability: 0.85, status: 'IN_PROGRESS', provenance: 'SIMULATED' },
];

export function EmergencyProvider({ children }) {
  const [currentRole, setCurrentRole] = useState('Command'); // 'GIS Admin' | 'AI Engine' | 'Responder' | 'Command'
  const [rainfall, setRainfall] = useState(75); // 0 to 200 mm/hr
  const [riverLevel, setRiverLevel] = useState(4.8); // meters
  const [scenario, setScenario] = useState('DEFAULT'); // 'DEFAULT' | 'HEAVY_RAIN' | 'ROAD_BLOCK' | 'EXTREME_FLOOD'
  const [baselineThreshold, setBaselineThreshold] = useState(50); // mm/hr
  const [reports, setReports] = useState(INITIAL_REPORTS);
  const [selectedSettlement, setSelectedSettlement] = useState(null);
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const [dataLayers, setDataLayers] = useState({
    liveCameras: true,
    precipitationRadar: true,
    roadSensors: true,
    activeUnits: false,
  });

  // Attempt to check if FastAPI backend is online, seamlessly fallback if not
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/health`, { method: 'GET', signal: AbortSignal.timeout(1500) });
        if (res.ok) {
          setIsBackendConnected(true);
        } else {
          setIsBackendConnected(false);
        }
      } catch (err) {
        setIsBackendConnected(false);
      }
    };
    checkBackend();
  }, []);

  // Dynamic calculations based on live sliders & scenarios (Offline Resilient)
  const dynamicState = useMemo(() => {
    const rainFactor = rainfall / 100;
    const riverFactor = riverLevel / 4.0;

    // Recalculate settlement risk levels
    const settlementsWithRisk = INITIAL_SETTLEMENTS.map((s) => {
      let riskScore = Math.min(1.0, Math.max(0.05, s.baseRisk * 0.4 + rainFactor * 0.45 + (riverFactor > 1 ? 0.2 : 0)));
      if (scenario === 'EXTREME_FLOOD') riskScore = Math.min(1.0, riskScore * 1.3);
      if (scenario === 'ROAD_BLOCK' && (s.id === 'S01' || s.id === 'S02' || s.id === 'S04')) riskScore = Math.min(1.0, riskScore + 0.25);

      let riskLevel = 'LOW';
      if (riskScore >= 0.75) riskLevel = 'CRITICAL';
      else if (riskScore >= 0.55) riskLevel = 'HIGH';
      else if (riskScore >= 0.35) riskLevel = 'MEDIUM';

      const isIsolated = riskScore >= 0.70;

      return {
        ...s,
        riskScore: Number(riskScore.toFixed(2)),
        riskLevel,
        isolated: isIsolated,
      };
    });

    const criticalCount = settlementsWithRisk.filter(s => s.riskLevel === 'CRITICAL').length;
    const atRiskCount = settlementsWithRisk.filter(s => s.riskLevel !== 'LOW').length;

    // Roads status
    let blockedCount = 5;
    let routesAffected = 3;
    if (rainfall > 120 || scenario === 'EXTREME_FLOOD') {
      blockedCount = 8;
      routesAffected = 6;
    } else if (rainfall < 35) {
      blockedCount = 2;
      routesAffected = 1;
    }

    let overallAiRisk = 'HIGH';
    if (rainfall < 40 && riverLevel < 3.5) overallAiRisk = 'LOW';
    else if (rainfall < 70 && riverLevel < 4.5) overallAiRisk = 'MEDIUM';
    else if (rainfall > 110 || criticalCount >= 5) overallAiRisk = 'CRITICAL';

    return {
      settlements: settlementsWithRisk,
      criticalSettlementsCount: criticalCount,
      atRiskSettlementsCount: atRiskCount,
      roadsBlockedCount: blockedCount,
      routesAffectedCount: routesAffected,
      aiRiskLevel: overallAiRisk,
      reportsCount: reports.length + 24, // 28 demo count
    };
  }, [rainfall, riverLevel, scenario, reports.length]);

  const applyScenario = async (scenarioName) => {
    setScenario(scenarioName);
    let newRain = 75;
    let newRiver = 4.8;

    if (scenarioName === 'HEAVY_RAIN') {
      newRain = 135;
      newRiver = 5.2;
    } else if (scenarioName === 'ROAD_BLOCK') {
      newRain = 80;
      newRiver = 4.5;
    } else if (scenarioName === 'EXTREME_FLOOD') {
      newRain = 185;
      newRiver = 6.4;
    }

    setRainfall(newRain);
    setRiverLevel(newRiver);

    // If backend is active, also notify the backend API
    try {
      await fetch(`${API_BASE_URL}/api/admin/config/rainfall`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rainfall_rate_mm_hr: newRain, global_multiplier: 1.0 }),
        signal: AbortSignal.timeout(2000),
      });
    } catch (e) {
      // Graceful offline fallback
    }
  };

  const addReport = async (newReport) => {
    const createdReport = {
      id: `REP-${String(reports.length + 1).padStart(2, '0')}`,
      time: 'Just now',
      status: 'VERIFIED',
      reliability: 0.96,
      ...newReport,
    };

    setReports((prev) => [createdReport, ...prev]);

    // Attempt backend sync
    try {
      await fetch(`${API_BASE_URL}/api/responder/field-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reporter_id: 'WEB-FIELD-CLIENT',
          edge: ['S01', 'S10'],
          hazard_type: newReport.type || 'LANDSLIDE',
          description: newReport.text || 'Citizen hazard observation',
          user_reliability_score: 0.98,
        }),
        signal: AbortSignal.timeout(2000),
      });
    } catch (e) {
      // Graceful offline fallback
    }
  };

  const toggleDataLayer = (layerKey) => {
    setDataLayers((prev) => ({
      ...prev,
      [layerKey]: !prev[layerKey],
    }));
  };

  const resetAll = async () => {
    setRainfall(75);
    setRiverLevel(4.8);
    setScenario('DEFAULT');
    setBaselineThreshold(50);

    try {
      await fetch(`${API_BASE_URL}/api/v1/alerts`, { method: 'DELETE', signal: AbortSignal.timeout(1000) });
    } catch (e) {
      // Offline fallback
    }
  };

  return (
    <EmergencyContext.Provider
      value={{
        currentRole,
        setCurrentRole,
        rainfall,
        setRainfall,
        riverLevel,
        setRiverLevel,
        scenario,
        applyScenario,
        baselineThreshold,
        setBaselineThreshold,
        reports,
        addReport,
        selectedSettlement,
        setSelectedSettlement,
        dataLayers,
        toggleDataLayer,
        resetAll,
        isBackendConnected,
        ...dynamicState,
      }}
    >
      {children}
    </EmergencyContext.Provider>
  );
}

export function useEmergency() {
  const context = useContext(EmergencyContext);
  if (!context) {
    throw new Error('useEmergency must be used within an EmergencyProvider');
  }
  return context;
}
