// E:\tradedo\app\frontend\components\analytics\daily-performance.tsx

"use client";

import { useDailyPerformance } from "@/lib/hooks/use-analytics";
import { Calendar, Loader2 } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";

export function DailyPerformance() {
  const { data, isLoading } = useDailyPerformance();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-brand" size={32} />
      </div>
    );
  }

  const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
  const dayData = days.map(day => ({
    day: day.slice(0, 3).toUpperCase(),
    fullDay: day,
    ...(data?.[day] || {}),
  }));

  const hasData = Object.keys(data || {}).length > 0;

  if (!hasData) {
    return (
      <div className="bg-card border border-border rounded-lg p-8 text-center corner-brackets h-full flex flex-col items-center justify-center">
        <Calendar className="text-muted-foreground mb-2" size={32} />
        <p className="text-sm text-muted-foreground">No daily data yet</p>
      </div>
    );
  }

  const bestDay = dayData.reduce((max, d) => (d.win_rate || 0) > (max.win_rate || 0) ? d : max, dayData[0]);

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Calendar size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">PERFORMANCE BY DAY</h3>
      </div>

      <div className="space-y-2">
        {dayData.map(d => {
          const isBest = d.fullDay === bestDay.fullDay && d.trades > 0;
          const winRate = d.win_rate || 0;
          
          return (
            <div 
              key={d.day} 
              className={cn(
                "p-3 rounded border transition-all",
                isBest 
                  ? "border-bull/30 bg-bull/5" 
                  : "border-border bg-accent/30"
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold flex items-center gap-1">
                  {d.day}
                  {isBest && <span className="text-[10px] text-bull">★ BEST</span>}
                </span>
                <span className={cn(
                  "text-sm font-mono font-bold",
                  winRate >= 60 && "text-bull",
                  winRate >= 40 && winRate < 60 && "text-neutral",
                  winRate < 40 && winRate > 0 && "text-bear",
                  winRate === 0 && "text-muted-foreground",
                )}>
                  {d.trades > 0 ? `${winRate}%` : "—"}
                </span>
              </div>
              
              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span>{d.trades || 0} trades</span>
                {d.avg_pnl !== undefined && (
                  <span className={d.avg_pnl >= 0 ? "text-bull" : "text-bear"}>
                    {formatCurrency(d.avg_pnl, 0)}
                  </span>
                )}
              </div>
              
              {/* Progress bar */}
              <div className="mt-2 h-1 bg-secondary rounded-full overflow-hidden">
                <div 
                  className={cn(
                    "h-full transition-all",
                    winRate >= 60 && "bg-bull",
                    winRate >= 40 && winRate < 60 && "bg-neutral",
                    winRate < 40 && winRate > 0 && "bg-bear",
                  )}
                  style={{ width: `${winRate}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}