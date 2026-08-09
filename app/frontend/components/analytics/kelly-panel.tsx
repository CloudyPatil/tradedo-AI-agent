// E:\tradedo\app\frontend\components\analytics\kelly-panel.tsx

"use client";

import { useKelly } from "@/lib/hooks/use-analytics";
import { Calculator } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function KellyPanel() {
  const { data, isLoading } = useKelly();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const kelly = data?.kelly_pct || 0;
  const recommended = data?.recommended_size_pct || 0;
  const interpretation = data?.interpretation || "Insufficient data";

  const isNegative = kelly < 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Calculator size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">KELLY CRITERION</h3>
      </div>

      {/* Big Kelly Number */}
      <div className="text-center py-6">
        <p className="text-[10px] text-muted-foreground tracking-wider mb-2">FULL KELLY</p>
        <p className={cn(
          "text-5xl font-mono font-bold",
          isNegative ? "text-bear" : "text-brand"
        )}>
          {kelly.toFixed(1)}%
        </p>
      </div>

      {/* Recommended Size */}
      <div className="p-3 bg-brand/10 border border-brand/30 rounded-md mb-3">
        <p className="text-[10px] text-brand tracking-wider font-bold mb-1">RECOMMENDED (25% Kelly)</p>
        <p className="text-2xl font-mono font-bold text-brand">
          {recommended.toFixed(2)}%
        </p>
        <p className="text-[10px] text-muted-foreground mt-1">
          Safer position sizing
        </p>
      </div>

      {/* Interpretation */}
      <div className="p-2 bg-accent/30 rounded text-[10px] text-muted-foreground text-center">
        {interpretation}
      </div>

      <div className="mt-4 pt-3 border-t border-border">
        <p className="text-[10px] text-muted-foreground leading-relaxed">
          Kelly Criterion suggests optimal position size for long-term capital growth. 
          Use 25% Kelly for safer sizing.
        </p>
      </div>
    </div>
  );
}