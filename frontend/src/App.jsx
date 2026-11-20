import React, { useState } from 'react';
import AppShell from './components/AppShell';
import ChatWindow from './components/ChatWindow';
import { sendChatMessage } from './services/chatTransport';

function createClientUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function createNewConversation() {
  return {
    id: `conv-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    backendId: null, // Initialized to null; set upon first successful POST /api/chat
    title: 'New Conversation',
    messages: [],
    isExpired: false,
    createdAt: new Date().toISOString(),
  };
}

export default function App() {
  const [conversations, setConversations] = useState(() => [createNewConversation()]);
  const [activeId, setActiveId] = useState(() => conversations[0]?.id);
  // Track which conversation IDs currently have a message in-flight
  const [pendingConversations, setPendingConversations] = useState({});

  const activeConversation = conversations.find((c) => c.id === activeId) || conversations[0];
  const isTyping = Boolean(pendingConversations[activeConversation?.id]);

  const handleNewChat = () => {
    if (activeConversation && activeConversation.messages.length === 0) {
      return;
    }
    const newConv = createNewConversation();
    setConversations((prev) => [newConv, ...prev]);
    setActiveId(newConv.id);
  };

  const handleSelectConversation = (id) => {
    setActiveId(id);
  };

  const handleDeleteConversation = (id) => {
    setConversations((prev) => {
      const filtered = prev.filter((c) => c.id !== id);
      if (filtered.length === 0) {
        const fresh = createNewConversation();
        setActiveId(fresh.id);
        return [fresh];
      }
      if (activeId === id) {
        setActiveId(filtered[0].id);
      }
      return filtered;
    });
  };

  const handleResetSession = () => {
    if (!activeConversation) return;
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeConversation.id
          ? { ...c, backendId: null, isExpired: false }
          : c
      )
    );
  };

  const dispatchMessage = async (targetConvId, clientMessageId, messageText) => {
    // Mark target conversation as pending
    setPendingConversations((prev) => ({ ...prev, [targetConvId]: true }));

    // Find current backendId for this specific target conversation
    const targetConv = conversations.find((c) => c.id === targetConvId);
    const backendConversationId = targetConv?.backendId || null;

    try {
      const responseData = await sendChatMessage({
        conversationId: backendConversationId,
        clientMessageId,
        message: messageText,
      });

      // Update specific target conversation with response and backend conversation ID
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id === targetConvId) {
            // Update user message to 'sent'
            const updatedMessages = c.messages.map((m) =>
              m.id === clientMessageId ? { ...m, status: 'sent', error: null } : m
            );

            // Append assistant response
            const assistantMsg = {
              id: responseData.message_id,
              role: 'assistant',
              content: responseData.reply,
              mode: responseData.mode,
              timestamp: new Date().toISOString(),
            };

            return {
              ...c,
              backendId: responseData.conversation_id,
              isExpired: false,
              messages: [...updatedMessages, assistantMsg],
            };
          }
          return c;
        })
      );
    } catch (err) {
      const is404 = err.status === 404;

      // Mark user message as error (preserve content, never fabricate assistant reply)
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id === targetConvId) {
            const updatedMessages = c.messages.map((m) =>
              m.id === clientMessageId
                ? {
                    ...m,
                    status: 'error',
                    error: is404
                      ? 'Backend session not found or expired.'
                      : err.message || 'Failed to send message to backend.',
                  }
                : m
            );

            return {
              ...c,
              isExpired: is404 ? true : c.isExpired,
              messages: updatedMessages,
            };
          }
          return c;
        })
      );
    } finally {
      // Clear pending state for target conversation
      setPendingConversations((prev) => {
        const next = { ...prev };
        delete next[targetConvId];
        return next;
      });
    }
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() || isTyping) return;

    const targetConvId = activeConversation.id;
    const clientMessageId = createClientUUID();

    const userMessage = {
      id: clientMessageId,
      role: 'user',
      content: text,
      status: 'pending',
      timestamp: new Date().toISOString(),
    };

    // Pre-append user message immediately and set title if first message
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id === targetConvId) {
          const isFirstMessage = c.messages.length === 0;
          const newTitle = isFirstMessage
            ? text.length > 28 ? `${text.substring(0, 28).trim()}...` : text
            : c.title;

          return {
            ...c,
            title: newTitle,
            messages: [...c.messages, userMessage],
          };
        }
        return c;
      })
    );

    await dispatchMessage(targetConvId, clientMessageId, text);
  };

  const handleRetryMessage = async (messageId) => {
    const targetConvId = activeConversation.id;
    const targetMessage = activeConversation.messages.find((m) => m.id === messageId);
    if (!targetMessage) return;

    // Reset message to pending
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id === targetConvId) {
          return {
            ...c,
            messages: c.messages.map((m) =>
              m.id === messageId ? { ...m, status: 'pending', error: null } : m
            ),
          };
        }
        return c;
      })
    );

    // Re-dispatch using original client_message_id (enforcing server idempotency)
    await dispatchMessage(targetConvId, targetMessage.id, targetMessage.content);
  };

  return (
    <AppShell
      conversations={conversations}
      activeId={activeId}
      onSelectConversation={handleSelectConversation}
      onNewChat={handleNewChat}
      onDeleteConversation={handleDeleteConversation}
    >
      <ChatWindow
        conversation={activeConversation}
        onSendMessage={handleSendMessage}
        onRetryMessage={handleRetryMessage}
        onResetSession={handleResetSession}
        isTyping={isTyping}
      />
    </AppShell>
  );
}
