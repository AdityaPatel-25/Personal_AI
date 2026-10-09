import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  Send,
  Square,
  Sparkles,
  Mic,
  Loader2,
  X,
  Check,
  AlertCircle,
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function MessageInput({
  input,
  setInput,
  onSend,
  onStop,
  isLoading,
  isStreaming,
  disabled,
  apiUrl = API_BASE_URL,
}) {
  const textareaRef = useRef(null);

  // Voice recording state
  const [recordingState, setRecordingState] = useState('idle'); // 'idle' | 'recording' | 'transcribing'
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [voiceError, setVoiceError] = useState(null);
  const [interimTranscript, setInterimTranscript] = useState('');

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);

  // Auto-resize textarea height as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [input]);

  // Clean up media tracks and timers
  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore
        }
      });
      streamRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      cleanupStream();
      if (timerRef.current) clearInterval(timerRef.current);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // ignore
        }
      }
    };
  }, [cleanupStream]);

  // Format seconds to mm:ss
  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Start voice recording
  const startRecording = async () => {
    if (disabled || isLoading || isStreaming || recordingState !== 'idle') return;

    setVoiceError(null);
    setInterimTranscript('');

    if (!navigator?.mediaDevices?.getUserMedia) {
      setVoiceError('Audio recording is not supported in this browser environment.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      // Select supported MIME type
      let mimeType = '';
      if (typeof MediaRecorder !== 'undefined') {
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        }
      }

      const options = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Optional Web Speech API for live interim feedback as user speaks
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';
          recognition.onresult = (event) => {
            let live = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
              live += event.results[i][0].transcript;
            }
            if (live) {
              setInterimTranscript(live);
            }
          };
          recognition.onerror = () => {};
          recognition.start();
          recognitionRef.current = recognition;
        } catch {
          // Web speech fallback ignored
        }
      }

      mediaRecorder.start(250);
      setRecordingState('recording');
      setRecordingSeconds(0);

      // Start timer (auto-stop at 120s max)
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => {
          if (prev >= 120) {
            stopRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err) {
      console.error('Microphone access failed:', err);
      if (
        err.name === 'NotAllowedError' ||
        err.name === 'PermissionDeniedError'
      ) {
        setVoiceError(
          'Microphone permission denied. Please allow microphone access in your browser settings.'
        );
      } else {
        setVoiceError(
          `Could not access microphone: ${err.message || 'Unknown error'}`
        );
      }
    }
  };

  // Stop recording and send audio to /transcribe endpoint
  const stopRecording = useCallback(async () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    }

    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === 'inactive') {
      cleanupStream();
      setRecordingState('idle');
      return;
    }

    setRecordingState('transcribing');

    return new Promise((resolve) => {
      recorder.onstop = async () => {
        cleanupStream();
        const chunks = audioChunksRef.current;
        const mimeType = recorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(chunks, { type: mimeType });

        if (audioBlob.size < 150) {
          setVoiceError('Recording was too short. Speak your question and press Stop.');
          setRecordingState('idle');
          resolve();
          return;
        }

        try {
          const formData = new FormData();
          const ext = mimeType.includes('mp4')
            ? 'mp4'
            : mimeType.includes('ogg')
            ? 'ogg'
            : 'webm';
          formData.append('file', audioBlob, `voice_prompt.${ext}`);

          const res = await fetch(`${apiUrl}/transcribe`, {
            method: 'POST',
            body: formData,
          });

          if (res.ok) {
            const data = await res.json();
            const text = (data.text || '').trim();

            if (text) {
              setInput((prev) => {
                const prevTrimmed = (prev || '').trim();
                return prevTrimmed ? `${prevTrimmed} ${text}` : text;
              });
              setVoiceError(null);
              // Focus textarea after inserting
              setTimeout(() => {
                textareaRef.current?.focus();
              }, 80);
            } else if (interimTranscript?.trim()) {
              // Fallback to interim speech recognition if Whisper returned blank
              setInput((prev) => {
                const prevTrimmed = (prev || '').trim();
                return prevTrimmed
                  ? `${prevTrimmed} ${interimTranscript.trim()}`
                  : interimTranscript.trim();
              });
            } else {
              setVoiceError('No speech was detected. Please speak clearly into your microphone.');
            }
          } else {
            // If backend failed, check if client-side interim transcript has text
            if (interimTranscript?.trim()) {
              setInput((prev) => {
                const prevTrimmed = (prev || '').trim();
                return prevTrimmed
                  ? `${prevTrimmed} ${interimTranscript.trim()}`
                  : interimTranscript.trim();
              });
            } else {
              const errData = await res.json().catch(() => ({}));
              setVoiceError(
                errData.detail || `Transcription error (HTTP ${res.status}).`
              );
            }
          }
        } catch (fetchErr) {
          console.error('Transcription upload failed:', fetchErr);
          if (interimTranscript?.trim()) {
            setInput((prev) => {
              const prevTrimmed = (prev || '').trim();
              return prevTrimmed
                ? `${prevTrimmed} ${interimTranscript.trim()}`
                : interimTranscript.trim();
            });
          } else {
            setVoiceError(
              `Could not connect to transcription service at ${apiUrl}. Make sure the backend is running.`
            );
          }
        } finally {
          setRecordingState('idle');
          setInterimTranscript('');
          resolve();
        }
      };

      recorder.stop();
    });
  }, [apiUrl, cleanupStream, interimTranscript, setInput]);

  // Cancel recording and discard audio
  const cancelRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    }
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== 'inactive'
    ) {
      mediaRecorderRef.current.onstop = null;
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // ignore
      }
    }
    cleanupStream();
    audioChunksRef.current = [];
    setRecordingState('idle');
    setRecordingSeconds(0);
    setInterimTranscript('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (recordingState === 'recording') {
        stopRecording();
        return;
      }
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
    if (recordingState === 'recording') {
      stopRecording();
      return;
    }
    if (input.trim() && !disabled) {
      onSend(input);
    }
  };

  const isBusy = isLoading || isStreaming;
  const isRecording = recordingState === 'recording';
  const isTranscribing = recordingState === 'transcribing';

  return (
    <footer className="w-full bg-[#0b0f17]/90 backdrop-blur-md border-t border-slate-800/80 px-3 py-2.5 sm:px-6 sm:py-3.5 shrink-0">
      <div className="max-w-4xl mx-auto">
        {/* Voice Error Banner */}
        {voiceError && (
          <div className="mb-2.5 px-3.5 py-2 rounded-xl bg-rose-950/60 border border-rose-800/70 text-rose-200 text-xs flex items-center justify-between gap-2 animate-fadeIn shadow-md">
            <div className="flex items-center gap-2 min-w-0">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span className="truncate">{voiceError}</span>
            </div>
            <button
              onClick={() => setVoiceError(null)}
              className="p-1 rounded-lg hover:bg-rose-900/60 text-rose-400 hover:text-rose-200 transition-colors cursor-pointer"
              title="Dismiss error"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="relative flex items-end gap-2">
          {/* Main Input Container / Active Recording Console */}
          <div className="relative flex-1 bg-slate-900/90 border border-slate-700/70 rounded-2xl shadow-inner focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all duration-200 overflow-hidden min-h-[44px]">
            {isRecording ? (
              /* Live Voice Recording UI */
              <div className="flex items-center justify-between px-3.5 py-2.5 sm:px-4 sm:py-3 bg-gradient-to-r from-rose-950/40 via-slate-900/80 to-slate-900/90 min-h-[44px]">
                <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
                  {/* Pulsing Red REC Pill */}
                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-rose-500/20 border border-rose-500/40 text-[11px] font-mono text-rose-300 font-semibold shrink-0">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500" />
                    </span>
                    <span>REC</span>
                    <span className="text-white ml-0.5">
                      {formatTime(recordingSeconds)}
                    </span>
                  </div>

                  {/* Audio Wave Visualizer Bars */}
                  <div className="flex items-center gap-1 h-5 shrink-0">
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                    <span className="voice-wave-bar" />
                  </div>

                  {/* Prompt Text / Live Transcript */}
                  <span className="text-xs sm:text-sm text-slate-300 truncate font-normal">
                    {interimTranscript ? (
                      <span className="text-indigo-300 italic">
                        "{interimTranscript}..."
                      </span>
                    ) : (
                      'Listening... Speak your algorithm question'
                    )}
                  </span>
                </div>

                {/* Cancel & Finish Recording Buttons inside console */}
                <div className="flex items-center gap-1.5 shrink-0 ml-2">
                  <button
                    type="button"
                    id="voice-cancel-btn"
                    onClick={cancelRecording}
                    className="p-1.5 rounded-xl text-slate-400 hover:text-rose-300 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/30 transition-colors text-xs flex items-center gap-1 cursor-pointer"
                    title="Cancel recording"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline text-[11px]">Cancel</span>
                  </button>
                  <button
                    type="button"
                    id="voice-done-btn"
                    onClick={stopRecording}
                    className="px-2.5 py-1 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1 transition-colors shadow-sm cursor-pointer"
                    title="Done speaking, convert to text"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span className="text-[11px]">Done</span>
                  </button>
                </div>
              </div>
            ) : isTranscribing ? (
              /* Transcribing State UI */
              <div className="flex items-center gap-2.5 px-3.5 py-2.5 sm:px-4 sm:py-3 bg-indigo-950/30 min-h-[44px]">
                <Loader2 className="w-4 h-4 text-indigo-400 animate-spin shrink-0" />
                <span className="text-xs sm:text-sm text-indigo-300 animate-pulse font-medium">
                  Transcribing voice to text with Groq Whisper AI...
                </span>
              </div>
            ) : (
              /* Standard Textarea */
              <textarea
                ref={textareaRef}
                id="chat-textarea"
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                placeholder={
                  isBusy
                    ? 'Coach is formulating guidance & streaming...'
                    : 'Ask about algorithms, DP, graphs, or paste code... (Enter to send)'
                }
                className="w-full bg-transparent text-slate-100 placeholder-slate-500 px-3.5 py-2.5 sm:px-4 sm:py-3 text-sm sm:text-base focus:outline-none resize-none max-h-40 min-h-[44px] overflow-y-auto leading-relaxed"
              />
            )}
          </div>

          {/* Voice Record Button */}
          {isRecording ? (
            /* Stop Recording Button */
            <button
              type="button"
              id="voice-stop-btn"
              onClick={stopRecording}
              className="shrink-0 h-11 w-11 sm:h-12 sm:w-12 rounded-2xl bg-rose-500/25 hover:bg-rose-500/35 text-rose-300 border border-rose-500/60 ring-2 ring-rose-500/40 flex items-center justify-center transition-all duration-200 shadow-lg shadow-rose-950/40 active:scale-95 group cursor-pointer animate-pulse"
              title="Stop recording and convert to text"
              aria-label="Stop recording"
            >
              <Square className="w-4 h-4 sm:w-5 sm:h-5 fill-rose-400 group-hover:scale-105 transition-transform" />
            </button>
          ) : isTranscribing ? (
            /* Transcribing Loader Button */
            <div
              className="shrink-0 h-11 w-11 sm:h-12 sm:w-12 rounded-2xl bg-indigo-950/60 border border-indigo-500/40 flex items-center justify-center shadow-md"
              title="Transcribing speech..."
            >
              <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-400 animate-spin" />
            </div>
          ) : (
            /* Microphone Trigger Button */
            <button
              type="button"
              id="voice-record-btn"
              onClick={startRecording}
              disabled={disabled || isBusy}
              className="shrink-0 h-11 w-11 sm:h-12 sm:w-12 rounded-2xl bg-slate-800/90 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 hover:border-indigo-500/50 flex items-center justify-center transition-all duration-200 shadow-md active:scale-95 group cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
              title="Record voice (Speech-to-Text)"
              aria-label="Record voice prompt"
            >
              <Mic className="w-4 h-4 sm:w-5 sm:h-5 text-indigo-400 group-hover:text-indigo-300 transition-colors" />
            </button>
          )}

          {/* Send / Stop Generation Button */}
          {isBusy ? (
            <button
              type="button"
              id="chat-stop-btn"
              onClick={onStop}
              className="shrink-0 h-11 w-11 sm:h-12 sm:w-12 rounded-2xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 flex items-center justify-center transition-all duration-200 shadow-lg shadow-rose-950/30 active:scale-95 group cursor-pointer"
              title="Stop generating"
              aria-label="Stop generation"
            >
              <Square className="w-4 h-4 sm:w-5 sm:h-5 fill-rose-400 group-hover:scale-105 transition-transform" />
            </button>
          ) : (
            <button
              type="submit"
              id="chat-send-btn"
              disabled={!input.trim() || disabled || isRecording || isTranscribing}
              className="shrink-0 h-11 w-11 sm:h-12 sm:w-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 hover:from-indigo-500 hover:to-violet-400 text-white disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-200 shadow-lg shadow-indigo-900/40 active:scale-95 group cursor-pointer"
              title="Send message (Enter)"
              aria-label="Send message"
            >
              <Send className="w-4 h-4 sm:w-5 sm:h-5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </button>
          )}
        </form>

        {/* Footer Hint Bar */}
        <div className="flex items-center justify-between mt-2 px-1 text-[11px] sm:text-xs text-slate-500">
          <div className="flex items-center gap-1.5 truncate">
            <Sparkles className="w-3 h-3 text-indigo-400 shrink-0" />
            <span className="truncate">AI Coach with Voice Input & Groq Whisper</span>
          </div>
          <div className="hidden sm:flex items-center gap-2 text-slate-500">
            <span>
              Click <kbd className="px-1 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700 text-[10px]">Mic</kbd> to record
            </span>
            <span>•</span>
            <span>
              <kbd className="px-1 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700 text-[10px]">Enter</kbd> to send
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
