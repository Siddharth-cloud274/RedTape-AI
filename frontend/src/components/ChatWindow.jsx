import React, { useState, useRef, useEffect } from 'react';
import WelcomeScreen from './WelcomeScreen';
import MessageBubble from './MessageBubble';
import ChatComposer from './ChatComposer';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ChatWindow({
  conversation,
  onSendMessage,
  onRetryMessage,
  onResetSession,
  isTyping = false,
}) {
  const [prefill, setPrefill] = useState('');
  const messagesEndRef = useRef(null);

  const messages = conversation?.messages || [];
  const hasMessages = messages.length > 0;
  const isExpired = conversation?.isExpired;

  // Auto-scroll to bottom whenever messages or typing state changes
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isTyping]);

  const handleSelectPrompt = (promptText) => {
    setPrefill(promptText);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950 relative">
      {/* Session Expired Notice Banner */}
      {isExpired && (
        <div className="bg-amber-950/70 border-b border-amber-800/60 px-4 py-2.5 flex items-center justify-between text-xs text-amber-200">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              Backend conversation session expired or was reset. Message history is preserved.
            </span>
          </div>
          {onResetSession && (
            <button
              type="button"
              onClick={onResetSession}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-900/60 hover:bg-amber-800 text-[11px] font-medium text-amber-100 border border-amber-700/60 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              Start Fresh Session
            </button>
          )}
        </div>
      )}

      {/* Scrollable Message History or Welcome Screen */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {!hasMessages ? (
          <WelcomeScreen onSelectPrompt={handleSelectPrompt} />
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                message={msg}
                onRetry={onRetryMessage}
              />
            ))}

            {isTyping && <MessageBubble isTyping={true} />}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Composer Dock */}
      <div className="shrink-0 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent pt-4">
        <ChatComposer
          onSendMessage={onSendMessage}
          disabled={isTyping}
          prefillValue={prefill}
          onClearPrefill={() => setPrefill('')}
        />
      </div>
    </div>
  );
}
