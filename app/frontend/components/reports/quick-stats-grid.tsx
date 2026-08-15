// E:\tradedo\app\frontend\components\reports\quick-stats-grid.tsx

"use client";

import { usePerformance } from "@/lib/hooks/use-analytics";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  DollarSign, Percent, TrendingUp, TrendingDown,
  Award, Target 
} from "lucide-react";

export function QuickStatsGrid() {
  const { data, isLoading } = usePerformance();

  if (isLoading) {
    return (
      <div className="grid grid-cols-6 gap-3">
        {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-24" />)}
      </div>
    );
  }

  const basic = data?.basic || {};
  
  const stats = [
    {
      icon: <DollarSign size={14} />,
      label: "Total P&L",
      value: formatCurrency(basic.total_pnl || 0, 0),
      color: (basic.total_pnl || 0) >= 0 ? "text-bull" : "text-bear",
    },
    {
      icon: <Percent size={14} />,
      label: "Win Rate",
      value: `${(basic.win_rate || 0).toFixed(1)}%`,
      color: (basic.win_rate || 0) >= 60 ? "text-bull" : "text-neutral",
    },
    {
      icon: <Target size={14} />,
      label: "Total Trades",
      value: (basic.total_trades || 0).toString(),
      color: "text-foreground",
    },
    {
      icon: <TrendingUp size={14} />,
      label: "Avg Win",
      value: formatCurrency(basic.avg_win || 0, 0),
      color: "text-bull",
    },
    {
      icon: <TrendingDown size={14} />,
      label: "Avg Loss",
      value: formatCurrency(basic.avg_loss || 0, 0),
      color: "text-bear",
    },
    {
      icon: <Award size={14} />,
      label: "Sharpe",
      value: (data?.sharpe_ratio || 0).toFixed(2),
      color: (data?.sharpe_ratio || 0) >= 1 ? "text-bull" : "text-neutral",
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {stats.map((s, i) => (
        <div 
          key={i}
          className="bg-card border border-border rounded-lg p-4 corner-brackets"
        >
          <div className="flex items-center gap-2 mb-2 text-muted-foreground">
            {s.icon}
            <span className="text-[10px] tracking-wider font-bold">{s.label}</span>
          </div>
          <p className={cn("text-xl font-mono font-bold tabular-nums", s.color)}>
            {s.value}
          </p>
        </div>
      ))}
    </div>
  );
}