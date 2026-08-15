// E:\tradedo\app\frontend\components\manual\manual-summary.tsx

"use client";

import { useManualSummary } from "@/lib/hooks/use-manual";
import { formatCurrency, cn } from "@/lib/utils";
import { 
  DollarSign, Wallet, TrendingUp, Target,
  BarChart3, Clock 
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function ManualSummary() {
  const { data, isLoading } = useManualSummary();

  if (isLoading) {
    return (
      <div className="grid grid-cols-6 gap-3">
        {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-24" />)}
      </div>
    );
  }

  const capital = data?.capital || 0;
  const available = data?.available || 0;
  const deployed = data?.deployed || 0;
  const totalPnl = data?.total_pnl || 0;
  const openPositions = data?.open_positions || 0;
  const pendingOrders = data?.pending_orders || 0;
  const todaysStats = data?.todays_stats || {};

  const stats = [
    {
      icon: <DollarSign size={16} />,
      label: "TOTAL VALUE",
      value: formatCurrency(capital, 0),
      subvalue: `Start: ${formatCurrency(data?.starting_capital || 100000, 0)}`,
      color: "text-foreground",
      highlight: true,
    },
    {
      icon: <Wallet size={16} />,
      label: "AVAILABLE",
      value: formatCurrency(available, 0),
      subvalue: `${((available / capital) * 100).toFixed(1)}% free`,
      color: "text-bull",
    },
    {
      icon: <BarChart3 size={16} />,
      label: "DEPLOYED",
      value: formatCurrency(deployed, 0),
      subvalue: `${((deployed / capital) * 100).toFixed(1)}% invested`,
      color: "text-brand",
    },
    {
      icon: <Target size={16} />,
      label: "POSITIONS",
      value: openPositions.toString().padStart(2, "0"),
      subvalue: `${pendingOrders} pending orders`,
      color: openPositions > 0 ? "text-brand" : "text-muted-foreground",
    },
    {
      icon: <TrendingUp size={16} />,
      label: "TODAY'S P&L",
      value: formatCurrency(todaysStats.pnl || 0, 0),
      subvalue: `${todaysStats.trades || 0} trades`,
      color: (todaysStats.pnl || 0) >= 0 ? "text-bull" : "text-bear",
    },
    {
      icon: <Clock size={16} />,
      label: "WIN/LOSS",
      value: `${todaysStats.wins || 0}W / ${todaysStats.losses || 0}L`,
      subvalue: "today",
      color: "text-foreground",
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
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
          <p className={cn("text-xl font-mono font-bold tabular-nums", s.color)}>
            {s.value}
          </p>
          <p className="text-[10px] text-muted-foreground mt-1 font-mono">
            {s.subvalue}
          </p>
        </div>
      ))}
    </div>
  );
}