// E:\tradedo\app\frontend\components\portfolio\portfolio-header.tsx

"use client";

import { Wallet, RefreshCw, TrendingUp, TrendingDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAgentStatus } from "@/lib/hooks/use-agent";
import { useQueryClient } from "@tanstack/react-query";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function PortfolioHeader() {
  const { data, isLoading, isFetching } = useAgentStatus();
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    queryClient.invalidateQueries();
  };

  const agent = data?.agent;
  const totalPnl = agent?.total_pnl || 0;
  const totalPnlPct = agent?.total_pnl_pct || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <Wallet className="text-brand" size={24} />
              PORTFOLIO
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider mt-1">
              PAPER TRADING · VIRTUAL CAPITAL
            </p>
          </div>

          {isLoading ? (
            <Skeleton className="h-16 w-40" />
          ) : (
            <div className="pl-6 border-l border-border">
              <p className="text-[10px] text-muted-foreground tracking-wider">TOTAL P&L</p>
              <p className={cn(
                "text-3xl font-mono font-bold flex items-center gap-2",
                totalPnl >= 0 ? "text-bull" : "text-bear"
              )}>
                {totalPnl >= 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
                {totalPnl >= 0 ? "+" : ""}{formatCurrency(totalPnl, 0)}
              </p>
              <p className={cn(
                "text-xs font-mono",
                totalPnl >= 0 ? "text-bull" : "text-bear"
              )}>
                {totalPnl >= 0 ? "+" : ""}{totalPnlPct.toFixed(2)}%
              </p>
            </div>
          )}
        </div>

        <Button variant="outline" onClick={handleRefresh} disabled={isFetching}>
          <RefreshCw size={14} className={cn("mr-2", isFetching && "animate-spin")} />
          REFRESH
        </Button>
      </div>
    </div>
  );
}