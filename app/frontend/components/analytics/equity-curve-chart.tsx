// E:\tradedo\app\frontend\components\analytics\equity-curve-chart.tsx

"use client";

import { useEquityCurve } from "@/lib/hooks/use-analytics";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine } from "recharts";
import { TrendingUp, Loader2 } from "lucide-react";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { useState } from "react";

export function EquityCurveChart() {
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
      <div className="bg-card border border-border rounded-lg p-8 text-center corner-brackets">
        <TrendingUp className="mx-auto text-muted-foreground mb-2" size={32} />
        <p className="text-sm text-muted-foreground">No trade history yet</p>
        <p className="text-xs text-muted-foreground mt-1">
          Close some trades to see your equity curve
        </p>
      </div>
    );
  }

  // Filter by range
  let filteredCurve = curve;
  if (range === "7d") filteredCurve = curve.slice(-7);
  else if (range === "30d") filteredCurve = curve.slice(-30);

  // Format for chart
  const chartData = filteredCurve.map((point: any, i: number) => ({
    index: i,
    date: new Date(point.timestamp).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }),
    equity: point.equity,
    pnl: point.pnl,
    return: point.return_pct,
    symbol: point.symbol,
  }));

  const startingCapital = 100000;
  const finalEquity = chartData[chartData.length - 1]?.equity || startingCapital;
  const totalReturn = ((finalEquity - startingCapital) / startingCapital) * 100;
  const isProfit = totalReturn >= 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
            <TrendingUp size={16} className="text-brand" />
            EQUITY CURVE
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            Capital growth over time · {filteredCurve.length} trades
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-[10px] text-muted-foreground">TOTAL RETURN</p>
            <p className={`text-2xl font-mono font-bold ${isProfit ? "text-bull" : "text-bear"}`}>
              {formatPercent(totalReturn)}
            </p>
          </div>

          {/* Range Selector */}
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

      {/* Chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
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
              label={{ value: "Starting", fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
            />
            
            <Area
              type="monotone"
              dataKey="equity"
              stroke={isProfit ? "#22C55E" : "#EF4444"}
              strokeWidth={2}
              fill="url(#equityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Stats bar */}
      <div className="mt-4 pt-4 border-t border-border grid grid-cols-4 gap-4 text-xs">
        <div>
          <p className="text-muted-foreground">STARTING</p>
          <p className="font-mono font-bold">{formatCurrency(startingCapital, 0)}</p>
        </div>
        <div>
          <p className="text-muted-foreground">CURRENT</p>
          <p className="font-mono font-bold">{formatCurrency(finalEquity, 0)}</p>
        </div>
        <div>
          <p className="text-muted-foreground">PROFIT/LOSS</p>
          <p className={`font-mono font-bold ${isProfit ? "text-bull" : "text-bear"}`}>
            {isProfit ? "+" : ""}{formatCurrency(finalEquity - startingCapital, 0)}
          </p>
        </div>
        <div>
          <p className="text-muted-foreground">TRADES</p>
          <p className="font-mono font-bold">{curve.length}</p>
        </div>
      </div>
    </div>
  );
}