import React, { useState } from 'react';
import {
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  FileText,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Landmark,
  Building2,
  HelpCircle,
} from 'lucide-react';

export default function OfficialResourcesCard({ resources }) {
  const [showAllDocs, setShowAllDocs] = useState(false);

  if (!resources) return null;

  const {
    title,
    issuing_authority,
    jurisdiction,
    overview,
    required_documents = [],
    official_links = [],
    is_verified = true,
    verification_badge = 'Verified Official',
    disclaimer,
  } = resources;

  const displayedDocs = showAllDocs
    ? required_documents
    : required_documents.slice(0, 3);

  const isVerified = is_verified !== false;

  return (
    <div
      className={`mt-3 rounded-xl border bg-gradient-to-b from-slate-900 via-slate-900/95 to-slate-950 p-4 text-slate-200 shadow-md ${
        isVerified ? 'border-emerald-900/60' : 'border-amber-900/60'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
              isVerified
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}
          >
            {isVerified ? (
              <ShieldCheck className="h-4 w-4" />
            ) : (
              <HelpCircle className="h-4 w-4" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`text-xs font-semibold uppercase tracking-wider ${
                  isVerified ? 'text-emerald-400' : 'text-amber-400'
                }`}
              >
                {isVerified ? 'Official Research & Portal' : 'Probable Portal & Guidance'}
              </span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-medium border ${
                  isVerified
                    ? 'bg-emerald-950 text-emerald-300 border-emerald-800/60'
                    : 'bg-amber-950 text-amber-300 border-amber-800/60'
                }`}
              >
                {verification_badge || (isVerified ? 'Verified Official' : 'Probable Guidance')}
              </span>
            </div>
            <h4 className="text-sm font-semibold text-white mt-0.5">{title}</h4>
          </div>
        </div>
      </div>

      {/* Probable Disclaimer Banner */}
      {!isVerified && disclaimer && (
        <div className="mt-2.5 flex items-start gap-2 rounded-lg bg-amber-950/40 p-2.5 border border-amber-800/50 text-xs text-amber-200/90 leading-snug">
          <AlertCircle className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
          <span>{disclaimer}</span>
        </div>
      )}

      {/* Issuing Authority & Jurisdiction */}
      <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="flex items-start gap-1.5 rounded-lg bg-slate-800/50 p-2 border border-slate-800">
          <Landmark
            className={`h-3.5 w-3.5 shrink-0 mt-0.5 ${
              isVerified ? 'text-emerald-400' : 'text-amber-400'
            }`}
          />
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-medium block">
              Issuing Authority
            </span>
            <span className="text-slate-200 font-medium leading-tight">
              {issuing_authority}
            </span>
          </div>
        </div>
        <div className="flex items-start gap-1.5 rounded-lg bg-slate-800/50 p-2 border border-slate-800">
          <Building2 className="h-3.5 w-3.5 text-teal-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-[10px] text-slate-400 uppercase font-medium block">
              Jurisdiction
            </span>
            <span className="text-slate-200 font-medium leading-tight">
              {jurisdiction}
            </span>
          </div>
        </div>
      </div>

      {/* Statutory / Procedural Overview */}
      {overview && (
        <p className="mt-2 text-xs text-slate-300 leading-relaxed bg-slate-900/60 rounded-lg p-2.5 border border-slate-800/80">
          {overview}
        </p>
      )}

      {/* Official Government Links */}
      {official_links && official_links.length > 0 && (
        <div className="mt-3">
          <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block mb-1.5">
            {isVerified ? 'Verified Portals & Forms' : 'Probable Official Portals'}
          </span>
          <div className="flex flex-col gap-1.5">
            {official_links.map((link, idx) => (
              <a
                key={idx}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`group flex items-center justify-between rounded-lg border border-slate-800 bg-slate-800/40 px-3 py-2 text-xs text-slate-200 transition-colors ${
                  isVerified
                    ? 'hover:border-emerald-600/60 hover:bg-emerald-950/20 hover:text-white'
                    : 'hover:border-amber-600/60 hover:bg-amber-950/20 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2 truncate pr-2">
                  <FileText
                    className={`h-3.5 w-3.5 shrink-0 transition-transform group-hover:scale-110 ${
                      isVerified ? 'text-emerald-400' : 'text-amber-400'
                    }`}
                  />
                  <div className="truncate">
                    <span
                      className={`font-medium ${
                        isVerified
                          ? 'text-emerald-300 group-hover:text-emerald-200'
                          : 'text-amber-300 group-hover:text-amber-200'
                      }`}
                    >
                      {link.title}
                    </span>
                    {link.description && (
                      <span className="text-[11px] text-slate-400 block truncate">
                        {link.description}
                      </span>
                    )}
                  </div>
                </div>
                <div
                  className={`flex items-center gap-1 shrink-0 text-slate-400 ${
                    isVerified ? 'group-hover:text-emerald-300' : 'group-hover:text-amber-300'
                  }`}
                >
                  <span className="text-[10px] capitalize">Open</span>
                  <ExternalLink className="h-3 w-3" />
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Supporting Documents Checklist */}
      {required_documents && required_documents.length > 0 && (
        <div className="mt-3 border-t border-slate-800 pt-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <span>{isVerified ? 'Required Documents' : 'Typical Supporting Documents'}</span>
              <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] text-slate-400 border border-slate-700">
                {required_documents.length}
              </span>
            </span>
            {required_documents.length > 3 && (
              <button
                type="button"
                onClick={() => setShowAllDocs(!showAllDocs)}
                className={`text-[11px] flex items-center gap-0.5 transition-colors ${
                  isVerified
                    ? 'text-emerald-400 hover:text-emerald-300'
                    : 'text-amber-400 hover:text-amber-300'
                }`}
              >
                {showAllDocs ? (
                  <>
                    Show less <ChevronUp className="h-3 w-3" />
                  </>
                ) : (
                  <>
                    View all {required_documents.length} <ChevronDown className="h-3 w-3" />
                  </>
                )}
              </button>
            )}
          </div>

          <ul className="space-y-1.5">
            {displayedDocs.map((doc, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-xs text-slate-300 leading-snug"
              >
                <CheckCircle2
                  className={`h-3.5 w-3.5 shrink-0 mt-0.5 ${
                    isVerified ? 'text-emerald-500' : 'text-amber-500'
                  }`}
                />
                <span>{doc}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
