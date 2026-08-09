// E:\tradedo\app\frontend\components\agent\trade-history.tsx

"use client";

import { useTrades } from "@/lib/hooks/use-agent";
import { History, Loader2 } from "lucide-react";
import { formatCurrency, cn, formatTime } from "@/lib/utils";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";

export function TradeHistory() {
  const { data, isLoading } = useTrades("closed");

  const trades = data?.trades?.slice(0, 10) || [];

  const totalPnl = trades.reduce((sum: number, t: any) => sum + (t.pnl || 0), 0);
  const wins = trades.filter((t: any) => (t.pnl || 0) > 0).length;

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets h-full flex flex-col">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">TRADE HISTORY</h3>
          <span className="text-xs text-muted-foreground">
            (Last {trades.length})
          </span>
        </div>
        
        {trades.length > 0 && (
          <div className="flex items-center gap-3 text-xs">
            <span className="text-muted-foreground">
              {wins}/{trades.length} wins
            </span>
            <span className={cn(
              "font-mono font-bold",
              totalPnl >= 0 ? "text-bull" : "text-bear"
            )}>
              {totalPnl >= 0 ? "+" : ""}{formatCurrency(totalPnl, 0)}
            </span>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="p-4 space-y-2">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      ) : trades.length === 0 ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <p className="text-sm text-muted-foreground">No closed trades yet</p>
        </div>
      ) : (
        <div className="overflow-y-auto flex-1">
          <table className="w-full">
            <thead className="bg-accent/30 sticky top-0">
              <tr>
                <th className="text-left px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">SYMBOL</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">ENTRY</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">EXIT</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">P&L</th>
                <th className="text-center px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">STATUS</th>
                <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">TIME</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade: any) => (
                <HistoryRow key={trade.id} trade={trade} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function HistoryRow({ trade }: { trade: any }) {
  const cleanSymbol = trade.symbol.replace(".NS", "");
  const pnl = trade.pnl || 0;
  const isWin = pnl > 0;

  const statusColors: Record<string, string> = {
    T1_HIT:   "text-bull bg-bull/10",
    T2_HIT:   "text-bull bg-bull/10",
    SL_HIT:   "text-bear bg-bear/10",
    EOD:      "text-neutral bg-neutral/10",
    MANUAL:   "text-muted-foreground bg-muted",
  };

  return (
    <tr className="border-t border-border hover:bg-accent/30 transition-colors">
      <td className="px-4 py-2">
        <Link 
          href={`/stock/${cleanSymbol}`}
          className="font-mono font-bold text-xs hover:text-brand"
        >
          {cleanSymbol}
        </Link>
      </td>
      
      <td className="px-4 py-2 text-right font-mono tabular-nums text-xs">
        ₹{trade.entry_price?.toFixed(2)}
      </td>
      
      <td className="px-4 py-2 text-right font-mono tabular-nums text-xs">
        ₹{trade.exit_price?.toFixed(2)}
      </td>
      
      <td className={cn(
        "px-4 py-2 text-right font-mono tabular-nums font-bold text-xs",
        isWin ? "text-bull" : "text-bear"
      )}>
        {isWin ? "+" : ""}{formatCurrency(pnl, 0)}
      </td>
      
      <td className="px-4 py-2 text-center">
        <span className={cn(
          "text-[10px] px-2 py-0.5 rounded font-bold",
          statusColors[trade.status] || "bg-muted"
        )}>
          {trade.status?.replace(/_/g, " ")}
        </span>
      </td>
      
      <td className="px-4 py-2 text-right text-[10px] text-muted-foreground font-mono">
        {trade.exit_time ? formatTime(trade.exit_time) : "—"}
      </td>
    </tr>
  );
}