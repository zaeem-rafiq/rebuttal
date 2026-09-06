'use client';

import React, { useState } from 'react';
import { Smartphone, Send, Check, CheckCheck, Scale, CheckCircle2, AlertCircle, RotateCcw } from 'lucide-react';
import { TWILIO_WEBHOOK_URL } from '@/lib/config';

interface SimulatedPhoneProps {
  disputeId: string;
  amountFormatted: string;
  customerName?: string;
  reason?: string;
  decisionStatus?: string;
  ownerSummary?: string;
  onReplySuccess?: (replyText: string) => void;
}

export const SimulatedPhone: React.FC<SimulatedPhoneProps> = ({
  disputeId,
  amountFormatted,
  customerName = 'Customer',
  reason = 'Dispute',
  decisionStatus = 'pending',
  ownerSummary,
  onReplySuccess,
}) => {
  const [replyMessage, setReplyMessage] = useState<string>('');
  const [sending, setSending] = useState<boolean>(false);
  const [sentReplies, setSentReplies] = useState<Array<{ text: string; time: string }>>([]);
  const [feedback, setFeedback] = useState<{
    type: 'success' | 'error';
    message: string;
    onRetry?: () => void;
  } | null>(null);

  const defaultAlert =
    ownerSummary ||
    `Rebuttal Alert: Dispute #${disputeId} (${amountFormatted}) for customer ${customerName}. Auto-defense brief compiled. Reply 1 to Authorize Evidence, 2 to Concede, 3 to Hold.`;

  const handleQuickReply = async (code: '1' | '2' | '3') => {
    const text = code === '1' ? '1. Authorize' : code === '2' ? '2. Concede' : '3. Hold';
    await sendReply(code, text);
  };

  const handleCustomSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyMessage.trim() || sending) return;
    const text = replyMessage.trim();
    setReplyMessage('');
    await sendReply(text, text);
  };

  const sendReply = async (bodyValue: string, displayValue: string) => {
    setSending(true);
    setFeedback(null);

    try {
      const formData = new URLSearchParams();
      formData.append('Body', bodyValue);
      formData.append('From', '+18129551686');
      formData.append('dispute_id', disputeId);

      await fetch(TWILIO_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
        mode: 'no-cors',
      });

      setSentReplies((prev) => [
        ...prev,
        { text: displayValue, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
      ]);

      setFeedback({
        type: 'success',
        message: `Decision token "${displayValue}" dispatched to Bedrock AgentCore!`,
      });
      if (onReplySuccess) {
        onReplySuccess(bodyValue);
      }
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: `Failed to dispatch decision: ${err.message || 'Network error'}`,
        onRetry: () => sendReply(bodyValue, displayValue),
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col items-center w-full">
      {/* Smartphone Chassis */}
      <div className="w-full max-w-[340px] bg-surface rounded-[32px] p-2.5 shadow-xl border-2 border-border relative">
        {/* Dynamic Island / Speaker */}
        <div aria-hidden="true" className="absolute top-4 left-1/2 -translate-x-1/2 w-20 h-3.5 bg-canvas rounded-full z-20 flex items-center justify-center space-x-1.5 border border-border">
          <div className="h-1 w-1 rounded-full bg-docket-text-muted" />
          <div className="h-1.5 w-1.5 rounded-full bg-surface-elevated ring-1 ring-border" />
        </div>

        {/* Screen Area */}
        <div className="bg-canvas rounded-[24px] overflow-hidden flex flex-col h-[520px] border border-border">
          {/* Phone Status Bar */}
          <div aria-hidden="true" className="pt-3 px-5 pb-2 flex justify-between items-center text-[10px] text-docket-text-muted select-none font-mono">
            <span className="font-semibold text-docket-text">09:41</span>
            <div className="flex items-center space-x-1.5">
              <span>LTE</span>
              <div className="w-4 h-2 border border-docket-text-muted rounded-xs p-0.5">
                <div className="h-full w-full bg-docket-gold rounded-xs" />
              </div>
            </div>
          </div>

          {/* SMS Contact Header */}
          <div className="px-4 py-2.5 border-b border-border bg-surface-elevated/70 flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded-full bg-docket-gold/15 border border-docket-gold/30 flex items-center justify-center text-docket-gold">
              <Scale className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-docket-text truncate">Rebuttal ApprovalGate</p>
              <p className="text-[10px] text-docket-text-muted font-mono">+1 (812) 955-1686</p>
            </div>
          </div>

          {/* Message Thread */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs">
            <div className="text-center font-mono text-[10px] text-docket-text-muted my-1">Arbitration Channel</div>

            {/* Inbound Alert Bubble from Rebuttal */}
            <div className="flex flex-col items-start max-w-[92%]">
              <div className="bg-surface-elevated text-docket-text p-3 rounded-xs border border-border leading-relaxed font-sans text-xs">
                <p>{defaultAlert}</p>
              </div>
              <span className="text-[10px] text-docket-gold mt-1 ml-1 flex items-center space-x-1 font-mono">
                <Scale className="h-3 w-3" />
                <span>AgentCore Intercept</span>
              </span>
            </div>

            {/* Outbound Reply Bubbles from Owner */}
            {sentReplies.map((reply, idx) => (
              <div key={idx} className="flex flex-col items-end ml-auto max-w-[85%]">
                <div className="bg-docket-gold text-canvas font-mono font-bold p-2.5 px-3.5 rounded-xs shadow-xs text-xs">
                  <p>{reply.text}</p>
                </div>
                <span className="text-[9px] text-docket-text-muted font-mono mt-1 mr-1 flex items-center space-x-1">
                  <span>{reply.time}</span>
                  <CheckCheck className="h-3 w-3 text-docket-gold" />
                </span>
              </div>
            ))}
          </div>

          {/* Quick Reply Action Buttons */}
          <div className="p-2.5 border-t border-border bg-surface-elevated/90">
            <p className="text-[10px] font-mono text-docket-text-muted mb-1.5 px-0.5 uppercase tracking-wider">
              Single-Tap Intercept:
            </p>
            <div className="grid grid-cols-3 gap-1.5 mb-2 font-mono">
              <button
                type="button"
                onClick={() => handleQuickReply('1')}
                disabled={sending}
                aria-label="Send reply 1 Authorize"
                className="py-2 px-1.5 rounded-xs bg-docket-gold text-canvas hover:bg-docket-gold-light text-xs font-bold transition-colors disabled:opacity-50 text-center"
              >
                1 Submit
              </button>
              <button
                type="button"
                onClick={() => handleQuickReply('2')}
                disabled={sending}
                aria-label="Send reply 2 Concede"
                className="py-2 px-1.5 rounded-xs bg-surface border border-border text-docket-text-secondary hover:text-docket-text text-xs font-semibold transition-colors disabled:opacity-50 text-center"
              >
                2 Concede
              </button>
              <button
                type="button"
                onClick={() => handleQuickReply('3')}
                disabled={sending}
                aria-label="Send reply 3 Hold"
                className="py-2 px-1.5 rounded-xs bg-surface border border-border text-docket-text-muted hover:text-docket-text text-xs font-semibold transition-colors disabled:opacity-50 text-center"
              >
                3 Hold
              </button>
            </div>

            {/* Custom Reply Input */}
            <form onSubmit={handleCustomSend} className="flex items-center space-x-1.5">
              <label htmlFor="sms-custom-reply" className="sr-only">
                Type reply message (1, 2, or 3)
              </label>
              <input
                id="sms-custom-reply"
                type="text"
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                placeholder="Type 1, 2, or 3..."
                disabled={sending}
                aria-label="Type reply message"
                className="flex-1 bg-canvas border border-border rounded-xs px-2.5 py-1.5 text-xs text-docket-text placeholder:text-docket-text-subtle focus:outline-none focus:border-docket-gold focus:ring-1 focus:ring-docket-gold font-mono"
              />
              <button
                type="submit"
                disabled={sending || !replyMessage.trim()}
                aria-label="Submit SMS reply"
                className="h-7 w-7 rounded-xs bg-docket-gold hover:bg-docket-gold-light text-canvas disabled:opacity-30 flex items-center justify-center transition-colors shrink-0 font-bold"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {feedback && (
        <div
          role="status"
          aria-live="polite"
          className={`mt-3 p-2.5 px-3 rounded-xs text-xs flex items-center justify-between gap-2 border shadow-xs max-w-[340px] w-full font-mono ${
            feedback.type === 'success'
              ? 'bg-status-won/10 border-status-won/30 text-status-won'
              : 'bg-status-action/10 border-status-action/30 text-status-action'
          }`}
        >
          <div className="flex items-center space-x-2 min-w-0">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
            ) : (
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
            )}
            <span className="truncate font-medium">{feedback.message}</span>
          </div>
          {feedback.onRetry && (
            <button
              type="button"
              onClick={feedback.onRetry}
              className="text-[11px] font-semibold bg-surface-elevated hover:bg-surface-hover text-docket-text px-2 py-0.5 rounded-xs border border-border flex items-center space-x-1 shrink-0 transition-colors"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Retry</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};
