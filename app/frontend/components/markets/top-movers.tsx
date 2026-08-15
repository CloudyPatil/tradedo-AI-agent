// E:\tradedo\app\frontend\components\markets\top-movers.tsx

"use client";

import { useWatchlist } from "@/lib/hooks/use-market";
import { TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { cn, formatPercent } from "@/lib/utils";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";
import { useState } from "react";

export function TopMovers() {
  const { data, isLoading } = useWatchlist("swing");
  const [view, setView] = useState<"gainers" | "losers">("gainers");

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12" />)}
        </div>
      </div>
    );
  }

  const stocks = data?.results || [];
  
  const withReturns = stocks
    .map((s: any) => ({
      ...s,
      change: s.indicators?.returns_5d || s.indicators?.returns_5 || 0,
    }))
    .filter((s: any) => s.change !== 0);

  const gainers = [...withReturns].sort((a, b) => b.change - a.change).slice(0, 5);
  const losers = [...withReturns].sort((a, b) => a.change - b.change).slice(0, 5);
  
  const display = view === "gainers" ? gainers : losers;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {view === "gainers" ? (
            <TrendingUp size={16} className="text-bull" />
          ) : (
            <TrendingDown size={16} className="text-bear" />
          )}
          <h3 className="text-sm font-bold tracking-wider">
            TOP {view === "gainers" ? "GAINERS" : "LOSERS"}
          </h3>
        </div>

        <div className="flex bg-secondary border border-border rounded-md p-1">
          <button
            onClick={() => setView("gainers")}
            className={cn(
              "px-3 py-1 rounded text-xs font-bold transition-colors",
              view === "gainers" ? "bg-bull text-white" : "text-muted-foreground"
            )}
          >
            GAINERS
          </button>
          <button
            onClick={() => setView("losers")}
            className={cn(
              "px-3 py-1 rounded text-xs font-bold transition-colors",
              view === "losers" ? "bg-bear text-white" : "text-muted-foreground"
            )}
          >
            LOSERS
          </button>
        </div>
      </div>

      {display.length === 0 ? (
        <div className="text-center py-8 text-sm text-muted-foreground">
          No data available
        </div>
      ) : (
        <div className="space-y-2">
          {display.map((stock: any, i: number) => (
            <MoverRow key={stock.symbol} rank={i + 1} stock={stock} isGainer={view === "gainers"} />
          ))}
        </div>
      )}
    </div>
  );
}

function MoverRow({ rank, stock, isGainer }: any) {
  const cleanSymbol = stock.symbol.replace(".NS", "");
  const change = stock.change || 0;
  const price = stock.current_price || 0;

  return (
    <Link 
      href={`/stock/${cleanSymbol}`}
      className="block p-3 rounded border border-border hover:border-brand hover:bg-accent/30 transition-all"
    >
      <div className="flex items-center gap-3">
        <div className={cn(
          "w-8 h-8 rounded-md flex items-center justify-center font-mono font-bold text-sm",
          isGainer ? "bg-bull/20 text-bull" : "bg-bear/20 text-bear"
        )}>
          #{rank}
        </div>

        <div className="flex-1">
          <p className="font-mono font-bold text-sm">{cleanSymbol}</p>
          <p className="text-[10px] text-muted-foreground">
            ₹{price.toFixed(2)}
          </p>
        </div>

        <div className="text-right">
          <p className={cn(
            "text-lg font-mono font-bold",
            isGainer ? "text-bull" : "text-bear"
          )}>
            {formatPercent(change)}
          </p>
          <p className="text-[10px] text-muted-foreground">5D</p>
        </div>
      </div>
    </Link>
  );
}