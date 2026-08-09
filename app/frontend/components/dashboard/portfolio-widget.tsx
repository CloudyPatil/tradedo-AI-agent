// E:\tradedo\app\frontend\components\dashboard\portfolio-widget.tsx

"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { formatCurrency, cn } from "@/lib/utils";
import { useAgentStatus } from "@/lib/hooks/use-agent";
import { Skeleton } from "@/components/ui/skeleton";

export function PortfolioWidget() {
  const { data, isLoading } = useAgentStatus();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <Skeleton className="h-3 w-24 mb-4" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  const agent = data?.agent;
  const capital = agent?.capital || 0;
  const available = agent?.available || 0;
  const deployed = agent?.current_exposure || 0;
  const totalPnl = agent?.total_pnl || 0;
  const totalPnlPct = agent?.total_pnl_pct || 0;

  const chartData = [
    { name: "Available",   value: available, color: "#94A3B8" },
    { name: "Deployed",    value: deployed,  color: "#FF5722" },
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      <h3 className="text-xs font-bold tracking-widest text-muted-foreground mb-4">
        PORTFOLIO SUMMARY
      </h3>

      <div className="flex items-center gap-4">
        <div className="w-24 h-24 relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={28}
                outerRadius={44}
                dataKey="value"
              >
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="flex-1">
          <p className="text-xs text-muted-foreground">TOTAL VALUE</p>
          <p className="text-xl font-mono font-bold tabular-nums">
            {formatCurrency(capital, 0)}
          </p>
          <p className={cn(
            "text-xs mt-1 font-mono",
            totalPnl >= 0 ? "text-bull" : "text-bear"
          )}>
            {totalPnl >= 0 ? "+" : ""}{formatCurrency(totalPnl, 0)} ({totalPnlPct.toFixed(2)}%)
          </p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-border space-y-2">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-slate-400" />
            <span className="text-muted-foreground">Available</span>
          </div>
          <span className="font-mono tabular-nums">
            {formatCurrency(available, 0)}
          </span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-brand" />
            <span className="text-muted-foreground">Deployed</span>
          </div>
          <span className="font-mono tabular-nums">
            {formatCurrency(deployed, 0)}
          </span>
        </div>
      </div>
    </div>
  );
}