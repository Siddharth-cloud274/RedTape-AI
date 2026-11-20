import React from 'react';
import { Sparkles, FileText, Store, GraduationCap, UtensilsCrossed } from 'lucide-react';

const SUGGESTIONS = [
  {
    icon: FileText,
    label: "Income Certificate",
    prompt: "I need an income certificate.",
  },
  {
    icon: Store,
    label: "Trade Licence",
    prompt: "I want a trade licence for my shop.",
  },
  {
    icon: GraduationCap,
    label: "Domicile Certificate",
    prompt: "I need a domicile certificate for college.",
  },
  {
    icon: UtensilsCrossed,
    label: "Food Business Registration",
    prompt: "I want to open a small bakery.",
  },
];

export default function WelcomeScreen({ onSelectPrompt }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-8 text-center max-w-2xl mx-auto my-auto">
      {/* Brand Icon */}
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-bold text-white shadow-xl shadow-emerald-950/60 mb-5 text-xl">
        RT
      </div>

      {/* Main Heading */}
      <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
        How can I help you today?
      </h2>

      {/* Supporting Text */}
      <p className="text-sm text-slate-400 max-w-md mx-auto mb-8 leading-relaxed">
        Describe your situation or bureaucratic need in plain language. RedTape AI identifies the required government procedures, documents, and authorities.
      </p>

      {/* Optional Suggestion Chips */}
      <div className="w-full">
        <div className="flex items-center justify-center gap-1.5 text-xs text-slate-500 mb-3 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          <span>Examples of what you can ask:</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
          {SUGGESTIONS.map((item, index) => {
            const Icon = item.icon;
            return (
              <button
                key={index}
                type="button"
                onClick={() => onSelectPrompt(item.prompt)}
                className="flex items-center gap-3 p-3 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all text-xs group"
              >
                <div className="w-7 h-7 rounded-lg bg-slate-800 group-hover:bg-emerald-950/60 flex items-center justify-center text-slate-400 group-hover:text-emerald-400 shrink-0 transition-colors">
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <span className="truncate">{item.prompt}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
