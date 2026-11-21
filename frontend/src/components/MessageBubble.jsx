import React from 'react';
import { User, Bot, AlertCircle, RotateCcw } from 'lucide-react';
import DocumentCard from './DocumentCard';
import OfficialResourcesCard from './OfficialResourcesCard';

function renderFormattedContent(content) {
  if (!content) return null;

  const regex = /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)|\*\*([^*]+)\*\*|(https?:\/\/[^\s\)]+)/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(content.substring(lastIndex, match.index));
    }

    if (match[1] && match[2]) {
      parts.push(
        <a
          key={match.index}
          href={match[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-0.5 text-emerald-400 hover:text-emerald-300 underline underline-offset-2 font-medium"
        >
          {match[1]}
        </a>
      );
    } else if (match[3]) {
      parts.push(
        <strong key={match.index} className="font-semibold text-white">
          {match[3]}
        </strong>
      );
    } else if (match[4]) {
      parts.push(
        <a
          key={match.index}
          href={match[4]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-emerald-400 hover:text-emerald-300 underline underline-offset-2 break-all"
        >
          {match[4]}
        </a>
      );
    }

    lastIndex = regex.lastIndex;
  }

  if (lastIndex < content.length) {
    parts.push(content.substring(lastIndex));
  }

  return parts;
}

export default function MessageBubble({ message, isTyping = false, onRetry, onUpdateDocument }) {
  if (isTyping) {
    return (
      <div className="flex items-start gap-3 max-w-3xl mr-auto py-2">
        <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400 shrink-0">
          <Bot className="w-4 h-4 animate-pulse" />
        </div>
        <div className="rounded-2xl px-4 py-3 bg-slate-900 border border-slate-800 text-slate-300 text-sm flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce [animation-delay:-0.3s]"></span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce [animation-delay:-0.15s]"></span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-bounce"></span>
        </div>
      </div>
    );
  }

  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const isPending = message.status === 'pending';

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className={`flex items-start gap-3 max-w-3xl py-2 ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-semibold ${
          isUser
            ? isError
              ? 'bg-rose-950/80 text-rose-300 border border-rose-800/60'
              : 'bg-slate-700 text-slate-200'
            : 'bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-sm shadow-emerald-950'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : 'RT'}
      </div>

      {/* Bubble Content */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] sm:max-w-xl`}>
        {/* Role & Mode Badge for Assistant */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-1 px-1">
            <span className="text-[11px] font-semibold text-slate-300">RedTape AI</span>
            {message.mode === 'gemini' && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.2 rounded font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                AI Assistant
              </span>
            )}
            {message.mode === 'backend_stub' && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.2 rounded font-mono bg-slate-800 text-slate-400 border border-slate-700">
                Backend Stub
              </span>
            )}
          </div>
        )}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words ${
            isUser
              ? isError
                ? 'bg-rose-950/30 text-slate-200 border border-rose-800/60 rounded-tr-sm'
                : 'bg-slate-800 text-slate-100 border border-slate-700 rounded-tr-sm'
              : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-tl-sm shadow-sm'
          }`}
        >
          {renderFormattedContent(message.content)}

          {/* Attached Official Government Resources & Checklist */}
          {!isUser && message.official_resources && (
            <OfficialResourcesCard resources={message.official_resources} />
          )}

          {/* Attached Document Draft Card */}
          {!isUser && message.document_draft && (
            <DocumentCard
              document={message.document_draft}
              onUpdateDocument={onUpdateDocument}
            />
          )}
        </div>

        {/* Status / Error & Retry Action */}
        {isUser && isError && (
          <div className="flex items-center gap-2 mt-1.5 px-1 text-xs text-rose-400">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate max-w-xs">{message.error || 'Failed to deliver message.'}</span>
            {onRetry && (
              <button
                type="button"
                onClick={() => onRetry(message.id)}
                className="inline-flex items-center gap-1 ml-1 px-2 py-0.5 rounded bg-rose-900/50 hover:bg-rose-800/60 text-[11px] text-rose-200 border border-rose-700/50 transition-colors"
              >
                <RotateCcw className="w-3 h-3" />
                Retry
              </button>
            )}
          </div>
        )}

        {isUser && isPending && (
          <span className="text-[10px] text-slate-500 mt-1 px-1 animate-pulse">
            Thinking...
          </span>
        )}

        {/* Timestamp */}
        {formattedTime && !isPending && !isError && (
          <span className="text-[10px] text-slate-500 mt-1 px-1">
            {formattedTime}
          </span>
        )}
      </div>
    </div>
  );
}
