// E:\tradedo\app\frontend\components\risk\stress-test-panel.tsx

"use client";

import { useStressTest } from "@/lib/hooks/use-risk";
import { Zap, TrendingDown, AlertTriangle } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function StressTestPanel() {
  const { data, isLoading } = useStressTest();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (!data?.has_positions) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
        <div className="flex items-center gap-2 mb-4">
          <Zap size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">STRESS TEST SCENARIOS</h3>
        </div>
        <div className="text-center py-8 text-sm text-muted-foreground">
          No positions to stress test
        </div>
      </div>
    );
  }

  const scenarios = data?.scenarios || {};
  const capital = data?.capital || 0;

  const scenarioConfig: Record<string, any> = {
    market_crash_5pct:  { label: "Market -5%",   icon: TrendingDown, color: "neutral" },
    market_crash_10pct: { label: "Market -10%",  icon: TrendingDown, color: "brand" },
    sector_crash:       { label: "Sector -15%",  icon: AlertTriangle, color: "brand" },
    all_sl_hit:         { label: "All SLs Hit",  icon: AlertTriangle, color: "bear" },
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">STRESS TEST SCENARIOS</h3>
        </div>
        <span className="text-[10px] text-muted-foreground font-mono">
          CAPITAL: {formatCurrency(capital, 0)}
        </span>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {Object.entries(scenarios).map(([key, scenario]: [string, any]) => {
          const config = scenarioConfig[key] || { label: key, icon: AlertTriangle, color: "brand" };
          const Icon = config.icon;
          const isSeverere = Math.abs(scenario.loss_pct) > 5;
          
          return (
            <div 
              key={key}
              className={cn(
                "p-4 rounded-lg border corner-brackets",
                isSeverere ? "border-bear/30 bg-bear/5" : "border-border bg-accent/20"
              )}
            >
              <div className="flex items-center gap-2 mb-2 text-muted-foreground">
                <Icon size={14} className={config.color === "bear" ? "text-bear" : config.color === "brand" ? "text-brand" : "text-neutral"} />
                <span className="text-[10px] font-bold tracking-wider">{config.label}</span>
              </div>

              <p className={cn(
                "text-2xl font-mono font-bold",
                isSeverere ? "text-bear" : "text-brand"
              )}>
                {formatCurrency(scenario.loss, 0)}
              </p>

              <p className={cn(
                "text-sm font-mono font-bold mt-1",
                isSeverere ? "text-bear" : "text-brand"
              )}>
                {scenario.loss_pct?.toFixed(2)}%
              </p>

              <p className="text-[10px] text-muted-foreground mt-2">
                {scenario.impact?.replace(/_/g, " ")}
              </p>

              {scenario.sector && (
                <p className="text-[10px] text-muted-foreground mt-1">
                  Worst: {scenario.sector}
                </p>
              )}

              {scenario.note && (
                <p className="text-[10px] text-muted-foreground italic mt-1">
                  {scenario.note}
                </p>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-border text-xs text-center text-muted-foreground">
        💡 These scenarios show maximum possible losses in different market conditions
      </div>
    </div>
  );
}