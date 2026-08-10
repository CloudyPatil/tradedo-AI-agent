// E:\tradedo\app\frontend\components\risk\risk-score-gauge.tsx

"use client";

import { useRiskScore } from "@/lib/hooks/use-risk";
import { Gauge } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function RiskScoreGauge() {
  const { data, isLoading } = useRiskScore();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  const score = data?.score || 0;
  const level = data?.level || "LOW";
  const factors = data?.factors || {};
  const angle = -90 + (score / 100) * 180;

  const levelColors: Record<string, string> = {
    LOW: "text-bull",
    MODERATE: "text-neutral",
    HIGH: "text-brand",
    CRITICAL: "text-bear",
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Gauge size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">OVERALL RISK SCORE</h3>
      </div>

      {/* Gauge */}
      <div className="relative flex items-center justify-center h-48">
        <svg viewBox="0 0 200 130" className="w-full h-full">
          <path
            d="M 20 110 A 80 80 0 0 1 180 110"
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth="14"
            strokeLinecap="round"
          />
          
          <path
            d="M 20 110 A 80 80 0 0 1 180 110"
            fill="none"
            stroke="url(#risk-gauge-gradient)"
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={`${(score / 100) * 251} 251`}
          />
          
          <defs>
            <linearGradient id="risk-gauge-gradient">
              <stop offset="0%" stopColor="#22C55E" />
              <stop offset="40%" stopColor="#F59E0B" />
              <stop offset="70%" stopColor="#FF5722" />
              <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>
          </defs>
          
          <line
            x1="100"
            y1="110"
            x2="100"
            y2="35"
            stroke="hsl(var(--foreground))"
            strokeWidth="2.5"
            strokeLinecap="round"
            style={{
              transformOrigin: "100px 110px",
              transform: `rotate(${angle}deg)`,
              transition: "transform 1s ease",
            }}
          />
          
          <circle cx="100" cy="110" r="8" fill="hsl(var(--foreground))" />
          <circle cx="100" cy="110" r="4" fill={
            level === "LOW" ? "#22C55E" :
            level === "MODERATE" ? "#F59E0B" :
            level === "HIGH" ? "#FF5722" :
            "#EF4444"
          } />
        </svg>

        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
          <p className="text-4xl font-mono font-bold">{score.toFixed(0)}</p>
          <p className={cn("text-xs font-bold tracking-wider", levelColors[level])}>
            {level}
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between text-[9px] text-muted-foreground font-mono px-2 mb-4">
        <span>0 SAFE</span>
        <span>50 MODERATE</span>
        <span>100 CRITICAL</span>
      </div>

      {/* Factors */}
      {Object.keys(factors).length > 0 && (
        <div className="pt-4 border-t border-border">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
            Risk Factors
          </p>
          <div className="space-y-1.5">
            {Object.entries(factors).map(([key, value]: [string, any]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground capitalize">
                  {key.replace(/_/g, " ")}
                </span>
                <span className="font-mono font-bold">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}