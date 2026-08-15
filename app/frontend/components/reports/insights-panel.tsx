// E:\tradedo\app\frontend\components\reports\insights-panel.tsx

"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { Brain, Loader2, TrendingUp, TrendingDown, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function InsightsPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ["journal-insights"],
    queryFn: () => api.get("/journal/insights").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });

  const { data: bestPatterns } = useQuery({
    queryKey: ["best-patterns"],
    queryFn: () => api.get("/journal/patterns/best").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });

  const { data: worstPatterns } = useQuery({
    queryKey: ["worst-patterns"],
    queryFn: () => api.get("/journal/patterns/worst").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Brain size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">🧠 AI INSIGHTS</h3>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="animate-spin text-brand" size={20} />
        </div>
      ) : !data?.data_ready_for_rl ? (
        <div className="p-4 bg-neutral/10 border border-neutral/20 rounded text-xs text-center">
          <AlertCircle size={20} className="mx-auto text-neutral mb-2" />
          <p className="font-bold mb-1">Building Insights...</p>
          <p className="text-muted-foreground">
            Need {20 - (data?.total_closed_trades || 0)} more trades for AI insights
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          
          {/* Best Patterns */}
          {bestPatterns?.patterns && bestPatterns.patterns.length > 0 && (
            <div>
              <p className="text-[10px] text-bull uppercase tracking-wider font-bold mb-2 flex items-center gap-1">
                <TrendingUp size={12} />
                Winning Patterns
              </p>
              <div className="space-y-2">
                {bestPatterns.patterns.slice(0, 3).map((p: any, i: number) => (
                  <div key={i} className="p-2 bg-bull/5 border border-bull/20 rounded text-xs">
                    <p className="font-mono font-bold text-bull">{p.pattern}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {p.win_rate}% win rate ({p.trades} trades)
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Worst Patterns */}
          {worstPatterns?.patterns && worstPatterns.patterns.length > 0 && (
            <div>
              <p className="text-[10px] text-bear uppercase tracking-wider font-bold mb-2 flex items-center gap-1">
                <TrendingDown size={12} />
                Losing Patterns
              </p>
              <div className="space-y-2">
                {worstPatterns.patterns.slice(0, 3).map((p: any, i: number) => (
                  <div key={i} className="p-2 bg-bear/5 border border-bear/20 rounded text-xs">
                    <p className="font-mono font-bold text-bear">{p.pattern}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {p.win_rate}% win rate - {p.recommendation}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Summary */}
          <div className="pt-3 border-t border-border">
            <p className="text-[10px] text-muted-foreground">
              Based on {data?.total_closed_trades} closed trades
            </p>
          </div>
        </div>
      )}
    </div>
  );
}