import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Sparkles } from 'lucide-react';

export default function ChatComposer({ onSendMessage, disabled = false, prefillValue = '', onClearPrefill }) {
  const [inputText, setInputText] = useState('');
  const textareaRef = useRef(null);

  // Sync prefill from suggestion chips
  useEffect(() => {
    if (prefillValue) {
      setInputText(prefillValue);
      if (onClearPrefill) onClearPrefill();
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [prefillValue, onClearPrefill]);

  // Auto-resize textarea height
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 180);
      textarea.style.height = `${newHeight}px`;
    }
  }, [inputText]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    const trimmed = inputText.trim();
    if (!trimmed || disabled) return;

    onSendMessage(trimmed);
    setInputText('');

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSend = inputText.trim().length > 0 && !disabled;

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4">
      <form
        onSubmit={handleSubmit}
        className="relative flex items-end gap-2 bg-obsidian-900/90 backdrop-blur-xl border border-obsidian-700/80 rounded-2xl p-2.5 shadow-2xl focus-within:border-crimson-500/60 focus-within:ring-2 focus-within:ring-crimson-500/20 transition-all duration-200"
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask anything about Indian bureaucracy, certificates, registrations..."
          aria-label="Chat input message"
          className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 text-sm px-3 py-1.5 resize-none outline-none max-h-44 leading-relaxed font-normal"
        />

        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all shrink-0 ${
            canSend
              ? 'bg-gradient-to-tr from-crimson-600 via-rose-600 to-crimson-500 text-white shadow-crimson-sm hover:shadow-crimson-glow cursor-pointer hover:scale-105 active:scale-95'
              : 'bg-obsidian-800 text-slate-600 cursor-not-allowed opacity-40'
          }`}
        >
          <ArrowUp className="w-4 h-4 stroke-[2.5]" />
        </button>
      </form>

      <div className="flex items-center justify-between mt-2.5 px-2 text-[11px] text-slate-500">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-3 h-3 text-crimson-400" />
          <span>RedTape AI &bull; Autonomous Bureaucracy Assistant</span>
        </div>
        <span className="hidden sm:inline-block font-mono text-[10px] text-slate-600">
          Enter ↵ to send &bull; Shift+Enter for newline
        </span>
      </div>
    </div>
  );
}
