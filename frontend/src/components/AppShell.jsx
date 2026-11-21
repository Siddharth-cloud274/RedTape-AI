import React, { useState } from 'react';
import { Menu, Plus } from 'lucide-react';
import Sidebar from './Sidebar';

export default function AppShell({
  conversations,
  activeId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  children,
}) {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden ambient-glow-bg text-slate-100 selection:bg-crimson-600 selection:text-white">
      {/* Sidebar (Desktop static & Mobile drawer) */}
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelectConversation={onSelectConversation}
        onNewChat={onNewChat}
        onDeleteConversation={onDeleteConversation}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Mobile Top App Bar */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-obsidian-900/90 backdrop-blur-md border-b border-obsidian-750 shrink-0 z-30">
          <button
            type="button"
            onClick={() => setIsMobileSidebarOpen(true)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-obsidian-800 transition-colors"
            aria-label="Open sidebar menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg overflow-hidden border border-titanium-400/20 shadow-crimson-sm">
              <img src="/logo.jpg" alt="RedTape AI" className="w-full h-full object-cover" />
            </div>
            <span className="font-bold text-sm tracking-tight text-white">RedTape AI</span>
          </div>

          <button
            type="button"
            onClick={onNewChat}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-obsidian-800 transition-colors"
            aria-label="Start new chat"
          >
            <Plus className="w-5 h-5" />
          </button>
        </header>

        {/* Chat Window / Main viewport */}
        <main className="flex-1 flex flex-col h-full overflow-hidden relative">
          {children}
        </main>
      </div>
    </div>
  );
}
