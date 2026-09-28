import React from 'react';
import { ShieldAlert, CheckCircle, Percent, Activity, Compass } from 'lucide-react';
import InfoPopover from './InfoPopover';

export default function ConformanceInspector({ conformanceData, isLoading, activeDirection, onTripSelect }) {
  if (!conformanceData) {
    if (isLoading) {
      return (
        <div className="w-full h-full bg-slate-50 flex flex-col items-center justify-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>
          <span className="text-xs font-semibold text-slate-500">
            Calculando conformidade normativa ({activeDirection || 'carregando'})...
          </span>
        </div>
      );
    }
    return (
      <div className="w-full h-full bg-slate-50 flex items-center justify-center text-slate-400 text-xs">
        Sem dados de conformidade carregados. Execute a mineração.
      </div>
    );
  }

  const { avg_fitness, fit_percentage, total_cases, skipped_stops, deviant_trips, total_interpolated } = conformanceData;
  const displayInterpolated = total_interpolated ?? (deviant_trips ? deviant_trips.reduce((acc, trip) => acc + (trip.interpolated_count || 0), 0) : 0);

  return (
    <div className="w-full h-full bg-slate-50 flex flex-col p-6 overflow-y-auto space-y-6">
      {isLoading && (
        <div className="flex items-center gap-2.5 p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-xs font-medium shadow-xs">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-300 border-t-blue-700 flex-shrink-0"></div>
          <span>Atualizando métricas de conformidade para o sentido <strong>{activeDirection}</strong>... Aguarde um instante.</span>
        </div>
      )}

      <div>
        <h2 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
          Inspetor de Conformidade Normativa Topológica
          <InfoPopover title="Conformidade Normativa">
            Estimativa estatística de aderência ao traçado planejado e detecção de paradas omitidas
          </InfoPopover>
        </h2>
      </div>

      {/* KPI Cards Grid */}
      <div className={`grid grid-cols-5 gap-4 transition-opacity duration-200 ${isLoading ? 'opacity-40 pointer-events-none' : ''}`}>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
            <Percent className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              Fitness Médio
              <InfoPopover title="Fitness Médio">
                Média do trace fitness (0–1) via Token-Based Replay (PM4Py): fração dos eventos que seguem estritamente a sequência normativa de paradas.
              </InfoPopover>
            </div>
            {isLoading
              ? <div className="h-7 w-20 bg-slate-200 animate-pulse rounded-md" />
              : <div className="text-xl font-extrabold text-slate-800">{avg_fitness ? avg_fitness.toFixed(3) : '0.000'}</div>}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
            <CheckCircle className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              Viagens Conformantes
              <InfoPopover title="Viagens Conformantes">
                Percentual de viagens com replay 100% conforme — sem tokens faltantes ou remanescentes no modelo normativo.
              </InfoPopover>
            </div>
            {isLoading
              ? <div className="h-7 w-20 bg-slate-200 animate-pulse rounded-md" />
              : <div className="text-xl font-extrabold text-slate-800">{fit_percentage ? fit_percentage.toFixed(1) : '0.0'}%</div>}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 bg-purple-50 text-purple-600 rounded-lg flex items-center justify-center">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              Total de Casos
              <InfoPopover title="Total de Casos">
                Viagens avaliadas no escopo atual (linha, sentido, período e filtros ativos).
              </InfoPopover>
            </div>
            {isLoading
              ? <div className="h-7 w-20 bg-slate-200 animate-pulse rounded-md" />
              : <div className="text-xl font-extrabold text-slate-800">{total_cases || 0}</div>}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 bg-amber-50 text-amber-600 rounded-lg flex items-center justify-center">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              Paradas Puladas
              <InfoPopover title="Paradas Puladas">
                Paradas planejadas sem evento de passagem na viagem — indício de evasão de itinerário ou de gap de GPS (cruzar com Incerteza GPS).
              </InfoPopover>
            </div>
            {isLoading
              ? <div className="h-7 w-20 bg-slate-200 animate-pulse rounded-md" />
              : (
                <div className="text-xl font-extrabold text-slate-800">
                  {skipped_stops ? skipped_stops.reduce((acc, curr) => acc + curr.count, 0) : 0}
                </div>
              )}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center gap-4">
          <div className="h-10 w-10 bg-indigo-50 text-indigo-600 rounded-lg flex items-center justify-center">
            <Compass className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
              Incerteza GPS (Interpoladas)
              <InfoPopover title="Incerteza GPS">
                Eventos com horário estimado por interpolação (PCHIP) em falhas de amostragem do GPS; representam incerteza de medição, não desvio operacional.
              </InfoPopover>
            </div>
            {isLoading
              ? <div className="h-7 w-20 bg-slate-200 animate-pulse rounded-md" />
              : <div className="text-xl font-extrabold text-slate-800">{displayInterpolated}</div>}
          </div>
        </div>
      </div>

      {/* Main Content Split Panels */}
      <div className={`grid grid-cols-5 gap-6 flex-1 min-h-0 transition-opacity duration-200 ${isLoading ? 'opacity-40 pointer-events-none' : ''}`}>
        {/* Left Side: Deviant Trips Table (3 cols) */}
        <div className="col-span-3 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col min-h-[300px]">
          <div className="p-4 border-b border-slate-200">
            <h3 className="text-xs font-bold text-slate-700">Top 10 Viagens com Maior Desvio (Skipped)</h3>
          </div>
          <div className="flex-1 overflow-x-auto overflow-y-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-500 font-bold border-b border-slate-100">
                  <th className="p-3">Prefixo</th>
                  <th className="p-3">Tabela</th>
                  <th className="p-3">Visitadas</th>
                  <th className="p-3 text-rose-600">Puladas</th>
                  <th className="p-3 text-slate-500">Gaps (GPS)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {!deviant_trips || deviant_trips.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-4 text-center text-slate-400">Nenhum desvio detectado nesta seleção.</td>
                  </tr>
                ) : (
                  deviant_trips.map((trip, idx) => (
                    <tr 
                      key={trip.case_id || idx} 
                      className="hover:bg-blue-50 transition-all font-medium text-slate-700 cursor-pointer"
                      onClick={() => onTripSelect && onTripSelect(trip.case_id)}
                      title="Clique para assistir o Replay desta viagem no Mapa"
                    >
                      <td className="p-3 font-mono font-bold text-slate-900">{trip.vehicle}</td>
                      <td className="p-3 font-mono">{trip.tabela}</td>
                      <td className="p-3">{trip.total_visited}</td>
                      <td className="p-3 text-rose-600 font-bold">{trip.skipped_count}</td>
                      <td className="p-3">{trip.interpolated_count}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Side: Skipped Stops Summary (2 cols) */}
        <div className="col-span-2 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col min-h-[300px]">
          <div className="p-4 border-b border-slate-200">
            <h3 className="text-xs font-bold text-slate-700">Frequência de Paradas Puladas</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {!skipped_stops || skipped_stops.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                Nenhum ponto pulado na seleção.
              </div>
            ) : (
              skipped_stops.map((stop, idx) => {
                const absolutePct = total_cases > 0 ? (stop.count / total_cases) * 100 : 0;
                
                let badgeColor = 'bg-emerald-100 text-emerald-700';
                let barColor = 'bg-emerald-500';
                
                if (absolutePct > 15) {
                  badgeColor = 'bg-rose-100 text-rose-700';
                  barColor = 'bg-rose-500';
                } else if (absolutePct > 5) {
                  badgeColor = 'bg-amber-100 text-amber-700';
                  barColor = 'bg-amber-500';
                }
                
                return (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
                      <div className="flex items-center gap-2 truncate">
                        <span className="truncate max-w-[180px]" title={stop.stop_name}>
                          {stop.stop_seq ? `[#${stop.stop_seq}] ` : ''}{stop.stop_name}
                        </span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${badgeColor}`}>
                          {absolutePct.toFixed(1)}%
                        </span>
                      </div>
                      <span className="text-slate-500 font-bold ml-2 shrink-0">{stop.count}x</span>
                    </div>
                    {/* Bar visual representation */}
                    <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                      <div
                        className={`${barColor} h-full rounded-full transition-all duration-500`}
                        style={{ width: `${Math.max(absolutePct, 2)}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
