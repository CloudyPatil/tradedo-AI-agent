// E:\tradedo\app\frontend\components\manual\order-history.tsx

"use client";

import { useManualOrders } from "@/lib/hooks/use-manual";
import { History } from "lucide-react";
import { formatTime, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function OrderHistory() {
  const { data, isLoading } = useManualOrders("all");

  // Filter to only show FILLED and CANCELLED (non-pending)
  const orders = (data?.orders || []).filter((o: any) => o.status !== "PENDING").slice(0, 20);

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets h-full">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">ORDER HISTORY</h3>
          <span className="text-xs text-muted-foreground">({orders.length})</span>
        </div>
      </div>

      {isLoading ? (
        <div className="p-4 space-y-2">
          {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-12" />)}
        </div>
      ) : orders.length === 0 ? (
        <div className="p-8 text-center text-sm text-muted-foreground">
          No order history
        </div>
      ) : (
        <div className="max-h-80 overflow-y-auto">
          {orders.map((order: any) => (
            <HistoryRow key={order.id} order={order} />
          ))}
        </div>
      )}
    </div>
  );
}

function HistoryRow({ order }: any) {
  const cleanSymbol = order.symbol.replace(".NS", "");
  const isBuy = order.side === "BUY";
  const isFilled = order.status === "FILLED";

  const statusColors: Record<string, string> = {
    FILLED:    "text-bull bg-bull/10",
    CANCELLED: "text-muted-foreground bg-muted",
    REJECTED:  "text-bear bg-bear/10",
    PARTIAL:   "text-neutral bg-neutral/10",
  };

  return (
    <div className="p-3 border-t border-border hover:bg-accent/30 transition-colors">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <span className="font-mono font-bold text-sm">{cleanSymbol}</span>
          <span className={cn(
            "text-[10px] px-2 py-0.5 rounded font-bold",
            isBuy ? "bg-bull/10 text-bull" : "bg-bear/10 text-bear"
          )}>
            {order.side}
          </span>
        </div>

        <span className={cn(
          "text-[10px] px-2 py-0.5 rounded font-bold",
          statusColors[order.status]
        )}>
          {order.status}
        </span>
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-2 text-muted-foreground">
          <span>{order.quantity} shares</span>
          {order.avg_fill_price && (
            <>
              <span>@</span>
              <span className="font-mono font-bold text-foreground">
                ₹{order.avg_fill_price.toFixed(2)}
              </span>
            </>
          )}
        </div>
        <span className="text-[10px] text-muted-foreground font-mono">
          {formatTime(order.filled_at || order.cancelled_at || order.created_at)}
        </span>
      </div>
    </div>
  );
}