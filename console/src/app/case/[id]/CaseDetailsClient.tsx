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
      <div className="space-y-6 animate-pulse">
        <Header
          lastUpdated={lastUpdated}
          isRefreshing={isRefreshing}
          onRefresh={fetchCaseDetails}
          secondsRemaining={secondsRemaining}
        />
        <div className="h-14 bg-surface border border-border rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <div className="h-56 bg-surface border border-border rounded-lg" />
            <div className="h-64 bg-surface border border-border rounded-lg" />
            <div className="h-48 bg-surface border border-border rounded-lg" />
          </div>
          <div className="lg:col-span-4">
            <div className="h-[520px] bg-surface border border-border rounded-lg" />
          </div>
        </div>
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
        <div className="bg-surface border border-border rounded-lg p-12 text-center text-slate-400">
          <ShieldAlert className="h-9 w-9 text-slate-500 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-slate-200">Dispute Not Found in Docket</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Dispute &ldquo;{disputeId}&rdquo; was not located in the active database. Use the verification toolbar on the ledger to inject a test case.
          </p>
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 mt-4 px-3 py-1.5 rounded-md text-xs font-medium bg-surface-elevated hover:bg-surface-hover text-slate-200 border border-border transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Return to Ledger</span>
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

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="space-y-1">
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 text-xs text-blue-400 hover:text-blue-300 font-medium py-1 px-1.5 -ml-1.5 rounded hover:bg-surface-elevated transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Back to Dispute Docket</span>
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold font-mono text-white tracking-tight">
              {disputeId}
            </h1>
            {dispute && <StatusChip status={dispute.status} />}
          </div>
          <p className="text-xs text-slate-400">
            <span className="font-semibold text-slate-300 uppercase tracking-wide">
              {dispute?.reason.replace(/_/g, ' ')}
            </span>
            <span className="mx-2 text-slate-600">|</span>
            Contested Amount: <strong className="font-mono text-white tabular-nums">{amountFormatted}</strong>
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
          {dispute?.evidence_due_by && (
            <div className="bg-surface border border-border px-3 py-1.5 rounded-md flex items-center space-x-1.5">
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              <span>Evidence Due: <strong className="text-slate-200">{new Date(dispute.evidence_due_by).toLocaleDateString()}</strong></span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-6">
          <div>
            <div className="flex items-center space-x-2 mb-2.5">
              <Cpu className="h-4 w-4 text-blue-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Agent Defense Strategy & Valuation
              </h2>
            </div>
            <StrategyCard
              decision={decision || undefined}
              amountCents={dispute ? dispute.amount_cents : 0}
            />
          </div>

          <div>
            <div className="flex items-center space-x-2 mb-2.5">
              <ShieldAlert className="h-4 w-4 text-emerald-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Evidentiary Dossier & Carrier Proof
              </h2>
            </div>
            <EvidencePacket order={order || undefined} />
          </div>

          <div>
            <div className="flex items-center space-x-2 mb-2.5">
              <Clock className="h-4 w-4 text-slate-400" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                AgentCore Telemetry & Audit Trail
              </h2>
            </div>
            <div className="bg-surface border border-border rounded-lg p-5">
              <AuditTimeline entries={auditLogs} />
            </div>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-6">
          <div className="sticky top-6">
            <div className="flex items-center space-x-2 mb-2.5">
              <span className="text-blue-400 text-sm">📱</span>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Owner Approval Stream (SMS)
              </h2>
            </div>
            <div className="bg-surface border border-border rounded-lg p-4 flex justify-center min-h-[580px]">
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
