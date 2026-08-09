// E:\tradedo\app\frontend\components\dashboard\positions-widget.tsx

"use client";

import { useTodaysPerformance, useAgentStatus } from "@/lib/hooks/use-agent";
import { Skeleton } from "@/components/ui/skeleton";

export function PositionsWidget() {
  const { data: perf, isLoading: perfLoading } = useTodaysPerformance();
  const { data: agent } = useAgentStatus();

  if (perfLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <Skeleton className="h-3 w-24 mb-4" />
        <Skeleton className="h-16 w-full mb-4" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  const openTrades = agent?.open_trades?.length || 0;
  const totalTrades = perf?.total_trades || 0;
  const winRate = perf?.win_rate || 0;
  const winning = perf?.winning_trades || 0;
  const losing = perf?.losing_trades || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      <h3 className="text-xs font-bold tracking-widest text-muted-foreground mb-4">
        ACTIVE POSITIONS
      </h3>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-muted-foreground">OPEN</p>
          <p className="text-3xl font-mono font-bold">
            {openTrades.toString().padStart(2, "0")}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">WIN RATE</p>
          <p className="text-3xl font-mono font-bold text-bull">
            {winRate.toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 pt-3 border-t border-border">
        <div>
          <p className="text-xs text-muted-foreground">WINS TODAY</p>
          <p className="text-2xl font-mono font-bold text-bull">
            {winning.toString().padStart(2, "0")}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">LOSSES</p>
          <p className="text-2xl font-mono font-bold text-bear">
            {losing.toString().padStart(2, "0")}
          </p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-border">
        <p className="text-xs text-muted-foreground">TOTAL TRADES</p>
        <p className="font-bold mt-1 font-mono">{totalTrades}</p>
      </div>
    </div>
  );
}