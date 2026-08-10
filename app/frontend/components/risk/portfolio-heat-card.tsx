// E:\tradedo\app\frontend\components\risk\portfolio-heat-card.tsx

"use client";

import { usePortfolioHeat } from "@/lib/hooks/use-risk";
import { Flame, TrendingUp } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function PortfolioHeatCard() {
  const { data, isLoading } = usePortfolioHeat();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (!data?.has_positions) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
        <div className="flex items-center gap-2 mb-4">
          <Flame size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">PORTFOLIO HEAT</h3>
        </div>
        <div className="flex items-center justify-center h-40 flex-col">
          <p className="text-4xl font-mono font-bold text-muted-foreground">0.0%</p>
          <p className="text-xs text-muted-foreground mt-2">No open positions</p>
        </div>
      </div>
    );
  }

  const heatPct = data?.heat_pct || 0;
  const totalAtRisk = data?.total_at_risk || 0;
  const capital = data?.capital || 0;
  const heatLevel = data?.heat_level || "";
  const numPositions = data?.num_positions || 0;

  const getHeatColor = () => {
    if (heatPct < 3) return "text-bull";
    if (heatPct < 6) return "text-neutral";
    if (heatPct < 10) return "text-brand";
    return "text-bear";
  };

  const getHeatBg = () => {
    if (heatPct < 3) return "from-bull/20 to-bull/5";
    if (heatPct < 6) return "from-neutral/20 to-neutral/5";
    if (heatPct < 10) return "from-brand/20 to-brand/5";
    return "from-bear/20 to-bear/5";
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Flame size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">PORTFOLIO HEAT</h3>
      </div>

      {/* Main heat display */}
      <div className={cn(
        "rounded-lg p-6 bg-gradient-to-br text-center",
        getHeatBg()
      )}>
        <p className={cn(
          "text-6xl font-mono font-bold",
          getHeatColor()
        )}>
          {heatPct.toFixed(2)}%
        </p>
        <p className="text-xs text-muted-foreground mt-2">of capital at risk</p>
      </div>

      {/* Progress bar */}
      <div className="mt-4">
        <div className="flex items-center justify-between text-[10px] mb-1">
          <span className="text-muted-foreground">0%</span>
          <span className="text-muted-foreground">10% MAX</span>
        </div>
        <div className="h-2 bg-secondary rounded-full overflow-hidden">
          <div 
            className={cn(
              "h-full rounded-full transition-all",
              heatPct < 3 && "bg-bull",
              heatPct >= 3 && heatPct < 6 && "bg-neutral",
              heatPct >= 6 && heatPct < 10 && "bg-brand",
              heatPct >= 10 && "bg-bear"
            )}
            style={{ width: `${Math.min(heatPct * 10, 100)}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="mt-4 pt-4 border-t border-border space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Total at Risk</span>
          <span className="font-mono font-bold">{formatCurrency(totalAtRisk, 0)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Capital</span>
          <span className="font-mono font-bold">{formatCurrency(capital, 0)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Open Positions</span>
          <span className="font-mono font-bold">{numPositions}</span>
        </div>
      </div>

      {heatLevel && (
        <div className={cn(
          "mt-3 p-2 rounded text-xs text-center font-bold",
          heatPct < 3 && "bg-bull/10 text-bull",
          heatPct >= 3 && heatPct < 6 && "bg-neutral/10 text-neutral",
          heatPct >= 6 && heatPct < 10 && "bg-brand/10 text-brand",
          heatPct >= 10 && "bg-bear/10 text-bear",
        )}>
          {heatLevel}
        </div>
      )}
    </div>
  );
}