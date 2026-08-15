// E:\tradedo\app\frontend\components\portfolio\holdings-list.tsx

"use client";

import { useTrades } from "@/lib/hooks/use-agent";
import { Briefcase, TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";

export function HoldingsList() {
  const { data, isLoading } = useTrades("open");
  const trades = data?.trades || [];

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Briefcase size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">CURRENT HOLDINGS</h3>
          <span className="text-xs text-muted-foreground">
            ({trades.length})
          </span>
        </div>
        
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
          <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse" />
          <span>REAL-TIME UPDATES</span>
        </div>
      </div>

      {isLoading ? (
        <div className="p-4 space-y-2">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : trades.length === 0 ? (
        <div className="p-12 text-center">
          <Briefcase className="mx-auto text-muted-foreground mb-3" size={32} />
          <p className="text-sm text-muted-foreground">No current holdings</p>
          <p className="text-xs text-muted-foreground mt-1">
            Agent will execute trades when good setups appear
          </p>
        </div>
      ) : (
        <table className="w-full">
          <thead className="bg-accent/30">
            <tr>
              <th className="text-left px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">SYMBOL</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">DIR</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">QTY</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">AVG COST</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">CMP</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">INVEST</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">CURRENT</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">P&L</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">P&L %</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold text-muted-foreground tracking-wider">STATUS</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade: any) => (
              <HoldingRow key={trade.id} trade={trade} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function HoldingRow({ trade }: { trade: any }) {
  const isLong = trade.direction === "LONG";
  const cleanSymbol = trade.symbol.replace(".NS", "");
  const currentPrice = trade.current_price || trade.entry_price;
  const investment = trade.investment || 0;
  const currentValue = trade.quantity * currentPrice;
  const pnl = trade.pnl || 0;
  const pnlPct = investment > 0 ? (pnl / investment) * 100 : 0;
  const isProfit = pnl >= 0;

  return (
    <tr className="border-t border-border hover:bg-accent/30 transition-colors">
      <td className="px-4 py-3">
        <Link 
          href={`/stock/${cleanSymbol}`}
          className="font-mono font-bold text-sm hover:text-brand"
        >
          {cleanSymbol}
        </Link>
        <p className="text-[10px] text-muted-foreground">
          {trade.sector} · #{trade.id}
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

      <td className="px-4 py-3 text-center">
        <span className="text-[10px] px-2 py-0.5 bg-brand/10 text-brand rounded font-bold">
          OPEN
        </span>
      </td>
    </tr>
  );
}