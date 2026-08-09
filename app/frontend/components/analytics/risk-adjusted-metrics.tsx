// E:\tradedo\app\frontend\components\analytics\risk-adjusted-metrics.tsx

"use client";

import { usePerformance } from "@/lib/hooks/use-analytics";
import { Shield, TrendingDown, Award } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function RiskAdjustedMetrics() {
  const { data, isLoading } = usePerformance();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      </div>
    );
  }

  const sharpe = data?.sharpe_ratio || 0;
  const sortino = data?.sortino_ratio || 0;
  const calmar = data?.calmar_ratio || 0;
  const drawdown = data?.max_drawdown || {};
  const profitFactor = data?.profit_factor || 0;
  const recovery = data?.recovery_factor || 0;
  const expectancy = data?.expectancy || {};

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Shield size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">RISK-ADJUSTED METRICS</h3>
      </div>

      <div className="space-y-3">
        <MetricRow
          label="Sharpe Ratio"
          value={sharpe.toFixed(2)}
          description={sharpeInterp(sharpe)}
          score={sharpe}
          scoreThresholds={{ good: 1, excellent: 2 }}
        />
        
        <MetricRow
          label="Sortino Ratio"
          value={sortino > 100 ? "∞" : sortino.toFixed(2)}
          description="Downside risk adjusted"
          score={sortino}
          scoreThresholds={{ good: 1.5, excellent: 3 }}
        />
        
        <MetricRow
          label="Calmar Ratio"
          value={calmar > 100 ? "∞" : calmar.toFixed(2)}
          description="Return / Max Drawdown"
          score={calmar}
          scoreThresholds={{ good: 1, excellent: 3 }}
        />
        
        <MetricRow
          label="Max Drawdown"
          value={`${(drawdown.max_dd_pct || 0).toFixed(2)}%`}
          description={`${formatCurrency(drawdown.max_dd_amount || 0, 0)} peak-to-trough`}
          score={100 - (drawdown.max_dd_pct || 0) * 10}
          scoreThresholds={{ good: 90, excellent: 95 }}
        />
        
        <MetricRow
          label="Profit Factor"
          value={profitFactor > 100 ? "∞" : profitFactor.toFixed(2)}
          description={profitFactorInterp(profitFactor)}
          score={profitFactor * 20}
          scoreThresholds={{ good: 30, excellent: 40 }}
        />
        
        <MetricRow
          label="Expectancy"
          value={formatCurrency(expectancy.expectancy || 0, 0)}
          description={expectancy.interpretation || "Per trade"}
          score={expectancy.expectancy || 0}
          scoreThresholds={{ good: 0, excellent: 100 }}
        />
        
        <MetricRow
          label="Recovery Factor"
          value={recovery > 100 ? "∞" : recovery.toFixed(2)}
          description="Total profit / Max DD"
          score={recovery * 10}
          scoreThresholds={{ good: 10, excellent: 30 }}
        />
      </div>
    </div>
  );
}

function MetricRow({ label, value, description, score, scoreThresholds }: any) {
  const isExcellent = score >= scoreThresholds.excellent;
  const isGood = score >= scoreThresholds.good;
  
  const color = isExcellent ? "text-bull" : isGood ? "text-neutral" : "text-bear";
  const bgColor = isExcellent ? "bg-bull/10" : isGood ? "bg-neutral/10" : "bg-bear/10";

  return (
    <div className={cn("p-3 rounded-md border border-border", bgColor)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold">{label}</span>
        <span className={cn("text-lg font-mono font-bold", color)}>{value}</span>
      </div>
      <p className="text-[10px] text-muted-foreground">{description}</p>
    </div>
  );
}

function sharpeInterp(s: number): string {
  if (s < 0) return "Poor - Losing money";
  if (s < 1) return "Sub-optimal";
  if (s < 2) return "Good performance";
  if (s < 3) return "Very good";
  return "Excellent!";
}

function profitFactorInterp(pf: number): string {
  if (pf < 1) return "Losing system";
  if (pf < 1.5) return "Marginal profit";
  if (pf < 2) return "Good system";
  return "Excellent system";
}