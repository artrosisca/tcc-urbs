import React, { useEffect, useRef } from 'react';
import svgPanZoom from 'svg-pan-zoom';

export default function ProcessVisualizer({ petriNetData }) {
  const containerRef = useRef(null);
  const panZoomRef = useRef(null);

  useEffect(() => {
    if (!petriNetData || !containerRef.current) return;

    const svgElement = containerRef.current.querySelector('svg');
    if (svgElement) {
      // Destruir instância anterior se existir
      if (panZoomRef.current) {
        panZoomRef.current.destroy();
        panZoomRef.current = null;
      }

      // Preparar o SVG para ocupar todo o espaço
      svgElement.setAttribute('width', '100%');
      svgElement.setAttribute('height', '100%');
      
      // O svg-pan-zoom prefere que o viewBox original seja mantido para calcular o fit
      svgElement.classList.add('cursor-grab', 'active:cursor-grabbing');

      // Inicializar biblioteca especializada em SVG
      panZoomRef.current = svgPanZoom(svgElement, {
        zoomEnabled: true,
        controlIconsEnabled: true, // Adiciona botões de +/- nativos
        fit: true, // Começa cabendo na tela
        center: true,
        minZoom: 0.1,
        maxZoom: 100, // Zoom máximo gigantesco
        zoomScaleSensitivity: 0.2
      });

      // Se for muito comprido, podemos ajustar o zoom inicial para algo mais focado
      // const initialZoom = panZoomRef.current.getZoom() * 2;
      // panZoomRef.current.zoom(initialZoom);
      // panZoomRef.current.pan({x: 20, y: 0});
    }

    return () => {
      if (panZoomRef.current) {
        panZoomRef.current.destroy();
        panZoomRef.current = null;
      }
    };
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
