// E:\tradedo\app\frontend\components\portfolio\allocation-chart.tsx

"use client";

import { useTrades } from "@/lib/hooks/use-agent";
import { useAgentStatus } from "@/lib/hooks/use-agent";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { PieChart as PieIcon } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const SECTOR_COLORS: Record<string, string> = {
  BANKING: "#3B82F6",
  IT: "#8B5CF6",
  AUTO: "#EC4899",
  PHARMA: "#10B981",
  FMCG: "#F59E0B",
  METALS: "#EF4444",
  ENERGY: "#F97316",
  REALTY: "#14B8A6",
  NBFC: "#6366F1",
  INSURANCE: "#0EA5E9",
  TELECOM: "#84CC16",
  UNKNOWN: "#6B7280",
};

export function AllocationChart() {
  const { data: tradesData, isLoading: tradesLoading } = useTrades("open");
  const { data: statusData } = useAgentStatus();

  if (tradesLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  const trades = tradesData?.trades || [];
  const capital = statusData?.agent?.capital || 100000;
  const available = statusData?.agent?.available || 0;

  // Group by sector
  const sectorMap: Record<string, number> = {};
  trades.forEach((trade: any) => {
    const sector = trade.sector || "UNKNOWN";
    sectorMap[sector] = (sectorMap[sector] || 0) + (trade.investment || 0);
  });

  const chartData = Object.entries(sectorMap).map(([sector, value]) => ({
    name: sector,
    value,
    color: SECTOR_COLORS[sector] || "#6B7280",
  }));

  // Add available cash
  if (available > 0) {
    chartData.push({
      name: "AVAILABLE",
      value: available,
      color: "#94A3B8",
    });
  }

  const hasData = chartData.length > 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <PieIcon size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">ALLOCATION</h3>
      </div>

      {!hasData ? (
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <p className="text-sm text-muted-foreground">No allocation data</p>
            <p className="text-xs text-muted-foreground mt-1">
              Open positions to see allocation
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Chart */}
          <div className="h-48 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.[0]) return null;
                    const data = payload[0].payload;
                    const pct = ((data.value / capital) * 100).toFixed(1);
                    return (
                      <div className="bg-card border border-border rounded p-2 text-xs shadow-lg">
                        <p className="font-bold">{data.name}</p>
                        <p className="text-muted-foreground">{formatCurrency(data.value, 0)}</p>
                        <p className="text-brand">{pct}%</p>
                      </div>
                    );
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Legend */}
          <div className="space-y-1.5 max-h-32 overflow-y-auto">
            {chartData.map((item, i) => {
              const pct = (item.value / capital) * 100;
              return (
                <div key={i} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-2 h-2 rounded-full" 
                      style={{ background: item.color }}
                    />
                    <span className="text-muted-foreground">{item.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs">{pct.toFixed(1)}%</span>
                    <span className="font-mono font-bold text-xs">
                      {formatCurrency(item.value, 0)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}