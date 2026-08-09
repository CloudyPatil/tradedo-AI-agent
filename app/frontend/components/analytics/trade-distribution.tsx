// E:\tradedo\app\frontend\components\analytics\trade-distribution.tsx

"use client";

import { useDistribution } from "@/lib/hooks/use-analytics";
import { BarChart3, Loader2 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { formatCurrency } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function TradeDistribution() {
  const { data, isLoading } = useDistribution();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-64">
        <Skeleton className="h-full w-full" />
      </div>
    );
  }

  const distribution = data?.distribution || {};

  const chartData = [
    { name: "Big Wins", key: "big_wins", value: distribution.big_wins || 0, range: "> ₹500", color: "#16A34A" },
    { name: "Med Wins", key: "medium_wins", value: distribution.medium_wins || 0, range: "₹100-500", color: "#22C55E" },
    { name: "Small Wins", key: "small_wins", value: distribution.small_wins || 0, range: "₹0-100", color: "#4ADE80" },
    { name: "Breakeven", key: "breakeven", value: distribution.breakeven || 0, range: "= 0", color: "#94A3B8" },
    { name: "Small Losses", key: "small_losses", value: distribution.small_losses || 0, range: "-₹100 to 0", color: "#FCA5A5" },
    { name: "Med Losses", key: "medium_losses", value: distribution.medium_losses || 0, range: "-₹500 to -100", color: "#F87171" },
    { name: "Big Losses", key: "big_losses", value: distribution.big_losses || 0, range: "< -₹500", color: "#DC2626" },
  ];

  const total = data?.total || 0;
  const median = data?.median_pnl || 0;
  const stdDev = data?.std_dev || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">TRADE P&L DISTRIBUTION</h3>
        </div>
        
        <div className="flex items-center gap-4 text-xs">
          <div>
            <span className="text-muted-foreground">Total: </span>
            <span className="font-mono font-bold">{total}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Median: </span>
            <span className="font-mono font-bold">{formatCurrency(median, 0)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Std Dev: </span>
            <span className="font-mono font-bold">{formatCurrency(stdDev, 0)}</span>
          </div>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
            
            <XAxis 
              dataKey="name" 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
            />
            
            <YAxis
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
            />
            
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.[0]) return null;
                const data = payload[0].payload;
                return (
                  <div className="bg-card border border-border rounded p-2 text-xs shadow-lg">
                    <p className="font-bold">{data.name}</p>
                    <p className="text-muted-foreground">{data.range}</p>
                    <p>Count: <span className="font-mono font-bold">{data.value}</span></p>
                  </div>
                );
              }}
            />
            
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}