import React, { useState, useEffect, useRef } from 'react';
import { Terminal, RefreshCw, CheckCircle, AlertCircle, ChevronDown, Copy, Check, Trash2, X } from 'lucide-react';

export default function MiningConsole({ logs = [], status = 'idle', onClear, onDismiss }) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef(null);

  // Automatically open the console when mining starts, but do NOT close it automatically on finish
  useEffect(() => {
    if (status === 'running') {
      setIsOpen(true);
    }
  }, [status]);

  // Auto-scroll to bottom as logs stream in
  useEffect(() => {
    const el = scrollRef.current;
    if (el && isOpen) {
      el.scrollTop = el.scrollHeight;
    }
  }, [logs, isOpen]);

  const handleCopyLogs = async (e) => {
    e.stopPropagation();
    if (!logs || logs.length === 0) return;
    try {
      await navigator.clipboard.writeText(logs.join('\n'));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error('Failed to copy logs to clipboard:', err);
    }
  };

  const handleClear = (e) => {
    e.stopPropagation();
    if (onClear) onClear();
  };

  const renderStatusBadge = () => {
    switch (status) {
      case 'running':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <RefreshCw className="h-2.5 w-2.5 animate-spin" />
            <span>Em execução</span>
          </span>
        );
      case 'success':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="h-2.5 w-2.5" />
            <span>Sucesso</span>
          </span>
        );
      case 'error':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-2.5 w-2.5" />
            <span>Erro</span>
          </span>
        );
      case 'idle':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <span className="h-1.5 w-1.5 rounded-full bg-slate-500"></span>
            <span>Ocioso</span>
          </span>
        );
    }
  };

  return (
    <div className="border-t border-slate-800 bg-slate-950 flex-shrink-0 select-none">
      {/* Console Toggle Header */}
      <div className="w-full p-3 flex items-center justify-between text-[10px] uppercase font-bold text-slate-400 tracking-wider">
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="flex items-center gap-2 hover:text-slate-200 transition-colors"
        >
          <Terminal className="h-3.5 w-3.5 text-blue-400" />
          <span>Console de Execução</span>
          {renderStatusBadge()}
        </button>
        <div className="flex items-center gap-2">
          {onDismiss && (
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onDismiss(); }}
              className="text-slate-500 hover:text-slate-200 transition-colors"
              title="Fechar console"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsOpen((prev) => !prev)}
            className="text-slate-500 hover:text-slate-200 transition-colors"
            aria-label={isOpen ? 'Recolher console' : 'Expandir console'}
          >
            <ChevronDown
              className={`h-3.5 w-3.5 transition-transform duration-200 ${
                isOpen ? 'rotate-180' : ''
              }`}
            />
          </button>
        </div>
      </div>

      {/* Expandable Console Body */}
      {isOpen && (
        <div className="px-3 pb-3 space-y-2">
          {/* Action Toolbar */}
          <div className="flex items-center justify-between text-[10px] text-slate-400 border-b border-slate-800/80 pb-1.5">
            <span className="font-mono text-[9px] text-slate-500">
              {logs.length} {logs.length === 1 ? 'linha' : 'linhas'} de saída
            </span>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleCopyLogs}
                disabled={logs.length === 0}
                className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                title="Copiar logs para a área de transferência"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 text-emerald-400" />
                    <span className="text-emerald-400 font-semibold">Copiado!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" />
                    <span>Copiar</span>
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleClear}
                disabled={logs.length === 0}
                className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-rose-300 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                title="Limpar logs"
              >
                <Trash2 className="h-3 w-3" />
                <span>Limpar</span>
              </button>
            </div>
          </div>

          {/* Logs Output Container */}
          <div
            ref={scrollRef}
            className="h-44 overflow-y-auto font-mono text-[10px] bg-slate-900 border border-slate-800 rounded-md p-2 space-y-1 select-text scrollbar-thin scrollbar-thumb-slate-700"
          >
            {logs.length === 0 ? (
              <div className="flex items-center justify-center h-full text-slate-600 italic">
                Aguardando execução...
              </div>
            ) : (
              logs.map((log, idx) => {
                const isSuccess =
                  log.includes('Concluído') ||
                  log.includes('salvo') ||
                  log.includes('sucesso') ||
                  log.includes('sucesso!');
                const isError =
                  log.includes('Erro') ||
                  log.includes('crítico') ||
                  log.includes('Falha') ||
                  log.includes('Exception');

                return (
                  <div
                    key={idx}
                    className={`leading-relaxed break-all ${
                      isSuccess
                        ? 'text-emerald-400 font-semibold'
                        : isError
                        ? 'text-rose-400 font-semibold'
                        : 'text-slate-300'
                    }`}
                  >
                    <span className="text-slate-600 mr-1 select-none">&gt;</span>
                    {log}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
