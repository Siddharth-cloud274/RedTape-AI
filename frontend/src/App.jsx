import React, { useState, useEffect } from 'react';
import AppShell from './components/AppShell';
import ChatWindow from './components/ChatWindow';
import { sendChatMessage } from './services/chatTransport';
import { getConversationHistory } from './services/api';

const STORAGE_KEY = 'redtape_conversations_v1';

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
    facts: [],
    isExpired: false,
    createdAt: new Date().toISOString(),
  };
}

function loadSavedConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map((item) => ({
          id: item.id || `conv-${Date.now()}`,
          backendId: item.backendId || null,
          title: item.title || 'Conversation',
          messages: item.messages || [],
          facts: item.facts || [],
          isExpired: false,
          createdAt: item.createdAt || new Date().toISOString(),
        }));
      }
    }
  } catch {
    // Ignore localStorage parse errors and fall through
  }
  return [createNewConversation()];
}

export default function App() {
  const [conversations, setConversations] = useState(loadSavedConversations);
  const [activeId, setActiveId] = useState(() => conversations[0]?.id);
  // Track which conversation IDs currently have a message in-flight
  const [pendingConversations, setPendingConversations] = useState({});

  const activeConversation = conversations.find((c) => c.id === activeId) || conversations[0];
  const isTyping = Boolean(pendingConversations[activeConversation?.id]);

  // Persist conversation summaries to localStorage
  useEffect(() => {
    try {
      const toSave = conversations.map((c) => ({
        id: c.id,
        backendId: c.backendId,
        title: c.title,
        createdAt: c.createdAt,
        // Persist messages so offline / fast-reload works seamlessly
        messages: c.messages,
        facts: c.facts || [],
      }));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
    } catch {
      // Ignore quota errors
    }
  }, [conversations]);

  // Re-hydrate full conversation history from SQLite if conversation has a backendId
  useEffect(() => {
    if (!activeConversation || !activeConversation.backendId) return;

    let isMounted = true;
    const backendId = activeConversation.backendId;

    getConversationHistory(backendId).then((res) => {
      if (!isMounted || !res.success || !res.data) return;

      const serverMessages = (res.data.messages || []).map((m, idx, arr) => {
        const isLastAssistant =
          m.role === 'assistant' &&
          !arr.slice(idx + 1).some((other) => other.role === 'assistant');
        return {
          id: m.id,
          role: m.role,
          content: m.content,
          mode: m.mode,
          status: 'sent',
          timestamp: m.created_at,
          document_draft: isLastAssistant ? res.data.document_draft : null,
          official_resources: isLastAssistant ? res.data.official_resources : null,
        };
      });

      setConversations((prev) =>
        prev.map((c) => {
          if (c.backendId === backendId) {
            return {
              ...c,
              title: res.data.title || c.title,
              messages: serverMessages,
              facts: res.data.facts || [],
              document_draft: res.data.document_draft || null,
              official_resources: res.data.official_resources || null,
              isExpired: false,
            };
          }
          return c;
        })
      );
    });

    return () => {
      isMounted = false;
    };
  }, [activeConversation?.backendId]);

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
              document_draft: responseData.document_draft || null,
              official_resources: responseData.official_resources || null,
            };

            return {
              ...c,
              backendId: responseData.conversation_id,
              isExpired: false,
              messages: [...updatedMessages, assistantMsg],
              facts: responseData.facts || c.facts || [],
              document_draft: responseData.document_draft || c.document_draft || null,
              official_resources: responseData.official_resources || c.official_resources || null,
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

  const handleUpdateDocument = (updatedDoc) => {
    if (!updatedDoc) return;
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id === activeId || c.backendId === updatedDoc.conversation_id) {
          const updatedMessages = c.messages.map((m, idx, arr) => {
            const isLastAssistant =
              m.role === 'assistant' &&
              !arr.slice(idx + 1).some((other) => other.role === 'assistant');
            return isLastAssistant ? { ...m, document_draft: updatedDoc } : m;
          });
          return {
            ...c,
            messages: updatedMessages,
            document_draft: updatedDoc,
          };
        }
        return c;
      })
    );
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
        onUpdateDocument={handleUpdateDocument}
        isTyping={isTyping}
      />
    </AppShell>
  );
}

