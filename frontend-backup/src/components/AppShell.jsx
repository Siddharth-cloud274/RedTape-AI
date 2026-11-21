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
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 selection:bg-emerald-500 selection:text-white">
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
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800 shrink-0">
          <button
            type="button"
            onClick={() => setIsMobileSidebarOpen(true)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Open sidebar menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-bold text-white text-xs">
              RT
            </div>
            <span className="font-semibold text-sm text-white">RedTape AI</span>
          </div>

          <button
            type="button"
            onClick={onNewChat}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Start new chat"
          >
            <Plus className="w-5 h-5" />
          </button>
        </header>

        {/* Chat Window / Main viewport */}
        <main className="flex-1 flex flex-col h-full overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
