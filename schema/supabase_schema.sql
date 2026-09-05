-- =============================================================================
-- Rebuttal Synthetic World - Supabase Schema
-- Issue: HAC-3 (R-01)
-- Tables:
--   1. customers
--   2. orders
--   3. order_items
--   4. shipments
--   5. shipment_events
--   6. customer_messages
--   7. disputes
--   8. decisions
--   9. audit_log
--   10. merchant_policy
-- =============================================================================

-- Enable UUID extension if available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. customers
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    shipping_address JSONB NOT NULL DEFAULT '{}'::jsonb,
    billing_address JSONB NOT NULL DEFAULT '{}'::jsonb,
    customer_value TEXT NOT NULL DEFAULT 'new' CHECK (customer_value IN ('new', 'repeat', 'vip')),
    order_count INTEGER NOT NULL DEFAULT 0,
    lifetime_value_cents BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 2. orders
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    currency TEXT NOT NULL DEFAULT 'usd',
    status TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')),
    payment_intent_id TEXT,
    charge_id TEXT,
    card_brand TEXT,
    card_last4 TEXT,
    avs_postal_match TEXT DEFAULT 'match',
    cvc_match TEXT DEFAULT 'match',
    shipping_address JSONB NOT NULL DEFAULT '{}'::jsonb,
    billing_address JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 3. order_items
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    sku TEXT,
    quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    total_price_cents INTEGER NOT NULL CHECK (total_price_cents >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 4. shipments
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shipments (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    carrier TEXT NOT NULL,
    tracking_number TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'label_created' CHECK (status IN ('label_created', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned')),
    shipped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at TIMESTAMPTZ,
    signed_by TEXT,
    shipping_address JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 5. shipment_events
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shipment_events (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL,
    location TEXT,
    details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 6. customer_messages
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_messages (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_id TEXT REFERENCES orders(id) ON DELETE SET NULL,
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    channel TEXT NOT NULL DEFAULT 'email' CHECK (channel IN ('email', 'sms', 'chat')),
    subject TEXT,
    body TEXT NOT NULL,
    has_shipping_change BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 7. disputes
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS disputes (
    id TEXT PRIMARY KEY,
    order_id TEXT REFERENCES orders(id) ON DELETE SET NULL,
    payment_intent_id TEXT,
    charge_id TEXT,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    currency TEXT NOT NULL DEFAULT 'usd',
    reason TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('needs_response', 'warning_needs_response', 'under_review', 'charge_refunded', 'won', 'lost')),
    evidence_due_by TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 8. decisions
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    dispute_id TEXT NOT NULL REFERENCES disputes(id) ON DELETE CASCADE,
    action TEXT NOT NULL CHECK (action IN ('fight', 'concede', 'refund_inquiry')),
    win_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (win_probability >= 0.0 AND win_probability <= 1.0),
    expected_value_cents INTEGER NOT NULL DEFAULT 0,
    evidence_strength TEXT NOT NULL DEFAULT 'mixed' CHECK (evidence_strength IN ('weak', 'mixed', 'strong')),
    customer_value TEXT NOT NULL DEFAULT 'new' CHECK (customer_value IN ('new', 'repeat', 'vip')),
    rationale TEXT,
    owner_summary TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'executed', 'overridden')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at TIMESTAMPTZ,
    answered_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ
);

-- -----------------------------------------------------------------------------
-- 9. audit_log
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    dispute_id TEXT REFERENCES disputes(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- 10. merchant_policy
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS merchant_policy (
    id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    approval_amount_cents INTEGER NOT NULL DEFAULT 20000,
    min_win_probability_to_fight DOUBLE PRECISION NOT NULL DEFAULT 0.50,
    always_concede_under_cents INTEGER NOT NULL DEFAULT 1500,
    vip_concede_max_cents INTEGER NOT NULL DEFAULT 50000,
    silence_action TEXT NOT NULL DEFAULT 'fight' CHECK (silence_action IN ('fight', 'concede')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_payment_intent_id ON orders(payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_order_id ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_tracking_number ON shipments(tracking_number);
CREATE INDEX IF NOT EXISTS idx_shipment_events_shipment_id ON shipment_events(shipment_id);
CREATE INDEX IF NOT EXISTS idx_customer_messages_customer_id ON customer_messages(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_messages_order_id ON customer_messages(order_id);
CREATE INDEX IF NOT EXISTS idx_disputes_order_id ON disputes(order_id);
CREATE INDEX IF NOT EXISTS idx_disputes_payment_intent_id ON disputes(payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_decisions_dispute_id ON decisions(dispute_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_dispute_id ON audit_log(dispute_id);
