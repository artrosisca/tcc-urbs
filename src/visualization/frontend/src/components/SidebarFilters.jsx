import React, { useState, useEffect } from 'react';
import { Play, Settings, RefreshCw, Terminal, CheckCircle, AlertCircle, Calendar } from 'lucide-react';

export default function SidebarFilters({
  filters,
  setFilters,
  onRunMining,
  processingLogs,
  isProcessing
}) {
  const [availableLines, setAvailableLines] = useState([]);
  const [tripStatus, setTripStatus] = useState(null);

  // Available regime presets
  const regimeConfig = {
    'Regime A (2m)': {
      regimeParam: 'A',
      periods: [
        { label: 'Semana Completa (24 a 30/10/2025)', start: '2025-10-24', end: '2025-10-30' },
        { label: '1 Dia (24/10/2025)', start: '2025-10-24', end: '2025-10-24' }
      ]
    },
    'Regime B (20s)': {
      regimeParam: 'B',
      periods: [
        { label: 'Semana Completa (02 a 08/12/2025)', start: '2025-12-02', end: '2025-12-08' },
        { label: '1 Dia (02/12/2025)', start: '2025-12-02', end: '2025-12-02' }
      ]
    }
  };

  const currentRegimeKey = Object.keys(regimeConfig).find(k => filters.regime.includes(k.split(' ')[0])) || 'Regime B (20s)';
  const currentPeriods = regimeConfig[currentRegimeKey]?.periods || [];

  useEffect(() => {
    const fetchLines = async () => {
      try {
        const regimeParam = currentRegimeKey.includes('20s') ? 'B' : 'A';
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
  }, [filters.regime]);

  // Check available trips status
  useEffect(() => {
    const checkStatus = async () => {
      if (!filters.line || !filters.startDate || !filters.endDate) return;
      try {
        const query = `line=${filters.line}&start_date=${filters.startDate}&end_date=${filters.endDate}&start_hour=${filters.startHour}&end_hour=${filters.endHour}`;
        const res = await fetch(`/api/check-trips?${query}`);
        if (res.ok) {
          const data = await res.json();
          setTripStatus(data);
        }
      } catch (err) {
        console.error('Error checking trips:', err);
      }
    };
    checkStatus();
  }, [filters.line, filters.startDate, filters.endDate, filters.startHour, filters.endHour]);

  const handleRegimeChange = (regimeKey) => {
    const defaultPeriod = regimeConfig[regimeKey].periods[0];
    setFilters(prev => ({
      ...prev,
      regime: regimeKey,
      startDate: defaultPeriod.start,
      endDate: defaultPeriod.end
    }));
  };

  const handlePeriodChange = (period) => {
    setFilters(prev => ({
      ...prev,
      startDate: period.start,
      endDate: period.end
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
      <div className="p-5 flex-1 overflow-y-auto space-y-5">
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
                  currentRegimeKey === regName
                    ? 'bg-slate-900 border-slate-900 text-white shadow-sm'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {regName}
              </button>
            ))}
          </div>
        </div>

        {/* Period Preset Selection */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
            <Calendar className="h-3.5 w-3.5" />
            <span>Período de Análise</span>
          </label>
          <div className="space-y-1.5">
            {currentPeriods.map((p, idx) => {
              const isSelected = filters.startDate === p.start && filters.endDate === p.end;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handlePeriodChange(p)}
                  className={`w-full py-1.5 px-2.5 text-xs rounded-lg border text-left flex items-center justify-between transition-all ${
                    isSelected
                      ? 'bg-blue-50 border-blue-300 text-blue-800 font-medium'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <span>{p.label}</span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>}
                </button>
              );
            })}
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

        {/* Trips Status Card */}
        {tripStatus && (
          <div className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
            tripStatus.status === 'processed'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : tripStatus.exists
              ? 'bg-amber-50 border-amber-200 text-amber-800'
              : 'bg-slate-50 border-slate-200 text-slate-600'
          }`}>
            {tripStatus.status === 'processed' ? (
              <CheckCircle className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
            )}
            <div className="leading-snug">
              <div className="font-semibold">
                {tripStatus.status === 'processed'
                  ? `Pronto (${tripStatus.count} viagens)`
                  : tripStatus.exists
                  ? `Disponível para minerar (${tripStatus.count} pts)`
                  : 'Sem dados para este filtro'}
              </div>
              <div className="text-[11px] opacity-80 mt-0.5">{tripStatus.message}</div>
            </div>
          </div>
        )}

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
          <span>{isProcessing ? 'Minerando Processos...' : 'Executar / Reprocessar Mineração'}</span>
        </button>
      </div>

      {/* SSE Log Box */}
      <div className="p-4 bg-slate-950 border-t border-slate-800 h-44 flex flex-col font-mono text-[10px] text-slate-300">
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
                  log.includes('Concluído') || log.includes('salvo') || log.includes('sucesso')
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
