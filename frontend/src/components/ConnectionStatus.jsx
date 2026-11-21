import React, { useState, useEffect } from 'react';
import { checkBackendHealth } from '../services/api';
import { RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

export default function ConnectionStatus({ className = '' }) {
  const [status, setStatus] = useState({
    loading: true,
    connected: false,
    version: null,
    error: null,
  });

  const performCheck = async () => {
    setStatus((prev) => ({ ...prev, loading: true }));
    const result = await checkBackendHealth();
    if (result.success) {
      setStatus({
        loading: false,
        connected: true,
        version: result.data.version,
        error: null,
      });
    } else {
      setStatus({
        loading: false,
        connected: false,
        version: null,
        error: result.error,
      });
    }
  };

  useEffect(() => {
    performCheck();
  }, []);

  return (
    <div className={`flex items-center justify-between text-xs px-3 py-2 rounded-xl bg-obsidian-850/80 border border-obsidian-750 backdrop-blur-md shadow-sm ${className}`}>
      <div className="flex items-center gap-2 overflow-hidden">
        {status.loading ? (
          <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-400 shrink-0" />
        ) : status.connected ? (
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        ) : (
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="relative inline-flex rounded-full h-2 w-2 bg-crimson-500"></span>
          </span>
        )}

        <div className="truncate">
          {status.loading ? (
            <span className="text-slate-400 font-mono text-[11px]">Connecting API...</span>
          ) : status.connected ? (
            <span className="text-slate-300 font-mono text-[11px]">Backend v{status.version || '0.1.0'}</span>
          ) : (
            <span className="text-crimson-400 font-mono text-[11px]">Offline (Mock mode)</span>
          )}
        </div>
      </div>

      <button
        type="button"
        onClick={performCheck}
        disabled={status.loading}
        title="Refresh backend status"
        className="p-1 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-40 rounded-md hover:bg-obsidian-750"
      >
        <RefreshCw className={`w-3 h-3 ${status.loading ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
}
