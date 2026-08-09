// E:\tradedo\app\frontend\components\signals\signals-grid.tsx

"use client";

import Link from "next/link";
import { TrendingUp, TrendingDown, Minus, Loader2, X } from "lucide-react";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { useRemoveFromWatchlist } from "@/lib/hooks/use-market";
import { Button } from "@/components/ui/button";

interface Props {
  stocks: any[];
  isLoading: boolean;
}

export function SignalsGrid({ stocks, isLoading }: Props) {
  const removeMutation = useRemoveFromWatchlist();

  if (isLoading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-4 h-56 animate-pulse" />
        ))}
      </div>
    );
  }

  if (stocks.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-12 text-center">
        <p className="text-muted-foreground">No stocks match your filters</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-4 gap-4">
      {stocks.map(stock => (
        <SignalCard
          key={stock.symbol}
          stock={stock}
          onRemove={() => removeMutation.mutate(stock.symbol)}
        />
      ))}
    </div>
  );
}

function SignalCard({ stock, onRemove }: { stock: any; onRemove: () => void }) {
  const cleanSymbol = stock.symbol.replace(".NS", "");
  const signal = stock.signal || "HOLD";
  const isPositive = stock.indicators?.returns_5 >= 0 || stock.indicators?.returns_5d >= 0;

  const signalConfig = {
    BUY:  { bg: "bg-bull/10", border: "border-bull/30", text: "text-bull",  icon: TrendingUp },
    SELL: { bg: "bg-bear/10", border: "border-bear/30", text: "text-bear",  icon: TrendingDown },
    HOLD: { bg: "bg-neutral/10", border: "border-neutral/30", text: "text-neutral", icon: Minus },
  };

  const config = signalConfig[signal as keyof typeof signalConfig] || signalConfig.HOLD;
  const Icon = config.icon;

  return (
    <div className={cn(
      "group bg-card border rounded-lg overflow-hidden transition-all hover:shadow-lg hover:shadow-brand/10 corner-brackets relative",
      config.border
    )}>
      {/* Remove button (shows on hover) */}
      <button
        onClick={onRemove}
        className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-bear/20 transition-all z-10"
      >
        <X size={12} className="text-muted-foreground hover:text-bear" />
      </button>

      <Link href={`/stock/${cleanSymbol}`} className="block p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <p className="font-mono font-bold text-lg">{cleanSymbol}</p>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">NSE</p>
          </div>
          
          <div className={cn("p-2 rounded-lg", config.bg)}>
            <Icon size={16} className={config.text} />
          </div>
        </div>

        {/* Price */}
        <div className="mb-3">
          <p className="text-2xl font-mono font-bold tabular-nums">
            ₹{stock.current_price?.toFixed(2) || "—"}
          </p>
          {(stock.indicators?.returns_5 || stock.indicators?.returns_5d) && (
            <p className={cn(
              "text-xs font-mono tabular-nums",
              isPositive ? "text-bull" : "text-bear"
            )}>
              {formatPercent(stock.indicators?.returns_5 || stock.indicators?.returns_5d || 0)}
            </p>
          )}
        </div>

        {/* Signal Badge */}
        <div className={cn(
          "text-center py-1.5 rounded-md border font-bold text-sm mb-3",
          config.bg, config.border, config.text
        )}>
          {signal}
        </div>

        {/* Confidence */}
        <div>
          <div className="flex items-center justify-between text-[10px] mb-1">
            <span className="text-muted-foreground uppercase tracking-wider">Confidence</span>
            <span className="font-mono font-bold">
              {stock.confidence_pct?.toFixed(1) || "—"}%
            </span>
          </div>
          <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
            <div
              className={cn("h-full rounded-full transition-all", 
                signal === "BUY" && "bg-bull",
                signal === "SELL" && "bg-bear",
                signal === "HOLD" && "bg-neutral"
              )}
              style={{ width: `${stock.confidence_pct || 0}%` }}
            />
          </div>
        </div>

        {/* Indicators Mini */}
        <div className="mt-3 pt-3 border-t border-border grid grid-cols-2 gap-2 text-[10px]">
          {stock.indicators?.rsi !== undefined && (
            <div>
              <p className="text-muted-foreground">RSI</p>
              <p className="font-mono font-bold">{stock.indicators.rsi?.toFixed(1)}</p>
            </div>
          )}
          {stock.prob_up !== undefined && (
            <div>
              <p className="text-muted-foreground">P(UP)</p>
              <p className="font-mono font-bold">{(stock.prob_up * 100).toFixed(0)}%</p>
            </div>
          )}
        </div>
      </Link>
    </div>
  );
}