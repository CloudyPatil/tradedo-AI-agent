// E:\tradedo\app\frontend\components\analytics\metrics-overview.tsx

"use client";

import { usePerformance } from "@/lib/hooks/use-analytics";
import { formatCurrency, cn, formatPercent } from "@/lib/utils";
import { Target, TrendingUp, TrendingDown, Trophy, XCircle, Activity } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function MetricsOverview() {
  const { data, isLoading } = usePerformance();

  if (isLoading) {
    return (
      <div className="grid grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
    );
  }

  const basic = data?.basic || {};

  const metrics = [
    {
      icon: <Target size={16} />,
      label: "TOTAL TRADES",
      value: basic.total_trades || 0,
      subvalue: `${basic.winning_trades || 0}W / ${basic.losing_trades || 0}L`,
      color: "text-foreground",
    },
    {
      icon: <Trophy size={16} />,
      label: "WIN RATE",
      value: `${basic.win_rate || 0}%`,
      subvalue: `${basic.winning_trades || 0} wins`,
      color: (basic.win_rate || 0) >= 60 ? "text-bull" : 
             (basic.win_rate || 0) >= 40 ? "text-neutral" : "text-bear",
      highlight: true,
    },
    {
      icon: <Activity size={16} />,
      label: "AVG WIN",
      value: formatCurrency(basic.avg_win || 0, 0),
      subvalue: "per trade",
      color: "text-bull",
    },
    {
      icon: <XCircle size={16} />,
      label: "AVG LOSS",
      value: formatCurrency(basic.avg_loss || 0, 0),
      subvalue: "per trade",
      color: "text-bear",
    },
    {
      icon: <TrendingUp size={16} />,
      label: "LARGEST WIN",
      value: formatCurrency(basic.largest_win || 0, 0),
      subvalue: "single trade",
      color: "text-bull",
    },
    {
      icon: <TrendingDown size={16} />,
      label: "LARGEST LOSS",
      value: formatCurrency(basic.largest_loss || 0, 0),
      subvalue: "single trade",
      color: "text-bear",
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-4">
      {metrics.map((metric, i) => (
        <MetricCard key={i} {...metric} />
      ))}
    </div>
  );
}

function MetricCard({ icon, label, value, subvalue, color, highlight }: any) {
  return (
    <div className={cn(
      "p-4 rounded-lg border corner-brackets transition-all",
      highlight 
        ? "border-brand/30 bg-brand/5 shadow-lg shadow-brand/10" 
        : "border-border bg-card"
    )}>
      <div className="flex items-center gap-2 mb-3 text-muted-foreground">
        {icon}
        <span className="text-[10px] tracking-wider font-bold">{label}</span>
      </div>
      <p className={cn("text-2xl font-mono font-bold tabular-nums", color)}>
        {value}
      </p>
      <p className="text-[10px] text-muted-foreground mt-1 font-mono">
        {subvalue}
      </p>
    </div>
  );
}