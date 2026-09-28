import React, { useState, useEffect, useRef } from 'react';
import { Info } from 'lucide-react';

/**
 * Lightweight methodological info popover ("(i)").
 * Closes on outside click or Escape. No external deps.
 */
export default function InfoPopover({ title, children, align = 'left', className = '' }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    };
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <span ref={rootRef} className={`relative inline-flex items-center ${className}`}>
      <button
        type="button"
        aria-label={`Informações: ${title}`}
        onClick={(e) => { e.stopPropagation(); setOpen(prev => !prev); }}
        className="text-slate-300 hover:text-blue-500 transition-colors cursor-pointer"
      >
        <Info className="h-3.5 w-3.5" />
      </button>
      {open && (
        <span
          role="tooltip"
          className={`absolute top-5 z-50 block w-64 p-3 bg-white border border-slate-200 rounded-xl shadow-lg text-left ${
            align === 'right' ? 'right-0' : 'left-0'
          }`}
        >
          <span className="block text-[11px] font-bold text-slate-700 mb-1 normal-case tracking-normal">{title}</span>
          <span className="block text-[11px] text-slate-500 leading-relaxed normal-case tracking-normal font-normal">
            {children}
          </span>
        </span>
      )}
    </span>
  );
}
