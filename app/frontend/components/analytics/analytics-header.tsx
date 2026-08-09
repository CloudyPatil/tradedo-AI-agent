// E:\tradedo\app\frontend\components\analytics\analytics-header.tsx

"use client";

import { BarChart3, RefreshCw, TrendingUp, TrendingDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePerformance } from "@/lib/hooks/use-analytics";
import { useQueryClient } from "@tanstack/react-query";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function AnalyticsHeader() {
  const { data, isLoading, isFetching } = usePerformance();
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["performance"] });
    queryClient.invalidateQueries({ queryKey: ["equity-curve"] });
    queryClient.invalidateQueries({ queryKey: ["sharpe-ratios"] });
    queryClient.invalidateQueries({ queryKey: ["drawdown"] });
  };

  const basic = data?.basic;
  const totalPnl = basic?.total_pnl || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <BarChart3 className="text-brand" size={24} />
              PERFORMANCE ANALYTICS
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider mt-1">
              PROFESSIONAL TRADING METRICS · REAL-TIME
            </p>
          </div>

          {isLoading ? (
            <div className="pl-6 border-l border-border">
              <Skeleton className="h-4 w-24 mb-1" />
              <Skeleton className="h-8 w-32" />
            </div>
          ) : (
            <div className="pl-6 border-l border-border">
              <p className="text-[10px] text-muted-foreground tracking-wider">TOTAL P&L</p>
              <p className={cn(
                "text-3xl font-mono font-bold flex items-center gap-2",
                totalPnl >= 0 ? "text-bull" : "text-bear"
              )}>
                {totalPnl >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                {formatCurrency(totalPnl, 0)}
              </p>
            </div>
          )}
        </div>

        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={isFetching}
        >
          <RefreshCw size={14} className={cn("mr-2", isFetching && "animate-spin")} />
          REFRESH
        </Button>
      </div>

      {!data?.has_enough_data && !isLoading && (
        <div className="mt-4 p-3 bg-neutral/10 border border-neutral/20 rounded-md text-xs text-neutral">
          ℹ️ Analytics require at least 5 closed trades. Trade more to see full metrics.
        </div>
      )}
    </div>
  );
}