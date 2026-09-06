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
import { ArrowLeft, Clock, Scale, Cpu, Smartphone, ShieldCheck } from 'lucide-react';

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
      <div className="space-y-6 animate-skeleton" aria-busy="true" aria-label="Loading Dispute Case Dossier">
        <Header
          lastUpdated={lastUpdated}
          isRefreshing={isRefreshing}
          onRefresh={fetchCaseDetails}
          secondsRemaining={secondsRemaining}
        />
        <div className="h-16 bg-surface border border-border rounded-xs" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <div className="h-56 bg-surface border border-border rounded-xs" />
            <div className="h-64 bg-surface border border-border rounded-xs" />
            <div className="h-48 bg-surface border border-border rounded-xs" />
          </div>
          <div className="lg:col-span-4">
            <div className="h-[520px] bg-surface border border-border rounded-xs" />
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
        <div className="bg-surface border border-border rounded-xs p-12 text-center text-docket-text-muted">
          <Scale className="h-10 w-10 text-docket-gold/60 mx-auto mb-3" />
          <h3 className="text-base font-serif font-medium text-docket-text">Dispute Not Found in Docket</h3>
          <p className="text-xs text-docket-text-muted mt-1 max-w-sm mx-auto font-mono">
            Dispute &ldquo;{disputeId}&rdquo; was not located in the active magistrate database. Return to the docket ledger to select an active case.
          </p>
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 mt-4 px-3.5 py-1.5 rounded-xs text-xs font-mono font-medium bg-surface-elevated hover:bg-surface-hover text-docket-text border border-border hover:border-docket-gold/60 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          >
            <ArrowLeft className="h-3.5 w-3.5 text-docket-gold" />
            <span>Return to Docket</span>
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

      {/* Case Header Folio Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="space-y-1.5">
          <Link
            href="/"
            className="inline-flex items-center space-x-1.5 text-xs text-docket-gold hover:text-docket-gold-light font-mono font-medium py-1 -ml-0.5 rounded-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-docket-gold"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>&larr; Return to Active Docket</span>
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-serif font-medium text-docket-text tracking-tight">
              Case Dossier: <span className="font-mono text-docket-gold font-bold">{disputeId}</span>
            </h1>
            {dispute && <StatusChip status={dispute.status} />}
          </div>
          <p className="text-xs text-docket-text-muted font-mono">
            Reason: <span className="font-semibold text-docket-text capitalize">{dispute?.reason.replace(/_/g, ' ')}</span>
            <span className="mx-2 text-border">|</span>
            Contested Value: <strong className="font-bold text-docket-gold tabular-nums">{amountFormatted} USD</strong>
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono text-docket-text-muted">
          {dispute?.evidence_due_by && (
            <div className="bg-surface-elevated border border-border px-3.5 py-1.5 rounded-xs flex items-center space-x-2">
              <Clock className="h-3.5 w-3.5 text-docket-gold" />
              <span>Evidence Due: <strong className="text-docket-text">{new Date(dispute.evidence_due_by).toLocaleDateString()}</strong></span>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Strategy, Evidence, and Audit Trace */}
        <div className="lg:col-span-8 space-y-6">
          <div>
            <div className="flex items-center space-x-2 mb-2.5">
              <Cpu className="h-4 w-4 text-docket-gold" />
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-docket-text">
                Bedrock Defense Strategy &amp; Expected Value Model
              </h2>
            </div>
            <StrategyCard
              decision={decision || undefined}
              amountCents={dispute ? dispute.amount_cents : 0}
            />
          </div>

          <div>
            <div className="flex items-center space-x-2 mb-2.5">
              <ShieldCheck className="h-4 w-4 text-status-won" />
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-docket-text">
                Evidentiary Exhibits &amp; Carrier Verification
              </h2>
            </div>
            <EvidencePacket order={order || undefined} />
          </div>

          <div>
            <div className="flex items-center space-x-2 mb-2.5">
              <Clock className="h-4 w-4 text-docket-text-muted" />
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-docket-text">
                AgentCore Audit Trail &amp; Telemetry
              </h2>
            </div>
            <div className="bg-surface border border-border rounded-xs p-5">
              <AuditTimeline entries={auditLogs} />
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Merchant ApprovalGate Handset */}
        <div className="lg:col-span-4 space-y-6">
          <div className="sticky top-6">
            <div className="flex items-center space-x-2 mb-2.5">
              <Smartphone className="h-4 w-4 text-docket-gold" />
              <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-docket-text">
                Merchant Intercept Handset (SMS)
              </h2>
            </div>
            <div className="bg-surface border border-border rounded-xs p-4 flex justify-center min-h-[580px]">
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
