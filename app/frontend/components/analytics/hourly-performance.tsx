// E:\tradedo\app\frontend\components\analytics\hourly-performance.tsx

"use client";

import { useHourlyPerformance } from "@/lib/hooks/use-analytics";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Clock, Loader2 } from "lucide-react";

export function HourlyPerformance() {
  const { data, isLoading } = useHourlyPerformance();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-80 flex items-center justify-center">
        <Loader2 className="animate-spin text-brand" size={32} />
      </div>
    );
  }

  const chartData = Object.entries(data || {}).map(([hour, stats]: [string, any]) => ({
    hour,
    win_rate: stats.win_rate || 0,
    trades: stats.trades || 0,
    avg_pnl: stats.avg_pnl || 0,
  }));

  if (chartData.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-8 text-center corner-brackets">
        <Clock className="mx-auto text-muted-foreground mb-2" size={32} />
        <p className="text-sm text-muted-foreground">No hourly data yet</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center gap-2 mb-4">
        <Clock size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">PERFORMANCE BY HOUR</h3>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
            
            <XAxis 
              dataKey="hour"
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10, fontFamily: "monospace" }}
            />
            
            <YAxis
              stroke="hsl(var(--muted-foreground))"
              tick={{ fontSize: 10 }}
              label={{ value: "Win Rate %", angle: -90, position: "insideLeft", style: { fontSize: 10 } }}
            />
            
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.[0]) return null;
                const data = payload[0].payload;
                return (
                  <div className="bg-card border border-border rounded p-2 text-xs shadow-lg">
                    <p className="font-bold">{data.hour}</p>
                    <p>Win Rate: <span className="font-mono font-bold">{data.win_rate}%</span></p>
                    <p>Trades: <span className="font-mono">{data.trades}</span></p>
                    <p className={data.avg_pnl >= 0 ? "text-bull" : "text-bear"}>
                      Avg P&L: <span className="font-mono font-bold">₹{data.avg_pnl.toFixed(0)}</span>
                    </p>
                  </div>
                );
              }}
            />
            
            <Bar dataKey="win_rate" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={
                  entry.win_rate >= 60 ? "#22C55E" :
                  entry.win_rate >= 40 ? "#F59E0B" :
                  "#EF4444"
                } />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs justify-center">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-bull" />
          <span className="text-muted-foreground">Win rate ≥ 60%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-neutral" />
          <span className="text-muted-foreground">40-59%</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-bear" />
          <span className="text-muted-foreground">&lt; 40%</span>
        </div>
      </div>
    </div>
  );
}