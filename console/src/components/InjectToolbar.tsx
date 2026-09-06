'use client';

import React, { useState, useEffect } from 'react';
import { Play, AlertCircle, CheckCircle2, Clock, Sparkles } from 'lucide-react';
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
        try {
          data = JSON.parse(text);
        } catch {
          data = { message: text || `HTTP ${resp.status}` };
        }
      }

      if (!resp.ok) {
        throw new Error(data.message || data.error || `HTTP ${resp.status}`);
      }

      const cooldownSecs = 10;
      setCooldown(cooldownSecs);
      localStorage.setItem(
        'rebuttal_inject_cooldown_until',
        (Date.now() + cooldownSecs * 1000).toString()
      );

      setStatusMessage({
        type: 'success',
        text: `Scenario ${scenario} injected successfully (${data.dispute_id || 'Dispute queued'}). Bedrock pipeline activated.`,
      });

      if (onInjectSuccess) {
        onInjectSuccess();
      }
    } catch (err: any) {
      console.error('Scenario injection error:', err);
      setStatusMessage({
        type: 'error',
        text: `Failed to inject ${scenario}: ${err.message || 'Network error'}`,
      });
    } finally {
      setLoadingScenario(null);
    }
  };

  return (
    <div className="bg-surface-plaque border border-border border-l-2 border-l-docket-gold p-3.5 sm:p-4 rounded-xs shadow-xs mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="flex items-center space-x-2.5">
          <div className="h-2 w-2 rounded-full bg-docket-gold" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-docket-text">
                Benchmark Scenario Injection
              </span>
              {cooldown > 0 && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-medium bg-surface-subtle text-status-pending border border-status-pending/30">
                  <Clock className="h-2.5 w-2.5 animate-spin" />
                  <span className="tabular-nums font-mono">Cooldown: {cooldown}s</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-docket-text-muted mt-0.5">
              Injects synthetic Stripe dispute webhooks into the autonomous Bedrock evidence compiler
            </p>
          </div>
        </div>

        {/* Scenario Switchers */}
        <div className="flex flex-wrap items-center gap-2">
          {/* S1 */}
          <button
            onClick={() => handleInject('S1')}
            disabled={cooldown > 0 || loadingScenario !== null}
            aria-busy={loadingScenario === 'S1'}
            aria-label="Inject S1 Delivery Proof Dispute"
            className="flex-1 sm:flex-none inline-flex items-center gap-2 px-3 py-1.5 min-h-[44px] sm:min-h-0 rounded-xs text-xs font-mono bg-surface-elevated hover:bg-surface-hover active:bg-surface-subtle text-docket-text border border-border hover:border-docket-gold/60 disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          >
            <span className="font-bold text-status-won">S1:</span>
            <span className="tabular-nums text-docket-text-muted">$48</span>
            <span className="text-docket-text-secondary">Carrier POD</span>
            {loadingScenario === 'S1' && <Clock className="h-3 w-3 animate-spin text-status-won ml-0.5" />}
          </button>

          {/* S2 (Primary Highlight) */}
          <button
            onClick={() => handleInject('S2')}
            disabled={cooldown > 0 || loadingScenario !== null}
            aria-busy={loadingScenario === 'S2'}
            aria-label="Inject S2 VIP Fraud Dispute"
            className="flex-1 sm:flex-none inline-flex items-center gap-2 px-3 py-1.5 min-h-[44px] sm:min-h-0 rounded-xs text-xs font-mono bg-surface-elevated hover:bg-surface-hover active:bg-surface-subtle text-docket-text border border-docket-gold/60 hover:border-docket-gold disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          >
            <span className="font-bold text-docket-gold">S2:</span>
            <span className="tabular-nums text-docket-text-muted">$340</span>
            <span className="text-docket-text font-medium">VIP Fraud</span>
            {loadingScenario === 'S2' && <Clock className="h-3 w-3 animate-spin text-docket-gold ml-0.5" />}
          </button>

          {/* S3 */}
          <button
            onClick={() => handleInject('S3')}
            disabled={cooldown > 0 || loadingScenario !== null}
            aria-busy={loadingScenario === 'S3'}
            aria-label="Inject S3 Subscription Cancellation Dispute"
            className="flex-1 sm:flex-none inline-flex items-center gap-2 px-3 py-1.5 min-h-[44px] sm:min-h-0 rounded-xs text-xs font-mono bg-surface-elevated hover:bg-surface-hover active:bg-surface-subtle text-docket-text border border-border hover:border-docket-gold/60 disabled:opacity-40 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          >
            <span className="font-bold text-docket-text-muted">S3:</span>
            <span className="tabular-nums text-docket-text-muted">$129</span>
            <span className="text-docket-text-secondary">Concession</span>
            {loadingScenario === 'S3' && <Clock className="h-3 w-3 animate-spin text-docket-text-muted ml-0.5" />}
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          role="status"
          aria-live="polite"
          className={`mt-3 p-2.5 rounded-xs text-xs flex items-start space-x-2 border font-mono ${
            statusMessage.type === 'success'
              ? 'bg-status-won/10 text-status-won border-status-won/30'
              : 'bg-status-action/10 text-status-action border-status-action/30'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-status-won shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5 text-status-action shrink-0 mt-0.5" />
          )}
          <p className="flex-1">{statusMessage.text}</p>
        </div>
      )}
    </div>
  );
};
