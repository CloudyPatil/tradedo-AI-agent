// E:\tradedo\app\frontend\components\screener\screener-stats.tsx

"use client";

import { useScreenerStats } from "@/lib/hooks/use-screener";
import { formatTime } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp, TrendingDown, Minus, Award } from "lucide-react";

export function ScreenerStats() {
  const { data, isLoading } = useScreenerStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-24" />)}
      </div>
    );
  }

  const total = data?.total_analyzed || 0;
  const bySignal = data?.by_signal || {};
  const highConf = data?.high_confidence || 0;
  const lastRun = data?.last_run;

  const stats = [
    {
      icon: <Award size={14} />,
      label: "TOTAL ANALYZED",
      value: total,
      color: "text-foreground",
      highlight: true,
    },
    {
      icon: <TrendingUp size={14} />,
      label: "BUY SIGNALS",
      value: bySignal.BUY || 0,
      color: "text-bull",
    },
    {
      icon: <Minus size={14} />,
      label: "HOLD SIGNALS",
      value: bySignal.HOLD || 0,
      color: "text-neutral",
    },
    {
      icon: <TrendingDown size={14} />,
      label: "SELL SIGNALS",
      value: bySignal.SELL || 0,
      color: "text-bear",
    },
    {
      icon: <Award size={14} />,
      label: "HIGH CONFIDENCE",
      value: highConf,
      color: "text-brand",
    },
  ];

  return (
    <>
      <div className="grid grid-cols-5 gap-3">
        {stats.map((s, i) => (
          <div
            key={i}
            className={cn(
              "p-4 rounded-lg border corner-brackets",
              s.highlight 
                ? "border-brand/30 bg-brand/5" 
                : "border-border bg-card"
            )}
          >
            <div className="flex items-center gap-2 mb-2 text-muted-foreground">
              {s.icon}
              <span className="text-[10px] tracking-wider font-bold">{s.label}</span>
            </div>
            <p className={cn("text-2xl font-mono font-bold tabular-nums", s.color)}>
              {s.value.toString().padStart(3, "0")}
            </p>
          </div>
        ))}
      </div>

      {lastRun && (
        <div className="text-xs text-muted-foreground text-right font-mono">
          Last scan: {lastRun.tier?.toUpperCase()} · {lastRun.stocks_scanned} stocks · 
          {" "}{lastRun.duration_seconds}s · 
          {" "}{new Date(lastRun.run_time).toLocaleString("en-IN")}
        </div>
      )}
    </>
  );
}