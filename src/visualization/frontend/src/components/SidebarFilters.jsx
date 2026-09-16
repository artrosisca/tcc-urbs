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
  const [minedLines, setMinedLines] = useState([]);
  const [rawLines, setRawLines] = useState([]);
  const [tripStatus, setTripStatus] = useState(null);
  const [showCustomDates, setShowCustomDates] = useState(false);

  // Available regime presets with full week and individual days
  const regimeConfig = {
    'Regime A (2m)': {
      regimeParam: 'A',
      week: { label: 'Semana Completa (24 a 30/10/2025)', start: '2025-10-24', end: '2025-10-30' },
      days: [
        { label: '24/10/2025 (Sex)', start: '2025-10-24', end: '2025-10-24' },
        { label: '25/10/2025 (Sáb)', start: '2025-10-25', end: '2025-10-25' },
        { label: '26/10/2025 (Dom)', start: '2025-10-26', end: '2025-10-26' },
        { label: '27/10/2025 (Seg)', start: '2025-10-27', end: '2025-10-27' },
        { label: '28/10/2025 (Ter)', start: '2025-10-28', end: '2025-10-28' },
        { label: '29/10/2025 (Qua)', start: '2025-10-29', end: '2025-10-29' },
        { label: '30/10/2025 (Qui)', start: '2025-10-30', end: '2025-10-30' }
      ]
    },
    'Regime B (20s)': {
      regimeParam: 'B',
      week: { label: 'Semana Completa (02 a 08/12/2025)', start: '2025-12-02', end: '2025-12-08' },
      days: [
        { label: '02/12/2025 (Ter)', start: '2025-12-02', end: '2025-12-02' },
        { label: '03/12/2025 (Qua)', start: '2025-12-03', end: '2025-12-03' },
        { label: '04/12/2025 (Qui)', start: '2025-12-04', end: '2025-12-04' },
        { label: '05/12/2025 (Sex)', start: '2025-12-05', end: '2025-12-05' },
        { label: '06/12/2025 (Sáb)', start: '2025-12-06', end: '2025-12-06' },
        { label: '07/12/2025 (Dom)', start: '2025-12-07', end: '2025-12-07' },
        { label: '08/12/2025 (Seg)', start: '2025-12-08', end: '2025-12-08' }
      ]
    }
  };

  const currentRegimeKey = regimeConfig[filters.regime]
    ? filters.regime
    : (filters.regime?.includes('20s') || filters.regime?.includes('B') ? 'Regime B (20s)' : 'Regime A (2m)');
  const currentRegime = regimeConfig[currentRegimeKey];

  useEffect(() => {
    const fetchLines = async () => {
      try {
        const regimeParam = currentRegimeKey.includes('20s') ? 'B' : 'A';
        const res = await fetch(`/api/lines?regime=${encodeURIComponent(regimeParam)}&include_raw=true`);
        if (res.ok) {
          const data = await res.json();
          const linesArray = data.lines || [];
          const mined = data.mined_lines || [];
          const raw = data.raw_lines || [];
          setAvailableLines(linesArray);
          setMinedLines(mined);
          setRawLines(raw);
          if (linesArray.length > 0 && !linesArray.includes(filters.line)) {
            setFilters(prev => ({ ...prev, line: mined[0] || linesArray[0] }));
          }
        }
      } catch (err) {
        console.error('Error fetching bus lines:', err);
      }
    };
    fetchLines();
  }, [currentRegimeKey]);

  // Check available trips status
  useEffect(() => {
    let isMounted = true;
    setTripStatus(null);
    const checkStatus = async () => {
      if (!filters.line || !filters.startDate || !filters.endDate) return;
      try {
        const query = `line=${filters.line}&start_date=${filters.startDate}&end_date=${filters.endDate}&start_hour=${filters.startHour}&end_hour=${filters.endHour}`;
        const res = await fetch(`/api/check-trips?${query}`);
        if (res.ok && isMounted) {
          const data = await res.json();
          setTripStatus(data);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Error checking trips:', err);
        }
      }
    };
    checkStatus();
    return () => {
      isMounted = false;
    };
  }, [filters.line, filters.startDate, filters.endDate, filters.startHour, filters.endHour]);

  const handleRegimeChange = (regimeKey) => {
    const defaultPeriod = regimeConfig[regimeKey].week;
    setFilters(prev => ({
      ...prev,
      regime: regimeKey,
      startDate: defaultPeriod.start,
      endDate: defaultPeriod.end
    }));
  };

  const handlePeriodChange = (start, end) => {
    setFilters(prev => ({
      ...prev,
      startDate: start,
      endDate: end
    }));
  };

  const isWeekSelected = filters.startDate === currentRegime.week.start && filters.endDate === currentRegime.week.end;
  const isSingleDaySelected = filters.startDate === filters.endDate;

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
        {/* Bus Line Selector */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Linha de Ônibus</label>
            <span className="text-[10px] font-bold text-slate-400">
              {rawLines.length + minedLines.length} linhas disponíveis
            </span>
          </div>
          <select
            value={filters.line}
            onChange={(e) => setFilters(prev => ({ ...prev, line: e.target.value }))}
            className="w-full bg-white border border-slate-200 rounded-lg py-2 px-3 text-xs text-slate-700 font-medium focus:border-slate-400 outline-none cursor-pointer"
          >
            {minedLines.length > 0 && (
              <optgroup label={`⭐ Linhas Mineradas / Prontas (${minedLines.length})`}>
                {minedLines.map(line => (
                  <option key={line} value={line}>
                    Linha {line} (Log de Eventos Pronto)
                  </option>
                ))}
              </optgroup>
            )}
            {rawLines.length > 0 && (
              <optgroup label={`📡 Dados Brutos de GPS (${rawLines.length} linhas)`}>
                {rawLines.map(line => (
                  <option key={line} value={line}>
                    Linha {line} (Bruto — requer mineração)
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>

        {/* Period Preset Selection */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5" />
              <span>Período de Análise</span>
            </label>
            <button
              type="button"
              onClick={() => setShowCustomDates(prev => !prev)}
              className="text-[10px] text-blue-600 hover:text-blue-800 font-medium"
            >
              {showCustomDates ? 'Predefinições' : 'Datas Livres'}
            </button>
          </div>

          {!showCustomDates ? (
            <div className="space-y-2">
              {/* Full Week Button */}
              <button
                type="button"
                onClick={() => handlePeriodChange(currentRegime.week.start, currentRegime.week.end)}
                className={`w-full py-2 px-3 text-xs rounded-lg border text-left flex items-center justify-between transition-all ${
                  isWeekSelected
                    ? 'bg-blue-50 border-blue-300 text-blue-800 font-semibold shadow-xs'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <span>{currentRegime.week.label}</span>
                {isWeekSelected && <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>}
              </button>

              {/* Day Selector Dropdown */}
              <div className="space-y-1">
                <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
                  Auditoria Diária (Dia Específico)
                </span>
                <select
                  value={isSingleDaySelected ? filters.startDate : ''}
                  onChange={(e) => {
                    if (e.target.value) {
                      handlePeriodChange(e.target.value, e.target.value);
                    }
                  }}
                  className={`w-full bg-white border rounded-lg py-1.5 px-2.5 text-xs outline-none cursor-pointer ${
                    isSingleDaySelected
                      ? 'border-blue-300 text-blue-800 font-medium bg-blue-50/50'
                      : 'border-slate-200 text-slate-600'
                  }`}
                >
                  <option value="">Selecione um dia da semana...</option>
                  {currentRegime.days.map((d) => (
                    <option key={d.start} value={d.start}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-semibold text-slate-500">Início</label>
                  <input
                    type="date"
                    value={filters.startDate}
                    onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
                    className="w-full bg-white border border-slate-200 rounded py-1 px-2 text-xs text-slate-700"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-semibold text-slate-500">Fim</label>
                  <input
                    type="date"
                    value={filters.endDate}
                    onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
                    className="w-full bg-white border border-slate-200 rounded py-1 px-2 text-xs text-slate-700"
                  />
                </div>
              </div>
            </div>
          )}
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

      {/* Advanced Settings & Logs details */}
      <details className="group bg-slate-950 border-t border-slate-800" open={isProcessing}>
        <summary className="p-3 text-[10px] uppercase font-bold text-slate-500 tracking-wider cursor-pointer hover:text-slate-300 transition-colors list-none flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Settings className="h-3.5 w-3.5" />
            <span>Configurações TCC / Logs</span>
          </div>
          <span className="group-open:rotate-180 transition-transform">▼</span>
        </summary>
        
        <div className="px-4 pb-4 space-y-4">
          {/* Regime Settings */}
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">Regime de Coleta</label>
            <div className="grid grid-cols-2 gap-2">
              {Object.keys(regimeConfig).map(regName => (
                <button
                  key={regName}
                  type="button"
                  onClick={() => handleRegimeChange(regName)}
                  className={`py-1.5 px-2 text-[10px] font-medium rounded border text-center transition-all ${
                    currentRegimeKey === regName
                      ? 'bg-blue-900 border-blue-700 text-white'
                      : 'bg-slate-900 border-slate-700 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  {regName}
                </button>
              ))}
            </div>
          </div>

          {/* SSE Logs */}
          <div className="flex flex-col font-mono text-[10px] text-slate-300 h-32">
            <div className="flex items-center gap-1.5 text-[9px] uppercase font-bold text-slate-500 mb-1 tracking-wider">
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
        </div>
      </details>
    </aside>
  );
}
