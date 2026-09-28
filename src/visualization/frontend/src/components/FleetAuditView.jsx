import React from 'react';
import { Activity, ChevronRight } from 'lucide-react';

export default function FleetAuditView({ auditData, loading, setFilters, setActiveTab }) {
  const handleInspectLine = (lineCode, targetDir = null) => {
    setFilters(prev => {
      let nextDir = targetDir;
      if (!nextDir) {
        const lineData = auditData?.lines?.find(l => l.line === lineCode);
        if (lineData?.skipped_by_direction) {
          const dirsWithSkips = Object.entries(lineData.skipped_by_direction).filter(([_, c]) => c > 0);
          if (dirsWithSkips.length === 1) {
            nextDir = dirsWithSkips[0][0];
          }
        }
      }
      return {
        ...prev,
        line: lineCode,
        direction: nextDir || prev.direction || 'VOLTA'
      };
    });
    setActiveTab('conformance');
  };

  if (!auditData) {
    return (
      <div className="flex h-full items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>
          <span className="text-xs font-semibold text-slate-500">Consolidando auditoria da frota...</span>
        </div>
      </div>
    );
  }

  const summary = auditData?.summary || {
    total_lines: 0,
    total_trips_audited: 0,
    avg_fleet_conformance: 0,
    total_skipped_stops: 0
  };

  const lines = auditData?.lines || [];

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-6 space-y-6">
      {/* Title & Scope Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-5">
        <div>
          <h2 className="text-lg font-bold text-slate-800 tracking-tight">
            Auditoria Operacional Diária — CCO URBS
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Painel executivo de encerramento do dia para fiscalização de itinerário, pontualidade e paradas omitidas
          </p>
        </div>
        <div className="flex items-center gap-2">
          {loading && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 animate-pulse">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
              Atualizando…
            </span>
          )}
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-200 text-slate-700">
            Período: {auditData?.date_range || 'N/D'}
          </span>
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Regime {auditData?.regime}
          </span>
        </div>
      </div>

      {/* Global Fleet KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Linhas Monitoradas</div>
          <div className="text-2xl font-black text-slate-800 mt-1">{summary.total_lines}</div>
          <div className="text-[11px] text-slate-500 mt-1">Arquétipos operacionais auditados</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Viagens Totais Auditadas</div>
          <div className="text-2xl font-black text-blue-600 mt-1">{summary.total_trips_audited.toLocaleString('pt-BR')}</div>
          <div className="text-[11px] text-slate-500 mt-1">Casos minerados no período (ambos os sentidos)</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Aderência Média da Frota</div>
          <div className="text-2xl font-black text-emerald-600 mt-1">{summary.avg_fleet_adherence ?? summary.avg_fleet_conformance}%</div>
          <div className="text-[11px] text-slate-500 mt-1">Aderência normativa ao traçado</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Paradas Omitidas Detectadas</div>
          <div className="text-2xl font-black text-amber-600 mt-1">{summary.total_skipped_stops.toLocaleString('pt-BR')}</div>
          <div className="text-[11px] text-slate-500 mt-1">Pontos não visitados (&gt;150m)</div>
        </div>
      </div>

      {/* Fleet Comparison Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800">
              Diagnóstico Operacional por Linha de Transporte
            </h3>
            <p className="text-xs text-slate-400">Classificação de conformidade e gargalos estruturais identificados</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-slate-400 font-bold text-[10px] uppercase tracking-wider">
                <th className="py-3 px-5">Linha</th>
                <th className="py-3 px-5">Nome / Tipo</th>
                <th className="py-3 px-5 text-right">Viagens (IDA+VOLTA)</th>
                <th className="py-3 px-5">Aderência / Conformidade</th>
                <th className="py-3 px-5 text-right">Paradas Puladas</th>
                <th className="py-3 px-5 text-right">Gargalos (&gt;2min)</th>
                <th className="py-3 px-5 text-center">Status</th>
                <th className="py-3 px-5 text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {lines.map((l) => {
                const score = l.adherence_pct ?? l.fit_percentage ?? 0;
                return (
                <tr key={l.line} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-5 font-bold text-slate-800">
                    <span className="bg-slate-100 px-2 py-1 rounded text-slate-700 font-mono">
                      {l.line}
                    </span>
                  </td>
                  <td className="py-3.5 px-5">
                    <div className="flex flex-col">
                      <span className="text-slate-700 font-semibold">{l.name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        Escopo: {l.direction || 'IDA+VOLTA'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-5 text-right font-mono text-slate-700">{l.total_cases}</td>
                  <td className="py-3.5 px-5">
                    <div className="w-40 flex flex-col gap-0.5">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-100 h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              score >= 80 ? 'bg-emerald-500' : score >= 45 ? 'bg-amber-500' : 'bg-rose-500'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                          />
                        </div>
                        <span className="text-[11px] font-bold text-slate-700 w-12 text-right">
                          {score.toFixed(1)}%
                        </span>
                      </div>
                      <span className="text-[9px] text-slate-400 font-mono">
                        {l.fit_percentage > 0 ? `${l.fit_percentage.toFixed(1)}% 100% conformes` : 'Subamostragem de 2m'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-5 text-right">
                    <div className="flex flex-col items-end">
                      <span className={`font-mono font-bold text-xs ${l.skipped_stops_count > 0 ? 'text-amber-700' : 'text-slate-500'}`}>
                        {l.skipped_stops_count}
                      </span>
                      {l.skipped_by_direction && Object.keys(l.skipped_by_direction).length > 0 && (
                        <div className="flex items-center gap-1 text-[10px] mt-0.5 font-mono">
                          {Object.entries(l.skipped_by_direction).map(([dir, count]) => (
                            <button
                              key={dir}
                              type="button"
                              onClick={() => handleInspectLine(l.line, dir)}
                              title={`Inspecionar linha ${l.line} no sentido ${dir} (${count} paradas puladas)`}
                              className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] transition-all cursor-pointer ${
                                count > 0
                                  ? 'font-bold text-amber-800 bg-amber-100 hover:bg-amber-200 border border-amber-300'
                                  : 'text-slate-400 hover:text-slate-600 bg-slate-100 hover:bg-slate-200'
                              }`}
                            >
                              {dir}: {count}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="py-3.5 px-5 text-right font-mono text-slate-700">{l.bottlenecks_count}</td>
                  <td className="py-3.5 px-5 text-center">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        l.status === 'CONFORME'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : l.status === 'ATENÇÃO'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}
                    >
                      {l.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-5 text-right">
                    <button
                      type="button"
                      onClick={() => handleInspectLine(l.line)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded-md transition-colors"
                    >
                      <span>Inspecionar</span>
                      <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
            </tbody>
          </table>
        </div>
      </div>

      {/* CCO Recommendations Banner */}
      <div className="bg-slate-900 text-white rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-blue-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Diretrizes de Fiscalização para o CCO
          </h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          Com base na mineração de processos da amostragem diária, os fiscais da URBS podem verificar diretamente as
          viagens identificadas com anomalias de itinerário e omissão de pontos de parada. Ao selecionar "Inspecionar" em qualquer
          linha, o painel abre os detalhes de conformidade e o replay geográfico das viagens afetadas.
        </p>
      </div>
    </div>
  );
}
