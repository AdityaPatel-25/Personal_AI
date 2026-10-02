import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, AlertCircle, Copy, Check, Terminal, Zap, BookOpen, Layers, RefreshCw } from 'lucide-react';

const SUGGESTED_PROMPTS = [
  {
    title: "Graph Traversal",
    prompt: "How do I choose between BFS and DFS for graph and tree problems?",
    icon: Layers,
    tag: "Fundamentals",
  },
  {
    title: "Shortest Path Intuition",
    prompt: "Explain Dijkstra's algorithm step-by-step with intuition and edge cases.",
    icon: Zap,
    tag: "Greedy / Graphs",
  },
  {
    title: "DP State Transitions",
    prompt: "How do I systematically formulate state transitions in Dynamic Programming?",
    icon: Terminal,
    tag: "Dynamic Programming",
  },
  {
    title: "Complexity Analysis",
    prompt: "What is the amortized time complexity of dynamic array resizing and why?",
    icon: BookOpen,
    tag: "Big-O Analysis",
  },
];

// Helper code block with copy button
function CodeBlock({ children, className }) {
  const [copied, setCopied] = React.useState(false);
  const codeText = String(children).replace(/\n$/, '');

  const handleCopy = () => {
    navigator.clipboard.writeText(codeText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-3 rounded-lg overflow-hidden border border-slate-700/60 bg-[#0d1117]">
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-800/80 border-b border-slate-700/60 text-xs text-slate-400 font-mono">
        <span>{className?.replace('language-', '') || 'code'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors px-2 py-0.5 rounded hover:bg-slate-700"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3.5 overflow-x-auto text-xs sm:text-sm font-mono text-slate-200 leading-relaxed">
        <code>{children}</code>
      </pre>
    </div>
  );
}

export default function MessageList({
  messages,
  isLoading,
  isStreaming,
  error,
  onSelectPrompt,
  onRetry,
}) {
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);

  // Auto-scroll to bottom smoothly when messages update or streaming continues
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, isStreaming]);

  const isEmpty = messages.length === 0;

  return (
    <main
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 py-6 sm:px-6 md:px-8 space-y-6"
    >
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Welcome Empty State */}
        {isEmpty && !isLoading && !error && (
          <div className="py-8 sm:py-12 text-center animate-fadeIn">
            <div className="inline-flex p-3 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-4 shadow-inner">
              <Bot className="w-10 h-10" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
              Competitive Programming & DSA Coach
            </h2>
            <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto mb-8 leading-relaxed">
              Your real-time algorithmic mentor. Ask questions about LeetCode problems, graph theory, dynamic programming transitions, or Big-O complexity analysis.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left max-w-2xl mx-auto">
              {SUGGESTED_PROMPTS.map((item, index) => {
                const IconComponent = item.icon;
                return (
                  <button
                    key={index}
                    onClick={() => onSelectPrompt(item.prompt)}
                    className="p-3.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-indigo-500/40 text-left transition-all duration-200 group shadow-sm hover:shadow-indigo-500/5 cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <IconComponent className="w-4 h-4 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
                        <span className="text-xs font-semibold text-slate-300 group-hover:text-white">
                          {item.title}
                        </span>
                      </div>
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 group-hover:bg-indigo-950/60 group-hover:text-indigo-300 border border-slate-700/50">
                        {item.tag}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 group-hover:text-slate-300 line-clamp-2 leading-relaxed">
                      {item.prompt}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          const isLastAssistant =
            !isUser && index === messages.length - 1 && isStreaming;

          return (
            <div
              key={msg.id || index}
              className={`flex items-start gap-3 sm:gap-4 ${
                isUser ? 'flex-row-reverse' : 'flex-row'
              } animate-fadeIn`}
            >
              {/* Avatar */}
              <div
                className={`flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center text-xs font-semibold shadow-md ${
                  isUser
                    ? 'bg-gradient-to-tr from-indigo-500 to-violet-600 text-white shadow-indigo-900/30'
                    : 'bg-slate-800/90 border border-slate-700/80 text-indigo-400 shadow-slate-950/40'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] sm:max-w-[78%] rounded-2xl px-4 py-3.5 shadow-md ${
                  isUser
                    ? 'bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-tr-sm shadow-indigo-950/30'
                    : 'bg-slate-900/85 border border-slate-800/90 text-slate-100 rounded-tl-sm shadow-black/20'
                }`}
              >
                {/* Header label & RAG sources pill */}
                <div className="flex items-center justify-between gap-2 mb-1.5 flex-wrap">
                  <div
                    className={`text-[11px] font-semibold tracking-wider uppercase ${
                      isUser ? 'text-indigo-200' : 'text-indigo-400'
                    }`}
                  >
                    {isUser ? 'You' : 'Algo Coach'}
                  </div>
                  {!isUser && msg.rag_sources && (
                    <div
                      className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/25 text-[10px] text-emerald-300 font-mono"
                      title={`Retrieved from: ${msg.rag_sources}`}
                    >
                      <BookOpen className="w-2.5 h-2.5 text-emerald-400" />
                      <span>Grounded in: {msg.rag_sources}</span>
                      {msg.rag_chunks && <span className="text-emerald-400/80">({msg.rag_chunks} chunks)</span>}
                    </div>
                  )}
                </div>

                {/* Content */}
                {isUser ? (
                  <div className="whitespace-pre-wrap text-sm sm:text-base leading-relaxed break-words font-normal">
                    {msg.content}
                  </div>
                ) : (
                  <div className="prose-dsa text-sm sm:text-base break-words">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({ inline, className, children, ...props }) {
                          if (inline) {
                            return (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          }
                          return (
                            <CodeBlock className={className}>
                              {children}
                            </CodeBlock>
                          );
                        },
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>

                    {/* Blinking cursor while this message is actively streaming */}
                    {isLastAssistant && <span className="cursor-blink" />}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Loading Indicator (Waiting for first token) */}
        {isLoading && (
          <div className="flex items-start gap-3 sm:gap-4 animate-fadeIn">
            <div className="flex-shrink-0 w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-slate-800/90 border border-slate-700/80 text-indigo-400 flex items-center justify-center shadow-md">
              <Bot className="w-4 h-4 animate-pulse" />
            </div>
            <div className="rounded-2xl rounded-tl-sm px-4 py-3 bg-slate-900/85 border border-slate-800/90 text-slate-300 shadow-md">
              <div className="text-[11px] font-semibold mb-1 text-indigo-400 uppercase tracking-wider">
                Algo Coach
              </div>
              <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-400">
                <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
                <span>Formulating algorithmic hint and complexity breakdown...</span>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 flex items-start justify-between gap-3 shadow-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-rose-300">
                  Backend Communication Error
                </div>
                <div className="text-xs text-rose-300/80 mt-1 leading-relaxed">
                  {error}
                </div>
                <div className="text-[11px] text-rose-400/70 mt-2 font-mono">
                  Make sure FastAPI is running (`uvicorn backend.main:app --reload --port 8000`)
                </div>
              </div>
            </div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="flex-shrink-0 px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-medium border border-rose-500/30 transition-colors flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry
              </button>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </main>
  );
}
