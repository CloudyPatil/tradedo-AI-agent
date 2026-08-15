// E:\tradedo\app\frontend\components\portfolio\portfolio-performance.tsx

"use client";

import { useEquityCurve } from "@/lib/hooks/use-analytics";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { TrendingUp, Loader2 } from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { useState } from "react";

export function PortfolioPerformance() {
  const { data, isLoading } = useEquityCurve();
  const [range, setRange] = useState<"7d" | "30d" | "all">("all");

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-80 flex items-center justify-center">
        <Loader2 className="animate-spin text-brand" size={32} />
      </div>
    );
  }

  const curve = data?.curve || [];

  if (curve.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-8 text-center corner-brackets h-full">
        <TrendingUp className="mx-auto text-muted-foreground mb-2" size={32} />
        <p className="text-sm text-muted-foreground">No performance data yet</p>
        <p className="text-xs text-muted-foreground mt-1">
          Complete trades to see portfolio growth
        </p>
      </div>
    );
  }

  let filtered = curve;
  if (range === "7d") filtered = curve.slice(-7);
  else if (range === "30d") filtered = curve.slice(-30);

  const chartData = filtered.map((point: any) => ({
    date: new Date(point.timestamp).toLocaleDateString("en-IN", { 
      day: "2-digit", month: "short" 
    }),
    equity: point.equity,
    pnl: point.pnl,
    symbol: point.symbol,
  }));

  const startingCapital = 100000;
  const finalEquity = chartData[chartData.length - 1]?.equity || startingCapital;
  const totalReturn = ((finalEquity - startingCapital) / startingCapital) * 100;
  const isProfit = totalReturn >= 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
            <TrendingUp size={16} className="text-brand" />
            PORTFOLIO GROWTH
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            {filtered.length} trades tracked
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-[10px] text-muted-foreground">TOTAL RETURN</p>
            <p className={`text-2xl font-mono font-bold ${isProfit ? "text-bull" : "text-bear"}`}>
              {formatPercent(totalReturn)}
            </p>
          </div>

          <div className="flex bg-secondary border border-border rounded-md p-1">
            {[
              { key: "7d", label: "7D" },
              { key: "30d", label: "30D" },
              { key: "all", label: "ALL" },
            ].map(r => (
              <button
                key={r.key}
                onClick={() => setRange(r.key as any)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  range === r.key ? "bg-brand text-white" : "text-muted-foreground"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={isProfit ? "#22C55E" : "#EF4444"} stopOpacity={0.3} />
                <stop offset="100%" stopColor={isProfit ? "#22C55E" : "#EF4444"} stopOpacity={0} />
              </linearGradient>
            </defs>
            
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
            
            <XAxis 
              dataKey="date" 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10, fontFamily: "monospace" }}
            />
            
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10, fontFamily: "monospace" }}
              tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`}
            />
            
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.[0]) return null;
                const data = payload[0].payload;
                return (
                  <div className="bg-card border border-border rounded p-2 text-xs shadow-lg">
                    <p className="font-bold">{data.symbol}</p>
                    <p className="text-muted-foreground">{data.date}</p>
                    <p>Equity: <span className="font-mono font-bold">{formatCurrency(data.equity, 0)}</span></p>
                    <p className={data.pnl >= 0 ? "text-bull" : "text-bear"}>
                      P&L: <span className="font-mono font-bold">{formatCurrency(data.pnl, 0)}</span>
                    </p>
                  </div>
                );
              }}
            />
            
            <ReferenceLine 
              y={startingCapital} 
              stroke="hsl(var(--muted-foreground))" 
              strokeDasharray="3 3"
            />
            
            <Area
              type="monotone"
              dataKey="equity"
              stroke={isProfit ? "#22C55E" : "#EF4444"}
              strokeWidth={2}
              fill="url(#portfolioGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}