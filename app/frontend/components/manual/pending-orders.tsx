// E:\tradedo\app\frontend\components\manual\pending-orders.tsx

"use client";

import { useManualOrders, useCancelOrder } from "@/lib/hooks/use-manual";
import { Clock, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatTime, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function PendingOrders() {
  const { data, isLoading } = useManualOrders("PENDING");
  const cancelMutation = useCancelOrder();

  const orders = data?.orders || [];

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets h-full">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">PENDING ORDERS</h3>
          <span className="text-xs text-muted-foreground">({orders.length})</span>
        </div>
      </div>

      {isLoading ? (
        <div className="p-4 space-y-2">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-12" />)}
        </div>
      ) : orders.length === 0 ? (
        <div className="p-8 text-center text-sm text-muted-foreground">
          No pending orders
        </div>
      ) : (
        <div className="max-h-80 overflow-y-auto">
          {orders.map((order: any) => (
            <OrderRow 
              key={order.id} 
              order={order} 
              onCancel={() => cancelMutation.mutate(order.id)}
              isCancelling={cancelMutation.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function OrderRow({ order, onCancel, isCancelling }: any) {
  const cleanSymbol = order.symbol.replace(".NS", "");
  const isBuy = order.side === "BUY";

  return (
    <div className="p-3 border-t border-border hover:bg-accent/30 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="font-mono font-bold text-sm">{cleanSymbol}</span>
          <span className={cn(
            "text-[10px] px-2 py-0.5 rounded font-bold",
            isBuy ? "bg-bull/10 text-bull" : "bg-bear/10 text-bear"
          )}>
            {order.side}
          </span>
          <span className="text-[10px] px-2 py-0.5 bg-brand/10 text-brand rounded font-bold">
            {order.order_type}
          </span>
        </div>

        <Button
          size="sm"
          variant="ghost"
          className="h-6 w-6 p-0 text-bear hover:bg-bear/10"
          onClick={onCancel}
          disabled={isCancelling}
        >
          {isCancelling ? <Loader2 className="animate-spin" size={10} /> : <X size={10} />}
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <p className="text-[10px] text-muted-foreground">QTY</p>
          <p className="font-mono font-bold">{order.quantity}</p>
        </div>
        {order.price && (
          <div>
            <p className="text-[10px] text-muted-foreground">PRICE</p>
            <p className="font-mono font-bold">₹{order.price}</p>
          </div>
        )}
        {order.trigger_price && (
          <div>
            <p className="text-[10px] text-muted-foreground">TRIGGER</p>
            <p className="font-mono font-bold">₹{order.trigger_price}</p>
          </div>
        )}
      </div>

      <p className="text-[10px] text-muted-foreground mt-2 font-mono">
        {formatTime(order.created_at)}
      </p>
    </div>
  );
}