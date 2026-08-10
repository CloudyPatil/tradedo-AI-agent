// E:\tradedo\app\frontend\components\risk\diversification-card.tsx

"use client";

import { useDiversification } from "@/lib/hooks/use-risk";
import { PieChart } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function DiversificationCard() {
  const { data, isLoading } = useDiversification();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const score = data?.score || 0;
  const maxScore = data?.max_score || 100;
  const level = data?.level || "NO_POSITIONS";
  const numPositions = data?.num_positions || 0;
  const numSectors = data?.num_sectors || 0;
  const breakdown = data?.breakdown || {};

  const levelColors: Record<string, string> = {
    EXCELLENT: "text-bull",
    GOOD: "text-bull",
    MODERATE: "text-neutral",
    POOR: "text-brand",
    VERY_POOR: "text-bear",
    NO_POSITIONS: "text-muted-foreground",
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <PieChart size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">DIVERSIFICATION</h3>
      </div>

      {/* Big Score */}
      <div className="text-center py-6">
        <p className="text-6xl font-mono font-bold text-brand">
          {score.toFixed(0)}
        </p>
        <p className="text-xs text-muted-foreground font-mono mt-1">/ {maxScore}</p>
        <p className={cn("text-sm font-bold tracking-wider mt-2", levelColors[level])}>
          {level.replace(/_/g, " ")}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-3 bg-accent/30 rounded text-center">
          <p className="text-[10px] text-muted-foreground uppercase">Positions</p>
          <p className="text-xl font-mono font-bold">{numPositions}</p>
        </div>
        <div className="p-3 bg-accent/30 rounded text-center">
          <p className="text-[10px] text-muted-foreground uppercase">Sectors</p>
          <p className="text-xl font-mono font-bold">{numSectors}</p>
        </div>
      </div>

      {/* Breakdown */}
      {Object.keys(breakdown).length > 0 && (
        <div className="pt-4 border-t border-border space-y-2 text-xs">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
            Breakdown
          </p>
          {Object.entries(breakdown).map(([key, value]: [string, any]) => (
            <div key={key}>
              <div className="flex justify-between mb-1">
                <span className="text-muted-foreground capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="font-mono font-bold">{value.toFixed(1)}</span>
              </div>
              <div className="h-1 bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full bg-brand rounded-full transition-all"
                  style={{ width: `${(value / 40) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {data?.recommendation && (
        <div className="mt-3 pt-3 border-t border-border">
          <p className="text-[10px] text-muted-foreground italic">
            {data.recommendation}
          </p>
        </div>
      )}
    </div>
  );
}