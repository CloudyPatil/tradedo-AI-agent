// E:\tradedo\app\frontend\components\markets\global-markets-panel.tsx

"use client";

import { useGlobalMarkets } from "@/lib/hooks/use-market";
import { Globe, TrendingUp, TrendingDown } from "lucide-react";
import { cn, formatNumber, formatPercent } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const GLOBAL_INDICES = [
  { key: "US_DOW", label: "Dow Jones", region: "🇺🇸 US" },
  { key: "US_SP500", label: "S&P 500", region: "🇺🇸 US" },
  { key: "US_NASDAQ", label: "Nasdaq", region: "🇺🇸 US" },
  { key: "NIKKEI", label: "Nikkei 225", region: "🇯🇵 Japan" },
  { key: "HANG_SENG", label: "Hang Seng", region: "🇭🇰 HK" },
  { key: "SHANGHAI", label: "Shanghai", region: "🇨🇳 China" },
  { key: "GOLD", label: "Gold", region: "🌍 Commodity" },
  { key: "SILVER", label: "Silver", region: "🌍 Commodity" },
  { key: "DOLLAR_INDEX", label: "USD Index", region: "🌍 Currency" },
];

export function GlobalMarketsPanel() {
  const { data, isLoading } = useGlobalMarkets();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="grid grid-cols-3 gap-3">
          {[...Array(9)].map((_, i) => <Skeleton key={i} className="h-20" />)}
        </div>
      </div>
    );
  }

  const raw = data?.raw_data || {};
  const usSignal = data?.us_signal || "NO_DATA";
  const asianSignal = data?.asian_signal || "NO_DATA";

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">GLOBAL MARKETS</h3>
        </div>
        
        <div className="flex items-center gap-4 text-xs">
          <SignalBadge label="US" signal={usSignal} />
          <SignalBadge label="Asian" signal={asianSignal} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {GLOBAL_INDICES.map(idx => (
          <GlobalIndexCard 
            key={idx.key} 
            label={idx.label}
            region={idx.region}
            data={raw[idx.key]}
          />
        ))}
      </div>

      {/* Overall context */}
      <div className="mt-4 pt-4 border-t border-border grid grid-cols-4 gap-3 text-xs">
        <ContextItem 
          label="US Markets" 
          value={usSignal} 
          change={data?.us_change_pct} 
        />
        <ContextItem 
          label="Asian Markets" 
          value={asianSignal} 
          change={data?.asian_change_pct} 
        />
        <ContextItem 
          label="Crude Oil" 
          value={data?.crude_signal} 
        />
        <ContextItem 
          label="India VIX" 
          value={data?.vix_level}
          vixValue={data?.vix_value}
        />
      </div>
    </div>
  );
}

function GlobalIndexCard({ label, region, data }: any) {
  if (!data) {
    return (
      <div className="p-3 bg-accent/30 rounded text-center">
        <p className="text-[10px] text-muted-foreground">{region}</p>
        <p className="text-xs font-bold">{label}</p>
        <p className="text-xs text-muted-foreground mt-1">—</p>
      </div>
    );
  }

  const isPositive = data.change >= 0;

  return (
    <div className="p-3 bg-accent/30 rounded ticker-card">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-muted-foreground">{region}</span>
        {isPositive ? (
          <TrendingUp size={10} className="text-bull" />
        ) : (
          <TrendingDown size={10} className="text-bear" />
        )}
      </div>
      
      <p className="text-xs font-bold mb-1">{label}</p>
      <p className="text-sm font-mono font-bold tabular-nums">
        {formatNumber(data.value)}
      </p>
      <p className={cn(
        "text-[10px] font-mono",
        isPositive ? "text-bull" : "text-bear"
      )}>
        {formatPercent(data.change_pct || 0)}
      </p>
    </div>
  );
}

function SignalBadge({ label, signal }: any) {
  const colors: Record<string, string> = {
    BULLISH: "text-bull",
    BEARISH: "text-bear",
    NEUTRAL: "text-neutral",
    NO_DATA: "text-muted-foreground",
  };

  return (
    <div className="flex items-center gap-1">
      <span className="text-muted-foreground">{label}:</span>
      <span className={cn("font-bold", colors[signal])}>{signal}</span>
    </div>
  );
}

function ContextItem({ label, value, change, vixValue }: any) {
  return (
    <div className="p-2 bg-accent/30 rounded">
      <p className="text-[10px] text-muted-foreground uppercase">{label}</p>
      <p className="text-sm font-bold">{value?.replace(/_/g, " ") || "—"}</p>
      {change !== undefined && (
        <p className={cn(
          "text-[10px] font-mono",
          change >= 0 ? "text-bull" : "text-bear"
        )}>
          {change >= 0 ? "+" : ""}{change?.toFixed(2)}%
        </p>
      )}
      {vixValue !== undefined && (
        <p className="text-[10px] font-mono text-muted-foreground">
          Value: {vixValue?.toFixed(1)}
        </p>
      )}
    </div>
  );
}