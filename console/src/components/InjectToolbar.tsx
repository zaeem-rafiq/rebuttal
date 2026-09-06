'use client';

import React, { useState, useEffect } from 'react';
import { Play, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
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
      const resp = await fetch(INJECT_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Console-Key': CONSOLE_KEY,
        },
        body: JSON.stringify({ scenario }),
      });

      const contentType = resp.headers.get('content-type') || '';
      let data: any = {};
      if (contentType.includes('application/json')) {
        data = await resp.json();
      } else {
        const text = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${text.slice(0, 100)}`);
      }

      if (!resp.ok) {
        if (resp.status === 429 && data.retry_after_seconds) {
          const cooldownUntil = Date.now() + data.retry_after_seconds * 1000;
          localStorage.setItem('rebuttal_inject_cooldown_until', cooldownUntil.toString());
          setCooldown(data.retry_after_seconds);
        }
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
    <div className="bg-[#0d131f] border border-border rounded-lg p-3.5 mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="h-6 w-6 rounded bg-blue-950/80 border border-blue-800/80 flex items-center justify-center shrink-0">
            <Play className="h-3 w-3 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Verification Cases
              </span>
              {cooldown > 0 && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-950/60 text-amber-300 border border-amber-800/60">
                  <Clock className="h-2.5 w-2.5 animate-spin" />
                  <span className="tabular-nums">Cooldown: {cooldown}s</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Dispatches live test webhooks into Stripe & Bedrock multi-agent pipeline
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* S1 Button */}
          <button
            onClick={() => handleInject('S1')}
            disabled={cooldown > 0 || loadingScenario !== null}
            aria-busy={loadingScenario === 'S1'}
            aria-label="Inject Scenario 1 Delivery Dispute"
            className="flex-1 sm:flex-none inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium bg-surface hover:bg-surface-elevated active:bg-surface-highlight text-slate-200 border border-border hover:border-border-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-brand"
          >
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0b0f17] text-blue-400 border border-blue-900/60">S1</span>
            <span className="font-medium">$48 · Delivery Proof</span>
            {loadingScenario === 'S1' && <Clock className="h-3 w-3 animate-spin text-blue-400 ml-0.5" />}
          </button>

          {/* S2 Button */}
          <button
            onClick={() => handleInject('S2')}
            disabled={cooldown > 0 || loadingScenario !== null}
            aria-busy={loadingScenario === 'S2'}
            aria-label="Inject Scenario 2 Fraud Dispute"
            className="flex-1 sm:flex-none inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium bg-surface hover:bg-surface-elevated active:bg-surface-highlight text-slate-200 border border-border hover:border-border-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-brand"
          >
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0b0f17] text-rose-400 border border-rose-900/60">S2</span>
            <span className="font-medium">$340 · VIP Fraud</span>
            {loadingScenario === 'S2' && <Clock className="h-3 w-3 animate-spin text-rose-400 ml-0.5" />}
          </button>

          {/* S3 Button */}
          <button
            onClick={() => handleInject('S3')}
            disabled={cooldown > 0 || loadingScenario !== null}
            aria-busy={loadingScenario === 'S3'}
            aria-label="Inject Scenario 3 Subscription Inquiry"
            className="flex-1 sm:flex-none inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium bg-surface hover:bg-surface-elevated active:bg-surface-highlight text-slate-200 border border-border hover:border-border-strong disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-brand"
          >
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0b0f17] text-amber-400 border border-amber-900/60">S3</span>
            <span className="font-medium">$129 · Inquiry</span>
            {loadingScenario === 'S3' && <Clock className="h-3 w-3 animate-spin text-amber-400 ml-0.5" />}
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          role="status"
          aria-live="polite"
          className={`mt-3 p-2.5 rounded-md text-xs flex items-start space-x-2 border ${
            statusMessage.type === 'success'
              ? 'bg-emerald-950/60 text-emerald-200 border-emerald-800/60'
              : 'bg-rose-950/60 text-rose-200 border-rose-800/60'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5 text-rose-400 shrink-0 mt-0.5" />
          )}
          <p className="flex-1">{statusMessage.text}</p>
        </div>
      )}
    </div>
  );
};
