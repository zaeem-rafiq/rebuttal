import React from 'react';
import { Order } from '@/lib/types';
import { Package, Truck, MessageSquare, CheckCircle, AlertTriangle } from 'lucide-react';

interface EvidencePacketProps {
  order?: Order;
}

export const EvidencePacket: React.FC<EvidencePacketProps> = ({ order }) => {
  if (!order) {
    return (
      <div className="bg-surface border border-border rounded-xs p-6 text-center text-docket-text-muted">
        <Package className="h-6 w-6 mx-auto mb-2 text-docket-gold/60" />
        <p className="text-xs font-serif font-medium text-docket-text">No Linked Fulfillment File</p>
        <p className="text-[11px] text-docket-text-muted mt-1 font-mono">Direct transaction without associated commercial catalog record.</p>
      </div>
    );
  }

  const shipment = order.shipments && order.shipments.length > 0 ? order.shipments[0] : null;

  return (
    <div className="space-y-3.5">
      {/* Order & Customer Dossier */}
      <div className="bg-surface border border-border rounded-xs p-4 space-y-3 shadow-xs">
        <div className="flex items-center justify-between border-b border-border pb-2.5">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider text-docket-text-muted">Order Reference</span>
            <p className="text-sm font-bold text-docket-text font-mono">{order.id}</p>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-mono uppercase tracking-wider text-docket-text-muted">Settled Volume</span>
            <p className="text-sm font-bold text-docket-gold font-mono tabular-nums">${(order.amount_cents / 100).toFixed(2)}</p>
          </div>
        </div>

        {order.customer && (
          <div className="text-xs space-y-0.5">
            <p className="text-docket-text font-serif font-medium text-sm">{order.customer.name}</p>
            <p className="text-docket-text-muted font-mono text-[11px]">{order.customer.email}</p>
            {order.customer.phone && (
              <p className="text-docket-text-muted font-mono text-[11px]">{order.customer.phone}</p>
            )}
          </div>
        )}

        {order.items && order.items.length > 0 && (
          <div className="pt-2.5 border-t border-border">
            <span className="text-xs font-mono uppercase tracking-wider text-docket-text-muted">
              Purchased Line Items
            </span>
            <div className="mt-1.5 space-y-1">
              {order.items.map((item) => (
                <div key={item.id} className="flex justify-between text-xs text-docket-text-secondary">
                  <span>
                    <span className="font-mono text-docket-text-muted">{item.quantity}x</span> {item.product_name}
                  </span>
                  <span className="font-mono tabular-nums text-docket-text-muted">
                    ${(item.total_price_cents / 100).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {shipment && (
        <div className="bg-surface border border-border rounded-xs p-4 space-y-3 shadow-xs">
          <div className="flex items-center justify-between border-b border-border pb-2.5">
            <div className="flex items-center space-x-2">
              <Truck className="h-4 w-4 text-status-won" />
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-docket-text">
                {shipment.carrier} Carrier Dossier
              </span>
            </div>
            <span className="text-xs font-mono font-bold text-docket-gold">
              {shipment.tracking_number}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center text-docket-text-secondary font-mono">
              <span className="text-docket-text-muted text-[11px]">Delivery Status:</span>
              <span className="font-semibold text-status-won capitalize">{shipment.status.replace('_', ' ')}</span>
            </div>
            {shipment.delivered_at && (
              <div className="flex justify-between items-center text-docket-text-secondary font-mono">
                <span className="text-docket-text-muted text-[11px]">Carrier Timestamp:</span>
                <span className="tabular-nums text-docket-text text-[11px]">{new Date(shipment.delivered_at).toLocaleString()}</span>
              </div>
            )}
            {shipment.signed_by && (
              <div className="flex justify-between items-center text-docket-text-secondary font-mono">
                <span className="text-docket-text-muted text-[11px]">Recipient Signature Seal:</span>
                <span className="text-[11px] font-bold text-status-won bg-status-won/15 px-2 py-0.5 rounded-xs border border-status-won/30">
                  ✓ {shipment.signed_by}
                </span>
              </div>
            )}
          </div>

          {shipment.events && shipment.events.length > 0 && (
            <div className="pt-2.5 border-t border-border">
              <span className="text-[10px] font-mono uppercase tracking-wider text-docket-text-muted">
                Carrier Scan Ledger
              </span>
              <div className="mt-2 space-y-2 font-mono">
                {shipment.events.map((ev) => (
                  <div key={ev.id} className="text-[11px] text-docket-text-muted flex items-start space-x-2">
                    <CheckCircle className="h-3.5 w-3.5 text-status-won shrink-0 mt-0.5" />
                    <div>
                      <p className="text-docket-text font-medium">{ev.details || ev.status}</p>
                      <p className="text-[10px] text-docket-text-muted tabular-nums">
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
        <div className="bg-surface border border-border rounded-xs p-4 space-y-3 shadow-xs">
          <div className="flex items-center space-x-2 border-b border-border pb-2.5">
            <MessageSquare className="h-4 w-4 text-docket-gold" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-docket-text">
              Customer Communications
            </span>
          </div>

          <div className="space-y-2.5">
            {order.messages.map((msg) => (
              <div
                key={msg.id}
                className="p-3 rounded-xs border border-border bg-canvas text-xs leading-relaxed"
              >
                <div className="flex items-center justify-between text-[10px] text-docket-text-muted mb-1 font-mono">
                  <span>{msg.direction} via {msg.channel}</span>
                  <span className="tabular-nums">{new Date(msg.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                {msg.subject && <p className="font-serif font-semibold text-docket-text mb-0.5">{msg.subject}</p>}
                <p className="text-docket-text-secondary font-sans">{msg.body}</p>
                {msg.has_shipping_change && (
                  <div className="mt-2 flex items-center space-x-1.5 text-[11px] text-docket-gold bg-docket-gold/10 p-1.5 rounded-xs border border-docket-gold/30 font-medium font-mono">
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
