import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, ShieldCheck, FileCheck, Sparkles, Cpu, Layers } from 'lucide-react';

export default function HeroSection({ onDismiss }) {
  const capabilities = [
    {
      icon: Cpu,
      title: "Agentic Discovery",
      desc: "Conversational AI that identifies exact government services from natural speech.",
    },
    {
      icon: FileCheck,
      title: "Document Navigation",
      desc: "Instant breakdown of required certificates, affidavits, fees, and portals.",
    },
    {
      icon: Layers,
      title: "Contextual Memory",
      desc: "Extracts and reconciles applicant facts with zero redundant questions.",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{
        opacity: 0,
        scale: 0.97,
        filter: "blur(12px)",
        transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
      }}
      className="fixed inset-0 z-50 flex flex-col justify-between ambient-glow-bg text-slate-100 overflow-y-auto overflow-x-hidden selection:bg-crimson-600 selection:text-white"
    >
      {/* Background Decorative Grid & Glows */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(#ffffff08_1px,transparent_1px)] [background-size:24px_24px] opacity-40" />

      {/* Top Header Pill */}
      <div className="relative pt-6 px-6 flex justify-between items-center max-w-6xl mx-auto w-full z-10">
        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-obsidian-800/80 border border-titanium-400/20 text-xs font-mono text-slate-300 backdrop-blur-md"
        >
          <span className="w-2 h-2 rounded-full bg-crimson-500 animate-ping" />
          <span>REDTAPE AI &bull; INTELLIGENT CITIZEN DESK</span>
        </motion.div>

        <motion.div
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-xs text-slate-400 font-medium hidden sm:flex items-center gap-1.5"
        >
          <ShieldCheck className="w-4 h-4 text-crimson-400" />
          <span>Hack-N-Pitch 2026 Edition</span>
        </motion.div>
      </div>

      {/* Main Center Content */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 py-8 text-center max-w-4xl mx-auto">
        {/* Big Animated Logo Container with Shared Layout ID */}
        <motion.div
          className="relative mb-6 cursor-pointer group"
          onClick={onDismiss}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
        >
          {/* Pulsing Crimson Aura behind the Logo */}
          <div className="absolute -inset-4 bg-gradient-to-r from-crimson-600/30 via-crimson-500/20 to-ruby/30 rounded-3xl blur-2xl opacity-75 group-hover:opacity-100 transition-opacity animate-pulse-slow pointer-events-none" />

          {/* Shared Element Logo Wrapper */}
          <motion.div
            layoutId="redtape-brand-logo"
            transition={{
              type: "spring",
              stiffness: 260,
              damping: 28,
            }}
            className="relative w-36 h-36 sm:w-44 sm:h-44 rounded-3xl p-1 bg-gradient-to-b from-slate-400/30 via-slate-700/20 to-crimson-900/40 shadow-crimson-lg backdrop-blur-md overflow-hidden"
          >
            <img
              src="/logo.jpg"
              alt="RedTape AI Logo"
              className="w-full h-full object-cover rounded-[22px] shadow-inner"
            />
            {/* Gloss Highlight Sheen */}
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent pointer-events-none rounded-[22px]" />
          </motion.div>
        </motion.div>

        {/* Title & Tagline */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.25, duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-crimson-950/60 border border-crimson-700/50 text-crimson-300 text-xs font-semibold mb-3 shadow-crimson-sm">
            <Sparkles className="w-3.5 h-3.5 text-crimson-400" />
            <span>Autonomous Bureaucracy Navigation</span>
          </div>

          <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-white mb-4">
             Simplifying Red Tape with{' '}
            <span className="bg-gradient-to-r from-crimson-400 via-rose-300 to-crimson-500 bg-clip-text text-transparent">
              Agentic AI
            </span>
          </h1>

          <p className="text-sm sm:text-base md:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed mb-8">
            Tell us what you need in everyday language. RedTape AI cuts through government complexity — discovering certificates, trade licenses, and FSSAI registrations without confusion or tedious forms.
          </p>
        </motion.div>

        {/* Action Button to Dissolve Hero into Chat UI */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.35, duration: 0.6 }}
          className="flex flex-col sm:flex-row items-center gap-4 mb-10"
        >
          <button
            type="button"
            onClick={onDismiss}
            className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-crimson-600 via-rose-600 to-crimson-700 hover:from-crimson-500 hover:to-crimson-600 text-white font-semibold text-base shadow-crimson-glow hover:shadow-crimson-lg transition-all transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer"
          >
            <span>Launch Assistant</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            {/* Glowing border ring */}
            <span className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
          </button>
          
          <span className="text-xs text-slate-500 font-mono">Click to launch workspace</span>
        </motion.div>

        {/* Three Value Pillars */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.45, duration: 0.6 }}
          className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 w-full text-left"
        >
          {capabilities.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-obsidian-850/70 border border-titanium-400/10 hover:border-crimson-500/40 backdrop-blur-md transition-all group"
              >
                <div className="w-8 h-8 rounded-lg bg-crimson-950/70 border border-crimson-800/50 flex items-center justify-center text-crimson-400 mb-2.5 group-hover:scale-105 transition-transform shadow-crimson-sm">
                  <Icon className="w-4 h-4" />
                </div>
                <h3 className="font-semibold text-sm text-slate-100 mb-1 group-hover:text-crimson-300 transition-colors">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            );
          })}
        </motion.div>
      </div>

      {/* Copyright Footer */}
      <motion.footer
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.55, duration: 0.6 }}
        className="relative z-10 py-5 px-6 border-t border-slate-800/60 text-center text-xs text-slate-500 bg-obsidian-950/60 backdrop-blur-sm"
      >
        <p className="font-medium tracking-wide">
          &copy; Made by Soul Coders, all rights reserved
        </p>
      </motion.footer>
    </motion.div>
  );
}
