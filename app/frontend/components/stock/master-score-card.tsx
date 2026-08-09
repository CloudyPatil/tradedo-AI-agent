// E:\tradedo\app\frontend\components\stock\master-score-card.tsx

"use client";

import { useMasterScore } from "@/lib/hooks/use-stock";
import { Loader2, Award, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  symbol: string;
}

export function MasterScoreCard({ symbol }: Props) {
  const { data, isLoading } = useMasterScore(symbol);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-brand" size={32} />
      </div>
    );
  }

  const score = data?.final_score || 0;
  const maxScore = data?.max_score || 200;
  const scorePct = data?.score_pct || 0;
  const verdict = data?.verdict || "UNKNOWN";
  const breakdown = data?.score_breakdown || {};
  const penalties = data?.penalty_breakdown || {};

  const verdictColors: Record<string, string> = {
    STRONG: "text-bull bg-bull/10 border-bull/30",
    GOOD: "text-brand bg-brand/10 border-brand/30",
    WEAK: "text-neutral bg-neutral/10 border-neutral/30",
    SKIP: "text-bear bg-bear/10 border-bear/30",
    HOLD: "text-muted-foreground bg-muted/30",
    BANNED: "text-bear bg-bear/20",
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
          <Award size={16} className="text-brand" />
          MASTER SCORE
        </h3>
      </div>

      {/* Score Display */}
      <div className="text-center py-4">
        <p className="text-5xl font-mono font-black text-brand">
          {score.toFixed(1)}
        </p>
        <p className="text-xs text-muted-foreground mt-1 font-mono">
          / {maxScore} pts
        </p>
        <p className="text-lg font-bold text-foreground mt-1">
          {scorePct.toFixed(1)}%
        </p>
      </div>

      {/* Progress Bar */}
      <div className="h-2 bg-secondary rounded-full overflow-hidden mb-3">
        <div
          className="h-full bg-gradient-to-r from-bear via-neutral to-bull rounded-full transition-all"
          style={{ width: `${scorePct}%` }}
        />
      </div>

      {/* Verdict */}
      <div className={cn(
        "text-center py-2 px-3 rounded-md border font-bold text-sm mb-4",
        verdictColors[verdict] || verdictColors.HOLD
      )}>
        {verdict}
      </div>

      {/* Breakdown */}
      <div className="flex-1 space-y-1.5">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium mb-2">
          Score Breakdown
        </p>
        {Object.entries(breakdown).map(([key, value]: [string, any]) => (
          <BreakdownRow key={key} label={key} value={value} />
        ))}
      </div>

      {/* Penalties */}
      {Object.keys(penalties).length > 0 && (
        <div className="mt-3 pt-3 border-t border-border">
          <p className="text-[10px] text-bear uppercase tracking-wider font-medium mb-2">
            Penalties
          </p>
          {Object.entries(penalties).map(([key, value]: [string, any]) => (
            <div key={key} className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground capitalize">
                {key.replace(/_/g, " ")}
              </span>
              <span className="font-mono text-bear font-bold">-{value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BreakdownRow({ label, value }: { label: string; value: number }) {
  const cleanLabel = label.replace(/_/g, " ").replace(/score/gi, "").trim();
  
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground capitalize">{cleanLabel}</span>
      <span className="font-mono font-bold text-foreground">
        {value.toFixed(1)}
      </span>
    </div>
  );
}