import React from 'react';
import { User, Bot, AlertCircle } from 'lucide-react';

export default function MessageBubble({ message, isTyping = false }) {
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
  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className={`flex items-start gap-3 max-w-3xl py-2 ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-semibold ${
          isUser
            ? 'bg-slate-700 text-slate-200'
            : 'bg-gradient-to-tr from-emerald-600 to-teal-500 text-white shadow-sm shadow-emerald-950'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : 'RT'}
      </div>

      {/* Bubble Content */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] sm:max-w-xl`}>
        {/* Role & Demo Label for Assistant */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-1 px-1">
            <span className="text-[11px] font-semibold text-slate-300">RedTape AI</span>
            {message.isMock && (
              <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.2 rounded font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <AlertCircle className="w-2.5 h-2.5" />
                Demo Mode
              </span>
            )}
          </div>
        )}

        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words ${
            isUser
              ? 'bg-slate-800 text-slate-100 border border-slate-700 rounded-tr-sm'
              : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-tl-sm shadow-sm'
          }`}
        >
          {message.content}
        </div>

        {/* Timestamp */}
        {formattedTime && (
          <span className="text-[10px] text-slate-500 mt-1 px-1">
            {formattedTime}
          </span>
        )}
      </div>
    </div>
  );
}
