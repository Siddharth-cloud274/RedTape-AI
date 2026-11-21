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
    <div className={`flex items-center justify-between text-xs px-3 py-2 rounded-lg bg-slate-900/80 border border-slate-800 ${className}`}>
      <div className="flex items-center gap-2 overflow-hidden">
        {status.loading ? (
          <RefreshCw className="w-3.5 h-3.5 animate-spin text-slate-400 shrink-0" />
        ) : status.connected ? (
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        ) : (
          <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
        )}
        <div className="truncate">
          {status.loading ? (
            <span className="text-slate-400">Checking API...</span>
          ) : status.connected ? (
            <span className="text-slate-300 font-mono">Backend v{status.version || '0.1.0'}</span>
          ) : (
            <span className="text-rose-400 font-mono">Backend Offline</span>
          )}
        </div>
      </div>

      <button
        type="button"
        onClick={performCheck}
        disabled={status.loading}
        title="Refresh backend status"
        className="p-1 text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-40"
      >
        <RefreshCw className={`w-3 h-3 ${status.loading ? 'animate-spin' : ''}`} />
      </button>
    </div>
  );
}
