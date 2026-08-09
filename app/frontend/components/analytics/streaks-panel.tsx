// E:\tradedo\app\frontend\components\analytics\streaks-panel.tsx

"use client";

import { useStreaks } from "@/lib/hooks/use-analytics";
import { Flame, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function StreaksPanel() {
  const { data, isLoading } = useStreaks();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const current = data?.current_streak || 0;
  const currentType = data?.current_streak_type || "NONE";
  const longestWin = data?.longest_win_streak || 0;
  const longestLoss = data?.longest_loss_streak || 0;
  const avgWin = data?.avg_win_streak || 0;
  const avgLoss = data?.avg_loss_streak || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Flame size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">STREAKS ANALYSIS</h3>
      </div>

      {/* Current Streak Big Card */}
      <div className={cn(
        "p-6 rounded-lg border-2 mb-4 text-center",
        currentType === "WIN" && "bg-bull/10 border-bull/30",
        currentType === "LOSS" && "bg-bear/10 border-bear/30",
        currentType === "NONE" && "bg-secondary border-border",
      )}>
        <p className="text-[10px] text-muted-foreground tracking-wider mb-2">CURRENT STREAK</p>
        <p className={cn(
          "text-5xl font-mono font-bold",
          currentType === "WIN" && "text-bull",
          currentType === "LOSS" && "text-bear",
        )}>
          {current}
        </p>
        <p className={cn(
          "text-sm font-bold mt-2 flex items-center justify-center gap-2",
          currentType === "WIN" && "text-bull",
          currentType === "LOSS" && "text-bear",
        )}>
          {currentType === "WIN" && <TrendingUp size={14} />}
          {currentType === "LOSS" && <TrendingDown size={14} />}
          {currentType === "NONE" ? "NO STREAK" : `${currentType} STREAK`}
        </p>
      </div>

      {/* Records */}
      <div className="space-y-2">
        <StreakRow 
          label="Longest Win Streak" 
          value={longestWin} 
          type="win" 
        />
        <StreakRow 
          label="Longest Loss Streak" 
          value={longestLoss} 
          type="loss" 
        />
        <StreakRow 
          label="Avg Win Streak" 
          value={avgWin.toFixed(1)} 
          type="win"
        />
        <StreakRow 
          label="Avg Loss Streak" 
          value={avgLoss.toFixed(1)} 
          type="loss"
        />
      </div>
    </div>
  );
}

function StreakRow({ label, value, type }: any) {
  return (
    <div className="flex items-center justify-between p-2 rounded bg-accent/30 text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span className={cn(
        "font-mono font-bold",
        type === "win" ? "text-bull" : "text-bear"
      )}>
        {value}
      </span>
    </div>
  );
}