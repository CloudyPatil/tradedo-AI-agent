// E:\tradedo\app\frontend\components\risk\risk-header.tsx

"use client";

import { Shield, RefreshCw, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRiskScore } from "@/lib/hooks/use-risk";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function RiskHeader() {
  const { data, isLoading, isFetching } = useRiskScore();
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["risk-report"] });
    queryClient.invalidateQueries({ queryKey: ["risk-score"] });
    queryClient.invalidateQueries({ queryKey: ["portfolio-heat"] });
    queryClient.invalidateQueries({ queryKey: ["stress-test"] });
  };

  const level = data?.level || "UNKNOWN";
  const score = data?.score || 0;

  const levelColors: Record<string, string> = {
    LOW: "text-bull bg-bull/10 border-bull/30",
    MODERATE: "text-neutral bg-neutral/10 border-neutral/30",
    HIGH: "text-brand bg-brand/10 border-brand/30",
    CRITICAL: "text-bear bg-bear/10 border-bear/30",
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <Shield className="text-brand" size={24} />
              RISK DASHBOARD
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider mt-1">
              PORTFOLIO RISK MANAGEMENT · REAL-TIME
            </p>
          </div>

          {isLoading ? (
            <div className="pl-6 border-l border-border">
              <Skeleton className="h-4 w-24 mb-1" />
              <Skeleton className="h-8 w-32" />
            </div>
          ) : (
            <div className={cn(
              "px-4 py-2 border rounded-md",
              levelColors[level] || "text-muted-foreground border-border"
            )}>
              <p className="text-[10px] tracking-wider font-bold">CURRENT RISK</p>
              <p className="text-2xl font-mono font-bold flex items-center gap-2">
                {(level === "HIGH" || level === "CRITICAL") && <AlertTriangle size={18} />}
                {level}
              </p>
              <p className="text-[10px] font-mono">SCORE: {score.toFixed(1)}/100</p>
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

      {data?.recommendation && (
        <div className={cn(
          "mt-4 p-3 rounded-md text-xs",
          level === "LOW" && "bg-bull/10 text-bull",
          level === "MODERATE" && "bg-neutral/10 text-neutral",
          level === "HIGH" && "bg-brand/10 text-brand",
          level === "CRITICAL" && "bg-bear/10 text-bear",
        )}>
          <strong>💡 {data.recommendation}</strong>
        </div>
      )}
    </div>
  );
}