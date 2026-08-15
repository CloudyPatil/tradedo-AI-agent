// E:\tradedo\app\frontend\components\markets\indices-grid.tsx

"use client";

import { useGlobalMarkets } from "@/lib/hooks/use-market";
import { TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { cn, formatNumber, formatPercent } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function IndicesGrid() {
  const { data, isLoading } = useGlobalMarkets();

  if (isLoading) {
    return (
      <div className="grid grid-cols-6 gap-3">
        {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-28" />)}
      </div>
    );
  }

  const raw = data?.raw_data || {};

  const indices = [
    { key: "NIFTY", label: "NIFTY 50", data: raw.NIFTY },
    { key: "SENSEX", label: "SENSEX", data: raw.SENSEX },
    { key: "BANK_NIFTY", label: "BANK NIFTY", data: raw.BANK_NIFTY },
    { key: "INDIA_VIX", label: "INDIA VIX", data: raw.INDIA_VIX },
    { key: "USDINR", label: "USD/INR", data: raw.USDINR },
    { key: "CRUDE", label: "CRUDE OIL", data: raw.CRUDE },
  ];

  return (
    <div>
      <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold mb-3">
        Key Indices
      </p>
      <div className="grid grid-cols-6 gap-3">
        {indices.map(idx => (
          <IndexCard key={idx.key} label={idx.label} data={idx.data} />
        ))}
      </div>
    </div>
  );
}

function IndexCard({ label, data }: any) {
  if (!data) {
    return (
      <div className="p-4 bg-card border border-border rounded-lg text-center">
        <p className="text-[10px] text-muted-foreground">{label}</p>
        <p className="text-sm text-muted-foreground mt-2">No data</p>
      </div>
    );
  }

  const isPositive = data.change >= 0;
  const value = data.value || 0;
  const changePct = data.change_pct || 0;

  return (
    <div className="p-4 bg-card border border-border rounded-lg corner-brackets ticker-card">
      <div className="flex items-start justify-between mb-2">
        <p className="text-[10px] text-muted-foreground tracking-widest font-bold">
          {label}
        </p>
        {isPositive ? (
          <TrendingUp size={12} className="text-bull" />
        ) : (
          <TrendingDown size={12} className="text-bear" />
        )}
      </div>
      
      <p className="text-lg font-mono font-bold tabular-nums mb-1">
        {formatNumber(value)}
      </p>
      
      <p className={cn(
        "text-xs font-mono tabular-nums",
        isPositive ? "text-bull" : "text-bear"
      )}>
        {formatPercent(changePct)}
      </p>

      <p className="text-[10px] text-muted-foreground mt-1">
        {data.direction}
      </p>
    </div>
  );
}