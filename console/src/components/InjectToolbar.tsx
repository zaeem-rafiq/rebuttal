'use client';

import React, { useState, useEffect } from 'react';
import { Play, Sparkles, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { INJECT_URL, CONSOLE_KEY } from '@/lib/config';

interface InjectToolbarProps {
  onInjectSuccess?: () => void;
}

export const InjectToolbar: React.FC<InjectToolbarProps> = ({ onInjectSuccess }) => {
  const [loadingScenario, setLoadingScenario] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Restore cooldown from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('rebuttal_inject_cooldown_until');
    if (saved) {
      const remaining = Math.max(0, Math.ceil((parseInt(saved, 10) - Date.now()) / 1000));
      if (remaining > 0) {
        setCooldown(remaining);
      }
    }
  }, []);

  // Timer countdown
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          localStorage.removeItem('rebuttal_inject_cooldown_until');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleInject = async (scenario: 'S1' | 'S2' | 'S3') => {
    if (cooldown > 0 || loadingScenario) return;

    setLoadingScenario(scenario);
    setStatusMessage(null);

    try {
      // First try via local API proxy, then direct Lambda Function URL
      let resp: Response;
      try {
        resp = await fetch('/api/inject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario }),
        });
      } catch (proxyErr) {
        resp = await fetch(INJECT_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Console-Key': CONSOLE_KEY,
          },
          body: JSON.stringify({ scenario }),
        });
      }

      const data = await resp.json();

      if (!resp.ok) {
        throw new Error(data.error || `HTTP ${resp.status}`);
      }

      // Success: set 60s cooldown
      const cooldownUntil = Date.now() + 60 * 1000;
      localStorage.setItem('rebuttal_inject_cooldown_until', cooldownUntil.toString());
      setCooldown(60);

      setStatusMessage({
        type: 'success',
        text: `Injected ${scenario} successfully! PaymentIntent: ${data.payment_intent_id}. Webhook will invoke agent within seconds.`,
      });

      if (onInjectSuccess) {
        onInjectSuccess();
      }
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: `Inject failed: ${err.message || String(err)}`,
      });
    } finally {
      setLoadingScenario(null);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 mb-8 shadow-xl shadow-black/40 backdrop-blur-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-amber-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-200">
              Live Scenario Injector
            </h2>
            {cooldown > 0 && (
              <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-mono bg-amber-500/10 text-amber-300 border border-amber-500/20">
                <Clock className="h-3 w-3 animate-spin" />
                <span>Cooldown: {cooldown}s</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Create a live test dispute in Stripe to test the Bedrock AgentCore defense pipeline end-to-end.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* S1 Button */}
          <button
            onClick={() => handleInject('S1')}
            disabled={cooldown > 0 || loadingScenario !== null}
            className="flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-xl text-xs font-medium bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-indigo-500/20 transition-all active:scale-[0.98]"
          >
            <Play className={`h-3.5 w-3.5 ${loadingScenario === 'S1' ? 'animate-spin' : ''}`} />
            <span>Inject S1 ($48 · Delivery)</span>
          </button>

          {/* S2 Button */}
          <button
            onClick={() => handleInject('S2')}
            disabled={cooldown > 0 || loadingScenario !== null}
            className="flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-xl text-xs font-medium bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-purple-500/20 transition-all active:scale-[0.98]"
          >
            <Play className={`h-3.5 w-3.5 ${loadingScenario === 'S2' ? 'animate-spin' : ''}`} />
            <span>Inject S2 ($340 · Fraud)</span>
          </button>

          {/* S3 Button */}
          <button
            onClick={() => handleInject('S3')}
            disabled={cooldown > 0 || loadingScenario !== null}
            className="flex-1 sm:flex-none flex items-center justify-center space-x-2 px-4 py-2 rounded-xl text-xs font-medium bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-amber-500/20 transition-all active:scale-[0.98]"
          >
            <Play className={`h-3.5 w-3.5 ${loadingScenario === 'S3' ? 'animate-spin' : ''}`} />
            <span>Inject S3 ($129 · Inquiry)</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          className={`mt-4 p-3 rounded-xl text-xs flex items-start space-x-2 border ${
            statusMessage.type === 'success'
              ? 'bg-emerald-950/60 text-emerald-200 border-emerald-800/60'
              : 'bg-rose-950/60 text-rose-200 border-rose-800/60'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
          )}
          <p className="flex-1">{statusMessage.text}</p>
        </div>
      )}
    </div>
  );
};
