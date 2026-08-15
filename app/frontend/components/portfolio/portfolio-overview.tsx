// E:\tradedo\app\frontend\components\portfolio\portfolio-overview.tsx

"use client";

import { useAgentStatus } from "@/lib/hooks/use-agent";
import { usePerformance } from "@/lib/hooks/use-analytics";
import { formatCurrency, cn } from "@/lib/utils";
import { 
  DollarSign, TrendingUp, PieChart, 
  Target, Trophy, Activity 
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function PortfolioOverview() {
  const { data: statusData, isLoading: statusLoading } = useAgentStatus();
  const { data: perfData, isLoading: perfLoading } = usePerformance();

  if (statusLoading || perfLoading) {
    return (
      <div className="grid grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-28" />)}
      </div>
    );
  }

  const agent = statusData?.agent;
  const capital = agent?.capital || 0;
  const startingCapital = agent?.starting_capital || 100000;
  const available = agent?.available || 0;
  const deployed = agent?.current_exposure || 0;
  const openTrades = statusData?.open_trades?.length || 0;
  const basic = perfData?.basic || {};

  const metrics = [
    {
      icon: <DollarSign size={16} />,
      label: "TOTAL VALUE",
      value: formatCurrency(capital, 0),
      subvalue: `Started with ${formatCurrency(startingCapital, 0)}`,
      color: "text-foreground",
      highlight: true,
    },
    {
      icon: <TrendingUp size={16} />,
      label: "AVAILABLE",
      value: formatCurrency(available, 0),
      subvalue: `${((available / capital) * 100).toFixed(1)}% free`,
      color: "text-bull",
    },
    {
      icon: <PieChart size={16} />,
      label: "DEPLOYED",
      value: formatCurrency(deployed, 0),
      subvalue: `${((deployed / capital) * 100).toFixed(1)}% invested`,
      color: "text-brand",
    },
    {
      icon: <Target size={16} />,
      label: "OPEN POSITIONS",
      value: openTrades.toString().padStart(2, "0"),
      subvalue: "active trades",
      color: openTrades > 0 ? "text-brand" : "text-muted-foreground",
    },
    {
      icon: <Trophy size={16} />,
      label: "WIN RATE",
      value: `${(basic.win_rate || 0).toFixed(1)}%`,
      subvalue: `${basic.winning_trades || 0}W · ${basic.losing_trades || 0}L`,
      color: (basic.win_rate || 0) >= 60 ? "text-bull" : "text-neutral",
    },
    {
      icon: <Activity size={16} />,
      label: "TOTAL TRADES",
      value: (basic.total_trades || 0).toString(),
      subvalue: "all-time",
      color: "text-foreground",
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-4">
      {metrics.map((m, i) => (
        <div
          key={i}
          className={cn(
            "p-4 rounded-lg border corner-brackets",
            m.highlight 
              ? "border-brand/30 bg-brand/5" 
              : "border-border bg-card"
          )}
        >
          <div className="flex items-center gap-2 mb-2 text-muted-foreground">
            {m.icon}
            <span className="text-[10px] tracking-wider font-bold">{m.label}</span>
          </div>
          <p className={cn("text-xl font-mono font-bold tabular-nums", m.color)}>
            {m.value}
          </p>
          <p className="text-[10px] text-muted-foreground mt-1 font-mono">
            {m.subvalue}
          </p>
        </div>
      ))}
    </div>
  );
}