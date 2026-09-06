import React from 'react';
import { Order } from '@/lib/types';
import { Package, Truck, MessageSquare, CheckCircle, AlertTriangle } from 'lucide-react';

interface EvidencePacketProps {
  order?: Order;
}

export const EvidencePacket: React.FC<EvidencePacketProps> = ({ order }) => {
  if (!order) {
    return (
      <div className="bg-surface-card border border-surface-border rounded-lg p-6 text-center text-text-muted">
        <Package className="h-5 w-5 mx-auto mb-2 text-text-muted" />
        <p className="text-xs font-semibold text-text-primary">No Linked Order File</p>
        <p className="text-[11px] text-text-muted mt-1">No order record was linked to this dispute event.</p>
      </div>
    );
  }

  const shipment = order.shipments && order.shipments.length > 0 ? order.shipments[0] : null;

  return (
    <div className="space-y-3.5">
      {/* Order & Customer Dossier */}
      <div className="bg-surface-card border border-surface-border rounded-lg p-4 space-y-3 shadow-xs">
        <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
          <div>
            <span className="text-[11px] font-mono text-text-muted">Order Reference</span>
            <p className="text-sm font-bold text-text-primary font-mono">{order.id}</p>
          </div>
          <div className="text-right">
            <span className="text-[11px] font-mono text-text-muted">Settled Total</span>
            <p className="text-sm font-bold text-brand-primary font-mono tabular-nums">${(order.amount_cents / 100).toFixed(2)}</p>
          </div>
        </div>

        {order.customer && (
          <div className="text-xs space-y-0.5">
            <p className="text-text-primary font-medium">{order.customer.name}</p>
            <p className="text-text-muted font-mono text-[11px]">{order.customer.email}</p>
            {order.customer.phone && (
              <p className="text-text-muted font-mono text-[11px]">{order.customer.phone}</p>
            )}
          </div>
        )}

        {order.items && order.items.length > 0 && (
          <div className="pt-2.5 border-t border-surface-border">
            <span className="text-xs font-medium text-text-muted">
              Purchased Line Items
            </span>
            <div className="mt-1.5 space-y-1">
              {order.items.map((item) => (
                <div key={item.id} className="flex justify-between text-xs text-text-secondary">
                  <span>
                    <span className="font-mono text-text-muted">{item.quantity}x</span> {item.product_name}
                  </span>
                  <span className="font-mono tabular-nums text-text-muted">
                    ${(item.total_price_cents / 100).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {shipment && (
        <div className="bg-surface-card border border-surface-border rounded-lg p-4 space-y-3 shadow-xs">
          <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
            <div className="flex items-center space-x-2">
              <Truck className="h-4 w-4 text-status-won-text" />
              <span className="text-xs font-semibold text-text-primary">
                {shipment.carrier} Carrier Dossier
              </span>
            </div>
            <span className="text-xs font-mono font-bold text-brand-primary">
              {shipment.tracking_number}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center text-text-secondary">
              <span className="text-text-muted text-[11px]">Delivery Status:</span>
              <span className="font-mono font-semibold text-status-won-text capitalize">{shipment.status.replace('_', ' ')}</span>
            </div>
            {shipment.delivered_at && (
              <div className="flex justify-between items-center text-text-secondary">
                <span className="text-text-muted text-[11px]">Carrier Timestamp:</span>
                <span className="font-mono tabular-nums text-text-primary text-[11px]">{new Date(shipment.delivered_at).toLocaleString()}</span>
              </div>
            )}
            {shipment.signed_by && (
              <div className="flex justify-between items-center text-text-secondary">
                <span className="text-text-muted text-[11px]">Recipient Signature Seal:</span>
                <span className="font-mono text-[11px] font-bold text-status-won-text bg-status-won-bg px-2 py-0.5 rounded border border-status-won-border">
                  ✓ {shipment.signed_by}
                </span>
              </div>
            )}
          </div>

          {shipment.events && shipment.events.length > 0 && (
            <div className="pt-2.5 border-t border-surface-border">
              <span className="text-xs font-medium text-text-muted">
                Carrier Scan Ledger
              </span>
              <div className="mt-2 space-y-2">
                {shipment.events.map((ev) => (
                  <div key={ev.id} className="text-[11px] text-text-muted flex items-start space-x-2">
                    <CheckCircle className="h-3.5 w-3.5 text-status-won-text shrink-0 mt-0.5" />
                    <div>
                      <p className="text-text-primary font-medium">{ev.details || ev.status}</p>
                      <p className="text-[10px] text-text-muted font-mono tabular-nums">
                        {ev.location} ({new Date(ev.timestamp).toLocaleString()})
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Customer Comms */}
      {order.messages && order.messages.length > 0 && (
        <div className="bg-surface-card border border-surface-border rounded-lg p-4 space-y-3 shadow-xs">
          <div className="flex items-center space-x-2 border-b border-surface-border pb-2.5">
            <MessageSquare className="h-4 w-4 text-brand-primary" />
            <span className="text-xs font-semibold text-text-primary">
              Customer Communications
            </span>
          </div>

          <div className="space-y-2.5">
            {order.messages.map((msg) => (
              <div
                key={msg.id}
                className="p-3 rounded-md border border-surface-border bg-canvas-base text-xs leading-relaxed"
              >
                <div className="flex items-center justify-between text-[10px] text-text-muted mb-1 font-mono">
                  <span>{msg.direction} via {msg.channel}</span>
                  <span className="tabular-nums">{new Date(msg.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                {msg.subject && <p className="font-semibold text-text-primary mb-0.5">{msg.subject}</p>}
                <p className="text-text-secondary">{msg.body}</p>
                {msg.has_shipping_change && (
                  <div className="mt-2 flex items-center space-x-1.5 text-[11px] text-status-review-text bg-status-review-bg p-1.5 rounded border border-status-review-border font-medium font-mono">
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                    <span>Customer requested alternate shipping address in message</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
