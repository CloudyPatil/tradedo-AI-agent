// E:\tradedo\app\frontend\components\markets\market-breadth.tsx

"use client";

import { useWatchlist } from "@/lib/hooks/use-market";
import { BarChart3, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function MarketBreadth() {
  const { data, isLoading } = useWatchlist("swing");

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const stocks = data?.results || [];
  
  const advancing = stocks.filter((s: any) => (s.indicators?.returns_5d || s.indicators?.returns_5 || 0) > 0).length;
  const declining = stocks.filter((s: any) => (s.indicators?.returns_5d || s.indicators?.returns_5 || 0) < 0).length;
  const unchanged = stocks.length - advancing - declining;
  
  const total = stocks.length;
  const advPct = total > 0 ? (advancing / total) * 100 : 0;
  const decPct = total > 0 ? (declining / total) * 100 : 0;

  // Determine breadth signal
  let signal = "NEUTRAL";
  if (advancing > declining * 2) signal = "STRONG_BULLISH";
  else if (advancing > declining) signal = "BULLISH";
  else if (declining > advancing * 2) signal = "STRONG_BEARISH";
  else if (declining > advancing) signal = "BEARISH";

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">MARKET BREADTH</h3>
      </div>

      {/* Ratio Big Display */}
      <div className="text-center py-4">
        <p className="text-4xl font-mono font-bold">
          <span className="text-bull">{advancing}</span>
          <span className="text-muted-foreground mx-2">:</span>
          <span className="text-bear">{declining}</span>
        </p>
        <p className="text-xs text-muted-foreground mt-1">Advance / Decline</p>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-[10px] mb-1">
          <span className="text-bull font-bold">↑ {advPct.toFixed(0)}%</span>
          <span className="text-bear font-bold">{decPct.toFixed(0)}% ↓</span>
        </div>
        <div className="flex h-3 rounded-full overflow-hidden">
          <div 
            className="bg-bull transition-all" 
            style={{ width: `${advPct}%` }}
          />
          <div 
            className="bg-muted transition-all" 
            style={{ width: `${(unchanged / total) * 100}%` }}
          />
          <div 
            className="bg-bear transition-all" 
            style={{ width: `${decPct}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2 bg-bull/10 rounded">
          <p className="text-[10px] text-bull uppercase font-bold">Advancing</p>
          <p className="text-xl font-mono font-bold text-bull">{advancing}</p>
        </div>
        <div className="p-2 bg-muted rounded">
          <p className="text-[10px] text-muted-foreground uppercase font-bold">Unchanged</p>
          <p className="text-xl font-mono font-bold">{unchanged}</p>
        </div>
        <div className="p-2 bg-bear/10 rounded">
          <p className="text-[10px] text-bear uppercase font-bold">Declining</p>
          <p className="text-xl font-mono font-bold text-bear">{declining}</p>
        </div>
      </div>

      {/* Signal */}
      <div className={cn(
        "mt-4 pt-4 border-t border-border text-center py-2 rounded font-bold text-xs",
        signal.includes("BULLISH") && "bg-bull/10 text-bull",
        signal.includes("BEARISH") && "bg-bear/10 text-bear",
        signal === "NEUTRAL" && "bg-neutral/10 text-neutral",
      )}>
        {signal.replace(/_/g, " ")}
      </div>
    </div>
  );
}