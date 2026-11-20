import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

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
        className="relative flex items-end gap-2 bg-slate-900 border border-slate-800 rounded-2xl p-2 shadow-xl focus-within:border-slate-700 focus-within:ring-1 focus-within:ring-emerald-500/40 transition-all"
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
          className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 text-sm px-3 py-2 resize-none outline-none max-h-44 leading-relaxed"
        />

        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className={`w-9 h-9 rounded-xl flex items-center justify-center transition-all shrink-0 ${
            canSend
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-950 cursor-pointer'
              : 'bg-slate-800 text-slate-600 cursor-not-allowed opacity-50'
          }`}
        >
          <ArrowUp className="w-4 h-4 stroke-[2.5]" />
        </button>
      </form>

      <div className="text-center mt-2">
        <p className="text-[11px] text-slate-500">
          RedTape AI Demo Mode &bull; Real regulatory interview and verification activate in Milestone M3.
        </p>
      </div>
    </div>
  );
}
