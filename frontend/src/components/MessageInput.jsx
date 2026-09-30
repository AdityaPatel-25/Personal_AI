import React, { useRef, useEffect } from 'react';
import { Send, Square, Sparkles } from 'lucide-react';

export default function MessageInput({
  input,
  setInput,
  onSend,
  onStop,
  isLoading,
  isStreaming,
  disabled,
}) {
  const textareaRef = useRef(null);

  // Auto-resize textarea height as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && (isLoading || isStreaming)) {
        return;
      }
      if (input.trim()) {
        onSend(input);
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isStreaming || isLoading) {
      onStop?.();
      return;
    }
    if (input.trim() && !disabled) {
      onSend(input);
    }
  };

  const isBusy = isLoading || isStreaming;

  return (
    <footer className="w-full bg-[#0b0f17]/90 backdrop-blur-md border-t border-slate-800/80 px-4 py-3.5 sm:px-6">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="relative flex items-end gap-2.5">
          <div className="relative flex-1 bg-slate-900/90 border border-slate-700/70 rounded-2xl shadow-inner focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all duration-200">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              placeholder={
                isBusy
                  ? "Coach is thinking and streaming response..."
                  : "Ask about algorithms, time complexity, DP, graphs, or paste code... (Enter to send)"
              }
              className="w-full bg-transparent text-slate-100 placeholder-slate-500 px-4 py-3 text-sm sm:text-base focus:outline-none resize-none max-h-44 min-h-[48px] overflow-y-auto leading-relaxed"
            />
          </div>

          {/* Action Button: Send or Stop */}
          {isBusy ? (
            <button
              type="button"
              onClick={onStop}
              className="flex-shrink-0 h-12 w-12 rounded-2xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 flex items-center justify-center transition-all duration-200 shadow-lg shadow-rose-950/30 active:scale-95 group"
              title="Stop generating"
              aria-label="Stop generation"
            >
              <Square className="w-5 h-5 fill-rose-400 group-hover:scale-105 transition-transform" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim() || disabled}
              className="flex-shrink-0 h-12 w-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 hover:from-indigo-500 hover:to-violet-400 text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 shadow-lg shadow-indigo-900/40 active:scale-95 group cursor-pointer"
              title="Send message (Enter)"
              aria-label="Send message"
            >
              <Send className="w-5 h-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </button>
          )}
        </form>

        <div className="flex items-center justify-between mt-2 px-1 text-[11px] sm:text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>AI Coach for LeetCode & Competitive Programming</span>
          </div>
          <div className="hidden sm:block">
            <span>Press <kbd className="px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700 text-[10px]">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700 text-[10px]">Shift+Enter</kbd> for newline</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
