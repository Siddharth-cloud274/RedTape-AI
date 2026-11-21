import React, { useState } from 'react';
import {
  FileText,
  Download,
  Eye,
  ExternalLink,
  ShieldCheck,
  Edit3,
  X,
  Check,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import {
  getDocumentPreviewUrl,
  getDocumentDownloadUrl,
  regenerateDocumentDraft,
} from '../services/api';

export default function DocumentCard({ document: initialDoc, onUpdateDocument }) {
  const [doc, setDoc] = useState(initialDoc);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editValues, setEditValues] = useState(() => doc?.filled_fields || {});
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenerateError, setRegenerateError] = useState(null);

  if (!doc) return null;

  const previewUrl = getDocumentPreviewUrl(doc.document_id);
  const downloadUrl = getDocumentDownloadUrl(doc.document_id);

  const handleEditChange = (key, value) => {
    setEditValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleSaveAndRegenerate = async (e) => {
    e.preventDefault();
    setIsRegenerating(true);
    setRegenerateError(null);

    const res = await regenerateDocumentDraft({
      documentId: doc.document_id,
      updatedFields: editValues,
    });

    setIsRegenerating(false);
    if (res.success && res.data?.document) {
      setDoc(res.data.document);
      setIsEditing(false);
      if (onUpdateDocument) {
        onUpdateDocument(res.data.document);
      }
    } else {
      setRegenerateError(res.error || 'Failed to regenerate draft.');
    }
  };

  return (
    <div className="mt-3 rounded-xl bg-slate-900 border border-emerald-900/50 p-4 shadow-lg text-slate-200">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-emerald-950 border border-emerald-800/80 flex items-center justify-center text-emerald-400 shrink-0">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-1.5">
              <span>{doc.title || 'Official Form Draft'}</span>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
                UNSUBMITTED DRAFT • v{doc.version}
              </span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              {doc.issuing_authority} • {doc.jurisdiction}
            </p>
          </div>
        </div>

        {/* Provenance link */}
        {doc.source_portal_url && (
          <a
            href={doc.source_portal_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-slate-400 hover:text-emerald-400 flex items-center gap-1 transition-colors shrink-0"
            title="View Official Government Portal"
          >
            <span>Source</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      {/* Security & Authenticity Banner */}
      <div className="mt-2.5 px-3 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center gap-2 text-[11px] text-slate-400">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        <span>
          Populated on verified Kolkata Collectorate template. Signature & official endorsement sections left blank.
        </span>
      </div>

      {/* Filled Fields Summary */}
      {!isEditing ? (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          {doc.filled_fields && Object.keys(doc.filled_fields).length > 0 ? (
            Object.entries(doc.filled_fields)
              .slice(0, 6)
              .map(([key, val]) => (
                <div key={key} className="bg-slate-950/60 rounded px-2.5 py-1.5 border border-slate-800/60">
                  <span className="text-[10px] font-mono text-slate-500 uppercase block tracking-wider">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="text-slate-200 font-medium truncate block">{val}</span>
                </div>
              ))
          ) : (
            <div className="text-xs text-slate-500 italic col-span-2">No fields populated yet.</div>
          )}
        </div>
      ) : (
        /* Edit Mode */
        <form onSubmit={handleSaveAndRegenerate} className="mt-3 space-y-2">
          <div className="text-xs font-semibold text-slate-300">Edit Draft Fields:</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {['applicant_name', 'father_name', 'date_of_birth', 'present_address'].map((field) => (
              <div key={field}>
                <label className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
                  {field.replace(/_/g, ' ')}
                </label>
                <input
                  type="text"
                  value={editValues[field] || ''}
                  onChange={(e) => handleEditChange(field, e.target.value)}
                  className="w-full text-xs px-2.5 py-1.5 rounded bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>
            ))}
          </div>

          {regenerateError && (
            <div className="text-xs text-rose-400 flex items-center gap-1.5 mt-1">
              <AlertCircle className="w-3.5 h-3.5 shrink-0" />
              <span>{regenerateError}</span>
            </div>
          )}

          <div className="flex items-center gap-2 pt-1">
            <button
              type="submit"
              disabled={isRegenerating}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-medium text-white transition-colors disabled:opacity-50"
            >
              {isRegenerating ? (
                <>
                  <RefreshCw className="w-3 h-3 animate-spin" />
                  <span>Regenerating...</span>
                </>
              ) : (
                <>
                  <Check className="w-3 h-3" />
                  <span>Update & Regenerate</span>
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Action Buttons */}
      <div className="mt-3.5 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setIsPreviewOpen(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors"
        >
          <Eye className="w-3.5 h-3.5 text-emerald-400" />
          <span>Preview PDF</span>
        </button>

        <a
          href={downloadUrl}
          download={`WB_Domicile_Draft_${doc.document_id.slice(0, 8)}.pdf`}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-medium text-white shadow-sm transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Download Draft PDF</span>
        </a>

        {!isEditing && (
          <button
            type="button"
            onClick={() => {
              setEditValues(doc.filled_fields || {});
              setIsEditing(true);
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-xs text-slate-400 hover:text-slate-200 border border-slate-800 transition-colors ml-auto"
          >
            <Edit3 className="w-3 h-3" />
            <span>Edit Fields</span>
          </button>
        )}
      </div>

      {/* Preview Modal */}
      {isPreviewOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="px-5 py-3.5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-semibold text-slate-100">
                  Document Preview: {doc.title}
                </span>
                <span className="text-xs text-amber-400 font-mono px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30">
                  Unsubmitted Draft v{doc.version}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={downloadUrl}
                  download={`WB_Domicile_Draft_${doc.document_id.slice(0, 8)}.pdf`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-xs text-white"
                >
                  <Download className="w-3 h-3" />
                  <span>Download</span>
                </a>
                <button
                  type="button"
                  onClick={() => setIsPreviewOpen(false)}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Body / Iframe */}
            <div className="flex-1 bg-slate-950 overflow-hidden relative">
              <iframe
                src={previewUrl}
                title="Document Preview"
                className="w-full h-full border-0"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
