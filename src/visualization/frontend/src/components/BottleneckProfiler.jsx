import React, { useEffect, useState } from 'react';
import * as d3 from 'd3';

export default function BottleneckProfiler({ performanceData }) {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [selectedLink, setSelectedLink] = useState(null);

  useEffect(() => {
    if (!performanceData || !performanceData.nodes) return;

    // Deep copy to prevent mutating incoming props in force layout
    const rawNodes = performanceData.nodes.map(n => ({ ...n }));
    const rawLinks = performanceData.links.map(l => ({
      ...l,
      source: l.source,
      target: l.target
    }));

    const width = 800;
    const height = 500;

    const simulation = d3.forceSimulation(rawNodes)
      .force('link', d3.forceLink(rawLinks).id(d => d.id).distance(130))
      .force('charge', d3.forceManyBody().strength(-220))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(45));

    simulation.on('tick', () => {
      rawNodes.forEach(node => {
        node.x = Math.max(40, Math.min(width - 40, node.x));
        node.y = Math.max(40, Math.min(height - 40, node.y));
      });
      setNodes([...rawNodes]);
      setLinks([...rawLinks]);
    });

    return () => simulation.stop();
  }, [performanceData]);

  // Color scale mapping mean duration (seconds) to hex color
  const getLinkColor = (duration) => {
    // scale blue-yellow-red
    if (duration < 60) return '#64748b'; // normal travel: gray
    if (duration < 120) return '#f59e0b'; // amber/warning: slow
    return '#ef4444'; // critical congestion: red
  };

  const getDurationText = (sec) => {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  return (
    <div className="w-full h-full bg-slate-50 flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-800">Perfilador de Gargalos Operacionais (Desempenho)</h2>
          <p className="text-xs text-slate-500">Mapeamento de tempos de trânsito médios entre paradas no Directly-Follows Graph (DFG)</p>
        </div>
        <div className="flex gap-4 text-xs font-semibold text-slate-600 bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-0.5 bg-slate-400"></span>
            <span>Normal (&lt;1 min)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-0.5 bg-amber-500"></span>
            <span>Lentidão (1-2 min)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-0.5 bg-red-500"></span>
            <span>Gargalo (&gt;2 min)</span>
          </div>
        </div>
      </div>

      {/* Main split canvas & side panel */}
      <div className="flex-1 grid grid-cols-4 gap-6 min-h-0">
        {/* Left Side: Interactive SVG (3 cols) */}
        <div className="col-span-3 bg-white border border-slate-200 rounded-xl shadow-sm relative overflow-hidden flex items-center justify-center">
          <svg viewBox="0 0 800 500" className="w-full h-full cursor-grab active:cursor-grabbing">
            {/* Arrow marker definition */}
            <defs>
              <marker
                id="arrow-perf"
                viewBox="0 0 10 10"
                refX="28"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
              </marker>
            </defs>

            {/* Links */}
            <g>
              {links.map((link, idx) => {
                const sx = link.source.x || 0;
                const sy = link.source.y || 0;
                const tx = link.target.x || 0;
                const ty = link.target.y || 0;
                const isSelected = selectedLink && selectedLink.source.id === link.source.id && selectedLink.target.id === link.target.id;

                return (
                  <line
                    key={idx}
                    x1={sx}
                    y1={sy}
                    x2={tx}
                    y2={ty}
                    stroke={getLinkColor(link.mean_duration)}
                    strokeWidth={isSelected ? '4' : '2'}
                    markerEnd="url(#arrow-perf)"
                    className="cursor-pointer hover:stroke-black transition-all"
                    onClick={() => setSelectedLink(link)}
                  />
                );
              })}
            </g>

            {/* Nodes */}
            <g>
              {nodes.map((node) => {
                const x = node.x || 0;
                const y = node.y || 0;

                return (
                  <g key={node.id} transform={`translate(${x}, ${y})`}>
                    <circle
                      r="16"
                      fill="#0f172a"
                      stroke="#475569"
                      strokeWidth="1.5"
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize="7px"
                      fontWeight="bold"
                      fill="#ffffff"
                    >
                      {/* Extract numeric stop ID if available */}
                      {node.id.length > 5 ? 'P' : node.id}
                    </text>
                    <title>{node.label}</title>
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* Right Side: Segment Detail panel (1 col) */}
        <div className="col-span-1 bg-white border border-slate-200 rounded-xl shadow-sm p-5 space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Detalhamento do Segmento</h3>
            
            {selectedLink ? (
              <div className="space-y-4 text-xs">
                <div>
                  <div className="text-[10px] font-semibold text-slate-400">Origem</div>
                  <div className="font-bold text-slate-800 break-words mt-0.5">
                    {selectedLink.source.label || selectedLink.source.id.replace('PASSAGEM_', '')}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-semibold text-slate-400">Destino</div>
                  <div className="font-bold text-slate-800 break-words mt-0.5">
                    {selectedLink.target.label || selectedLink.target.id.replace('PASSAGEM_', '')}
                  </div>
                </div>

                <div className="border-t border-slate-100 pt-3 space-y-3">
                  <div>
                    <div className="text-[10px] font-semibold text-slate-400">Tempo Médio de Viagem</div>
                    <div className="text-base font-extrabold text-slate-900 mt-0.5">
                      {getDurationText(selectedLink.mean_duration)}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] font-semibold text-slate-400">Tempo Mediano</div>
                    <div className="text-base font-extrabold text-slate-700 mt-0.5">
                      {getDurationText(selectedLink.median_duration)}
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] font-semibold text-slate-400">Total de Passagens</div>
                    <div className="font-bold text-slate-800 mt-0.5">
                      {selectedLink.count} ônibus passantes
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-slate-400 text-xs italic py-10 text-center">
                Selecione uma conexão no grafo para carregar a análise de gargalos.
              </div>
            )}
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-[10px] text-slate-500 font-medium">
            💡 Dica: Arcos avermelhados indicam gargalos com trânsito lento, necessitando auditoria de tráfego.
          </div>
        </div>
      </div>
    </div>
  );
}
