'use client';

import React, { useState } from 'react';
import { Smartphone, Send, Check, CheckCheck, Shield, Sparkles } from 'lucide-react';
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
  const [feedback, setFeedback] = useState<string | null>(null);

  const defaultAlert = ownerSummary || `Rebuttal: New ${reason} dispute for ${amountFormatted} from ${customerName}. Win prob: 78%. Recommendation: Fight with delivery confirmation. Reply 1 to Fight, 2 to Concede, 3 to Hold.`;

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
      let resp: Response;
      try {
        resp = await fetch('/api/reply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ Body: bodyValue, dispute_id: disputeId }),
        });
      } catch {
        const formData = new URLSearchParams();
        formData.append('Body', bodyValue);
        formData.append('From', '+18129551686');
        resp = await fetch(TWILIO_WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString(),
        });
      }

      setSentReplies((prev) => [
        ...prev,
        { text: displayValue, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
      ]);

      setFeedback(`Reply "${displayValue}" sent to Twilio handler!`);
      if (onReplySuccess) {
        onReplySuccess(bodyValue);
      }
    } catch (err: any) {
      setFeedback(`Failed to send reply: ${err.message}`);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col items-center">
      {/* Smartphone Chassis */}
      <div className="w-full max-w-[340px] bg-slate-950 rounded-[44px] p-3 shadow-2xl shadow-indigo-950/40 border-[4px] border-slate-800 relative">
        {/* Dynamic Island / Speaker */}
        <div className="absolute top-5 left-1/2 -translate-x-1/2 w-24 h-4 bg-slate-900 rounded-full z-20 flex items-center justify-center space-x-1.5">
          <div className="h-1.5 w-1.5 rounded-full bg-slate-700" />
          <div className="h-2 w-2 rounded-full bg-slate-800 ring-1 ring-slate-700" />
        </div>

        {/* Screen Area */}
        <div className="bg-slate-900 rounded-[34px] overflow-hidden flex flex-col h-[520px] border border-slate-800">
          {/* Phone Status Bar */}
          <div className="pt-3 px-6 pb-2 flex justify-between items-center text-[10px] text-slate-400 select-none">
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
            <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white">
              <Shield className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-slate-200 truncate">Rebuttal Security</p>
              <p className="text-[10px] text-slate-500">+1 (812) 955-1686</p>
            </div>
          </div>

          {/* Message Thread */}
          <div className="flex-1 p-3 overflow-y-auto space-y-3 text-xs">
            <div className="text-center text-[10px] text-slate-500 my-1">Today</div>

            {/* Inbound Alert Bubble from Rebuttal */}
            <div className="flex flex-col items-start max-w-[85%]">
              <div className="bg-slate-800 text-slate-100 p-3 rounded-2xl rounded-tl-sm border border-slate-700/60 shadow-sm leading-relaxed">
                <p>{defaultAlert}</p>
              </div>
              <span className="text-[9px] text-slate-500 mt-1 ml-1 flex items-center space-x-1">
                <Sparkles className="h-2.5 w-2.5 text-indigo-400" />
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
                className="py-1.5 px-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-semibold text-[11px] transition-all disabled:opacity-50"
              >
                1 Fight
              </button>
              <button
                type="button"
                onClick={() => handleQuickReply('2')}
                disabled={sending}
                className="py-1.5 px-2 rounded-lg bg-rose-600 hover:bg-rose-500 active:scale-95 text-white font-semibold text-[11px] transition-all disabled:opacity-50"
              >
                2 Concede
              </button>
              <button
                type="button"
                onClick={() => handleQuickReply('3')}
                disabled={sending}
                className="py-1.5 px-2 rounded-lg bg-slate-700 hover:bg-slate-600 active:scale-95 text-white font-semibold text-[11px] transition-all disabled:opacity-50"
              >
                3 Hold
              </button>
            </div>

            {/* Custom Reply Input */}
            <form onSubmit={handleCustomSend} className="flex items-center space-x-1.5">
              <input
                type="text"
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                placeholder="Type 1, 2, or 3..."
                disabled={sending}
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1 text-xs text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
              <button
                type="submit"
                disabled={sending || !replyMessage.trim()}
                className="h-7 w-7 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 flex items-center justify-center text-white transition-colors"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {feedback && (
        <p className="text-xs text-emerald-400 mt-3 font-medium text-center">
          ✓ {feedback}
        </p>
      )}
    </div>
  );
};
