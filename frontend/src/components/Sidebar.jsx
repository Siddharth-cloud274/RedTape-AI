import React from 'react';
import { motion } from 'framer-motion';
import { Plus, MessageSquare, Trash2, X, Shield, Sparkles } from 'lucide-react';
import ConnectionStatus from './ConnectionStatus';

export default function Sidebar({
  conversations,
  activeId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  isOpenMobile,
  onCloseMobile,
}) {
  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 bg-black/80 backdrop-blur-md z-40 md:hidden transition-opacity"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 flex flex-col w-72 bg-obsidian-900 border-r border-obsidian-700/80 transition-transform duration-300 ease-in-out ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand & Mobile Close Header */}
        <div className="flex items-center justify-between p-4 border-b border-obsidian-750">
          <div className="flex items-center gap-3">
            {/* Shared Motion Logo */}
            <motion.div
              layoutId="redtape-brand-logo"
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 28,
              }}
              className="relative w-9 h-9 rounded-xl p-0.5 bg-gradient-to-b from-slate-400/40 via-slate-600/30 to-crimson-800/50 shadow-crimson-sm overflow-hidden shrink-0"
            >
              <img
                src="/logo.jpg"
                alt="RedTape Logo"
                className="w-full h-full object-cover rounded-[10px]"
              />
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent pointer-events-none rounded-[10px]" />
            </motion.div>

            <div>
              <h1 className="font-bold text-sm tracking-tight text-white flex items-center gap-1.5">
                <span>RedTape AI</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-crimson-950/80 text-crimson-400 border border-crimson-800/60">
                  v0.1
                </span>
              </h1>
              <p className="text-[11px] text-slate-400 font-medium">Citizen Bureaucracy AI</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onCloseMobile}
            className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-obsidian-800 transition-colors"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action Button: New Chat with Crimson Ribbon Theme */}
        <div className="p-3">
          <button
            type="button"
            onClick={() => {
              onNewChat();
              if (isOpenMobile) onCloseMobile();
            }}
            className="w-full group relative flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-crimson-600 via-rose-600 to-crimson-700 hover:from-crimson-500 hover:to-crimson-600 text-white font-semibold text-xs tracking-wide transition-all shadow-crimson-sm hover:shadow-crimson-glow active:scale-[0.99] cursor-pointer"
          >
            <Plus className="w-4 h-4 transition-transform group-hover:rotate-90 duration-300" />
            <span>New Consultation</span>
            <span className="absolute -inset-0.5 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          </button>
        </div>

        {/* Conversation History List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <div className="flex items-center justify-between px-2 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            <span>Conversations</span>
            <Sparkles className="w-3 h-3 text-crimson-500/70" />
          </div>

          {conversations.length === 0 ? (
            <div className="px-3 py-8 text-center text-xs text-slate-500">
              No active sessions. Start a new consultation above.
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeId;
              return (
                <div
                  key={conv.id}
                  className={`group relative flex items-center justify-between rounded-xl px-3 py-2.5 text-xs transition-all cursor-pointer ${
                    isActive
                      ? 'bg-obsidian-800 text-white font-medium border border-crimson-600/40 shadow-crimson-sm'
                      : 'text-slate-400 hover:bg-obsidian-800/60 hover:text-slate-200 border border-transparent'
                  }`}
                  onClick={() => {
                    onSelectConversation(conv.id);
                    if (isOpenMobile) onCloseMobile();
                  }}
                >
                  {/* Active glowing indicator pill */}
                  {isActive && (
                    <div className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-gradient-to-b from-crimson-400 to-crimson-600 shadow-crimson-sm" />
                  )}

                  <div className="flex items-center gap-2.5 min-w-0 pr-6 pl-1">
                    <MessageSquare
                      className={`w-3.5 h-3.5 shrink-0 ${
                        isActive ? 'text-crimson-400' : 'text-slate-500 group-hover:text-slate-400'
                      }`}
                    />
                    <span className="truncate">{conv.title || 'New Conversation'}</span>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    title="Delete conversation"
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-crimson-400 rounded-lg hover:bg-obsidian-700/60 transition-all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer with Backend Health Status & Soul Coders Copyright */}
        <div className="p-3 border-t border-obsidian-750 space-y-2 bg-obsidian-950/60 backdrop-blur-md">
          <ConnectionStatus />
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-500 pt-1">
            <Shield className="w-3 h-3 text-slate-500" />
            <span>Hack-N-Pitch 2026 &bull; M6</span>
          </div>
        </div>
      </aside>
    </>
  );
}
