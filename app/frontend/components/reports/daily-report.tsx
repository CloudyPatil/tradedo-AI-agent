// E:\tradedo\app\frontend\components\reports\daily-report.tsx

"use client";

import { useTodaysPerformance } from "@/lib/hooks/use-agent";
import { useTrades } from "@/lib/hooks/use-agent";
import { Calendar, TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { formatCurrency, formatTime, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function DailyReport() {
  const { data: perf, isLoading: perfLoading } = useTodaysPerformance();
  const { data: tradesData, isLoading: tradesLoading } = useTrades("all");

  if (perfLoading || tradesLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6" id="daily-report">
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const trades = (tradesData?.trades || []).filter((t: any) => {
    const today = new Date().toDateString();
    return new Date(t.entry_time).toDateString() === today;
  });

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets" id="daily-report">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Calendar size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">TODAY'S REPORT</h3>
        </div>
        <span className="text-xs text-muted-foreground font-mono">
          {new Date().toLocaleDateString("en-IN", { 
            weekday: "long", 
            day: "2-digit", 
            month: "short", 
            year: "numeric" 
          })}
        </span>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="p-3 bg-accent/30 rounded text-center">
          <p className="text-[10px] text-muted-foreground uppercase">Total Trades</p>
          <p className="text-2xl font-mono font-bold">{perf?.total_trades || 0}</p>
        </div>
        <div className="p-3 bg-bull/10 rounded text-center">
          <p className="text-[10px] text-bull uppercase font-bold">Wins</p>
          <p className="text-2xl font-mono font-bold text-bull">{perf?.winning_trades || 0}</p>
        </div>
        <div className="p-3 bg-bear/10 rounded text-center">
          <p className="text-[10px] text-bear uppercase font-bold">Losses</p>
          <p className="text-2xl font-mono font-bold text-bear">{perf?.losing_trades || 0}</p>
        </div>
        <div className={cn(
          "p-3 rounded text-center",
          (perf?.total_pnl || 0) >= 0 ? "bg-bull/10" : "bg-bear/10"
        )}>
          <p className="text-[10px] uppercase font-bold">Day P&L</p>
          <p className={cn(
            "text-2xl font-mono font-bold",
            (perf?.total_pnl || 0) >= 0 ? "text-bull" : "text-bear"
          )}>
            {formatCurrency(perf?.total_pnl || 0, 0)}
          </p>
        </div>
      </div>

      {/* Today's Trades */}
      {trades.length === 0 ? (
        <div className="text-center py-8 text-sm text-muted-foreground">
          No trades executed today
        </div>
      ) : (
        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
            Today's Trades ({trades.length})
          </p>
          <div className="space-y-2">
            {trades.map((trade: any) => (
              <div 
                key={trade.id}
                className={cn(
                  "p-3 rounded border flex items-center justify-between text-xs",
                  trade.status === "OPEN" && "border-brand/30 bg-brand/5",
                  trade.pnl > 0 && "border-bull/30 bg-bull/5",
                  trade.pnl < 0 && "border-bear/30 bg-bear/5",
                )}
              >
                <div className="flex items-center gap-3">
                  {trade.direction === "LONG" ? 
                    <TrendingUp size={12} className="text-bull" /> : 
                    <TrendingDown size={12} className="text-bear" />
                  }
                  <div>
                    <p className="font-mono font-bold">{trade.symbol.replace(".NS", "")}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {formatTime(trade.entry_time)}
                    </p>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className={cn(
                    "font-mono font-bold",
                    trade.pnl > 0 && "text-bull",
                    trade.pnl < 0 && "text-bear",
                    trade.status === "OPEN" && "text-brand",
                  )}>
                    {trade.status === "OPEN" 
                      ? "RUNNING" 
                      : `${trade.pnl > 0 ? "+" : ""}${formatCurrency(trade.pnl || 0, 0)}`}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    {trade.status?.replace(/_/g, " ")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}