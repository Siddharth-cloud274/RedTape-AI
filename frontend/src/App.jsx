import React, { useState, useEffect } from 'react';
import { checkBackendHealth, API_BASE_URL } from './services/api';
import { Activity, ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [healthStatus, setHealthStatus] = useState({
    loading: true,
    connected: false,
    data: null,
    error: null,
    lastChecked: null,
  });

  const performHealthCheck = async () => {
    setHealthStatus((prev) => ({ ...prev, loading: true }));
    const result = await checkBackendHealth();

    if (result.success) {
      setHealthStatus({
        loading: false,
        connected: true,
        data: result.data,
        error: null,
        lastChecked: new Date().toLocaleTimeString(),
      });
    } else {
      setHealthStatus({
        loading: false,
        connected: false,
        data: null,
        error: result.error,
        lastChecked: new Date().toLocaleTimeString(),
      });
    }
  };

  useEffect(() => {
    performHealthCheck();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation / Brand Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-bold text-white shadow-lg shadow-emerald-900/30">
              RT
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                RedTape AI
                <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  M1 Foundation
                </span>
              </h1>
              <p className="text-xs text-slate-400">Agentic Bureaucracy Assistant for Indian Citizens</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-slate-400">Target: {API_BASE_URL}</span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-3xl w-full mx-auto px-6 py-12 flex-1 flex flex-col justify-center">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur">
          <div className="flex items-center gap-3 mb-6">
            <Activity className="w-6 h-6 text-emerald-400" />
            <h2 className="text-lg font-semibold text-white">System Connectivity & Health Status</h2>
          </div>

          {/* Status Display */}
          {healthStatus.loading ? (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-300 animate-pulse">
              <RefreshCw className="w-5 h-5 animate-spin text-emerald-400" />
              <span>Checking connection to FastAPI backend...</span>
            </div>
          ) : healthStatus.connected ? (
            <div className="space-y-4">
              <div className="flex items-start gap-4 p-5 rounded-xl bg-emerald-950/40 border border-emerald-700/50 text-emerald-200">
                <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-emerald-300">Backend Connected Successfully</h3>
                    <span className="text-xs font-mono bg-emerald-900/60 text-emerald-300 px-2.5 py-0.5 rounded-full border border-emerald-700/50">
                      HTTP 200 OK
                    </span>
                  </div>
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono text-slate-300">
                    <p><span className="text-slate-400">Service:</span> {healthStatus.data?.service}</p>
                    <p><span className="text-slate-400">Status:</span> {healthStatus.data?.status}</p>
                    <p><span className="text-slate-400">Version:</span> {healthStatus.data?.version}</p>
                    <p><span className="text-slate-400">Checked at:</span> {healthStatus.lastChecked}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start gap-4 p-5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200">
                <AlertCircle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-rose-300">Backend Disconnected</h3>
                    <span className="text-xs font-mono bg-rose-900/60 text-rose-300 px-2.5 py-0.5 rounded-full border border-rose-700/50">
                      Connection Failed
                    </span>
                  </div>
                  <p className="text-xs text-rose-300/80 mt-2">
                    {healthStatus.error || "Unable to reach the FastAPI backend service."}
                  </p>
                  <p className="text-xs font-mono text-slate-400 mt-1">
                    Expected URL: <span className="text-slate-200">{API_BASE_URL}/api/health</span>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="mt-6 flex items-center justify-between pt-6 border-t border-slate-800">
            <span className="text-xs text-slate-400">
              {healthStatus.lastChecked ? `Last check: ${healthStatus.lastChecked}` : 'Initial check pending'}
            </span>
            <button
              onClick={performHealthCheck}
              disabled={healthStatus.loading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-xs font-medium text-slate-200 transition-colors border border-slate-700"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${healthStatus.loading ? 'animate-spin' : ''}`} />
              Re-check Health
            </button>
          </div>
        </div>

        {/* Milestone Notice */}
        <div className="mt-8 text-center text-xs text-slate-400 max-w-lg mx-auto leading-relaxed">
          <p className="font-medium text-slate-300">Milestone M1 Foundation Verification</p>
          <p className="mt-1">
            RedTape AI strictly follows a conversational UX. Service selection menus and dropdowns are intentionally omitted. The conversational chat interface will be activated in upcoming milestones.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-400">
        RedTape AI &bull; Hack-N-Pitch 2026
      </footer>
    </div>
  );
}
