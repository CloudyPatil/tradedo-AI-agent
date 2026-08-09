// E:\tradedo\app\frontend\components\dashboard\sentiment-gauge.tsx

"use client";

import { useRiskScore } from "@/lib/hooks/use-risk";
import { Skeleton } from "@/components/ui/skeleton";

export function SentimentGauge() {
  const { data, isLoading } = useRiskScore();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <Skeleton className="h-3 w-24 mb-4" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const score = data?.score || 0;
  const level = data?.level || "LOW";
  const color = data?.color || "green";
  const angle = -90 + (score / 100) * 180;

  const levelColors: Record<string, string> = {
    LOW: "text-bull",
    MODERATE: "text-neutral",
    HIGH: "text-brand",
    CRITICAL: "text-bear",
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      <h3 className="text-xs font-bold tracking-widest text-muted-foreground mb-4">
        PORTFOLIO RISK
      </h3>

      <div className="relative flex items-center justify-center h-40">
        <svg viewBox="0 0 200 130" className="w-full h-full">
          <path
            d="M 20 110 A 80 80 0 0 1 180 110"
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth="12"
            strokeLinecap="round"
          />
          
          <path
            d="M 20 110 A 80 80 0 0 1 180 110"
            fill="none"
            stroke="url(#risk-gradient)"
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${(score / 100) * 251} 251`}
          />
          
          <defs>
            <linearGradient id="risk-gradient">
              <stop offset="0%" stopColor="#22C55E" />
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>
          </defs>
          
          <line
            x1="100"
            y1="110"
            x2="100"
            y2="35"
            stroke="hsl(var(--foreground))"
            strokeWidth="2"
            strokeLinecap="round"
            style={{
              transformOrigin: "100px 110px",
              transform: `rotate(${angle}deg)`,
              transition: "transform 1s ease",
            }}
          />
          
          <circle cx="100" cy="110" r="6" fill="hsl(var(--foreground))" />
        </svg>

        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
          <p className="text-3xl font-mono font-bold">{score.toFixed(0)}</p>
          <p className={`text-xs font-bold tracking-wider ${levelColors[level] || "text-foreground"}`}>
            {level}
          </p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs">
        <span className="text-muted-foreground">RISK SCORE</span>
        <span className="font-mono font-bold">{score.toFixed(0)} / 100</span>
      </div>
    </div>
  );
}