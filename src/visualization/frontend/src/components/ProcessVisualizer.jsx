import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function ProcessVisualizer({ petriNetData }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!petriNetData || !containerRef.current) return;

    // Apply D3 zoom to the injected SVG
    const svgElement = containerRef.current.querySelector('svg');
    if (svgElement) {
      // Set width/height 100% to fit container
      svgElement.setAttribute('width', '100%');
      svgElement.setAttribute('height', '100%');
      svgElement.classList.add('cursor-grab', 'active:cursor-grabbing');

      const svg = d3.select(svgElement);
      
      // Wrap internal contents in a g tag if not already (Graphviz outputs a top-level <g> usually)
      const g = svg.select('g');
      if (!g.empty()) {
        const zoom = d3.zoom()
          .scaleExtent([0.1, 4])
          .on('zoom', (event) => {
            g.attr('transform', event.transform);
          });

        svg.call(zoom);
        
        // Reset zoom to fit graph automatically on load
        svg.call(zoom.transform, d3.zoomIdentity);
      }
    }
  }, [petriNetData]);

  return (
    <div className="w-full h-full bg-slate-50 flex flex-col p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-slate-800">Rede de Petri Normativa (Descoberta)</h2>
          <p className="text-xs text-slate-500">Fluxo lógico sequencial gerado via algoritmo Inductive Miner do PM4Py</p>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm relative overflow-hidden flex items-center justify-center">
        {!petriNetData ? (
          <div className="text-slate-400 text-xs">Sem dados da rede de Petri carregados.</div>
        ) : (
          <div 
            ref={containerRef}
            className="w-full h-full flex items-center justify-center"
            dangerouslySetInnerHTML={{ __html: petriNetData }}
          />
        )}
      </div>
    </div>
  );
}
