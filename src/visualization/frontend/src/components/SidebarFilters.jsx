import React, { useState, useEffect } from 'react';
import { Play, Settings, RefreshCw, Terminal, CheckCircle } from 'lucide-react';

export default function SidebarFilters({
  filters,
  setFilters,
  onRunMining,
  processingLogs,
  isProcessing
}) {
  const [availableLines, setAvailableLines] = useState([]);
  
  // Hardcoded date ranges corresponding to Regime A (Oct 24-30) and Regime B (Dec 02-08)
  const regimeConfig = {
    'Regime A (2 min)': { start: '2025-10-24', end: '2025-10-30' },
    'Regime B (20s)': { start: '2025-12-02', end: '2025-12-08' }
  };

  useEffect(() => {
    // Fetch available bus lines for current regime
    const fetchLines = async () => {
      try {
        const regimeParam = filters.regime.includes('Regime A') ? 'Regime A' : 'Regime B';
        const res = await fetch(`/api/lines?regime=${encodeURIComponent(regimeParam)}`);
        if (res.ok) {
          const data = await res.json();
          const linesArray = data.lines || [];
          setAvailableLines(linesArray);
          if (linesArray.length > 0 && !linesArray.includes(filters.line)) {
            setFilters(prev => ({ ...prev, line: linesArray[0] }));
          }
        }
      } catch (err) {
        console.error('Error fetching bus lines:', err);
      }
    };
    fetchLines();
  }, [filters.regime, setFilters]);

  const handleRegimeChange = (regime) => {
    const dates = regimeConfig[regime];
    setFilters(prev => ({
      ...prev,
      regime,
      startDate: dates.start,
      endDate: dates.end
    }));
  };

  return (
    <aside className="w-80 bg-white border-r border-slate-200 flex flex-col h-full flex-shrink-0">
      {/* Title */}
      <div className="p-5 border-b border-slate-200 flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-800 tracking-tight flex items-center gap-2">
          <span>🚌 URBS Process Mining</span>
        </h1>
        <span className="bg-blue-50 text-blue-700 text-xs px-2.5 py-0.5 rounded-full font-medium border border-blue-100">
          CCO Dashboard
        </span>
      </div>

      {/* Config Form */}
      <div className="p-5 flex-1 overflow-y-auto space-y-6">
        {/* Regime Selection */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Regime de Coleta</label>
          <div className="grid grid-cols-2 gap-2">
            {Object.keys(regimeConfig).map(regName => (
              <button
                key={regName}
                type="button"
                onClick={() => handleRegimeChange(regName)}
                className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition-all ${
                  filters.regime === regName
                    ? 'bg-slate-900 border-slate-900 text-white shadow-sm'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {regName.split(' ')[0]} {regName.includes('20s') ? '(20s)' : '(2m)'}
              </button>
            ))}
          </div>
        </div>

        {/* Date Fields (Read Only) */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-500">Início</label>
            <input
              type="text"
              readOnly
              value={filters.startDate}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg py-1.5 px-3 text-xs text-slate-600 outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-500">Fim</label>
            <input
              type="text"
              readOnly
              value={filters.endDate}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg py-1.5 px-3 text-xs text-slate-600 outline-none"
            />
          </div>
        </div>

        {/* Bus Line Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Linha de Ônibus</label>
          <select
            value={filters.line}
            onChange={(e) => setFilters(prev => ({ ...prev, line: e.target.value }))}
            className="w-full bg-white border border-slate-200 rounded-lg py-2 px-3 text-xs text-slate-700 font-medium focus:border-slate-400 outline-none cursor-pointer"
          >
            {availableLines.map(line => (
              <option key={line} value={line}>
                Linha {line}
              </option>
            ))}
          </select>
        </div>

        {/* Direction Toggle */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Sentido Operacional</label>
          <div className="grid grid-cols-2 gap-2">
            {['VOLTA', 'IDA'].map(dir => (
              <button
                key={dir}
                type="button"
                onClick={() => setFilters(prev => ({ ...prev, direction: dir }))}
                className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition-all ${
                  filters.direction === dir
                    ? 'bg-slate-900 border-slate-900 text-white shadow-sm'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {dir}
              </button>
            ))}
          </div>
        </div>

        {/* Start and End Hours */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-500">Hora Início</label>
            <input
              type="text"
              value={filters.startHour}
              placeholder="00:00"
              onChange={(e) => setFilters(prev => ({ ...prev, startHour: e.target.value }))}
              className="w-full bg-white border border-slate-200 rounded-lg py-1.5 px-3 text-xs text-slate-700 focus:border-slate-400 outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-500">Hora Fim</label>
            <input
              type="text"
              value={filters.endHour}
              placeholder="24:00"
              onChange={(e) => setFilters(prev => ({ ...prev, endHour: e.target.value }))}
              className="w-full bg-white border border-slate-200 rounded-lg py-1.5 px-3 text-xs text-slate-700 focus:border-slate-400 outline-none"
            />
          </div>
        </div>

        {/* Run Button */}
        <button
          type="button"
          onClick={onRunMining}
          disabled={isProcessing}
          className={`w-full py-2.5 px-4 text-xs font-semibold rounded-lg flex items-center justify-center gap-2 shadow-sm transition-all ${
            isProcessing
              ? 'bg-slate-100 border border-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-blue-600 border border-blue-600 text-white hover:bg-blue-700 active:scale-98'
          }`}
        >
          {isProcessing ? (
            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Play className="h-3.5 w-3.5 fill-current" />
          )}
          <span>{isProcessing ? 'Minerando Processos...' : 'Executar Mineração'}</span>
        </button>
      </div>

      {/* SSE Log Box */}
      <div className="p-4 bg-slate-950 border-t border-slate-800 h-56 flex flex-col font-mono text-[10px] text-slate-300">
        <div className="flex items-center gap-1.5 text-[9px] uppercase font-bold text-slate-500 mb-2 tracking-wider">
          <Terminal className="h-3 w-3" />
          <span>Console de Execução</span>
        </div>
        <div className="flex-1 overflow-y-auto space-y-1 p-2 bg-slate-900 border border-slate-800 rounded-md">
          {processingLogs.length === 0 ? (
            <span className="text-slate-600">Aguardando execução...</span>
          ) : (
            processingLogs.map((log, idx) => (
              <div
                key={idx}
                className={
                  log.includes('Concluído') || log.includes('salvo')
                    ? 'text-emerald-400'
                    : log.includes('Erro')
                    ? 'text-rose-400'
                    : 'text-slate-300'
                }
              >
                &gt; {log}
              </div>
            ))
          )}
        </div>
      </div>
    </aside>
  );
}
