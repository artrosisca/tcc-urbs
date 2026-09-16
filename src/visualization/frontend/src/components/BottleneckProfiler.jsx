import React, { useEffect, useRef } from 'react';
import svgPanZoom from 'svg-pan-zoom';

export default function BottleneckProfiler({ performanceData }) {
  const containerRef = useRef(null);
  const panZoomRef = useRef(null);

  useEffect(() => {
    if (!performanceData || !containerRef.current || typeof performanceData !== 'string') return;

    const svgElement = containerRef.current.querySelector('svg');
    if (svgElement) {
      if (panZoomRef.current) {
        panZoomRef.current.destroy();
        panZoomRef.current = null;
      }

      svgElement.setAttribute('width', '100%');
      svgElement.setAttribute('height', '100%');
      svgElement.classList.add('cursor-grab', 'active:cursor-grabbing');

      panZoomRef.current = svgPanZoom(svgElement, {
        zoomEnabled: true,
        controlIconsEnabled: true,
        fit: true,
        center: true,
        minZoom: 0.1,
        maxZoom: 100,
        zoomScaleSensitivity: 0.2
      });
    }

    return () => {
      if (panZoomRef.current) {
        panZoomRef.current.destroy();
        panZoomRef.current = null;
      }
    };
  }, [performanceData]);

  return (
    <div className="w-full h-full bg-slate-50 flex flex-col p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-slate-800">Perfilador de Gargalos Operacionais (Desempenho)</h2>
          <p className="text-xs text-slate-500">Mapeamento de tempos de trânsito médios (em dias, horas, minutos) no Directly-Follows Graph gerado nativamente pela PM4Py</p>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm relative overflow-hidden flex items-center justify-center">
        
        {!performanceData || typeof performanceData !== 'string' ? (
          <div className="text-slate-400 text-xs">Sem dados de Desempenho carregados.</div>
        ) : (
          <div 
            ref={containerRef}
            className="w-full h-full flex items-center justify-center"
            dangerouslySetInnerHTML={{ __html: performanceData }}
          />
        )}
      </div>
    </div>
  );
}
