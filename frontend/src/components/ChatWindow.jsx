import React, { useState, useRef, useEffect } from 'react';
import WelcomeScreen from './WelcomeScreen';
import MessageBubble from './MessageBubble';
import ChatComposer from './ChatComposer';

export default function ChatWindow({
  conversation,
  onSendMessage,
  isTyping = false,
}) {
  const [prefill, setPrefill] = useState('');
  const messagesEndRef = useRef(null);

  const messages = conversation?.messages || [];
  const hasMessages = messages.length > 0;

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
      {/* Scrollable Message History or Welcome Screen */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {!hasMessages ? (
          <WelcomeScreen onSelectPrompt={handleSelectPrompt} />
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
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
