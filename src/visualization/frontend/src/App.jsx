import React, { useState, useEffect, useRef } from 'react';
import SidebarFilters from './components/SidebarFilters';
import GeospatialConsole from './components/GeospatialConsole';
import ProcessVisualizer from './components/ProcessVisualizer';
import ConformanceInspector from './components/ConformanceInspector';
import BottleneckProfiler from './components/BottleneckProfiler';
import FleetAuditView from './components/FleetAuditView';
import MiningConsole from './components/MiningConsole';
import { Layers, GitCommit, ShieldAlert, BarChart3, ClipboardCheck, ArrowLeft } from 'lucide-react';

const STORAGE_FILTERS_KEY = 'urbs_pm_filters';
const STORAGE_TAB_KEY = 'urbs_pm_active_tab';

const DEFAULT_FILTERS = {
  regime: 'Regime B (20s)',
  line: '541',
  direction: 'VOLTA',
  startDate: '2025-12-02',
  endDate: '2025-12-08'
};

function getSavedFilters() {
  try {
    const raw = localStorage.getItem(STORAGE_FILTERS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...DEFAULT_FILTERS, ...parsed };
    }
  } catch {}
  return DEFAULT_FILTERS;
}

function getSavedTab() {
  try {
    const raw = localStorage.getItem(STORAGE_TAB_KEY);
    if (raw && ['audit', 'conformance', 'performance', 'map', 'petri'].includes(raw)) {
      return raw;
    }
  } catch {}
  return 'audit';
}

export default function App() {
  const [filters, setFilters] = useState(getSavedFilters);
  const [activeTab, setActiveTab] = useState(getSavedTab);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_FILTERS_KEY, JSON.stringify(filters));
    } catch {}
  }, [filters]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_TAB_KEY, activeTab);
    } catch {}
  }, [activeTab]);
  const [activeTripId, setActiveTripId] = useState(null);
  const [processingLogs, setProcessingLogs] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [miningStatus, setMiningStatus] = useState('idle');
  const [isLogicalMode, setIsLogicalMode] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // Elevated fleet audit state (avoids duplicate fetch and supplies activeLineName)
  const [fleetAudit, setFleetAudit] = useState(null);
  const [fleetAuditLoading, setFleetAuditLoading] = useState(false);
  const fleetAuditReqSeq = useRef(0);
  const regimeParam = filters.regime?.includes('20s') || filters.regime?.includes('B') ? 'B' : 'A';

  const fetchFleetAudit = async () => {
    const seq = ++fleetAuditReqSeq.current;
    setFleetAuditLoading(true);
    try {
      const res = await fetch(`/api/fleet-audit?regime=${regimeParam}&start_date=${filters.startDate}&end_date=${filters.endDate}`);
      const data = res.ok ? await res.json() : null;
      if (seq === fleetAuditReqSeq.current && data) setFleetAudit(data);
    } catch {} finally {
      if (seq === fleetAuditReqSeq.current) setFleetAuditLoading(false);
    }
  };

  useEffect(() => {
    fetchFleetAudit();
  }, [regimeParam, filters.startDate, filters.endDate]);

  const activeLineName = fleetAudit?.lines?.find(l => l.line === filters.line)?.name || null;

  // Loaded data states
  const [mapData, setMapData] = useState(null);
  const [petriNetData, setPetriNetData] = useState(null);
  const [conformanceData, setConformanceData] = useState(null);
  const [conformanceLoading, setConformanceLoading] = useState(false);
  const conformanceReqSeq = useRef(0);
  const [performanceData, setPerformanceData] = useState(null);

  // Independent, fast conformance fetch (decoupled from the heavy overview pipeline)
  const fetchConformance = async () => {
    const seq = ++conformanceReqSeq.current;
    setConformanceLoading(true);
    const { line, startDate, endDate, direction } = filters;
    const query = `line=${line}&start_date=${startDate}&end_date=${endDate}&direction=${direction}`;
    try {
      const res = await fetch(`/api/conformance?${query}`);
      if (seq === conformanceReqSeq.current) setConformanceData(res.ok ? await res.json() : null);
    } catch {
      if (seq === conformanceReqSeq.current) setConformanceData(null);
    } finally {
      if (seq === conformanceReqSeq.current) setConformanceLoading(false);
    }
  };

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    setIsLoading(true);
    const { line, startDate, endDate, direction } = filters;
    const query = `line=${line}&start_date=${startDate}&end_date=${endDate}&direction=${direction}`;

    try {
      const res = await fetch(`/api/dashboard-overview?${query}`);
      if (res.ok) {
        const data = await res.json();
        setMapData(data.map_data || null);
        setPetriNetData(data.discovery || null);
        setPerformanceData(data.performance || null);
      } else {
        setMapData(null);
        setPetriNetData(null);
        setPerformanceData(null);
      }
    } catch (err) {
      console.error('Error fetching dashboard metrics:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Triggered on page load or parameters change (if logs exist)
  useEffect(() => {
    fetchConformance();
    fetchDashboardData();
  }, [filters.line, filters.direction, filters.startDate, filters.endDate]);

  // Execute Event Log generation via SSE
  const handleRunMining = () => {
    setIsProcessing(true);
    setMiningStatus('running');
    setProcessingLogs([]);
    
    const { line, startDate, endDate } = filters;
    const sse = new EventSource(`/api/process-stream?line=${line}&start_date=${startDate}&end_date=${endDate}`);

    sse.onmessage = (event) => {
      const msg = event.data;
      if (msg === '__SUCCESS__') {
        setProcessingLogs(prev => [...prev, 'Log de Eventos processado com sucesso!']);
        setIsProcessing(false);
        setMiningStatus('success');
        sse.close();
        fetchConformance(); // Refresh UI
        fetchDashboardData();
        fetchFleetAudit();
      } else if (msg === '__FAILURE__') {
        setProcessingLogs(prev => [...prev, 'Erro crítico no processamento dos dados.']);
        setIsProcessing(false);
        setMiningStatus('error');
        sse.close();
      } else {
        setProcessingLogs(prev => [...prev, msg]);
      }
    };

    sse.onerror = () => {
      setProcessingLogs(prev => [...prev, 'Falha de comunicação com o servidor SSE.']);
      setIsProcessing(false);
      setMiningStatus('error');
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
        isProcessing={isProcessing}
        activeTab={activeTab}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Top Header / Funnel Navigation & Breadcrumbs */}
        <header className="bg-white border-b border-slate-200 flex flex-col flex-shrink-0 shadow-xs">
          {/* Row 1: Funnel Navigation Tabs (1 -> 2 -> 3 -> 4 -> 5) */}
          <div className="h-12 px-6 flex items-center justify-between">
            <div className="flex items-center gap-1">
              <button
                id="tab-audit"
                type="button"
                onClick={() => setActiveTab('audit')}
                className={`flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                  activeTab === 'audit'
                    ? 'bg-slate-100 text-slate-800 font-bold'
                    : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                <ClipboardCheck className="h-3.5 w-3.5" />
                <span>1. Auditoria Diária (CCO)</span>
              </button>

              <button
                id="tab-conformance"
                type="button"
                onClick={() => setActiveTab('conformance')}
                className={`flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                  activeTab === 'conformance'
                    ? 'bg-slate-100 text-slate-800 font-bold'
                    : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                <ShieldAlert className="h-3.5 w-3.5" />
                <span>2. Conformidade Normativa</span>
              </button>

              <button
                id="tab-performance"
                type="button"
                onClick={() => setActiveTab('performance')}
                className={`flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                  activeTab === 'performance'
                    ? 'bg-slate-100 text-slate-800 font-bold'
                    : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                <BarChart3 className="h-3.5 w-3.5" />
                <span>3. Gargalos Operacionais (DFG)</span>
              </button>

              <button
                id="tab-map"
                type="button"
                onClick={() => setActiveTab('map')}
                className={`flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                  activeTab === 'map'
                    ? 'bg-slate-100 text-slate-800 font-bold'
                    : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                <span>4. Mapa de Replay</span>
              </button>

              <button
                id="tab-petri"
                type="button"
                onClick={() => setActiveTab('petri')}
                className={`flex items-center gap-1.5 py-1.5 px-3 rounded-lg text-xs font-semibold tracking-tight transition-all ${
                  activeTab === 'petri'
                    ? 'bg-slate-100 text-slate-800 font-bold'
                    : 'text-slate-500 hover:bg-slate-50'
                }`}
              >
                <GitCommit className="h-3.5 w-3.5" />
                <span>5. Descoberta de Processos</span>
              </button>
            </div>
          </div>

          {/* Row 2: Contextual Breadcrumb & Quick Metrics */}
          <div className="h-10 px-6 border-t border-slate-100 flex items-center justify-between bg-slate-50/50">
            {activeTab === 'audit' ? (
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-slate-700">
                  Visão Geral da Frota URBS — Painel Executivo CCO
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-100 text-blue-800">
                  Regime {regimeParam}
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2 overflow-x-auto py-1">
                <button
                  type="button"
                  onClick={() => setActiveTab('audit')}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-blue-600 transition-colors shadow-xs mr-2"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Voltar à Frota</span>
                </button>

                <div className="flex items-center gap-1.5 text-[11px]">
                  <button
                    type="button"
                    onClick={() => setActiveTab('audit')}
                    className="text-slate-400 hover:text-slate-600 font-medium transition-colors"
                  >
                    Auditoria CCO
                  </button>
                  <span className="text-slate-300">›</span>
                  <span className="font-semibold text-slate-800">
                    Linha {filters.line} {activeLineName ? `(${activeLineName})` : ''}
                  </span>
                  <span className="text-slate-300">›</span>
                  <span className="font-semibold text-blue-700">
                    {filters.direction}
                  </span>
                  <span className="text-slate-300">›</span>
                  <span className="text-slate-500 font-mono">
                    {filters.startDate === filters.endDate
                      ? filters.startDate.split('-').reverse().join('/')
                      : `${filters.startDate.split('-').reverse().join('/')} a ${filters.endDate.split('-').reverse().join('/')}`}
                  </span>
                  <span className="ml-1 px-1.5 py-0.5 text-[10px] font-bold rounded bg-blue-100 text-blue-800">
                    Regime {regimeParam}
                  </span>
                </div>
              </div>
            )}

            {/* Quick Metrics display (active when on line-specific tabs) */}
            {activeTab !== 'audit' && (
              <div className="flex items-center gap-4 text-xs transition-opacity duration-200">
                {(isLoading || conformanceLoading) && (
                  <div className="flex items-center gap-1.5 text-blue-600 font-semibold text-[11px] bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200 shadow-2xs">
                    <div className="h-3 w-3 animate-spin rounded-full border-2 border-blue-300 border-t-blue-700"></div>
                    <span>Atualizando {filters.direction}...</span>
                  </div>
                )}
                {conformanceLoading ? (
                  <>
                    <div className="flex flex-col text-right">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Fitness</span>
                      <span className="inline-block h-4 w-10 bg-slate-200 animate-pulse rounded" />
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Conformidade</span>
                      <span className="inline-block h-4 w-10 bg-slate-200 animate-pulse rounded" />
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Total Viagens</span>
                      <span className="inline-block h-4 w-10 bg-slate-200 animate-pulse rounded" />
                    </div>
                  </>
                ) : conformanceData && (
                  <>
                    <div className="flex flex-col text-right">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Fitness</span>
                      <span className="font-extrabold text-slate-700">
                        {conformanceData.avg_fitness ? conformanceData.avg_fitness.toFixed(3) : '0.000'}
                      </span>
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Conformidade</span>
                      <span className="font-extrabold text-slate-700">
                        {conformanceData.fit_percentage ? conformanceData.fit_percentage.toFixed(1) : '0.0'}%
                      </span>
                    </div>
                    <div className="flex flex-col text-right">
                      <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">Total Viagens</span>
                      <span className="font-extrabold text-slate-700">{conformanceData.total_cases || 0}</span>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </header>

        {/* Tab Content Rendering */}
        <div className="flex-1 min-h-0 relative">
          {activeTab === 'audit' && (
            <FleetAuditView
              auditData={fleetAudit}
              loading={fleetAuditLoading}
              setFilters={setFilters}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'conformance' && (
            <ConformanceInspector
              conformanceData={conformanceData}
              isLoading={conformanceLoading}
              activeDirection={filters.direction}
              onTripSelect={(id) => {
                setActiveTripId(id);
                setActiveTab('map');
              }}
            />
          )}

          {activeTab === 'performance' && (
            <BottleneckProfiler performanceData={performanceData} />
          )}

          {activeTab === 'map' && (
            <GeospatialConsole
              mapData={mapData}
              isLogicalMode={isLogicalMode}
              setIsLogicalMode={setIsLogicalMode}
              isLoading={isLoading}
              filters={filters}
              activeTripId={activeTripId}
              onClearTrip={() => setActiveTripId(null)}
            />
          )}

          {activeTab === 'petri' && (
            <ProcessVisualizer petriNetData={petriNetData} />
          )}
        </div>
      </main>

      {/* Floating execution console drawer (on demand) */}
      {miningStatus !== 'idle' && (
        <div className="fixed bottom-4 right-4 z-50 w-96 max-w-[calc(100vw-2rem)] shadow-2xl rounded-xl overflow-hidden border border-slate-800">
          <MiningConsole
            logs={processingLogs}
            status={miningStatus}
            onClear={() => setProcessingLogs([])}
            onDismiss={miningStatus !== 'running'
              ? () => { setProcessingLogs([]); setMiningStatus('idle'); }
              : undefined}
          />
        </div>
      )}
    </div>
  );
}

