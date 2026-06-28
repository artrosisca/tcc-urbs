import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

export default function ProcessVisualizer({ petriNetData }) {
  const svgRef = useRef(null);
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);

  useEffect(() => {
    if (!petriNetData || !petriNetData.places) return;

    // Combine places and transitions into nodes
    const rawNodes = [
      ...petriNetData.places.map(p => ({ ...p, id: p.id, type: 'place' })),
      ...petriNetData.transitions.map(t => ({ ...t, id: t.id, type: 'transition' }))
    ];

    // Arcs map sources to targets
    const rawLinks = petriNetData.arcs.map(a => ({
      source: a.source,
      target: a.target
    }));

    // Setup D3 force simulation
    const width = 800;
    const height = 500;

    const simulation = d3.forceSimulation(rawNodes)
      .force('link', d3.forceLink(rawLinks).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    simulation.on('tick', () => {
      // Keep nodes within boundary
      rawNodes.forEach(node => {
        node.x = Math.max(40, Math.min(width - 40, node.x));
        node.y = Math.max(40, Math.min(height - 40, node.y));
      });
      setNodes([...rawNodes]);
      setLinks([...rawLinks]);
    });

    return () => simulation.stop();
  }, [petriNetData]);

  return (
    <div className="w-full h-full bg-slate-50 flex flex-col p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-slate-800">Rede de Petri Normativa (Descoberta)</h2>
          <p className="text-xs text-slate-500">Fluxo lógico sequencial gerado via algoritmo Inductive Miner do PM4Py</p>
        </div>
        <div className="flex gap-4 text-xs font-semibold text-slate-600 bg-white p-2 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-white border-2 border-slate-400"></span>
            <span>Lugar (Status)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 bg-slate-800 border border-slate-700"></span>
            <span>Transição (Atividade)</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm relative overflow-hidden flex items-center justify-center">
        <svg
          ref={svgRef}
          viewBox="0 0 800 500"
          className="w-full h-full cursor-grab active:cursor-grabbing"
        >
          {/* Arrow marker for links */}
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="32"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
            </marker>
          </defs>

          {/* Draw Link/Arc lines */}
          <g>
            {links.map((link, idx) => {
              const sx = link.source.x || 0;
              const sy = link.source.y || 0;
              const tx = link.target.x || 0;
              const ty = link.target.y || 0;

              return (
                <line
                  key={idx}
                  x1={sx}
                  y1={sy}
                  x2={tx}
                  y2={ty}
                  stroke="#cbd5e1"
                  strokeWidth="2"
                  markerEnd="url(#arrow)"
                />
              );
            })}
          </g>

          {/* Draw Nodes */}
          <g>
            {nodes.map((node) => {
              const x = node.x || 0;
              const y = node.y || 0;

              if (node.type === 'place') {
                const isStart = node.id === 'source' || node.id === 'place_start';
                const isEnd = node.id === 'sink' || node.id.includes('place_15') || node.id.includes('place_13');
                
                return (
                  <g key={node.id} transform={`translate(${x}, ${y})`}>
                    <circle
                      r="18"
                      fill={isStart ? '#10b981' : isEnd ? '#ef4444' : '#ffffff'}
                      stroke={isStart ? '#059669' : isEnd ? '#dc2626' : '#64748b'}
                      strokeWidth="2.5"
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fontSize="9px"
                      fontWeight="bold"
                      fill={isStart || isEnd ? '#ffffff' : '#475569'}
                    >
                      {node.id === 'source' ? 'IN' : node.id === 'sink' ? 'OUT' : 'P'}
                    </text>
                    <title>{node.id}</title>
                  </g>
                );
              } else {
                // Transition: Square/Rectangle
                const width = node.silent ? 12 : 75;
                const height = node.silent ? 25 : 30;
                
                return (
                  <g key={node.id} transform={`translate(${x}, ${y})`}>
                    <rect
                      x={-width / 2}
                      y={-height / 2}
                      width={width}
                      height={height}
                      fill={node.silent ? '#64748b' : '#0f172a'}
                      stroke={node.silent ? '#475569' : '#000000'}
                      strokeWidth="1.5"
                      rx="3"
                    />
                    {!node.silent && (
                      <text
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fontSize="7px"
                        fontWeight="semibold"
                        fill="#ffffff"
                        className="pointer-events-none select-none font-sans"
                      >
                        {/* Trim the Passage label to fit */}
                        {node.label.length > 15 ? node.label.substring(0, 13) + '..' : node.label}
                      </text>
                    )}
                    <title>{node.label}</title>
                  </g>
                );
              }
            })}
          </g>
        </svg>
      </div>
    </div>
  );
}
