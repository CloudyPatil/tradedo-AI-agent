// E:\tradedo\app\frontend\components\agent\open-trades-table.tsx

"use client";

import { useTrades } from "@/lib/hooks/use-agent";
import { Target, TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { formatCurrency, cn, formatTime } from "@/lib/utils";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";

export function OpenTradesTable() {
  const { data, isLoading } = useTrades("open");

  const trades = data?.trades || [];

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">OPEN POSITIONS</h3>
          <span className="text-xs text-muted-foreground">
            ({trades.length})
          </span>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse" />
          <span>LIVE</span>
        </div>
      </div>

      {isLoading ? (
        <div className="p-4 space-y-2">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : trades.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-sm text-muted-foreground">No open positions</p>
          <p className="text-xs text-muted-foreground mt-1">
            Agent will execute trades when good setups appear
          </p>
        </div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="bg-accent/30">
              <th className="text-left px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">SYMBOL</th>
              <th className="text-center px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">DIR</th>
              <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">ENTRY</th>
              <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">CMP</th>
              <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">SL</th>
              <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">T1</th>
              <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">QTY</th>
              <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">P&L</th>
              <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">TIME</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade: any) => (
              <TradeRow key={trade.id} trade={trade} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function TradeRow({ trade }: { trade: any }) {
  const isLong = trade.direction === "LONG";
  const pnl = trade.pnl || 0;
  const cleanSymbol = trade.symbol.replace(".NS", "");
  const currentPrice = trade.current_price || trade.entry_price;

  return (
    <tr className="border-t border-border hover:bg-accent/30 transition-colors">
      <td className="px-4 py-3">
        <Link 
          href={`/stock/${cleanSymbol}`}
          className="font-mono font-bold hover:text-brand"
        >
          {cleanSymbol}
        </Link>
        <p className="text-[10px] text-muted-foreground">
          #{trade.id}
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
      
      <td className="px-4 py-3 text-right font-mono tabular-nums">
        ₹{trade.entry_price?.toFixed(2)}
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums font-bold">
        ₹{currentPrice?.toFixed(2)}
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums text-bear text-xs">
        ₹{(trade.trailing_sl || trade.stop_loss)?.toFixed(2)}
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums text-bull text-xs">
        ₹{trade.target_1?.toFixed(2)}
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums">
        {trade.quantity}
      </td>
      
      <td className={cn(
        "px-4 py-3 text-right font-mono tabular-nums font-bold",
        pnl >= 0 ? "text-bull" : "text-bear"
      )}>
        {pnl >= 0 ? "+" : ""}{formatCurrency(pnl, 0)}
      </td>
      
      <td className="px-4 py-3 text-right text-xs text-muted-foreground font-mono">
        {trade.entry_time ? formatTime(trade.entry_time) : "—"}
      </td>
    </tr>
  );
}