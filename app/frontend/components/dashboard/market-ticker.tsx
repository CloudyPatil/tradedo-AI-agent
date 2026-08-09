// E:\tradedo\app\frontend\components\dashboard\market-ticker.tsx

"use client";

import { TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import { cn, formatNumber, formatPercent } from "@/lib/utils";
import { useGlobalMarkets } from "@/lib/hooks/use-market";
import { Skeleton } from "@/components/ui/skeleton";

interface TickerProps {
  label: string;
  value: number;
  change: number;
  changePercent: number;
  isLoading?: boolean;
}

export function MarketTicker({ label, value, change, changePercent }: TickerProps) {
  const isPositive = change >= 0;
  const heights = [45, 62, 38, 71, 55, 48, 82, 67, 43, 59, 74, 51, 68, 39, 77, 63, 46, 72, 58, 66];

  return (
    <div className="ticker-card p-4 bg-card border border-border rounded-lg corner-brackets">
      <div className="flex items-start justify-between mb-2">
        <p className="text-[10px] text-muted-foreground tracking-widest font-medium">
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
        {formatPercent(changePercent)}
      </p>

      <div className="h-8 mt-2 flex items-end gap-0.5">
        {heights.map((height, i) => (
          <div
            key={i}
            className={cn(
              "flex-1 rounded-sm",
              isPositive ? "bg-bull/40" : "bg-bear/40"
            )}
            style={{ height: `${height}%` }}
          />
        ))}
      </div>
    </div>
  );
}

function TickerSkeleton() {
  return (
    <div className="p-4 bg-card border border-border rounded-lg">
      <Skeleton className="h-3 w-16 mb-2" />
      <Skeleton className="h-6 w-24 mb-1" />
      <Skeleton className="h-3 w-16 mb-2" />
      <Skeleton className="h-8 w-full" />
    </div>
  );
}

export function MarketTickerBar() {
  const { data, isLoading, error } = useGlobalMarkets();

  if (isLoading) {
    return (
      <div className="grid grid-cols-6 gap-3">
        {[...Array(6)].map((_, i) => (
          <TickerSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error || !data?.raw_data) {
    return (
      <div className="grid grid-cols-6 gap-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="p-4 bg-card border border-border rounded-lg text-center">
            <p className="text-xs text-muted-foreground">Data unavailable</p>
          </div>
        ))}
      </div>
    );
  }

  const raw = data.raw_data;

  // Map backend data to our tickers
  const tickers = [
    {
      label: "NIFTY 50",
      value: raw.NIFTY?.value || 0,
      change: raw.NIFTY?.change || 0,
      changePercent: raw.NIFTY?.change_pct || 0,
    },
    {
      label: "SENSEX",
      value: raw.SENSEX?.value || 0,
      change: raw.SENSEX?.change || 0,
      changePercent: raw.SENSEX?.change_pct || 0,
    },
    {
      label: "BANK NIFTY",
      value: raw.BANK_NIFTY?.value || 0,
      change: raw.BANK_NIFTY?.change || 0,
      changePercent: raw.BANK_NIFTY?.change_pct || 0,
    },
    {
      label: "INDIA VIX",
      value: raw.INDIA_VIX?.value || 0,
      change: raw.INDIA_VIX?.change || 0,
      changePercent: raw.INDIA_VIX?.change_pct || 0,
    },
    {
      label: "USD/INR",
      value: raw.USDINR?.value || 0,
      change: raw.USDINR?.change || 0,
      changePercent: raw.USDINR?.change_pct || 0,
    },
    {
      label: "CRUDE",
      value: raw.CRUDE?.value || 0,
      change: raw.CRUDE?.change || 0,
      changePercent: raw.CRUDE?.change_pct || 0,
    },
  ];

  return (
    <div className="grid grid-cols-6 gap-3">
      {tickers.map(ticker => (
        <MarketTicker key={ticker.label} {...ticker} />
      ))}
    </div>
  );
}