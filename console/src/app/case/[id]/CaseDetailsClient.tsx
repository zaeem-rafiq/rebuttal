'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import { Dispute, Decision, AuditLogEntry, Order } from '@/lib/types';
import { Header } from '@/components/Header';
import { StatusChip } from '@/components/StatusChip';
import { StrategyCard } from '@/components/StrategyCard';
import { AuditTimeline } from '@/components/AuditTimeline';
import { EvidencePacket } from '@/components/EvidencePacket';
import { SimulatedPhone } from '@/components/SimulatedPhone';
import { ArrowLeft, Clock, ShieldAlert, Cpu } from 'lucide-react';

export default function CaseDetailsPage() {
  const params = useParams();
  const disputeId = params?.id as string;

  const [dispute, setDispute] = useState<Dispute | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(5);

  const fetchCaseDetails = useCallback(async () => {
    if (!disputeId) return;
    setIsRefreshing(true);

    try {
      const { data: dData } = await supabase
        .from('disputes')
        .select('*')
        .eq('id', disputeId)
        .single();

      if (dData) {
        setDispute(dData as Dispute);

        const { data: decData } = await supabase
          .from('decisions')
          .select('*')
          .eq('dispute_id', disputeId)
          .maybeSingle();

        if (decData) setDecision(decData as Decision);

        const { data: logsData } = await supabase
          .from('audit_log')
          .select('*')
          .eq('dispute_id', disputeId)
          .order('created_at', { ascending: false });

        if (logsData) setAuditLogs(logsData as AuditLogEntry[]);

        if (dData.order_id) {
          const { data: oData } = await supabase
            .from('orders')
            .select(`
              *,
              customer:customers(*),
              items:order_items(*),
              shipments:shipments(*, events:shipment_events(*)),
              messages:customer_messages(*)
            `)
            .eq('id', dData.order_id)
            .maybeSingle();

          if (oData) setOrder(oData as Order);
        }
      }
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to load case details:', err);
    } finally {
      setIsRefreshing(false);
      setLoading(false);
    }
  }, [disputeId]);

  useEffect(() => {
    fetchCaseDetails();
  }, [fetchCaseDetails]);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          fetchCaseDetails();
          return 5;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [fetchCaseDetails]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center text-slate-400 space-y-3">
        <div className="h-8 w-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
        <p className="text-sm">Loading dispute case details...</p>
      </div>
    );
  }

  if (!dispute) {
    return (
      <div className="space-y-6">
        <Header
          lastUpdated={lastUpdated}
          isRefreshing={isRefreshing}
          onRefresh={fetchCaseDetails}
          secondsRemaining={secondsRemaining}
        />
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center text-slate-400">
          <ShieldAlert className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-200">Dispute Not Found</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Dispute &ldquo;{disputeId}&rdquo; was not found in the database. Use the Scenario Injector on the dashboard to generate a live dispute case.
          </p>
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 mt-4 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to All Disputes</span>
          </Link>
        </div>
      </div>
    );
  }

  const amountFormatted = `$${(dispute.amount_cents / 100).toFixed(2)}`;

  return (
    <div className="space-y-6">
      <Header
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={fetchCaseDetails}
        secondsRemaining={secondsRemaining}
      />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-medium py-1.5 px-2 -ml-2 rounded-lg hover:bg-slate-800/60 min-h-[28px] transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to All Disputes</span>
          </Link>
          <div className="flex flex-wrap items-center space-x-3">
            <h1 className="text-2xl font-bold font-mono text-white tracking-tight">
              {disputeId}
            </h1>
            {dispute && <StatusChip status={dispute.status} />}
          </div>
          <p className="text-xs text-slate-400">
            {dispute?.reason.replace(/_/g, ' ').toUpperCase()} · Amount: <strong className="text-slate-200">{amountFormatted}</strong>
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
          {dispute?.evidence_due_by && (
            <div className="bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl flex items-center space-x-1.5">
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              <span>Due: {new Date(dispute.evidence_due_by).toLocaleDateString()}</span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-6">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-indigo-400" />
              <span>1. Agent Strategy & Win Probability</span>
            </h2>
            <StrategyCard
              decision={decision || undefined}
              amountCents={dispute ? dispute.amount_cents : 0}
            />
          </div>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
              <ShieldAlert className="h-4 w-4 text-emerald-400" />
              <span>2. Synthetic World Evidence Packet</span>
            </h2>
            <EvidencePacket order={order || undefined} />
          </div>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
              <Clock className="h-4 w-4 text-purple-400" />
              <span>3. AgentCore Audit Timeline</span>
            </h2>
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
              <AuditTimeline entries={auditLogs} />
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-6">
          <div className="sticky top-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
              <span>📱 4. Merchant Owner Mobile Interface</span>
            </h2>
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 flex justify-center min-h-[580px]">
              <SimulatedPhone
                disputeId={disputeId}
                amountFormatted={amountFormatted}
                customerName={order?.customer?.name}
                reason={dispute?.reason}
                decisionStatus={decision?.status}
                ownerSummary={decision?.owner_summary}
                onReplySuccess={() => fetchCaseDetails()}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
