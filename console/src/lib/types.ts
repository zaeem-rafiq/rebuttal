export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  shipping_address?: Record<string, unknown>;
  customer_value: 'new' | 'repeat' | 'vip';
  order_count: number;
  lifetime_value_cents: number;
}

export interface OrderItem {
  id: string;
  product_name: string;
  sku?: string;
  quantity: number;
  unit_price_cents: number;
  total_price_cents: number;
}

export interface ShipmentEvent {
  id: string;
  timestamp: string;
  status: string;
  location?: string;
  details?: string;
}

export interface Shipment {
  id: string;
  carrier: string;
  tracking_number: string;
  status: string;
  shipped_at: string;
  delivered_at?: string;
  signed_by?: string;
  events?: ShipmentEvent[];
}

export interface CustomerMessage {
  id: string;
  direction: 'inbound' | 'outbound';
  channel: string;
  subject?: string;
  body: string;
  has_shipping_change: boolean;
  created_at: string;
}

export interface Order {
  id: string;
  customer_id: string;
  amount_cents: number;
  currency: string;
  status: string;
  payment_intent_id?: string;
  charge_id?: string;
  card_brand?: string;
  card_last4?: string;
  avs_postal_match?: string;
  cvc_match?: string;
  customer?: Customer;
  items?: OrderItem[];
  shipments?: Shipment[];
  messages?: CustomerMessage[];
}

export interface Decision {
  id: string;
  dispute_id: string;
  action: 'fight' | 'concede' | 'refund_inquiry';
  win_probability: number;
  expected_value_cents: number;
  evidence_strength: 'weak' | 'mixed' | 'strong';
  customer_value: 'new' | 'repeat' | 'vip';
  rationale?: string;
  owner_summary?: string;
  status: 'pending' | 'approved' | 'executed' | 'overridden';
  created_at: string;
  approved_at?: string;
  answered_at?: string;
  executed_at?: string;
}

export interface AuditLogEntry {
  id: string;
  dispute_id: string;
  action: string;
  actor: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface Dispute {
  id: string;
  order_id?: string;
  payment_intent_id?: string;
  charge_id?: string;
  amount_cents: number;
  currency: string;
  reason: string;
  status: 'needs_response' | 'warning_needs_response' | 'under_review' | 'charge_refunded' | 'refunded_inquiry' | 'won' | 'lost';
  evidence_due_by?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  decision?: Decision;
  order?: Order;
}

export interface CarrierTimelineDossier {
  type: 'carrier_timeline';
  trackingNumber: string;
  carrier: string;
  service?: string;
  shippedAt: string;
  deliveredAt?: string;
  signedBy?: string;
  deliveryLocation: string;
  events: Array<{
    timestamp: string;
    location: string;
    status: string;
    details?: string;
  }>;
}

export interface SignedDeliverySlipDossier {
  type: 'delivery_slip';
  signerName: string;
  signatureTimestamp: string;
  deliveryAddress: string;
  trackingNumber: string;
  carrier: string;
  confirmationCode: string;
  signatureType: 'digital_pad' | 'physical_scan';
  verifiedDeliveryDate: string;
}

export interface RadarRiskDossier {
  type: 'radar_risk';
  riskScore: number;
  riskLevel: 'normal' | 'elevated' | 'highest';
  threeDSecure: 'authenticated' | 'attempted' | 'not_supported';
  threeDSecureVersion?: string;
  avsPostalCheck: 'match' | 'mismatch' | 'unchecked';
  avsLine1Check: 'match' | 'mismatch' | 'unchecked';
  cvcCheck: 'match' | 'mismatch' | 'unchecked';
  ipAddress: string;
  ipLocation: string;
  chargeId: string;
}

export interface TermsAcceptanceDossier {
  type: 'terms_acceptance';
  version: string;
  effectiveDate: string;
  acceptedAt: string;
  ipAddress: string;
  userAgent: string;
  checkboxAcknowledgment: boolean;
  clauseTitle: string;
  clauseExcerpt: string;
}

export interface CustomerCommunicationDossier {
  type: 'customer_communication';
  threadId: string;
  messages: Array<{
    id: string;
    sender: 'customer' | 'merchant';
    channel: 'email' | 'sms';
    timestamp: string;
    subject?: string;
    body: string;
  }>;
}

export interface OrderLedgerDossier {
  type: 'order_ledger';
  customerName: string;
  customerId: string;
  membershipStatus: string;
  lifetimeSpendFormatted: string;
  completedOrdersCount: number;
  disputeHistoryRate: string;
  firstOrderDate: string;
  lastOrderDate: string;
  priorOrders: Array<{
    orderId: string;
    date: string;
    amount: string;
    status: string;
    destination: string;
  }>;
}

export interface MissingEvidenceDossier {
  type: 'missing_evidence';
  reason: string;
  disclosure: string;
}

export type ExhibitDossier =
  | CarrierTimelineDossier
  | SignedDeliverySlipDossier
  | RadarRiskDossier
  | TermsAcceptanceDossier
  | CustomerCommunicationDossier
  | OrderLedgerDossier
  | MissingEvidenceDossier;

export interface ExhibitItem {
  letter: string;
  title: string;
  field: string;
  source: string;
  summary: string;
  status: 'attached' | 'missing';
  dossier?: ExhibitDossier;
}

export interface CaseFileMemo {
  customerName: string;
  orderRef: string;
  headlineAmount: string;
  respondByDate: string;
  respondByDays: number;
  briefNarrative: string;
  recommendation: string;
  exhibits: ExhibitItem[];
  smsText: string | null;
  smsRecipient: string | null;
  smsTime: string | null;
}
