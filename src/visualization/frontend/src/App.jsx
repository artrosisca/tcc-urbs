import React, { useState, useEffect } from 'react';
import SidebarFilters from './components/SidebarFilters';
import GeospatialConsole from './components/GeospatialConsole';
import ProcessVisualizer from './components/ProcessVisualizer';
import ConformanceInspector from './components/ConformanceInspector';
import BottleneckProfiler from './components/BottleneckProfiler';
import FleetAuditView from './components/FleetAuditView';
import { Layers, GitCommit, ShieldAlert, BarChart3, Database, ClipboardCheck } from 'lucide-react';

export default function App() {
  const [filters, setFilters] = useState({
    regime: 'Regime B (20s)',
    line: '541',
    direction: 'VOLTA',
    startDate: '2025-12-02',
    endDate: '2025-12-08',
    startHour: '00:00',
    endHour: '24:00'
  });

   const [activeTab, setActiveTab] = useState('map');
  const [processingLogs, setProcessingLogs] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isLogicalMode, setIsLogicalMode] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // Loaded data states
  const [mapData, setMapData] = useState(null);
  const [petriNetData, setPetriNetData] = useState(null);
  const [conformanceData, setConformanceData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    setIsLoading(true);
    const { line, startDate, endDate, direction, startHour, endHour } = filters;
    const query = `line=${line}&start_date=${startDate}&end_date=${endDate}&direction=${direction}&start_hour=${startHour}&end_hour=${endHour}`;

    try {
      const [mapRes, petriRes, confRes, perfRes] = await Promise.all([
        fetch(`/api/map-data?${query}`),
        fetch(`/api/discovery-json?${query}`),
        fetch(`/api/conformance?${query}`),
        fetch(`/api/performance-json?${query}`)
      ]);

      if (mapRes.ok) {
        setMapData(await mapRes.json());
      } else {
        setMapData(null);
      }

      if (petriRes.ok) {
        setPetriNetData(await petriRes.json());
      } else {
        setPetriNetData(null);
      }

      if (confRes.ok) {
        setConformanceData(await confRes.json());
      } else {
        setConformanceData(null);
      }

      if (perfRes.ok) {
        setPerformanceData(await perfRes.json());
      } else {
        setPerformanceData(null);
      }
    } catch (err) {
      console.error('Error fetching dashboard metrics:', err);
      setMapData(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Triggered on page load or parameters change (if logs exist)
  useEffect(() => {
    fetchDashboardData();
  }, [filters.line, filters.direction, filters.startHour, filters.endHour, filters.startDate, filters.endDate]);

  // Execute Event Log generation via SSE
  const handleRunMining = () => {
    setIsProcessing(true);
    setProcessingLogs([]);
    
    const { line, startDate, endDate } = filters;
    const sse = new EventSource(`/api/process-stream?line=${line}&start_date=${startDate}&end_date=${endDate}`);

    sse.onmessage = (event) => {
      const msg = event.data;
      if (msg === '__SUCCESS__') {
        setProcessingLogs(prev => [...prev, 'Log de Eventos processado com sucesso!']);
        setIsProcessing(false);
        sse.close();
        fetchDashboardData(); // Refresh UI
      } else if (msg === '__FAILURE__') {
        setProcessingLogs(prev => [...prev, 'Erro crítico no processamento dos dados.']);
        setIsProcessing(false);
        sse.close();
      } else {
        setProcessingLogs(prev => [...prev, msg]);
      }
    };

    sse.onerror = () => {
      setProcessingLogs(prev => [...prev, 'Falha de comunicação com o servidor SSE.']);
      setIsProcessing(false);
      sse.close();
    };
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      {/* Sidebar Filters */}
      <SidebarFilters
        filters={filters}
        setFilters={setFilters}
        onRunMining={handleRunMining}
        processingLogs={processingLogs}
        isProcessing={isProcessing}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Top Header / Stats Overview */}
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between flex-shrink-0 shadow-xs">
          {/* Navigation/Views Tab selectors */}
          <div className="flex items-center gap-1">
            <button
              id="tab-audit"
              type="button"
              onClick={() => setActiveTab('audit')}
              className={`flex items-center gap-1.5 py-2 px-4 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                activeTab === 'audit'
                  ? 'bg-slate-100 text-slate-800 font-bold'
                  : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              <ClipboardCheck className="h-3.5 w-3.5" />
              <span>Auditoria Diária (CCO)</span>
            </button>

            <button
              id="tab-map"
              type="button"
              onClick={() => setActiveTab('map')}
              className={`flex items-center gap-1.5 py-2 px-4 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                activeTab === 'map'
                  ? 'bg-slate-100 text-slate-800 font-bold'
                  : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Mapa de Replay</span>
            </button>

            <button
              id="tab-petri"
              type="button"
              onClick={() => setActiveTab('petri')}
              className={`flex items-center gap-1.5 py-2 px-4 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                activeTab === 'petri'
                  ? 'bg-slate-100 text-slate-800 font-bold'
                  : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              <GitCommit className="h-3.5 w-3.5" />
              <span>Descoberta (Petri Net)</span>
            </button>

            <button
              id="tab-conformance"
              type="button"
              onClick={() => setActiveTab('conformance')}
              className={`flex items-center gap-1.5 py-2 px-4 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                activeTab === 'conformance'
                  ? 'bg-slate-100 text-slate-800 font-bold'
                  : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              <span>Conformidade</span>
            </button>

            <button
              id="tab-performance"
              type="button"
              onClick={() => setActiveTab('performance')}
              className={`flex items-center gap-1.5 py-2 px-4 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                activeTab === 'performance'
                  ? 'bg-slate-100 text-slate-800 font-bold'
                  : 'text-slate-500 hover:bg-slate-50'
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span>Desempenho (DFG)</span>
            </button>
          </div>

          {/* Active Operational Context Badge */}
          <div className="hidden xl:flex items-center gap-2 bg-slate-50 border border-slate-200/80 px-3 py-1.5 rounded-lg text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                filters.regime?.includes('20s') || filters.regime?.includes('B')
                  ? 'bg-indigo-500'
                  : 'bg-amber-500'
              }`}
            />
            <span className="font-bold text-slate-800">
              Linha {filters.line}
            </span>
            <span className="text-slate-300">•</span>
            <span className="font-semibold text-slate-600">
              {filters.direction}
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-slate-500 text-[11px]">
              {filters.startDate === filters.endDate
                ? filters.startDate.split('-').reverse().join('/')
                : `${filters.startDate.split('-').reverse().join('/')} a ${filters.endDate.split('-').reverse().join('/')}`}
            </span>
            <span
              className={`px-1.5 py-0.5 text-[10px] font-extrabold rounded ${
                filters.regime?.includes('20s') || filters.regime?.includes('B')
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {filters.regime?.includes('20s') || filters.regime?.includes('B')
                ? 'Regime B (20s)'
                : 'Regime A (2m)'}
            </span>
          </div>

          {/* Quick Metrics display */}
          <div className="flex items-center gap-6 text-xs border-l border-slate-100 pl-6 h-8">
            {conformanceData && (
              <>
                <div className="flex flex-col text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Fitness</span>
                  <span className="font-extrabold text-slate-700">{conformanceData.avg_fitness ? conformanceData.avg_fitness.toFixed(3) : '0.000'}</span>
                </div>
                <div className="flex flex-col text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Conformidade</span>
                  <span className="font-extrabold text-slate-700">{conformanceData.fit_percentage ? conformanceData.fit_percentage.toFixed(1) : '0.0'}%</span>
                </div>
                <div className="flex flex-col text-right">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Viagens</span>
                  <span className="font-extrabold text-slate-700">{conformanceData.total_cases || 0}</span>
                </div>
              </>
            )}
          </div>
        </header>

        {/* Tab Content Rendering */}
        <div className="flex-1 min-h-0 relative">
          {activeTab === 'audit' && (
            <FleetAuditView
              filters={filters}
              setFilters={setFilters}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'map' && (
            <GeospatialConsole
              mapData={mapData}
              isLogicalMode={isLogicalMode}
              setIsLogicalMode={setIsLogicalMode}
              isLoading={isLoading}
              filters={filters}
            />
          )}

          {activeTab === 'petri' && (
            <ProcessVisualizer petriNetData={petriNetData} />
          )}

          {activeTab === 'conformance' && (
            <ConformanceInspector conformanceData={conformanceData} />
          )}

          {activeTab === 'performance' && (
            <BottleneckProfiler performanceData={performanceData} />
          )}
        </div>
      </main>
    </div>
  );
}
