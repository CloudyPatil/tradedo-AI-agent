// E:\tradedo\app\frontend\components\trades\trades-table.tsx

"use client";

import { TrendingUp, TrendingDown, Eye, Loader2 } from "lucide-react";
import { formatCurrency, formatTime, cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

interface Props {
  trades: any[];
  isLoading: boolean;
  onSelectTrade: (trade: any) => void;
}

export function TradesTable({ trades, isLoading, onSelectTrade }: Props) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 space-y-2">
        {[...Array(10)].map((_, i) => (
          <Skeleton key={i} className="h-14" />
        ))}
      </div>
    );
  }

  if (trades.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-12 text-center corner-brackets">
        <p className="text-sm text-muted-foreground">No trades match your filters</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-accent/30 sticky top-0">
            <tr>
              <th className="text-left px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">SYMBOL</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">DIR</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">ENTRY</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">EXIT</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">QTY</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">SL</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">TARGET</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">CONF</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">P&L</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">STATUS</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">TIME</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">ACTION</th>
            </tr>
          </thead>
          <tbody>
            {trades.map(trade => (
              <TradeRow key={trade.id} trade={trade} onSelect={() => onSelectTrade(trade)} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TradeRow({ trade, onSelect }: any) {
  const isLong = trade.direction === "LONG";
  const pnl = trade.pnl || 0;
  const isWin = pnl > 0;
  const isOpen = trade.status === "OPEN";
  const cleanSymbol = trade.symbol.replace(".NS", "");

  const statusColors: Record<string, string> = {
    OPEN:    "text-brand bg-brand/10",
    T1_HIT:  "text-bull bg-bull/10",
    T2_HIT:  "text-bull bg-bull/10",
    SL_HIT:  "text-bear bg-bear/10",
    EOD:     "text-neutral bg-neutral/10",
    MANUAL:  "text-muted-foreground bg-muted",
  };

  return (
    <tr className="border-t border-border hover:bg-accent/30 transition-colors">
      <td className="px-4 py-3">
        <Link
          href={`/stock/${cleanSymbol}`}
          className="font-mono font-bold text-sm hover:text-brand"
        >
          {cleanSymbol}
        </Link>
        <p className="text-[10px] text-muted-foreground">#{trade.id}</p>
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
        ₹{trade.entry_price?.toFixed(2)}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
        {trade.exit_price ? `₹${trade.exit_price.toFixed(2)}` : "—"}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
        {trade.quantity}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-bear text-xs">
        ₹{(trade.trailing_sl || trade.stop_loss)?.toFixed(2)}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-bull text-xs">
        ₹{trade.target_2?.toFixed(2)}
      </td>

      <td className="px-4 py-3 text-right font-mono tabular-nums text-xs">
        {trade.ml_confidence?.toFixed(1)}%
      </td>

      <td className={cn(
        "px-4 py-3 text-right font-mono tabular-nums font-bold text-sm",
        !isOpen && (isWin ? "text-bull" : "text-bear")
      )}>
        {isOpen ? (
          <span className="text-brand">RUNNING</span>
        ) : (
          <>{isWin ? "+" : ""}{formatCurrency(pnl, 0)}</>
        )}
      </td>

      <td className="px-4 py-3 text-center">
        <span className={cn(
          "text-[10px] px-2 py-0.5 rounded font-bold",
          statusColors[trade.status] || "bg-muted"
        )}>
          {trade.status?.replace(/_/g, " ")}
        </span>
      </td>

      <td className="px-4 py-3 text-center text-[10px] text-muted-foreground font-mono">
        {trade.entry_time ? formatTime(trade.entry_time) : "—"}
      </td>

      <td className="px-4 py-3 text-center">
        <Button
          variant="ghost"
          size="icon"
          className="w-7 h-7"
          onClick={onSelect}
        >
          <Eye size={14} className="text-muted-foreground hover:text-brand" />
        </Button>
      </td>
    </tr>
  );
}