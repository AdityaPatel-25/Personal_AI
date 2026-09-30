import React, { useState, useRef, useEffect } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { Terminal, Trash2 } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'

  const abortControllerRef = useRef(null);
  const lastPromptRef = useRef('');

  // Check backend health periodically or on mount
  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/`, { method: 'GET' });
        if (res.ok && isMounted) {
          setBackendStatus('online');
        } else if (isMounted) {
          setBackendStatus('offline');
        }
      } catch {
        if (isMounted) {
          setBackendStatus('offline');
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleSendMessage = async (textToSend) => {
    const trimmed = textToSend.trim();
    if (!trimmed || isLoading || isStreaming) return;

    setError(null);
    lastPromptRef.current = trimmed;
    setInput('');

    // Generate unique IDs
    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `ai-${Date.now()}`;

    // Add user message to conversation list
    const updatedMessages = [
      ...messages,
      { id: userMessageId, role: 'user', content: trimmed },
    ];
    setMessages(updatedMessages);

    // Initial loading state while waiting for the first token
    setIsLoading(true);
    setIsStreaming(false);

    // Prepare abort controller for cancellation
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: trimmed }),
        signal: controller.signal,
      });

      if (!response.ok) {
        let errorDetail = `HTTP ${response.status} ${response.statusText}`;
        try {
          const errorJson = await response.json();
          if (errorJson?.detail) {
            errorDetail = typeof errorJson.detail === 'string'
              ? errorJson.detail
              : JSON.stringify(errorJson.detail);
          }
        } catch {
          // If response body is not JSON, leave errorDetail as is
        }
        throw new Error(errorDetail);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported or empty response body from backend.');
      }

      // Stream handling setup
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      let accumulatedContent = '';
      let isFirstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        if (!chunkText) continue;

        if (isFirstChunk) {
          // First token received! Switch from loading spinner to active streaming
          isFirstChunk = false;
          setIsLoading(false);
          setIsStreaming(true);

          accumulatedContent += chunkText;
          setMessages([
            ...updatedMessages,
            { id: assistantMessageId, role: 'assistant', content: accumulatedContent },
          ]);
        } else {
          accumulatedContent += chunkText;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: accumulatedContent }
                : msg
            )
          );
        }
      }

      // Flush decoder
      const finalChunk = decoder.decode();
      if (finalChunk) {
        accumulatedContent += finalChunk;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: accumulatedContent }
              : msg
          )
        );
      }

      setBackendStatus('online');
    } catch (err) {
      if (err.name === 'AbortError') {
        // User stopped generation intentionally
        console.log('Stream aborted by user');
      } else {
        console.error('Chat error:', err);
        setError(
          err.message ||
            'Could not reach the FastAPI backend. Check that the server is running on port 8000.'
        );
        setBackendStatus('offline');
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleClearChat = () => {
    if (isLoading || isStreaming) {
      handleStop();
    }
    setMessages([]);
    setError(null);
  };

  const handleRetry = () => {
    if (lastPromptRef.current) {
      handleSendMessage(lastPromptRef.current);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-[#0b0f17] text-slate-100 antialiased overflow-hidden">
      {/* Top Header */}
      <header className="w-full bg-[#0f1422]/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-3 sm:px-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 p-0.5 flex items-center justify-center shadow-lg shadow-indigo-900/30">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Terminal className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold tracking-tight text-white m-0 p-0 leading-tight">
                AlgoCoach AI
              </h1>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Day 2
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Competitive Programming & DSA Mentorship
            </p>
          </div>
        </div>

        {/* Status indicator & Actions */}
        <div className="flex items-center gap-3">
          {/* Backend Status Pill */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
              backendStatus === 'online'
                ? 'bg-emerald-950/40 text-emerald-400 border-emerald-800/50'
                : backendStatus === 'offline'
                ? 'bg-rose-950/40 text-rose-400 border-rose-800/50'
                : 'bg-slate-800/40 text-slate-400 border-slate-700/50'
            }`}
            title={`Backend status at ${API_BASE_URL}`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === 'online'
                  ? 'bg-emerald-400 animate-pulse'
                  : backendStatus === 'offline'
                  ? 'bg-rose-400'
                  : 'bg-slate-400'
              }`}
            />
            <span className="hidden sm:inline">
              {backendStatus === 'online'
                ? 'FastAPI Online'
                : backendStatus === 'offline'
                ? 'FastAPI Offline'
                : 'Connecting...'}
            </span>
            <span className="sm:hidden">:8000</span>
          </div>

          {/* Clear Chat Button */}
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition-colors border border-transparent hover:border-slate-700/60"
              title="Clear conversation"
              aria-label="Clear chat"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </header>

      {/* Main Conversation Stream */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        isStreaming={isStreaming}
        error={error}
        onSelectPrompt={(prompt) => {
          setInput(prompt);
          handleSendMessage(prompt);
        }}
        onRetry={handleRetry}
      />

      {/* Bottom Message Input Bar */}
      <MessageInput
        input={input}
        setInput={setInput}
        onSend={handleSendMessage}
        onStop={handleStop}
        isLoading={isLoading}
        isStreaming={isStreaming}
        disabled={false}
      />
    </div>
  );
}
