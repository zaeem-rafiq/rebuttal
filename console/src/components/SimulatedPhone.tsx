'use client';

import React, { useState } from 'react';
import { Smartphone, Send, Check, CheckCheck, Shield, CheckCircle2, AlertCircle, RotateCcw } from 'lucide-react';
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
    `Rebuttal Security Alert: New ${(reason || 'Dispute').replace(/_/g, ' ')} dispute for ${amountFormatted} from ${customerName}. Evidentiary dossier compiled. Reply 1 to Fight, 2 to Concede, 3 to Hold.`;

  const handleQuickReply = async (code: '1' | '2' | '3') => {
    const text = code === '1' ? '1. Fight' : code === '2' ? '2. Concede' : '3. Hold';
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
        message: `Reply "${displayValue}" dispatched successfully!`,
      });
      if (onReplySuccess) {
        onReplySuccess(bodyValue);
      }
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: `Failed to dispatch reply: ${err.message || 'Network error'}`,
        onRetry: () => sendReply(bodyValue, displayValue),
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col items-center">
      {/* Smartphone Chassis */}
      <div className="w-full max-w-[340px] bg-slate-950 rounded-[44px] p-3 shadow-2xl shadow-black/50 border-[4px] border-slate-800 relative">
        {/* Dynamic Island / Speaker */}
        <div aria-hidden="true" className="absolute top-5 left-1/2 -translate-x-1/2 w-24 h-4 bg-slate-900 rounded-full z-20 flex items-center justify-center space-x-1.5">
          <div className="h-1.5 w-1.5 rounded-full bg-slate-700" />
          <div className="h-2 w-2 rounded-full bg-slate-800 ring-1 ring-slate-700" />
        </div>

        {/* Screen Area */}
        <div className="bg-slate-900 rounded-[34px] overflow-hidden flex flex-col h-[520px] border border-slate-800">
          {/* Phone Status Bar */}
          <div aria-hidden="true" className="pt-3 px-6 pb-2 flex justify-between items-center text-[10px] text-slate-400 select-none">
            <span className="font-semibold text-slate-200">9:41</span>
            <div className="flex items-center space-x-1.5">
              <span>5G</span>
              <div className="w-5 h-2.5 border border-slate-400 rounded-sm p-0.5">
                <div className="h-full w-full bg-slate-200 rounded-[1px]" />
              </div>
            </div>
          </div>

          {/* SMS Contact Header */}
          <div className="px-4 py-2 border-b border-slate-800 bg-slate-900/90 flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200">
              <Shield className="h-3.5 w-3.5 text-indigo-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-200 truncate">Rebuttal Security</p>
              <p className="text-[10px] text-slate-400 font-mono">+1 (812) 955-1686</p>
            </div>
          </div>

          {/* Message Thread */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs">
            <div className="text-center text-[10px] text-slate-400 my-1">Today</div>

            {/* Inbound Alert Bubble from Rebuttal */}
            <div className="flex flex-col items-start max-w-[85%]">
              <div className="bg-slate-800 text-slate-100 p-3 rounded-2xl rounded-tl-sm border border-slate-700/60 shadow-sm leading-relaxed">
                <p>{defaultAlert}</p>
              </div>
              <span className="text-[10px] text-slate-400 mt-1 ml-1 flex items-center space-x-1">
                <Shield className="h-3 w-3 text-emerald-400" />
                <span>Rebuttal Agent</span>
              </span>
            </div>

            {/* Outbound Reply Bubbles from Owner */}
            {sentReplies.map((reply, idx) => (
              <div key={idx} className="flex flex-col items-end ml-auto max-w-[85%]">
                <div className="bg-indigo-600 text-white p-2.5 px-3 rounded-2xl rounded-tr-sm shadow-md">
                  <p>{reply.text}</p>
                </div>
                <span className="text-[9px] text-slate-400 mt-1 mr-1 flex items-center space-x-1">
                  <span>{reply.time}</span>
                  <CheckCheck className="h-3 w-3 text-indigo-400" />
                </span>
              </div>
            ))}
          </div>

          {/* Quick Reply Action Buttons */}
          <div className="p-2 border-t border-slate-800 bg-slate-950/80">
            <p className="text-[10px] uppercase font-semibold text-slate-400 mb-1.5 px-1">
              Quick Reply:
            </p>
            <div className="grid grid-cols-3 gap-1.5 mb-2">
              <button
                type="button"
                onClick={() => handleQuickReply('1')}
                disabled={sending}
                aria-label="Send reply 1 Fight"
                className="py-2 px-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 active:scale-95 text-white font-semibold text-xs transition-all disabled:opacity-50 shadow-sm"
              >
                1 Fight
              </button>
              <button
                type="button"
                onClick={() => handleQuickReply('2')}
                disabled={sending}
                aria-label="Send reply 2 Concede"
                className="py-2 px-2 rounded-lg bg-rose-700 hover:bg-rose-600 active:scale-95 text-white font-semibold text-xs transition-all disabled:opacity-50 shadow-sm"
              >
                2 Concede
              </button>
              <button
                type="button"
                onClick={() => handleQuickReply('3')}
                disabled={sending}
                aria-label="Send reply 3 Hold"
                className="py-2 px-2 rounded-lg bg-slate-700 hover:bg-slate-600 active:scale-95 text-white font-semibold text-xs transition-all disabled:opacity-50 shadow-sm"
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
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1 text-xs text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
              />
              <button
                type="submit"
                disabled={sending || !replyMessage.trim()}
                aria-label="Submit SMS reply"
                className="h-7 w-7 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-40 flex items-center justify-center transition-colors"
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
          className={`mt-3 p-2.5 px-3 rounded-xl text-xs flex items-center justify-between gap-2 border shadow-md max-w-[340px] w-full ${
            feedback.type === 'success'
              ? 'bg-emerald-950/70 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/80 border-rose-800 text-rose-300'
          }`}
        >
          <div className="flex items-center space-x-2 min-w-0">
            {feedback.type === 'success' ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="h-3.5 w-3.5 text-rose-400 shrink-0" />
            )}
            <span className="truncate font-medium">{feedback.message}</span>
          </div>
          {feedback.onRetry && (
            <button
              type="button"
              onClick={feedback.onRetry}
              className="text-[11px] font-semibold bg-rose-800 hover:bg-rose-700 text-white px-2 py-0.5 rounded flex items-center space-x-1 shrink-0 transition-colors"
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
