import {
  Dispute,
  CaseFileMemo,
  ExhibitItem,
} from './types';

/**
 * Format string to strict Sentence Case
 * E.g. "product_not_received" -> "Product not received"
 * E.g. "FRAUDULENT" -> "Fraudulent"
 */
export function formatSentenceCase(str: string): string {
  if (!str) return '';
  const clean = str.replace(/_/g, ' ').trim();
  return clean.charAt(0).toUpperCase() + clean.slice(1).toLowerCase();
}

/**
 * Build rich CaseFileMemo with authentic evidence dossiers for each scenario/dispute
 */
export function getCaseFileMemo(dispute: Dispute): CaseFileMemo {
  const isFraud = dispute.reason === 'fraudulent' || dispute.id.includes('S2');
  const isSubscription =
    dispute.reason === 'subscription_canceled' ||
    dispute.reason === 'canceled_subscription' ||
    dispute.id.includes('S3');
  const isPNR =
    dispute.reason === 'product_not_received' ||
    dispute.id.includes('S1') ||
    (!isFraud && !isSubscription);

  if (isFraud) {
    const exhibits: ExhibitItem[] = [
      {
        letter: 'A',
        title: 'Stripe Radar risk evaluation',
        field: 'customer_communication',
        source: 'Stripe Radar',
        summary: 'Risk score 12/100, 3D Secure authenticated, CVC & AVS postal match',
        status: 'attached',
        dossier: {
          type: 'radar_risk',
          riskScore: 12,
          riskLevel: 'normal',
          threeDSecure: 'authenticated',
          threeDSecureVersion: '3D Secure 2.2.0 (Frictionless flow)',
          avsPostalCheck: 'match',
          avsLine1Check: 'match',
          cvcCheck: 'match',
          ipAddress: '73.189.44.12',
          ipLocation: 'San Francisco, CA (Comcast Cable Communications)',
          chargeId: 'ch_3PiTestCharge441',
        },
      },
      {
        letter: 'B',
        title: 'Merchant checkout terms of service',
        field: 'cancellation_policy',
        source: 'Store checkout policy v2.4',
        summary: 'Accepted by cardholder at checkout with timestamp and IP log',
        status: 'attached',
        dossier: {
          type: 'terms_acceptance',
          version: 'Merchant Terms v2.4',
          effectiveDate: '01 Jan 2026',
          acceptedAt: '2026-08-25 09:15:02 UTC',
          ipAddress: '73.189.44.12',
          userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
          checkboxAcknowledgment: true,
          clauseTitle: '§ 4.2 Authorized Purchaser Affirmation & Dispute Waiver',
          clauseExcerpt: 'Cardholder affirms authorized status and agrees to contact merchant support before initiating card brand chargebacks. Electronic acceptance is recorded with cryptographic transaction binding.',
        },
      },
      {
        letter: 'C',
        title: 'Prior order ledger and customer history',
        field: 'prior_undisputed_transaction_description',
        source: 'Shopify customer ledger',
        summary: '14 prior orders ($4,820 lifetime spend) delivered to verified address',
        status: 'attached',
        dossier: {
          type: 'order_ledger',
          customerName: 'Sarah Jenkins',
          customerId: 'CUST-002',
          membershipStatus: 'VIP Member',
          lifetimeSpendFormatted: '$4,820.00',
          completedOrdersCount: 14,
          disputeHistoryRate: '0.0% historical disputes (first in history)',
          firstOrderDate: '12 Nov 2024',
          lastOrderDate: '18 Aug 2026',
          priorOrders: [
            {
              orderId: 'ORD-940',
              date: '18 Aug 2026',
              amount: '$380.00',
              status: 'Delivered',
              destination: '880 Harrison St, San Francisco, CA 94107',
            },
            {
              orderId: 'ORD-892',
              date: '02 Jul 2026',
              amount: '$410.00',
              status: 'Delivered',
              destination: '880 Harrison St, San Francisco, CA 94107',
            },
            {
              orderId: 'ORD-845',
              date: '15 May 2026',
              amount: '$365.00',
              status: 'Delivered',
              destination: '880 Harrison St, San Francisco, CA 94107',
            },
            {
              orderId: 'ORD-790',
              date: '29 Mar 2026',
              amount: '$425.00',
              status: 'Delivered',
              destination: '880 Harrison St, San Francisco, CA 94107',
            },
          ],
        },
      },
      {
        letter: 'D',
        title: 'Proof of delivery and cardholder signature',
        field: 'shipping_documentation',
        source: 'FedEx tracking #449044301542',
        summary: 'Delivered to 880 Harrison St, San Francisco, CA; signed by cardholder',
        status: 'attached',
        dossier: {
          type: 'carrier_timeline',
          trackingNumber: '449044301542',
          carrier: 'FedEx',
          service: 'FedEx Priority Overnight',
          shippedAt: '2026-08-26T11:00:00Z',
          deliveredAt: '2026-08-29T11:20:00Z',
          signedBy: 'S. JENKINS',
          deliveryLocation: '880 Harrison St, San Francisco, CA 94107',
          events: [
            {
              timestamp: '2026-08-26 11:00 UTC',
              location: 'Springfield, OR',
              status: 'Label created',
              details: 'Shipping label created with destination 880 Harrison St, San Francisco, CA',
            },
            {
              timestamp: '2026-08-27 18:30 UTC',
              location: 'Oakland, CA',
              status: 'In transit',
              details: 'In transit at FedEx Northern California distribution hub',
            },
            {
              timestamp: '2026-08-29 07:15 UTC',
              location: 'San Francisco, CA',
              status: 'Out for delivery',
              details: 'Out for delivery with FedEx courier vehicle #402',
            },
            {
              timestamp: '2026-08-29 11:20 UTC',
              location: 'San Francisco, CA',
              status: 'Delivered',
              details: 'Delivered to commercial reception desk. Signed by: S. JENKINS',
            },
          ],
        },
      },
      {
        letter: 'E',
        title: 'Cardholder signature on file',
        field: 'signature',
        source: 'Stripe charge object',
        summary: 'Missing from Stripe charge object',
        status: 'missing',
        dossier: {
          type: 'missing_evidence',
          reason: 'Card-not-present online transaction',
          disclosure: 'Card-not-present e-commerce purchase executed through 3DS frictionless authentication. Physical sales draft signature is not applicable for web checkout.',
        },
      },
    ];

    return {
      customerName: 'Sarah Jenkins',
      orderRef: 'Order #8841',
      headlineAmount: `$${(dispute.amount_cents / 100).toFixed(2)}`,
      respondByDate: '22 Sep 2026',
      respondByDays: 16,
      briefNarrative:
        'Cardholder Sarah Jenkins disputes transaction of $340.00 citing unauthorized fraud. Internal ledger verification demonstrates an established commercial relationship spanning 14 prior completed orders totaling $4,820.00 lifetime spend, all delivered to the identical verified cardholder address with zero historical disputes. Stripe Radar score was 12/100 (low risk) and AVS postal code returned a full match. Rebuttal recommends defending this claim with high confidence, subject to owner authorization to confirm customer relationship preservation.',
      recommendation: 'Recommend: fight (confidence 92%)',
      exhibits,
      smsText:
        'Alert: Dispute #8841 ($340.00) flagged for VIP Sarah Jenkins ($4,820 spend). Reply 1 to authorize evidence submission, or 2 to refund.',
      smsRecipient: '+1 ••• 4471',
      smsTime: '14:02',
    };
  }

  if (isSubscription) {
    const exhibits: ExhibitItem[] = [
      {
        letter: 'A',
        title: 'Merchant subscription policy terms',
        field: 'cancellation_policy',
        source: 'Store subscription policy v1.8',
        summary: 'Policy mandates full refund upon pre-renewal notice',
        status: 'attached',
        dossier: {
          type: 'terms_acceptance',
          version: 'Store Subscription Agreement v1.8',
          effectiveDate: '01 Jan 2026',
          acceptedAt: '2026-07-28 14:20:00 UTC',
          ipAddress: '67.180.12.94',
          userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
          checkboxAcknowledgment: true,
          clauseTitle: '§ 4.2 Pre-Renewal Cancellation Rights',
          clauseExcerpt: 'Subscription cancellations submitted prior to the recurring billing renewal date must be honored and processed without dispute, administrative charge, or penalty.',
        },
      },
      {
        letter: 'B',
        title: 'Customer cancellation request',
        field: 'customer_communication',
        source: 'Support desk email thread',
        summary: 'Customer requested subscription cancellation prior to renewal charge',
        status: 'attached',
        dossier: {
          type: 'customer_communication',
          threadId: 'TH-1003',
          messages: [
            {
              id: 'MSG-001',
              sender: 'customer',
              channel: 'email',
              timestamp: '2026-08-26 14:30 UTC',
              subject: 'When will it arrive?',
              body: 'Hi, when should I expect order ORD-1001 to arrive? Thanks, Michael',
            },
            {
              id: 'MSG-002',
              sender: 'merchant',
              channel: 'email',
              timestamp: '2026-08-26 16:45 UTC',
              subject: 'Re: When will it arrive?',
              body: 'Hello Michael, your order has shipped via UPS tracking number 1Z9999999999999991 and is scheduled for delivery on August 28th.',
            },
            {
              id: 'MSG-003',
              sender: 'customer',
              channel: 'email',
              timestamp: '2026-08-25 14:10 UTC',
              subject: 'Address change for ORD-1002',
              body: 'Hello, I just placed order ORD-1002 but I am traveling for work. Could you please ship it to my office at 880 Harrison St, San Francisco, CA 94107 instead? Thanks! Jessica Lee',
            },
            {
              id: 'MSG-004',
              sender: 'merchant',
              channel: 'email',
              timestamp: '2026-08-25 15:00 UTC',
              subject: 'Re: Address change for ORD-1002',
              body: 'Hi Jessica, we have updated the shipping address to 880 Harrison St, San Francisco, CA 94107 as requested. Your order is being packed now!',
            },
            {
              id: 'MSG-005',
              sender: 'customer',
              channel: 'email',
              timestamp: '2026-08-28 10:00 UTC',
              subject: 'Cancel subscription ORD-1003',
              body: 'Hi support, please cancel my coffee subscription ORD-1003 before the renewal charge. Thanks, Roberto',
            },
            {
              id: 'MSG-006',
              sender: 'customer',
              channel: 'email',
              timestamp: '2026-08-29 12:00 UTC',
              subject: 'Follow-up on cancellation',
              body: 'I noticed a pending charge on my card for ORD-1003. Please refund this immediately.',
            },
          ],
        },
      },
      {
        letter: 'C',
        title: 'Pre-chargeback inquiry fee avoidance disclosure',
        field: 'uncategorized_text',
        source: 'Visa Pre-Arbitration Inquiry (VPI)',
        summary: 'Scheme inquiry allows concession with $0 dispute fee',
        status: 'attached',
        dossier: {
          type: 'missing_evidence',
          reason: 'Pre-chargeback inquiry phase',
          disclosure: 'Card scheme registered as early inquiry prior to dispute booking. Conceding this inquiry incurs $0 dispute fee, avoiding $15.00 statutory scheme loss fee + chargeback record on merchant account.',
        },
      },
    ];

    return {
      customerName: 'Roberto Alvarez',
      orderRef: 'Order #8842',
      headlineAmount: `$${(dispute.amount_cents / 100).toFixed(2)}`,
      respondByDate: '24 Sep 2026',
      respondByDays: 18,
      briefNarrative:
        'Dispute received as a pre-chargeback inquiry for recurring coffee subscription ORD-1003. Audit trail shows cardholder Roberto Alvarez submitted cancellation request MSG-005 on August 28th, 24 hours prior to recurring billing batch. Under store terms § 4.2, cancellation prior to renewal requires prompt refund. Conceding now incurs $0 dispute fee; contesting risks $15 fee plus likely loss. Rebuttal recommends immediate concession.',
      recommendation: 'Recommend: refund inquiry ($15 fee avoided)',
      exhibits,
      smsText: null,
      smsRecipient: null,
      smsTime: null,
    };
  }

  // Default: PNR (Product Not Received - Michael Okafor / ORD-1001)
  const exhibits: ExhibitItem[] = [
    {
      letter: 'A',
      title: 'Carrier proof of delivery and signature',
      field: 'shipping_documentation',
      source: 'UPS tracking #1Z9999999999999991',
      summary: 'Physical delivery confirmed to 1424 Elm St with recipient signature OKAFOR',
      status: 'attached',
      dossier: {
        type: 'carrier_timeline',
        trackingNumber: '1Z9999999999999991',
        carrier: 'UPS',
        service: 'UPS Ground Commercial',
        shippedAt: '2026-08-25T10:00:00Z',
        deliveredAt: '2026-08-28T14:32:00Z',
        signedBy: 'OKAFOR',
        deliveryLocation: '1424 Elm St, Apt 4B, Austin, TX 78701',
        events: [
          {
            timestamp: '2026-08-25 10:00 UTC',
            location: 'Austin, TX',
            status: 'Label created',
            details: 'Shipping label created, package awaiting carrier pickup',
          },
          {
            timestamp: '2026-08-26 04:15 UTC',
            location: 'Dallas, TX',
            status: 'In transit',
            details: 'Arrived at UPS distribution facility',
          },
          {
            timestamp: '2026-08-28 07:45 UTC',
            location: 'Austin, TX',
            status: 'Out for delivery',
            details: 'Out for delivery with UPS courier',
          },
          {
            timestamp: '2026-08-28 14:32 UTC',
            location: 'Austin, TX',
            status: 'Delivered',
            details: 'Delivered to front desk/mail room. Signed by: OKAFOR',
          },
        ],
      },
    },
    {
      letter: 'B',
      title: 'Signed delivery slip and signature confirmation',
      field: 'receipt',
      source: 'UPS electronic delivery record',
      summary: 'Physical delivery confirmed with signature capture OKAFOR',
      status: 'attached',
      dossier: {
        type: 'delivery_slip',
        signerName: 'Michael Okafor',
        signatureTimestamp: '2026-08-28 14:32:00 UTC',
        deliveryAddress: '1424 Elm St, Apt 4B, Austin, TX 78701',
        trackingNumber: '1Z9999999999999991',
        carrier: 'UPS',
        confirmationCode: 'UPS-SIG-8840-OKAFOR',
        signatureType: 'digital_pad',
        verifiedDeliveryDate: '28 Aug 2026',
      },
    },
    {
      letter: 'C',
      title: 'Customer delivery notification thread',
      field: 'customer_communication',
      source: 'Support desk email thread',
      summary: 'Customer delivery inquiry answered with active UPS tracking reference',
      status: 'attached',
      dossier: {
        type: 'customer_communication',
        threadId: 'TH-1001',
        messages: [
          {
            id: 'MSG-001',
            sender: 'customer',
            channel: 'email',
            timestamp: '2026-08-26 16:00 UTC',
            subject: 'When will it arrive?',
            body: 'Hi, when should I expect order ORD-1001 to arrive? Thanks, Michael',
          },
          {
            id: 'MSG-002',
            sender: 'merchant',
            channel: 'email',
            timestamp: '2026-08-26 16:45 UTC',
            subject: 'Re: When will it arrive?',
            body: 'Hello Michael, your order has shipped via UPS tracking number 1Z9999999999999991 and is scheduled for delivery on August 28th.',
          },
        ],
      },
    },
    {
      letter: 'D',
      title: 'Cardholder non-receipt declaration',
      field: 'customer_communication',
      source: 'Card brand scheme network',
      summary: 'Missing formal cardholder affidavit or written declaration',
      status: 'missing',
      dossier: {
        type: 'missing_evidence',
        reason: 'Missing from issuer filing',
        disclosure: 'Dispute was initiated automatically via scheme code without formal cardholder affidavit or written declaration.',
      },
    },
  ];

  return {
    customerName: 'Michael Okafor',
    orderRef: 'Order #8840',
    headlineAmount: `$${(dispute.amount_cents / 100).toFixed(2)}`,
    respondByDate: '20 Sep 2026',
    respondByDays: 14,
    briefNarrative:
      'Cardholder claims goods were not received. Carrier tracking scan from UPS confirms physical delivery directly to cardholder documented shipping address in Austin, TX, with direct signature confirmation matching claimant name. Counter-evidence packet assembled and submitted to card scheme automatically under merchant rule threshold (< $100).',
    recommendation: 'Recommend: fight (confidence 98%)',
    exhibits,
    smsText: null,
    smsRecipient: null,
    smsTime: null,
  };
}
