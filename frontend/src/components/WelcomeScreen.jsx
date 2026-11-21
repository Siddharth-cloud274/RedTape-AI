import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, FileText, Store, GraduationCap, UtensilsCrossed, ArrowUpRight } from 'lucide-react';

const SUGGESTIONS = [
  {
    icon: FileText,
    label: "Income Certificate",
    prompt: "I need an income certificate.",
    detail: "E-District portal & revenue inspector process",
  },
  {
    icon: Store,
    label: "Trade Licence",
    prompt: "I want a trade licence for my shop.",
    detail: "Municipal corporation / Gram Panchayat clearance",
  },
  {
    icon: GraduationCap,
    label: "Domicile Certificate",
    prompt: "I need a domicile certificate for college.",
    detail: "Proforma A1/A2, SDO, and 10-year residency proofs",
  },
  {
    icon: UtensilsCrossed,
    label: "Food Business Registration",
    prompt: "I want to open a small bakery.",
    detail: "FSSAI FoSCoS registration vs state license thresholds",
  },
];

export default function WelcomeScreen({ onSelectPrompt }) {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const itemAnim = {
    hidden: { y: 16, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { duration: 0.4, ease: "easeOut" } },
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-8 text-center max-w-2xl mx-auto my-auto relative z-10">
      {/* Brand Icon with Pulsing Crimson Glow */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative mb-5 group"
      >
        <div className="absolute -inset-3 bg-crimson-600/30 rounded-2xl blur-xl opacity-70 group-hover:opacity-100 transition-opacity animate-pulse-slow pointer-events-none" />
        <div className="relative w-16 h-16 rounded-2xl p-0.5 bg-gradient-to-b from-slate-400/30 via-slate-700/20 to-crimson-900/40 shadow-crimson-glow overflow-hidden">
          <img
            src="/logo.jpg"
            alt="RedTape Logo"
            className="w-full h-full object-cover rounded-[14px]"
          />
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent pointer-events-none rounded-[14px]" />
        </div>
      </motion.div>

      {/* Main Heading */}
      <motion.h2
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.1, duration: 0.4 }}
        className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-2"
      >
        How can I help you today?
      </motion.h2>

      {/* Supporting Text */}
      <motion.p
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.15, duration: 0.4 }}
        className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto mb-8 leading-relaxed"
      >
        Describe your situation or bureaucratic goal in plain language. RedTape AI identifies the required government procedures, documents, eligibility criteria, and portals.
      </motion.p>

      {/* Optional Suggestion Chips */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="w-full"
      >
        <div className="flex items-center justify-center gap-1.5 text-xs text-slate-400 mb-3.5 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-crimson-400" />
          <span>Quick scenarios to explore:</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left">
          {SUGGESTIONS.map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.button
                key={index}
                variants={itemAnim}
                type="button"
                onClick={() => onSelectPrompt(item.prompt)}
                className="group relative flex items-start gap-3 p-3.5 rounded-2xl bg-obsidian-850/80 hover:bg-obsidian-800 border border-titanium-400/10 hover:border-crimson-500/40 text-slate-300 hover:text-white transition-all text-xs backdrop-blur-md shadow-sm hover:shadow-crimson-sm cursor-pointer"
              >
                <div className="w-8 h-8 rounded-xl bg-obsidian-750 group-hover:bg-crimson-950/70 border border-titanium-400/10 group-hover:border-crimson-700/50 flex items-center justify-center text-slate-400 group-hover:text-crimson-400 shrink-0 transition-all mt-0.5 shadow-sm">
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0 pr-4">
                  <div className="font-semibold text-slate-200 group-hover:text-white truncate">
                    {item.label}
                  </div>
                  <p className="text-[11px] text-slate-400 group-hover:text-slate-300 truncate mt-0.5">
                    "{item.prompt}"
                  </p>
                </div>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-crimson-400 opacity-0 group-hover:opacity-100 transition-all absolute top-3.5 right-3.5" />
              </motion.button>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
