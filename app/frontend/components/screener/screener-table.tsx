// E:\tradedo\app\frontend\components\screener\screener-table.tsx

"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Minus, Eye } from "lucide-react";
import { cn, formatPercent } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface Props {
  stocks: any[];
  isLoading: boolean;
}

export function ScreenerTable({ stocks, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 space-y-2">
        {[...Array(10)].map((_, i) => <Skeleton key={i} className="h-14" />)}
      </div>
    );
  }

  if (stocks.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-12 text-center corner-brackets">
        <p className="text-sm text-muted-foreground mb-2">No stocks match filters</p>
        <p className="text-xs text-muted-foreground">
          Try running a scan first or adjusting filters
        </p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-bold tracking-wider">
          ANALYZED STOCKS ({stocks.length})
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-accent/30">
              <th className="text-left px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">#</th>
              <th className="text-left px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">SYMBOL</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">SECTOR</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">PRICE</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">SIGNAL</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">CONFIDENCE</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">P(UP)</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">RSI</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">5D%</th>
              <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">20D%</th>
              <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">ACTION</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock, i) => (
              <ScreenerRow key={stock.symbol} rank={i + 1} stock={stock} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ScreenerRow({ rank, stock }: any) {
  const cleanSymbol = stock.symbol.replace(".NS", "");
  const signal = stock.signal || "HOLD";
  const isProfit = (stock.returns_5d || 0) >= 0;
  
  const signalConfig = {
    BUY:  { bg: "bg-bull/10", text: "text-bull",  icon: TrendingUp },
    SELL: { bg: "bg-bear/10", text: "text-bear",  icon: TrendingDown },
    HOLD: { bg: "bg-neutral/10", text: "text-neutral", icon: Minus },
  };
  
  const config = signalConfig[signal as keyof typeof signalConfig] || signalConfig.HOLD;
  const SignalIcon = config.icon;
  
  return (
    <tr className="border-t border-border hover:bg-accent/30 transition-colors">
      <td className="px-4 py-3 text-xs text-muted-foreground font-mono">
        {rank}
      </td>
      
      <td className="px-4 py-3">
        <Link 
          href={`/stock/${cleanSymbol}`}
          className="font-mono font-bold text-sm hover:text-brand"
        >
          {cleanSymbol}
        </Link>
      </td>
      
      <td className="px-4 py-3 text-center">
        <span className="text-[10px] px-2 py-0.5 bg-secondary rounded font-bold">
          {stock.sector}
        </span>
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
        ₹{stock.current_price?.toFixed(2) || "—"}
      </td>
      
      <td className="px-4 py-3 text-center">
        <div className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold",
          config.bg, config.text
        )}>
          <SignalIcon size={12} />
          {signal}
        </div>
      </td>
      
      <td className="px-4 py-3">
        <div className="w-full max-w-[100px] mx-auto">
          <div className="flex items-center justify-between text-[10px] mb-1">
            <span className="font-mono font-bold">
              {stock.confidence_pct?.toFixed(1) || "—"}%
            </span>
          </div>
          <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
            <div
              className={cn("h-full rounded-full",
                signal === "BUY" && "bg-bull",
                signal === "SELL" && "bg-bear",
                signal === "HOLD" && "bg-neutral"
              )}
              style={{ width: `${stock.confidence_pct || 0}%` }}
            />
          </div>
        </div>
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums text-xs">
        {stock.prob_up ? `${(stock.prob_up * 100).toFixed(0)}%` : "—"}
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums text-xs">
        {stock.rsi?.toFixed(1) || "—"}
      </td>
      
      <td className={cn(
        "px-4 py-3 text-right font-mono tabular-nums text-xs font-bold",
        isProfit ? "text-bull" : "text-bear"
      )}>
        {stock.returns_5d ? formatPercent(stock.returns_5d) : "—"}
      </td>
      
      <td className={cn(
        "px-4 py-3 text-right font-mono tabular-nums text-xs font-bold",
        (stock.returns_20d || 0) >= 0 ? "text-bull" : "text-bear"
      )}>
        {stock.returns_20d ? formatPercent(stock.returns_20d) : "—"}
      </td>
      
      <td className="px-4 py-3 text-center">
        <Link href={`/stock/${cleanSymbol}`}>
          <button className="p-1.5 rounded hover:bg-brand/10 text-muted-foreground hover:text-brand transition-colors">
            <Eye size={14} />
          </button>
        </Link>
      </td>
    </tr>
  );
}