import React, { useState, useEffect } from 'react';
import {
  ClipboardCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  Download,
  Eye,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Edit3,
  Landmark,
  Building2,
  Check,
  X,
} from 'lucide-react';
import {
  approveApplicationReview,
  requestReviewChanges,
  fetchHandoffGuidance,
  recordHandoffAction,
  getDocumentPreviewUrl,
  getDocumentDownloadUrl,
} from '../services/api';

export default function ApplicationReviewCard({
  conversationId,
  initialReview,
  latestDocument,
  onApprovalSuccess,
  onChangesRequested,
}) {
  const [review, setReview] = useState(initialReview);
  const [confirmCorrectness, setConfirmCorrectness] = useState(false);
  const [acknowledgeUnsubmitted, setAcknowledgeUnsubmitted] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [approvalError, setApprovalError] = useState(null);

  // Edit / Change Request state
  const [isRequestingChanges, setIsRequestingChanges] = useState(false);
  const [changeReason, setChangeReason] = useState('');
  const [isSubmittingChanges, setIsSubmittingChanges] = useState(false);

  // Handoff state
  const [handoff, setHandoff] = useState(null);
  const [isLoadingHandoff, setIsLoadingHandoff] = useState(false);

  useEffect(() => {
    if (initialReview) {
      setReview(initialReview);
    }
  }, [initialReview]);

  // Load handoff guidance when approved
  useEffect(() => {
    let isMounted = true;
    if (review?.review_status === 'user_approved' && conversationId) {
      setIsLoadingHandoff(true);
      fetchHandoffGuidance(conversationId).then((res) => {
        if (isMounted && res.success && res.data) {
          setHandoff(res.data);
        }
        if (isMounted) setIsLoadingHandoff(false);
      });
    }
    return () => {
      isMounted = false;
    };
  }, [review?.review_status, conversationId]);

  if (!review) return null;

  const currentVersion = latestDocument?.version || review.latest_document_version || 1;
  const isApproved = review.review_status === 'user_approved';
  const isInvalidated = review.review_status === 'approval_invalidated';
  const isChangesRequested = review.review_status === 'review_changes_requested';
  const isReady = review.review_status === 'review_ready' || review.can_approve;

  const handleApprove = async () => {
    if (!confirmCorrectness || !acknowledgeUnsubmitted) {
      setApprovalError('Please check both confirmation boxes to proceed.');
      return;
    }

    setIsApproving(true);
    setApprovalError(null);

    const res = await approveApplicationReview({
      conversationId,
      documentId: latestDocument?.document_id || review.latest_document_id,
      documentVersion: currentVersion,
      confirmCorrectness,
      acknowledgeUnsubmitted,
    });

    setIsApproving(false);
    if (res.success && res.data) {
      setReview((prev) => ({
        ...prev,
        review_status: res.data.review_status,
        active_approval: res.data.approval,
      }));
      if (onApprovalSuccess) {
        onApprovalSuccess(res.data);
      }
    } else {
      setApprovalError(res.error || 'Failed to record approval.');
    }
  };

  const handleSubmitChangeRequest = async (e) => {
    e.preventDefault();
    if (!changeReason.trim()) return;

    setIsSubmittingChanges(true);
    const res = await requestReviewChanges({
      conversationId,
      reason: changeReason.trim(),
    });
    setIsSubmittingChanges(false);

    if (res.success) {
      setReview((prev) => ({
        ...prev,
        review_status: 'review_changes_requested',
        active_approval: null,
      }));
      setIsRequestingChanges(false);
      setChangeReason('');
      if (onChangesRequested) {
        onChangesRequested(res.data);
      }
    }
  };

  const handlePortalOpen = async (url) => {
    await recordHandoffAction({
      conversationId,
      action: 'open_portal',
      urlTarget: url,
    });
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const handleDownloadFinal = async (docId) => {
    await recordHandoffAction({
      conversationId,
      action: 'download_final',
    });
    window.location.href = getDocumentDownloadUrl(docId);
  };

  return (
    <div className="mt-3 rounded-xl border border-emerald-900/70 bg-gradient-to-b from-slate-900 via-slate-900/95 to-slate-950 p-4 text-slate-200 shadow-xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${
              isApproved
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : isInvalidated || isChangesRequested
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-teal-500/10 border-teal-500/30 text-teal-400'
            }`}
          >
            <ClipboardCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                Human Review & Checkpoint
              </span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-medium border ${
                  isApproved
                    ? 'bg-emerald-950 text-emerald-300 border-emerald-800/80'
                    : isInvalidated
                    ? 'bg-rose-950 text-rose-300 border-rose-800/80'
                    : isChangesRequested
                    ? 'bg-amber-950 text-amber-300 border-amber-800/80'
                    : 'bg-slate-800 text-slate-300 border-slate-700'
                }`}
              >
                {isApproved
                  ? `Approved • Draft v${review.active_approval?.document_version || currentVersion}`
                  : isInvalidated
                  ? 'Approval Invalidated • Revision Required'
                  : isChangesRequested
                  ? 'Changes Requested'
                  : `Review Ready • Draft v${currentVersion}`}
              </span>
            </div>
            <h4 className="text-sm font-semibold text-white mt-0.5">
              {review.service_title || 'Application Review'}
            </h4>
          </div>
        </div>
      </div>

      {/* Invalidation Alert Banner */}
      {isInvalidated && (
        <div className="mt-3 flex items-start gap-2 rounded-lg bg-rose-950/40 p-2.5 border border-rose-800/60 text-xs text-rose-200">
          <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Prior Approval Invalidated</span>
            <span>
              Application details or document draft were updated to a new version.
              Please inspect the revised particulars below and re-approve.
            </span>
          </div>
        </div>
      )}

      {/* Particulars Summary */}
      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="rounded-lg bg-slate-800/40 p-2 border border-slate-800/80">
          <span className="text-[10px] uppercase text-slate-400 font-medium block">
            Applicant Name
          </span>
          <span className="font-medium text-slate-100">
            {review.confirmed_facts?.applicant_name || 'Not provided'}
          </span>
        </div>
        <div className="rounded-lg bg-slate-800/40 p-2 border border-slate-800/80">
          <span className="text-[10px] uppercase text-slate-400 font-medium block">
            Father / Guardian's Name
          </span>
          <span className="font-medium text-slate-100">
            {review.confirmed_facts?.father_name || 'Not provided'}
          </span>
        </div>
        <div className="rounded-lg bg-slate-800/40 p-2 border border-slate-800/80">
          <span className="text-[10px] uppercase text-slate-400 font-medium block">
            Date of Birth
          </span>
          <span className="font-medium text-slate-100">
            {review.confirmed_facts?.date_of_birth || 'Not provided'}
          </span>
        </div>
        <div className="rounded-lg bg-slate-800/40 p-2 border border-slate-800/80">
          <span className="text-[10px] uppercase text-slate-400 font-medium block">
            Residential Address
          </span>
          <span className="font-medium text-slate-100 truncate block">
            {review.confirmed_facts?.present_address || review.confirmed_facts?.location || 'Not provided'}
          </span>
        </div>
        <div className="rounded-lg bg-slate-800/40 p-2 border border-slate-800/80">
          <span className="text-[10px] uppercase text-slate-400 font-medium block">
            Issuing Authority
          </span>
          <span className="font-medium text-slate-100">
            {review.issuing_authority}
          </span>
        </div>
        <div className="rounded-lg bg-slate-800/40 p-2 border border-slate-800/80">
          <span className="text-[10px] uppercase text-slate-400 font-medium block">
            Jurisdiction
          </span>
          <span className="font-medium text-slate-100">
            {review.jurisdiction}
          </span>
        </div>
      </div>

      {/* Generated Draft Section */}
      {(latestDocument || review.latest_document_id) && (
        <div className="mt-3 flex items-center justify-between rounded-lg border border-slate-800 bg-slate-900/80 p-2.5">
          <div className="flex items-center gap-2 truncate">
            <FileText className="h-4 w-4 text-emerald-400 shrink-0" />
            <div className="truncate text-xs">
              <span className="font-medium text-slate-200 block truncate">
                Official PDF Draft • Version {currentVersion}
              </span>
              <span className="text-[11px] text-slate-400">
                Populated unsubmitted draft with verified fields
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <a
              href={getDocumentPreviewUrl(latestDocument?.document_id || review.latest_document_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded bg-slate-800 hover:bg-slate-700 px-2 py-1 text-xs text-slate-200 transition-colors"
            >
              <Eye className="h-3 w-3" />
              <span>Preview</span>
            </a>
            <a
              href={getDocumentDownloadUrl(latestDocument?.document_id || review.latest_document_id)}
              className="inline-flex items-center gap-1 rounded bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/40 px-2 py-1 text-xs text-emerald-300 transition-colors"
            >
              <Download className="h-3 w-3" />
              <span>Download</span>
            </a>
          </div>
        </div>
      )}

      {/* Human Approval Checkpoint Controls */}
      {!isApproved ? (
        <div className="mt-3.5 rounded-lg border border-slate-800 bg-slate-900/90 p-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-2">
            Citizen Authorization & Approval
          </span>

          <div className="space-y-2 text-xs text-slate-300">
            <label className="flex items-start gap-2.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={confirmCorrectness}
                onChange={(e) => setConfirmCorrectness(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-slate-700 bg-slate-800 text-emerald-500 focus:ring-emerald-500/40"
              />
              <span>
                I have inspected the application information above and confirm that all details are accurate.
              </span>
            </label>

            <label className="flex items-start gap-2.5 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={acknowledgeUnsubmitted}
                onChange={(e) => setAcknowledgeUnsubmitted(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-slate-700 bg-slate-800 text-emerald-500 focus:ring-emerald-500/40"
              />
              <span>
                I acknowledge that this document draft has <strong className="text-amber-300">NOT been submitted</strong> to the government.
                I authorize this draft for my personal use.
              </span>
            </label>
          </div>

          {approvalError && (
            <div className="mt-2 text-xs text-rose-400 flex items-center gap-1.5">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              <span>{approvalError}</span>
            </div>
          )}

          <div className="mt-3 flex items-center gap-2">
            <button
              type="button"
              disabled={isApproving || !confirmCorrectness || !acknowledgeUnsubmitted}
              onClick={handleApprove}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white transition-colors"
            >
              {isApproving ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Recording Approval...
                </>
              ) : (
                <>
                  <Check className="h-3.5 w-3.5" />
                  Approve Draft (v{currentVersion})
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => setIsRequestingChanges(!isRequestingChanges)}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-750 px-2.5 py-1.5 text-xs text-slate-300 transition-colors"
            >
              <Edit3 className="h-3.5 w-3.5" />
              Request Corrections
            </button>
          </div>

          {/* Correction input box */}
          {isRequestingChanges && (
            <form onSubmit={handleSubmitChangeRequest} className="mt-3 border-t border-slate-800 pt-2.5">
              <label className="text-[11px] text-slate-400 block mb-1">
                Describe the corrections needed (e.g. correct spelling of father's name or updated address):
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={changeReason}
                  onChange={(e) => setChangeReason(e.target.value)}
                  placeholder="Enter correction details..."
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={isSubmittingChanges || !changeReason.trim()}
                  className="rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-40 px-3 py-1.5 text-xs font-medium text-white transition-colors"
                >
                  {isSubmittingChanges ? 'Submitting...' : 'Submit Revision'}
                </button>
              </div>
            </form>
          )}
        </div>
      ) : (
        /* Approved Checkpoint Status & Handoff Guidance */
        <div className="mt-3.5 rounded-lg border border-emerald-900/80 bg-emerald-950/20 p-3.5">
          <div className="flex items-center justify-between border-b border-emerald-900/50 pb-2.5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
              <span className="text-xs font-semibold text-emerald-300">
                Approved for Personal Use (v{review.active_approval?.document_version || currentVersion})
              </span>
            </div>
            <button
              type="button"
              onClick={() => setIsRequestingChanges(!isRequestingChanges)}
              className="text-[11px] text-slate-400 hover:text-amber-300 flex items-center gap-1 transition-colors"
            >
              <Edit3 className="h-3 w-3" />
              Reopen & Revise
            </button>
          </div>

          {isRequestingChanges && (
            <form onSubmit={handleSubmitChangeRequest} className="mt-2.5 border-b border-slate-800 pb-2.5">
              <label className="text-[11px] text-slate-400 block mb-1">
                Reopening will invalidate your approval. Describe needed corrections:
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={changeReason}
                  onChange={(e) => setChangeReason(e.target.value)}
                  placeholder="Describe needed corrections..."
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={isSubmittingChanges || !changeReason.trim()}
                  className="rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-40 px-3 py-1.5 text-xs font-medium text-white transition-colors"
                >
                  Invalidate & Edit
                </button>
              </div>
            </form>
          )}

          {/* Sourced Submission Handoff */}
          <div className="mt-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 block mb-2">
              Official Submission Instructions ({handoff?.handoff_type?.toUpperCase() || review.handoff_type?.toUpperCase()})
            </span>

            {isLoadingHandoff ? (
              <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-emerald-400" />
                <span>Loading verified submission guidance...</span>
              </div>
            ) : handoff ? (
              <div className="space-y-2 text-xs">
                <ol className="space-y-1.5 text-slate-300">
                  {handoff.submission_instructions?.map((step, idx) => (
                    <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                      <span className="font-semibold text-emerald-400 shrink-0">•</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>

                {/* Handoff Actions */}
                <div className="mt-3 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
                  {handoff.handoff_type === 'offline' && (
                    <button
                      type="button"
                      onClick={() => handleDownloadFinal(latestDocument?.document_id || review.latest_document_id)}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-colors"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Download Approved Submission Pack
                    </button>
                  )}

                  {handoff.official_portal_url && (
                    <button
                      type="button"
                      onClick={() => handlePortalOpen(handoff.official_portal_url)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-600/60 bg-emerald-950/40 hover:bg-emerald-900/50 px-3 py-1.5 text-xs font-medium text-emerald-300 transition-colors"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open Official Government Portal
                    </button>
                  )}
                </div>
              </div>
            ) : null}

            {/* Legal Submission Transparency Notice */}
            <div className="mt-3 flex items-start gap-2 rounded-lg bg-slate-950/80 p-2.5 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
              <ShieldAlert className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
              <span>
                <strong className="text-slate-300">NOT SUBMITTED TO GOVERNMENT:</strong> RedTape AI prepares unsubmitted drafts and procedural guides.
                You remain in full control of physical submission, online authentication (OTP/Aadhaar), and official filing.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
