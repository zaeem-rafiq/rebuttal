'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  ExhibitItem,
  CarrierTimelineDossier,
  SignedDeliverySlipDossier,
  RadarRiskDossier,
  TermsAcceptanceDossier,
  CustomerCommunicationDossier,
  OrderLedgerDossier,
  MissingEvidenceDossier,
} from '@/lib/types';

interface ExhibitInspectorProps {
  exhibits: ExhibitItem[];
}

export const ExhibitInspector: React.FC<ExhibitInspectorProps> = ({ exhibits }) => {
  const [selectedExhibitLetter, setSelectedExhibitLetter] = useState<string | null>(null);
  const triggerRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  // Handle ESC key to close inspector drawer/expanded state and return focus
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedExhibitLetter !== null) {
        e.preventDefault();
        const letter = selectedExhibitLetter;
        setSelectedExhibitLetter(null);
        // Return focus to the trigger button
        if (triggerRefs.current[letter]) {
          triggerRefs.current[letter]?.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedExhibitLetter]);

  const toggleExhibit = (letter: string) => {
    setSelectedExhibitLetter((prev) => (prev === letter ? null : letter));
  };

  const renderCarrierTimeline = (dossier: CarrierTimelineDossier) => (
    <div className="space-y-3 font-sans text-xs">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pb-2 border-b border-rule">
        <div>
          <span className="text-secondary-ink block">Carrier & service:</span>
          <span className="font-mono font-medium text-ink">
            {dossier.carrier} · {dossier.service || 'Standard'}
          </span>
        </div>
        <div>
          <span className="text-secondary-ink block">Tracking number:</span>
          <span className="font-mono font-medium text-ink tabular-nums">
            {dossier.trackingNumber}
          </span>
        </div>
        <div>
          <span className="text-secondary-ink block">Delivery location:</span>
          <span className="font-medium text-ink">{dossier.deliveryLocation}</span>
        </div>
        {dossier.signedBy && (
          <div>
            <span className="text-secondary-ink block">Signature on delivery:</span>
            <span className="font-mono font-medium text-ink">{dossier.signedBy}</span>
          </div>
        )}
      </div>

      <div>
        <span className="text-secondary-ink block font-mono mb-2">Tracking milestone history:</span>
        <div className="space-y-2">
          {dossier.events.map((evt, idx) => (
            <div
              key={idx}
              className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 py-1.5 border-b border-rule last:border-b-0"
            >
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-secondary-ink whitespace-nowrap tabular-nums text-[11px]">
                  {evt.timestamp}
                </span>
                <span className="text-ink font-medium">{evt.location}</span>
                <span className="text-secondary-ink">— {evt.status}</span>
              </div>
              {evt.details && (
                <div className="text-secondary-ink italic text-[11px] sm:text-right">
                  {evt.details}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderDeliverySlip = (dossier: SignedDeliverySlipDossier) => (
    <div className="space-y-3 font-sans text-xs">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pb-2 border-b border-rule">
        <div>
          <span className="text-secondary-ink block">Signer name:</span>
          <span className="font-medium text-ink">{dossier.signerName}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Signature timestamp:</span>
          <span className="font-mono text-ink tabular-nums">{dossier.signatureTimestamp}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Carrier verification:</span>
          <span className="font-mono text-ink">{dossier.carrier}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Electronic confirmation code:</span>
          <span className="font-mono text-ink tabular-nums">{dossier.confirmationCode}</span>
        </div>
      </div>

      <div className="py-2 border-b border-rule">
        <span className="text-secondary-ink block mb-1">Destination address:</span>
        <div className="font-mono text-ink">{dossier.deliveryAddress}</div>
      </div>

      <div className="text-[11px] text-secondary-ink italic">
        Digital signature captured on courier electronic terminal at delivery point. Signature record cryptographically bound to waybill {dossier.trackingNumber}.
      </div>
    </div>
  );

  const renderRadarRisk = (dossier: RadarRiskDossier) => (
    <div className="space-y-3 font-sans text-xs">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pb-2 border-b border-rule">
        <div>
          <span className="text-secondary-ink block">Radar risk score:</span>
          <span className="font-mono font-medium text-ink tabular-nums">
            {dossier.riskScore} / 100
          </span>
          <span className="text-secondary-ink block text-[11px]">
            ({dossier.riskLevel === 'normal' ? 'Low risk' : dossier.riskLevel})
          </span>
        </div>
        <div>
          <span className="text-secondary-ink block">3D Secure status:</span>
          <span className="font-mono font-medium text-decision-green">
            {dossier.threeDSecure}
          </span>
          {dossier.threeDSecureVersion && (
            <span className="text-secondary-ink block text-[11px]">
              {dossier.threeDSecureVersion}
            </span>
          )}
        </div>
        <div>
          <span className="text-secondary-ink block">AVS & CVC checks:</span>
          <span className="font-mono text-ink block">AVS postal: {dossier.avsPostalCheck}</span>
          <span className="font-mono text-ink block">CVC: {dossier.cvcCheck}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-secondary-ink block">Cardholder IP & network:</span>
          <span className="font-mono text-ink tabular-nums">{dossier.ipAddress}</span>
          <span className="text-secondary-ink block text-[11px]">{dossier.ipLocation}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Stripe charge identifier:</span>
          <span className="font-mono text-ink">{dossier.chargeId}</span>
        </div>
      </div>
    </div>
  );

  const renderTermsAcceptance = (dossier: TermsAcceptanceDossier) => (
    <div className="space-y-3 font-sans text-xs">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pb-2 border-b border-rule">
        <div>
          <span className="text-secondary-ink block">Agreement policy:</span>
          <span className="font-medium text-ink">{dossier.version}</span>
          <span className="text-secondary-ink block text-[11px]">Effective: {dossier.effectiveDate}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Consent timestamp:</span>
          <span className="font-mono text-ink tabular-nums">{dossier.acceptedAt}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Consent IP address:</span>
          <span className="font-mono text-ink tabular-nums">{dossier.ipAddress}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Acknowledgment status:</span>
          <span className="font-medium text-decision-green">
            {dossier.checkboxAcknowledgment ? 'Affirmatively checked at checkout' : 'Implied'}
          </span>
        </div>
      </div>

      <div className="py-2 border-b border-rule">
        <span className="text-secondary-ink block font-mono text-[11px] mb-1">
          {dossier.clauseTitle}:
        </span>
        <blockquote className="border-l-2 border-rule-strong pl-3 text-ink italic leading-relaxed text-xs">
          "{dossier.clauseExcerpt}"
        </blockquote>
      </div>

      <div className="text-[11px] text-secondary-ink font-mono break-all">
        Client User-Agent: {dossier.userAgent}
      </div>
    </div>
  );

  const renderCustomerCommunication = (dossier: CustomerCommunicationDossier) => (
    <div className="space-y-3 font-sans text-xs">
      <div className="text-secondary-ink font-mono text-xs pb-1 border-b border-rule">
        Thread identifier: {dossier.threadId} ({dossier.messages.length} messages logged)
      </div>

      <div className="space-y-2">
        {dossier.messages.map((msg) => (
          <div
            key={msg.id}
            className="p-2.5 bg-desk/30 border border-rule space-y-1.5"
          >
            <div className="flex items-baseline justify-between gap-2 text-[11px] font-mono">
              <span className="font-semibold text-ink">
                {msg.sender === 'customer' ? 'Customer' : 'Merchant support'} ({msg.id})
              </span>
              <span className="text-secondary-ink tabular-nums">{msg.timestamp}</span>
            </div>
            {msg.subject && (
              <div className="font-medium text-ink text-xs">
                Subject: {msg.subject}
              </div>
            )}
            <div className="text-ink whitespace-pre-wrap leading-relaxed">
              {msg.body}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderOrderLedger = (dossier: OrderLedgerDossier) => (
    <div className="space-y-3 font-sans text-xs">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pb-2 border-b border-rule">
        <div>
          <span className="text-secondary-ink block">Customer account:</span>
          <span className="font-medium text-ink">{dossier.customerName}</span>
          <span className="text-secondary-ink block text-[11px] font-mono">{dossier.customerId} · {dossier.membershipStatus}</span>
        </div>
        <div>
          <span className="text-secondary-ink block">Lifetime transaction volume:</span>
          <span className="font-mono font-medium text-ink tabular-nums">
            {dossier.lifetimeSpendFormatted}
          </span>
          <span className="text-secondary-ink block text-[11px]">
            {dossier.completedOrdersCount} orders since {dossier.firstOrderDate}
          </span>
        </div>
        <div>
          <span className="text-secondary-ink block">Dispute rate:</span>
          <span className="font-mono font-medium text-decision-green">
            {dossier.disputeHistoryRate}
          </span>
        </div>
      </div>

      <div>
        <span className="text-secondary-ink block font-mono mb-1.5">Prior fulfilled transactions:</span>
        <div className="border border-rule divide-y divide-rule">
          {dossier.priorOrders.map((ord) => (
            <div
              key={ord.orderId}
              className="flex items-baseline justify-between gap-2 p-2 text-[11px] font-mono"
            >
              <div className="flex items-baseline gap-2">
                <span className="font-semibold text-ink">{ord.orderId}</span>
                <span className="text-secondary-ink tabular-nums">{ord.date}</span>
                <span className="text-secondary-ink font-sans truncate max-w-[200px]">{ord.destination}</span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-secondary-ink font-sans">{ord.status}</span>
                <span className="text-ink font-semibold tabular-nums">{ord.amount}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderMissingEvidence = (dossier: MissingEvidenceDossier) => (
    <div className="space-y-2 font-sans text-xs">
      <div className="text-secondary-ink font-medium">
        Evidence status: Missing ({dossier.reason})
      </div>
      <div className="text-secondary-ink leading-relaxed">
        {dossier.disclosure}
      </div>
    </div>
  );

  const renderDossierContent = (item: ExhibitItem) => {
    if (!item.dossier) {
      return (
        <div className="text-xs text-secondary-ink font-sans">
          No additional granular dossier attached for this exhibit.
        </div>
      );
    }

    switch (item.dossier.type) {
      case 'carrier_timeline':
        return renderCarrierTimeline(item.dossier);
      case 'delivery_slip':
        return renderDeliverySlip(item.dossier);
      case 'radar_risk':
        return renderRadarRisk(item.dossier);
      case 'terms_acceptance':
        return renderTermsAcceptance(item.dossier);
      case 'customer_communication':
        return renderCustomerCommunication(item.dossier);
      case 'order_ledger':
        return renderOrderLedger(item.dossier);
      case 'missing_evidence':
        return renderMissingEvidence(item.dossier);
      default:
        return null;
    }
  };

  return (
    <div className="divide-y divide-rule border-t border-b border-rule font-sans">
      {exhibits.map((ex) => {
        const isExpanded = selectedExhibitLetter === ex.letter;

        return (
          <div key={ex.letter} className="transition-colors">
            {/* Exhibit Header Trigger */}
            <button
              type="button"
              ref={(el) => {
                triggerRefs.current[ex.letter] = el;
              }}
              onClick={() => toggleExhibit(ex.letter)}
              aria-expanded={isExpanded}
              aria-controls={`dossier-${ex.letter}`}
              className={`w-full py-2.5 text-left flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 text-xs hover:bg-desk/40 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2 ${
                isExpanded ? 'bg-desk/30' : ''
              }`}
            >
              <div className="flex-1 max-w-[65ch]">
                <span className="font-medium text-ink mr-2">
                  Exhibit {ex.letter}: {ex.title}
                </span>
                <span className="font-mono text-secondary-ink mr-2">
                  [{ex.field}]
                </span>
                <span className="text-secondary-ink">
                  — {ex.source}: {ex.summary}
                </span>
              </div>
              <div className="font-mono text-right shrink-0 flex items-center gap-2 self-start sm:self-auto">
                {ex.status === 'attached' ? (
                  <span className="text-secondary-ink">attached</span>
                ) : (
                  <span className="text-secondary-ink font-medium">Missing</span>
                )}
                <span className="text-secondary-ink text-[11px] underline">
                  {isExpanded ? 'close' : 'inspect'}
                </span>
              </div>
            </button>

            {/* Interactive Dossier Drawer / Inline Panel */}
            {isExpanded && (
              <section
                id={`dossier-${ex.letter}`}
                role="region"
                aria-label={`Dossier details for Exhibit ${ex.letter}`}
                className="bg-sheet border-t border-b border-rule p-4 sm:p-5 my-1"
              >
                <div className="flex items-baseline justify-between border-b border-rule pb-2 mb-3">
                  <div className="text-xs font-mono text-ink font-semibold">
                    Dossier Exhibit {ex.letter} · {ex.title}
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleExhibit(ex.letter)}
                    className="text-xs font-mono text-secondary-ink underline hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink focus-visible:outline-offset-2"
                  >
                    Close (Esc)
                  </button>
                </div>

                {renderDossierContent(ex)}
              </section>
            )}
          </div>
        );
      })}
    </div>
  );
};
