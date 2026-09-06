import React from 'react';
import { Order } from '@/lib/types';
import { Package, Truck, MessageSquare, CheckCircle, AlertTriangle } from 'lucide-react';

interface EvidencePacketProps {
  order?: Order;
}

export const EvidencePacket: React.FC<EvidencePacketProps> = ({ order }) => {
  if (!order) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-center text-slate-400">
        <Package className="h-6 w-6 mx-auto mb-2 text-slate-600" />
        <p className="text-sm">No linked order found for this dispute.</p>
      </div>
    );
  }

  const shipment = order.shipments && order.shipments.length > 0 ? order.shipments[0] : null;

  return (
    <div className="space-y-4">
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
          <div>
            <span className="text-[10px] font-mono text-slate-400 uppercase">Order ID</span>
            <p className="text-sm font-bold text-slate-200 font-mono">{order.id}</p>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-mono text-slate-400 uppercase">Total</span>
            <p className="text-sm font-bold text-indigo-400 font-mono">${(order.amount_cents / 100).toFixed(2)}</p>
          </div>
        </div>

        {order.customer && (
          <div className="text-xs space-y-1">
            <p className="text-slate-300 font-medium">{order.customer.name}</p>
            <p className="text-slate-400 font-mono text-[11px]">{order.customer.email}</p>
            {order.customer.phone && (
              <p className="text-slate-400 font-mono text-[11px]">{order.customer.phone}</p>
            )}
          </div>
        )}

        {order.items && order.items.length > 0 && (
          <div className="pt-2 border-t border-slate-800/80">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              Purchased Items
            </span>
            <div className="mt-1.5 space-y-1">
              {order.items.map((item) => (
                <div key={item.id} className="flex justify-between text-xs text-slate-300">
                  <span>
                    {item.quantity}x {item.product_name}
                  </span>
                  <span className="font-mono text-slate-400">
                    ${(item.total_price_cents / 100).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {shipment && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center space-x-2">
              <Truck className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-semibold text-slate-200">
                {shipment.carrier.toUpperCase()} Tracking
              </span>
            </div>
            <span className="text-xs font-mono font-semibold text-indigo-400">
              {shipment.tracking_number}
            </span>
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-400">Status:</span>
              <span className="font-semibold text-emerald-400 capitalize">{shipment.status.replace('_', ' ')}</span>
            </div>
            {shipment.delivered_at && (
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Delivered At:</span>
                <span className="font-mono text-slate-200">{new Date(shipment.delivered_at).toLocaleString()}</span>
              </div>
            )}
            {shipment.signed_by && (
              <div className="flex justify-between text-slate-300">
                <span className="text-slate-400">Signed Confirmation:</span>
                <span className="font-semibold text-emerald-300 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                  ✓ {shipment.signed_by}
                </span>
              </div>
            )}
          </div>

          {shipment.events && shipment.events.length > 0 && (
            <div className="pt-2 border-t border-slate-800">
              <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                Carrier Scan Events
              </span>
              <div className="mt-2 space-y-2">
                {shipment.events.map((ev) => (
                  <div key={ev.id} className="text-[11px] text-slate-400 flex items-start space-x-2">
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-slate-200 font-medium">{ev.details || ev.status}</p>
                      <p className="text-[10px] text-slate-400 font-mono">
                        {ev.location} · {new Date(ev.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {order.messages && order.messages.length > 0 && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-3">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
            <MessageSquare className="h-4 w-4 text-sky-400" />
            <span className="text-xs font-semibold text-slate-200">Customer Communication History</span>
          </div>

          <div className="space-y-2.5">
            {order.messages.map((msg) => (
              <div
                key={msg.id}
                className={`p-3 rounded-xl border text-xs leading-relaxed ${
                  msg.direction === 'inbound'
                    ? 'bg-slate-950/80 border-slate-800 text-slate-200'
                    : 'bg-indigo-950/40 border-indigo-900/50 text-indigo-200 ml-3'
                }`}
              >
                <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                  <span className="font-semibold uppercase">{msg.direction} ({msg.channel})</span>
                  <span>{new Date(msg.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                {msg.subject && <p className="font-semibold text-white mb-1">{msg.subject}</p>}
                <p>{msg.body}</p>
                {msg.has_shipping_change && (
                  <div className="mt-2 flex items-center space-x-1.5 text-[11px] text-amber-300 bg-amber-950/60 p-1.5 rounded-lg border border-amber-800/50">
                    <AlertTriangle className="h-3 w-3 shrink-0" />
                    <span>Customer requested shipping address change via message</span>
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
