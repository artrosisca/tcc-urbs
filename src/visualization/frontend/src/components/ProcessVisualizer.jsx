import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function ProcessVisualizer({ petriNetData }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!petriNetData || !containerRef.current) return;

    const svgElement = containerRef.current.querySelector('svg');
    if (svgElement) {
      // Parse original dimensions
      const originalViewBox = svgElement.getAttribute('viewBox');
      
      // Let the SVG fill the container, but remove viewBox so the browser doesn't auto-shrink it
      svgElement.setAttribute('width', '100%');
      svgElement.setAttribute('height', '100%');
      svgElement.removeAttribute('viewBox');
      svgElement.classList.add('cursor-grab', 'active:cursor-grabbing');

      const svg = d3.select(svgElement);
      const g = svg.select('g'); // the root graph0 element from Graphviz

      if (!g.empty()) {
        const zoom = d3.zoom()
          .scaleExtent([0.1, 100]) // Allow massive zoom-in
          .on('zoom', (event) => {
            g.attr('transform', event.transform);
          });

        svg.call(zoom);

        // Instead of shrinking to fit, start with a comfortable scale at the left (source)
        // Adjust Y so it's centered vertically
        const containerHeight = containerRef.current.clientHeight || 500;
        const initialScale = 1.5; // Starts larger!
        const initialY = containerHeight / 2 - (100 * initialScale);

        const initialTransform = d3.zoomIdentity
          .translate(20, initialY)
          .scale(initialScale);
          
        svg.call(zoom.transform, initialTransform);
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
