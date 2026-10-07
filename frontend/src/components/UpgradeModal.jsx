import React from 'react';
import { X, Sparkles, Check, Zap, Shield, Cpu, Database } from 'lucide-react';

export default function UpgradeModal({ isOpen, onClose, currentPlan = 'Go' }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md rounded-2xl bg-[#131722] border border-slate-700/80 shadow-2xl p-6 text-slate-200">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Subscription & Plan</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 rounded-xl bg-gradient-to-tr from-indigo-950/60 to-violet-950/40 border border-indigo-500/30 mb-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-300">
                Current Plan
              </span>
              <h4 className="text-xl font-extrabold text-white">{currentPlan} Plan</h4>
            </div>
            <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-semibold">
              Active
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Unlocked full access to competitive programming mentoring, real-time RAG grounding, and high-speed Groq Whisper voice input.
          </p>
        </div>

        <div className="space-y-2.5 text-xs text-slate-300">
          <div className="flex items-center gap-2.5">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Groq Llama 3.3 70B Versatile with sub-second streaming</span>
          </div>
          <div className="flex items-center gap-2.5">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>ChromaDB Vector Store with 37+ DSA knowledge chunks</span>
          </div>
          <div className="flex items-center gap-2.5">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Groq Whisper Large v3 Voice-to-Text conversion</span>
          </div>
          <div className="flex items-center gap-2.5">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Unlimited conversation memory & multi-account switching</span>
          </div>
        </div>

        <div className="mt-6 pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
}
