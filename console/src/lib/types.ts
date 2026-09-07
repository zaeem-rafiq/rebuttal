export interface Customer {
  id: string;
  name: string;
  email: string;
  phone?: string;
  shipping_address?: Record<string, any>;
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
  details: Record<string, any>;
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
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  decision?: Decision;
  order?: Order;
}
