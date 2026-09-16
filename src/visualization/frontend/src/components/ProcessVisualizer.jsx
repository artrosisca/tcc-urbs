import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

export default function ProcessVisualizer({ petriNetData }) {
  const containerRef = useRef(null);
  const [scale, setScale] = useState(1);
  const d3ZoomRef = useRef(null);
  const d3SvgRef = useRef(null);

  useEffect(() => {
    if (!petriNetData || !containerRef.current) return;

    const svgElement = containerRef.current.querySelector('svg');
    if (svgElement) {
      // Remove viewBox to prevent the browser from shrinking the huge graph to fit the screen
      svgElement.setAttribute('width', '100%');
      svgElement.setAttribute('height', '100%');
      svgElement.removeAttribute('viewBox');
      svgElement.classList.add('cursor-grab', 'active:cursor-grabbing');

      // Create a wrapper group for D3 zoom so we don't overwrite Graphviz's own transforms
      let zoomWrapper = svgElement.querySelector('g.d3-zoom-wrapper');
      if (!zoomWrapper) {
        zoomWrapper = document.createElementNS("http://www.w3.org/2000/svg", "g");
        zoomWrapper.setAttribute('class', 'd3-zoom-wrapper');
        const children = Array.from(svgElement.childNodes);
        children.forEach(child => zoomWrapper.appendChild(child));
        svgElement.appendChild(zoomWrapper);
      }

      const svg = d3.select(svgElement);
      const g = d3.select(zoomWrapper);

      const zoom = d3.zoom()
        .scaleExtent([0.1, 10]) // Cap slider max to something reasonable
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
          setScale(event.transform.k);
        });

      d3ZoomRef.current = zoom;
      d3SvgRef.current = svg;
      svg.call(zoom);

      // Center the graph vertically and start at the left edge
      const containerHeight = containerRef.current.clientHeight || 500;
      const initialScale = 1.0; 
      const initialY = containerHeight / 2 - (50 * initialScale);

      const initialTransform = d3.zoomIdentity
        .translate(20, initialY)
        .scale(initialScale);
        
      svg.call(zoom.transform, initialTransform);
    }
  }, [petriNetData]);

  const handleSliderChange = (e) => {
    const newScale = parseFloat(e.target.value);
    if (d3SvgRef.current && d3ZoomRef.current) {
      d3ZoomRef.current.scaleTo(d3SvgRef.current, newScale);
    }
  };

  const handleResetZoom = () => {
    if (d3SvgRef.current && d3ZoomRef.current) {
      const containerHeight = containerRef.current.clientHeight || 500;
      const initialY = containerHeight / 2 - 50;
      const initialTransform = d3.zoomIdentity.translate(20, initialY).scale(1);
      d3SvgRef.current.transition().duration(500).call(d3ZoomRef.current.transform, initialTransform);
    }
  };

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
        
        {petriNetData && (
          <div className="absolute top-4 right-4 bg-white/90 backdrop-blur border border-slate-200 shadow-md rounded-lg p-3 flex items-center gap-3 z-10">
            <span className="text-xs text-slate-600 font-semibold uppercase tracking-wide">Zoom</span>
            <input 
              type="range" 
              min="0.1" 
              max="5" 
              step="0.05" 
              value={scale} 
              onChange={handleSliderChange}
              className="w-32 accent-blue-600"
            />
            <span className="text-xs text-slate-700 w-12 text-right font-mono">{(scale * 100).toFixed(0)}%</span>
            <div className="w-px h-4 bg-slate-300 mx-1"></div>
            <button 
              onClick={handleResetZoom} 
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Resetar
            </button>
          </div>
        )}

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
