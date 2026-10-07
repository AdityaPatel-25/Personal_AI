import React from 'react';
import { X, Settings, Shield, Database, Cpu, Check } from 'lucide-react';

export default function SettingsModal({ isOpen, onClose, activeAccount }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md rounded-2xl bg-[#131722] border border-slate-700/80 shadow-2xl p-6 text-slate-200">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Settings</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4 text-xs">
          {/* Account Info */}
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
              Google Account
            </span>
            <div className="flex items-center gap-3">
              <div className={`w-9 h-9 rounded-full ${activeAccount?.avatarColor || 'bg-emerald-600'} text-white font-semibold text-xs flex items-center justify-center shrink-0`}>
                {activeAccount?.initials || 'AP'}
              </div>
              <div>
                <p className="font-semibold text-white text-sm">{activeAccount?.name || 'Aditya Patel'}</p>
                <p className="text-slate-400">{activeAccount?.email || 'pateladityanov.25@gmail.com'}</p>
              </div>
            </div>
          </div>

          {/* Model & Architecture */}
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span className="font-medium text-slate-300">Inference Model</span>
              </div>
              <span className="font-mono text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
                Llama 3.3 70B Versatile
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-indigo-400" />
                <span className="font-medium text-slate-300">RAG Vector Store</span>
              </div>
              <span className="font-mono text-emerald-300 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                ChromaDB (384-d MiniLM)
              </span>
            </div>

            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-indigo-400" />
                <span className="font-medium text-slate-300">Speech Engine</span>
              </div>
              <span className="font-mono text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
                Groq Whisper v3 Turbo
              </span>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
