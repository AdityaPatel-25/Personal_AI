import React, { useState } from 'react';
import { X, Check, Plus, User, ArrowRight, ShieldCheck } from 'lucide-react';

export function GoogleLogo({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

export default function GoogleAuthModal({
  isOpen,
  onClose,
  accounts,
  activeAccount,
  onSelectAccount,
  onAddAccount,
}) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleAddNew = (e) => {
    e.preventDefault();
    const trimmedEmail = newEmail.trim();
    const trimmedName = newName.trim() || trimmedEmail.split('@')[0] || 'User';

    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      setError('Please enter a valid Google email address.');
      return;
    }

    const initials = trimmedName
      .split(' ')
      .map((part) => part[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'G';

    const colors = [
      'bg-emerald-600',
      'bg-teal-600',
      'bg-indigo-600',
      'bg-blue-600',
      'bg-violet-600',
    ];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];

    const account = {
      id: `acc-${Date.now()}`,
      name: trimmedName,
      email: trimmedEmail,
      initials,
      plan: 'Go',
      avatarColor: randomColor,
    };

    onAddAccount(account);
    setNewName('');
    setNewEmail('');
    setShowAddForm(false);
    setError('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md rounded-2xl bg-[#131722] border border-slate-700/80 shadow-2xl overflow-hidden text-slate-200">
        {/* Header with Google Logo */}
        <div className="p-6 text-center border-b border-slate-800/80 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="inline-flex p-3 rounded-2xl bg-white/5 border border-white/10 shadow-inner mb-3">
            <GoogleLogo className="w-8 h-8" />
          </div>

          <h3 className="text-xl font-bold text-white tracking-tight">
            Sign in with Google
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
            Choose an account to continue to <span className="text-indigo-400 font-medium">AlgoCoach AI</span>
          </p>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 max-h-[65vh] overflow-y-auto">
          {!showAddForm ? (
            <>
              {/* Existing Google Accounts List */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1">
                  Saved Google Accounts
                </div>

                {accounts.map((acc) => {
                  const isActive = activeAccount?.id === acc.id;
                  return (
                    <button
                      key={acc.id}
                      onClick={() => {
                        onSelectAccount(acc);
                        onClose();
                      }}
                      className={`w-full flex items-center justify-between p-3 rounded-xl border text-left transition-all cursor-pointer group ${
                        isActive
                          ? 'bg-indigo-600/15 border-indigo-500/50 shadow-sm'
                          : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/60'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        {/* Avatar */}
                        <div
                          className={`w-10 h-10 rounded-full ${acc.avatarColor || 'bg-emerald-600'} text-white font-semibold text-xs flex items-center justify-center shrink-0 shadow-sm`}
                        >
                          {acc.initials}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-sm text-white truncate">
                            {acc.name}
                          </p>
                          <p className="text-xs text-slate-400 truncate">
                            {acc.email}
                          </p>
                        </div>
                      </div>

                      {isActive && (
                        <div className="shrink-0 p-1 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/40">
                          <Check className="w-4 h-4" />
                        </div>
                      )}
                    </button>
                  );
                })}

                {/* Add Another Account Button */}
                <button
                  onClick={() => setShowAddForm(true)}
                  className="w-full flex items-center gap-3 p-3 rounded-xl bg-slate-900/40 hover:bg-slate-800/60 border border-dashed border-slate-700/80 hover:border-indigo-500/50 text-slate-300 hover:text-white transition-all text-left text-sm font-medium cursor-pointer"
                >
                  <div className="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400 shrink-0">
                    <Plus className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="block font-medium">Use another account</span>
                    <span className="text-xs text-slate-500">Sign in with a different Google account</span>
                  </div>
                </button>
              </div>

              {/* Fast 1-Tap Google Button */}
              <div className="pt-2">
                <button
                  onClick={() => {
                    if (accounts.length > 0) {
                      onSelectAccount(accounts[0]);
                      onClose();
                    } else {
                      setShowAddForm(true);
                    }
                  }}
                  className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-medium text-sm flex items-center justify-center gap-2.5 transition-colors shadow-md cursor-pointer"
                >
                  <GoogleLogo className="w-4 h-4" />
                  <span>Continue with Google</span>
                </button>
              </div>
            </>
          ) : (
            /* Add Account Form */
            <form onSubmit={handleAddNew} className="space-y-3.5 animate-fadeIn">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Connect Google Account
                </span>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 cursor-pointer"
                >
                  Back to accounts
                </button>
              </div>

              {error && (
                <div className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Aditya Patel"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Google Email Address *
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. yourname@gmail.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-md cursor-pointer"
                >
                  <span>Sign in</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>
          )}

          {/* Privacy Note */}
          <div className="pt-2 border-t border-slate-800/80 flex items-center gap-2 text-[11px] text-slate-500">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
            <span>
              Google secures your account. Your sessions and personal AI memory are stored securely.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
