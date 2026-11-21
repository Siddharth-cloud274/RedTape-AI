import React from 'react';
import { User, Bot, AlertCircle, RotateCcw, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

export default function MessageBubble({ message, isTyping = false, onRetry }) {
  if (isTyping) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start gap-3 max-w-3xl mr-auto py-2"
      >
        {/* Assistant Logo Badge */}
        <div className="w-8 h-8 rounded-xl p-0.5 bg-gradient-to-b from-slate-400/40 via-slate-600/30 to-crimson-800/50 shadow-crimson-sm overflow-hidden shrink-0">
          <img src="/logo.jpg" alt="RT" className="w-full h-full object-cover rounded-[10px]" />
        </div>

        {/* Dynamic Crimson Wave Typing Indicator */}
        <div className="rounded-2xl px-4 py-3 bg-obsidian-900/90 border border-obsidian-750 text-slate-300 text-sm flex items-center gap-2 shadow-sm">
          <span className="text-xs font-mono text-slate-400">Analyzing bureaucracy</span>
          <div className="flex items-center gap-1.5 ml-1">
            <span className="w-1.5 h-1.5 rounded-full bg-crimson-500 animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-crimson-400 animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1.5 h-1.5 rounded-full bg-crimson-300 animate-bounce" />
          </div>
        </div>
      </motion.div>
    );
  }

  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const isPending = message.status === 'pending';

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`flex items-start gap-3 max-w-3xl py-2 ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-semibold overflow-hidden ${
          isUser
            ? isError
              ? 'bg-rose-950/80 text-rose-300 border border-rose-800/60'
              : 'bg-obsidian-800 text-slate-200 border border-titanium-400/20 shadow-sm'
            : 'p-0.5 bg-gradient-to-b from-slate-400/40 via-slate-600/30 to-crimson-800/50 shadow-crimson-sm'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-slate-300" />
        ) : (
          <img src="/logo.jpg" alt="RT" className="w-full h-full object-cover rounded-[10px]" />
        )}
      </div>

      {/* Bubble Content */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] sm:max-w-xl`}>
        {/* Role & Mode Badge for Assistant */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-1.5 px-1">
            <span className="text-[11px] font-semibold text-slate-200 tracking-tight">RedTape AI</span>
            {message.mode === 'gemini' && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-mono bg-crimson-950/80 text-crimson-300 border border-crimson-800/60">
                <Sparkles className="w-2.5 h-2.5 text-crimson-400" />
                Gemini Agent
              </span>
            )}
            {message.mode === 'backend_stub' && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-full font-mono bg-obsidian-800 text-slate-400 border border-obsidian-700">
                Backend Stub
              </span>
            )}
          </div>
        )}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words transition-all ${
            isUser
              ? isError
                ? 'bg-rose-950/30 text-slate-200 border border-rose-800/60 rounded-tr-xs'
                : 'bg-obsidian-800 text-slate-100 border border-titanium-400/20 rounded-tr-xs shadow-md'
              : 'bg-obsidian-900/90 text-slate-200 border border-obsidian-750 rounded-tl-xs shadow-sm'
          }`}
        >
          {message.content}
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
                className="inline-flex items-center gap-1 ml-1 px-2.5 py-0.5 rounded-lg bg-rose-950/80 hover:bg-rose-900 text-[11px] text-rose-200 border border-rose-800/60 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                Retry
              </button>
            )}
          </div>
        )}

        {isUser && isPending && (
          <span className="text-[10px] text-crimson-400 mt-1 px-1 flex items-center gap-1 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-crimson-500 animate-ping" />
            Connecting to agent...
          </span>
        )}

        {/* Timestamp */}
        {formattedTime && !isPending && !isError && (
          <span className="text-[10px] text-slate-500 mt-1 px-1">
            {formattedTime}
          </span>
        )}
      </div>
    </motion.div>
  );
}
