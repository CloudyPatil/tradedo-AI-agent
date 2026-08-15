// E:\tradedo\app\frontend\components\markets\markets-header.tsx

"use client";

import { TrendingUp, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useQueryClient } from "@tanstack/react-query";
import { useGlobalMarkets } from "@/lib/hooks/use-market";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { useState, useEffect } from "react";
import { formatTime } from "@/lib/utils";

export function MarketsHeader() {
  const { data, isLoading, isFetching } = useGlobalMarkets();
  const queryClient = useQueryClient();
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleRefresh = () => {
    queryClient.invalidateQueries();
  };

  const bias = data?.overall_bias || "NEUTRAL";

  const biasColors: Record<string, string> = {
    BULLISH: "bg-bull/10 text-bull border-bull/30",
    BEARISH: "bg-bear/10 text-bear border-bear/30",
    NEUTRAL: "bg-neutral/10 text-neutral border-neutral/30",
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <TrendingUp className="text-brand" size={24} />
              MARKETS
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider mt-1">
              LIVE MARKET DATA · GLOBAL INDICES · SECTOR ANALYSIS
            </p>
          </div>

          {isLoading ? (
            <Skeleton className="h-16 w-40" />
          ) : (
            <div className={cn(
              "px-4 py-2 rounded-md border",
              biasColors[bias]
            )}>
              <p className="text-[10px] tracking-wider font-bold">MARKET BIAS</p>
              <p className="text-2xl font-mono font-bold">{bias}</p>
              <p className="text-[10px] font-mono">
                Score: {data?.overall_score?.toFixed(2) || "0.00"}
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right text-xs font-mono">
            <p className="text-foreground font-bold">
              {now ? formatTime(now) : "--:--:--"}
            </p>
            <p className="text-muted-foreground">IST</p>
          </div>

          <Button variant="outline" onClick={handleRefresh} disabled={isFetching}>
            <RefreshCw size={14} className={cn("mr-2", isFetching && "animate-spin")} />
            REFRESH
          </Button>
        </div>
      </div>
    </div>
  );
}