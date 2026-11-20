import React, { useState } from 'react';
import AppShell from './components/AppShell';
import ChatWindow from './components/ChatWindow';
import { sendChatMessage } from './services/chatTransport';

function createNewConversation() {
  const id = `conv-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
  return {
    id,
    title: 'New Conversation',
    messages: [],
    createdAt: new Date().toISOString(),
  };
}

export default function App() {
  // Initialize with one fresh conversation
  const [conversations, setConversations] = useState(() => [createNewConversation()]);
  const [activeId, setActiveId] = useState(() => conversations[0]?.id);
  const [isTyping, setIsTyping] = useState(false);

  // Active conversation object
  const activeConversation = conversations.find((c) => c.id === activeId) || conversations[0];

  const handleNewChat = () => {
    // If the active conversation is already empty, just keep it active
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

  const handleSendMessage = async (text) => {
    const userMessage = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    const targetConvId = activeConversation.id;

    // Append user message immediately & update conversation title if first message
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

    setIsTyping(true);

    try {
      // Dispatch to isolated transport adapter
      const assistantResponse = await sendChatMessage(targetConvId, text);

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id === targetConvId) {
            return {
              ...c,
              messages: [...c.messages, assistantResponse],
            };
          }
          return c;
        })
      );
    } catch (err) {
      const errorResponse = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: 'Error: Failed to obtain response. Please try again.',
        timestamp: new Date().toISOString(),
        isMock: true,
      };

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id === targetConvId) {
            return {
              ...c,
              messages: [...c.messages, errorResponse],
            };
          }
          return c;
        })
      );
    } finally {
      setIsTyping(false);
    }
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
        isTyping={isTyping}
      />
    </AppShell>
  );
}
