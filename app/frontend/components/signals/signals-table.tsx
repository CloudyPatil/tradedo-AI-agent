// E:\tradedo\app\frontend\components\signals\signals-table.tsx

"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Minus, Trash2 } from "lucide-react";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { useRemoveFromWatchlist } from "@/lib/hooks/use-market";
import { Button } from "@/components/ui/button";

interface Props {
  stocks: any[];
  isLoading: boolean;
}

export function SignalsTable({ stocks, isLoading }: Props) {
  const removeMutation = useRemoveFromWatchlist();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 space-y-2">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-12 bg-secondary rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border bg-accent/30">
            <th className="text-left px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">STOCK</th>
            <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">PRICE</th>
            <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">SIGNAL</th>
            <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">CONFIDENCE</th>
            <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">RSI</th>
            <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">P(UP)</th>
            <th className="text-right px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">RETURN</th>
            <th className="text-center px-4 py-3 text-[10px] font-bold tracking-wider text-muted-foreground">ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map(stock => (
            <TableRow
              key={stock.symbol}
              stock={stock}
              onRemove={() => removeMutation.mutate(stock.symbol)}
            />
          ))}
        </tbody>
      </table>

      {stocks.length === 0 && (
        <div className="p-12 text-center text-sm text-muted-foreground">
          No stocks match your filters
        </div>
      )}
    </div>
  );
}

function TableRow({ stock, onRemove }: { stock: any; onRemove: () => void }) {
  const cleanSymbol = stock.symbol.replace(".NS", "");
  const signal = stock.signal || "HOLD";
  const returnPct = stock.indicators?.returns_5 || stock.indicators?.returns_5d || 0;
  const isPositive = returnPct >= 0;

  const signalColors: Record<string, string> = {
    BUY:  "text-bull bg-bull/10",
    SELL: "text-bear bg-bear/10",
    HOLD: "text-neutral bg-neutral/10",
  };

  const SignalIcon = signal === "BUY" ? TrendingUp : signal === "SELL" ? TrendingDown : Minus;

  return (
    <tr className="border-b border-border hover:bg-accent/30 transition-colors">
      <td className="px-4 py-3">
        <Link href={`/stock/${cleanSymbol}`} className="font-mono font-bold hover:text-brand">
          {cleanSymbol}
        </Link>
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums font-bold">
        ₹{stock.current_price?.toFixed(2) || "—"}
      </td>
      
      <td className="px-4 py-3">
        <div className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold",
          signalColors[signal]
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
          <div className="h-1 bg-secondary rounded-full overflow-hidden">
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
      
      <td className="px-4 py-3 text-right font-mono tabular-nums">
        {stock.indicators?.rsi?.toFixed(1) || "—"}
      </td>
      
      <td className="px-4 py-3 text-right font-mono tabular-nums">
        {stock.prob_up ? `${(stock.prob_up * 100).toFixed(0)}%` : "—"}
      </td>
      
      <td className={cn(
        "px-4 py-3 text-right font-mono tabular-nums font-bold",
        isPositive ? "text-bull" : "text-bear"
      )}>
        {formatPercent(returnPct)}
      </td>
      
      <td className="px-4 py-3">
        <div className="flex items-center justify-center gap-1">
          <Link href={`/stock/${cleanSymbol}`}>
            <Button variant="ghost" size="sm" className="text-xs h-7">
              ANALYZE →
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="icon"
            className="w-7 h-7 hover:text-bear"
            onClick={onRemove}
          >
            <Trash2 size={12} />
          </Button>
        </div>
      </td>
    </tr>
  );
}