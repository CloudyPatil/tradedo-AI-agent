// E:\tradedo\app\frontend\components\manual\open-positions.tsx

"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useManualTrades, useClosePosition } from "@/lib/hooks/use-manual";
import { api } from "@/lib/api/client";
import { Briefcase, TrendingUp, TrendingDown, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { TradeModal } from "./trade-modal";

export function OpenPositions() {
  const { data, isLoading } = useManualTrades("OPEN");
  const closeMutation = useClosePosition();
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [modalSide, setModalSide] = useState<"BUY" | "SELL">("SELL");

  const trades = data?.trades || [];

  const handleQuickSell = (symbol: string) => {
    setSelectedSymbol(symbol);
    setModalSide("SELL");
    setModalOpen(true);
  };

  const handleQuickBuy = (symbol: string) => {
    setSelectedSymbol(symbol);
    setModalSide("BUY");
    setModalOpen(true);
  };

  return (
    <>
      <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Briefcase size={16} className="text-brand" />
            <h3 className="text-sm font-bold tracking-wider">OPEN POSITIONS</h3>
            <span className="text-xs text-muted-foreground">({trades.length})</span>
          </div>
          <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
            <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse" />
            <span>LIVE P&L</span>
          </div>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-2">
            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-14" />)}
          </div>
        ) : trades.length === 0 ? (
          <div className="p-12 text-center">
            <Briefcase className="mx-auto text-muted-foreground mb-3" size={32} />
            <p className="text-sm text-muted-foreground">No open positions</p>
            <p className="text-xs text-muted-foreground mt-1">
              Place an order to start trading
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-accent/30">
              <tr>
                <th className="text-left px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">SYMBOL</th>
                <th className="text-center px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">DIR</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">QTY</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">AVG</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">CMP</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">INVESTED</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">CURRENT</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">P&L</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">P&L %</th>
                <th className="text-center px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade: any) => (
                <PositionRow 
                  key={trade.id} 
                  trade={trade}
                  onBuy={() => handleQuickBuy(trade.symbol)}
                  onSell={() => handleQuickSell(trade.symbol)}
                  onClose={() => closeMutation.mutate(trade.id)}
                  isClosing={closeMutation.isPending}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      <TradeModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        symbol={selectedSymbol}
        defaultSide={modalSide}
      />
    </>
  );
}

// UPDATE PositionRow function in open-positions.tsx

function PositionRow({ trade, onBuy, onSell, onClose, isClosing }: any) {
  const isLong = trade.direction === "LONG";
  const cleanSymbol = trade.symbol.replace(".NS", "");
  const currentPrice = trade.current_price || trade.entry_price;
  const investment = trade.investment || 0;
  const currentValue = trade.quantity * currentPrice;
  const pnl = trade.unrealized_pnl || 0;
  const pnlPct = investment > 0 ? (pnl / investment) * 100 : 0;
  const isProfit = pnl >= 0;

  // Fetch product type from order
  const { data: orderData } = useQuery({
    queryKey: ["order", trade.entry_order_id],
    queryFn: () => trade.entry_order_id 
      ? api.get(`/manual/orders`).then(r => 
          r.data.orders?.find((o: any) => o.id === trade.entry_order_id)
        )
      : null,
    enabled: !!trade.entry_order_id,
    staleTime: Infinity,
  });

  const productType = orderData?.product_type || "INTRADAY";
  const isIntraday = productType === "INTRADAY";

  // Calculate hold time
  const entryTime = new Date(trade.entry_time);
  const now = new Date();
  const hoursHeld = Math.floor((now.getTime() - entryTime.getTime()) / (1000 * 60 * 60));
  const daysHeld = Math.floor(hoursHeld / 24);
  
  const holdTimeStr = daysHeld > 0 
    ? `${daysHeld}d ${hoursHeld % 24}h`
    : hoursHeld > 0 
      ? `${hoursHeld}h ${Math.floor(((now.getTime() - entryTime.getTime()) / (1000 * 60)) % 60)}m`
      : `${Math.floor((now.getTime() - entryTime.getTime()) / (1000 * 60))}m`;

  return (
    <tr className="border-t border-border hover:bg-accent/30 transition-colors">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <Link 
            href={`/stock/${cleanSymbol}`}
            className="font-mono font-bold text-sm hover:text-brand"
          >
            {cleanSymbol}
          </Link>
          {/* Product Type Badge */}
          <span className={cn(
            "text-[9px] px-1.5 py-0.5 rounded font-bold",
            isIntraday 
              ? "bg-brand/10 text-brand" 
              : "bg-bull/10 text-bull"
          )}>
            {isIntraday ? "MIS" : "CNC"}
          </span>
        </div>
        <p className="text-[10px] text-muted-foreground">
          {trade.sector} · {holdTimeStr}
          {isIntraday && (
            <span className="ml-1 text-neutral">· EOD 3:15 PM</span>
          )}
        </p>
      </td>

      <td className="px-4 py-3 text-center">
        <div className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold",
          isLong ? "text-bull bg-bull/10" : "text-bear bg-bear/10"
        )}>
          {isLong ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
          {trade.direction}
        </div>
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
        {trade.quantity}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
        ₹{trade.entry_price?.toFixed(2)}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm font-bold">
        ₹{currentPrice?.toFixed(2)}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
        {formatCurrency(investment, 0)}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
        {formatCurrency(currentValue, 0)}
      </td>

      <td className={cn(
        "px-4 py-3 text-right font-mono tabular-nums font-bold text-sm",
        isProfit ? "text-bull" : "text-bear"
      )}>
        {isProfit ? "+" : ""}{formatCurrency(pnl, 0)}
      </td>

      <td className={cn(
        "px-4 py-3 text-right font-mono tabular-nums font-bold text-sm",
        isProfit ? "text-bull" : "text-bear"
      )}>
        {isProfit ? "+" : ""}{pnlPct.toFixed(2)}%
      </td>

      <td className="px-4 py-3">
        <div className="flex items-center justify-center gap-1">
          <Button
            size="sm"
            variant="outline"
            className="h-7 px-2 text-[10px] border-bull/30 text-bull hover:bg-bull/10"
            onClick={onBuy}
          >
            +BUY
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 px-2 text-[10px] border-bear/30 text-bear hover:bg-bear/10"
            onClick={onSell}
          >
            SELL
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="h-7 w-7 p-0 text-bear hover:bg-bear/10"
            onClick={onClose}
            disabled={isClosing}
            title="Close at market price"
          >
            {isClosing ? <Loader2 className="animate-spin" size={12} /> : <X size={12} />}
          </Button>
        </div>
      </td>
    </tr>
  );
}
