import React, { useState, useRef, useEffect } from 'react';
import {
  Plus,
  MessageSquare,
  Trash2,
  X,
  Code2,
  Clock,
  ChevronRight,
  Check,
  Sparkles,
  Sliders,
  User,
  Settings,
  HelpCircle,
  LogOut,
} from 'lucide-react';
import { GoogleLogo } from './GoogleAuthModal';

function formatTimestamp(timestampStr) {
  if (!timestampStr) return '';
  try {
    const date = new Date(timestampStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return '';
  }
}

export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  isOpen,
  onToggleOpen,
  user,
  accounts = [],
  onSelectAccount,
  onOpenGoogleLogin,
  onLogout,
  onOpenPersonalization,
  onOpenSettings,
  onOpenUpgrade,
}) {
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const menuRef = useRef(null);
  const profileButtonRef = useRef(null);

  // Close profile popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target) &&
        profileButtonRef.current &&
        !profileButtonRef.current.contains(event.target)
      ) {
        setShowProfileMenu(false);
      }
    };

    if (showProfileMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProfileMenu]);

  return (
    <>
      {/* Mobile Backdrop overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-30 lg:hidden transition-opacity"
          onClick={onToggleOpen}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-72 bg-[#0d121d] border-r border-slate-800/80 flex flex-col transition-all duration-300 ease-in-out shrink-0 ${
          isOpen
            ? 'translate-x-0 shadow-2xl shadow-black/80 lg:shadow-none lg:static lg:translate-x-0'
            : '-translate-x-full lg:-ml-72'
        }`}
      >
        {/* Sidebar Header & Brand */}
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Code2 className="w-4 h-4" />
            </div>
            <div>
              <span className="font-semibold text-sm tracking-tight text-white block leading-tight">
                AlgoCoach
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                Persistent Memory
              </span>
            </div>
          </div>

          {/* Close button for mobile */}
          <button
            onClick={onToggleOpen}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 lg:hidden transition-colors"
            aria-label="Close sidebar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Action Button */}
        <div className="p-3">
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-xs sm:text-sm shadow-md shadow-indigo-900/30 hover:shadow-indigo-800/40 transition-all duration-200 cursor-pointer active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <div className="px-2 pb-1.5 flex items-center justify-between text-[11px] font-medium uppercase tracking-wider text-slate-500">
            <span>Conversations</span>
            <span className="font-mono text-[10px] text-slate-600">
              {conversations.length}
            </span>
          </div>

          {conversations.length === 0 ? (
            <div className="px-3 py-8 text-center text-xs text-slate-500 border border-dashed border-slate-800/80 rounded-xl my-2">
              <MessageSquare className="w-6 h-6 mx-auto mb-2 text-slate-600 opacity-60" />
              <p className="font-medium text-slate-400">No past chats yet</p>
              <p className="text-[11px] mt-1 text-slate-500">
                Start asking a DSA question to create one.
              </p>
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = conv.id === activeConversationId;
              const formattedTime = formatTimestamp(
                conv.last_message_at || conv.created_at
              );

              return (
                <div
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-xs cursor-pointer transition-all duration-150 border ${
                    isActive
                      ? 'bg-indigo-600/15 text-indigo-200 border-indigo-500/40 shadow-xs'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-slate-100 border-transparent hover:border-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    <MessageSquare
                      className={`w-3.5 h-3.5 shrink-0 ${
                        isActive
                          ? 'text-indigo-400'
                          : 'text-slate-500 group-hover:text-slate-400'
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-[13px] leading-tight text-inherit">
                        {conv.title || 'Untitled Conversation'}
                      </p>
                      {formattedTime && (
                        <div className="flex items-center gap-1 mt-0.5 text-[10px] text-slate-500">
                          <Clock className="w-2.5 h-2.5" />
                          <span>{formattedTime}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Delete Conversation Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all ml-1 shrink-0"
                    title="Delete conversation"
                    aria-label="Delete conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* ChatGPT-Style Profile Footer with Popup Menu */}
        <div className="relative p-2.5 border-t border-slate-800/80 bg-[#0b0e17]/80">
          {/* Floating ChatGPT-Style Popup Menu */}
          {showProfileMenu && user && (
            <div
              ref={menuRef}
              className="absolute bottom-16 left-2 right-2 rounded-2xl bg-[#171b26] border border-slate-700/80 shadow-2xl p-1.5 z-50 text-slate-200 animate-fadeIn space-y-1"
            >
              {/* Account Switcher Subcard */}
              <div className="p-1.5 rounded-xl bg-slate-900/80 border border-slate-800/90 space-y-1">
                {accounts.map((acc) => {
                  const isActive = user?.id === acc.id || user?.email === acc.email;
                  return (
                    <button
                      key={acc.id}
                      onClick={() => {
                        onSelectAccount?.(acc);
                        setShowProfileMenu(false);
                      }}
                      className={`w-full flex items-center justify-between p-2 rounded-lg text-left transition-colors cursor-pointer ${
                        isActive
                          ? 'bg-slate-800/90 text-white'
                          : 'hover:bg-slate-800/50 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div
                          className={`w-7 h-7 rounded-full ${
                            acc.avatarColor || 'bg-emerald-600'
                          } text-white font-semibold text-[11px] flex items-center justify-center shrink-0`}
                        >
                          {acc.initials || 'AP'}
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-xs text-white truncate leading-tight">
                            {acc.name}
                          </p>
                          <p className="text-[10px] text-slate-400 truncate leading-tight">
                            {acc.email}
                          </p>
                        </div>
                      </div>

                      {isActive && (
                        <Check className="w-3.5 h-3.5 text-slate-200 shrink-0 ml-1" />
                      )}
                    </button>
                  );
                })}

                {/* + Add account */}
                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    onOpenGoogleLogin?.();
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors cursor-pointer"
                >
                  <Plus className="w-4 h-4 text-slate-400" />
                  <span className="font-medium text-xs">Add account</span>
                </button>
              </div>

              {/* Menu items */}
              <div className="py-1 space-y-0.5 text-xs">
                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    onOpenUpgrade?.();
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/70 transition-colors text-left cursor-pointer"
                >
                  <Sparkles className="w-4 h-4 text-indigo-400" />
                  <span>Upgrade plan</span>
                </button>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    onOpenPersonalization?.();
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/70 transition-colors text-left cursor-pointer"
                >
                  <Sliders className="w-4 h-4 text-slate-400" />
                  <span>Personalization</span>
                </button>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    onOpenSettings?.();
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/70 transition-colors text-left cursor-pointer"
                >
                  <User className="w-4 h-4 text-slate-400" />
                  <span>Profile</span>
                </button>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    onOpenSettings?.();
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/70 transition-colors text-left cursor-pointer"
                >
                  <Settings className="w-4 h-4 text-slate-400" />
                  <span>Settings</span>
                </button>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    alert(
                      'AlgoCoach AI Help:\n• Type algorithm questions to get step-by-step intuition.\n• Use the mic button for voice dictation via Groq Whisper.\n• Notes and ChromaDB vector store automatically ground responses.'
                    );
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/70 transition-colors text-left cursor-pointer"
                >
                  <HelpCircle className="w-4 h-4 text-slate-400" />
                  <span>Help</span>
                </button>

                <div className="my-1 border-t border-slate-800" />

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    onLogout?.();
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-rose-300 hover:text-rose-200 hover:bg-rose-500/10 transition-colors text-left cursor-pointer"
                >
                  <LogOut className="w-4 h-4 text-rose-400" />
                  <span>Log out</span>
                </button>
              </div>
            </div>
          )}

          {/* Profile Trigger Button at Bottom of Sidebar */}
          {user ? (
            <button
              ref={profileButtonRef}
              onClick={() => setShowProfileMenu((prev) => !prev)}
              className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-slate-800/70 transition-colors text-left group cursor-pointer border border-transparent hover:border-slate-800"
              title="Account settings & switcher"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                {/* Circular Avatar */}
                <div
                  className={`w-8 h-8 rounded-full ${
                    user.avatarColor || 'bg-emerald-600'
                  } text-white font-semibold text-xs flex items-center justify-center shrink-0 shadow-sm`}
                >
                  {user.initials || 'AP'}
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-xs text-white truncate leading-tight group-hover:text-indigo-200">
                    {user.name || 'Aditya Patel'}
                  </p>
                  <p className="text-[11px] text-slate-400 truncate leading-tight">
                    {user.plan || 'Go'}
                  </p>
                </div>
              </div>

              <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors shrink-0" />
            </button>
          ) : (
            /* Sign In with Google Prompt when logged out */
            <button
              onClick={onOpenGoogleLogin}
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-medium text-xs shadow-md transition-colors cursor-pointer"
            >
              <GoogleLogo className="w-4 h-4" />
              <span>Sign in with Google</span>
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
