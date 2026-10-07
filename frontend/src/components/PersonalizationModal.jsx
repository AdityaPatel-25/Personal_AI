import React, { useState, useEffect } from 'react';
import { X, Sliders, Check, Sparkles } from 'lucide-react';

export default function PersonalizationModal({ isOpen, onClose }) {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('personal_ai_pref_lang') || 'Python';
  });
  const [platform, setPlatform] = useState(() => {
    return localStorage.getItem('personal_ai_pref_platform') || 'LeetCode';
  });
  const [teachingStyle, setTeachingStyle] = useState(() => {
    return localStorage.getItem('personal_ai_pref_style') || 'Intuition & Socratic Hints';
  });
  const [savedToast, setSavedToast] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem('personal_ai_pref_lang', language);
    localStorage.setItem('personal_ai_pref_platform', platform);
    localStorage.setItem('personal_ai_pref_style', teachingStyle);
    setSavedToast(true);
    setTimeout(() => {
      setSavedToast(false);
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md rounded-2xl bg-[#131722] border border-slate-700/80 shadow-2xl p-6 text-slate-200">
        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-white">Personalization</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
              Preferred Language
            </label>
            <div className="grid grid-cols-2 gap-2">
              {['Python', 'C++', 'Java', 'JavaScript/TS'].map((lang) => (
                <button
                  key={lang}
                  type="button"
                  onClick={() => setLanguage(lang)}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border text-left transition-all ${
                    language === lang
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  {lang}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
              Target CP Platform
            </label>
            <div className="grid grid-cols-2 gap-2">
              {['LeetCode', 'Codeforces', 'AtCoder', 'System Coding'].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPlatform(p)}
                  className={`px-3 py-2 rounded-xl text-xs font-medium border text-left transition-all ${
                    platform === p
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1.5 uppercase tracking-wider">
              Coaching Pedagogy
            </label>
            <div className="space-y-1.5">
              {[
                'Intuition & Socratic Hints',
                'Rigorous Big-O & Proofs',
                'Code Templates & Patterns First',
              ].map((style) => (
                <button
                  key={style}
                  type="button"
                  onClick={() => setTeachingStyle(style)}
                  className={`w-full px-3 py-2 rounded-xl text-xs font-medium border text-left transition-all flex items-center justify-between ${
                    teachingStyle === style
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span>{style}</span>
                  {teachingStyle === style && <Check className="w-3.5 h-3.5 text-indigo-400" />}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 pt-3 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-500 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Applied to all chats
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-md"
            >
              {savedToast ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span>Saved!</span>
                </>
              ) : (
                <span>Save preferences</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
