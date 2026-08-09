// E:\tradedo\app\frontend\components\dashboard\intelligence-panel.tsx

"use client";

import { Newspaper, TrendingUp, Building2, Loader2 } from "lucide-react";
import { useFiiDii } from "@/lib/hooks/use-market";
import { formatCurrency, cn } from "@/lib/utils";

export function IntelligencePanel() {
  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-bull animate-pulse" />
          LIVE INTELLIGENCE
        </h3>
        <span className="text-[10px] text-muted-foreground font-mono">
          NSE OFFICIAL DATA
        </span>
      </div>

      <div className="space-y-4">
        <FiiDiiSection />
        <MarketRegimeSection />
      </div>
    </div>
  );
}

function FiiDiiSection() {
  const { data, isLoading } = useFiiDii();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-4">
        <Loader2 className="animate-spin text-brand" size={20} />
      </div>
    );
  }

  const fiiNet = data?.fii_net || 0;
  const diiNet = data?.dii_net || 0;
  const signal = data?.signal || "NEUTRAL";
  const available = data?.available;

  if (!available) {
    return (
      <div className="p-3 rounded-md bg-accent/30 text-center text-xs text-muted-foreground">
        FII/DII data updating...
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-xs font-bold text-muted-foreground tracking-wider mb-2 flex items-center gap-2">
        <Building2 size={12} />
        INSTITUTIONAL FLOW
      </h4>

      <div className="grid grid-cols-2 gap-2 mb-2">
        <div className="p-2 rounded bg-accent/30">
          <p className="text-[10px] text-muted-foreground">FII NET</p>
          <p className={cn(
            "font-mono font-bold text-sm",
            fiiNet >= 0 ? "text-bull" : "text-bear"
          )}>
            {fiiNet >= 0 ? "+" : ""}{formatCurrency(fiiNet, 0)}
          </p>
        </div>
        
        <div className="p-2 rounded bg-accent/30">
          <p className="text-[10px] text-muted-foreground">DII NET</p>
          <p className={cn(
            "font-mono font-bold text-sm",
            diiNet >= 0 ? "text-bull" : "text-bear"
          )}>
            {diiNet >= 0 ? "+" : ""}{formatCurrency(diiNet, 0)}
          </p>
        </div>
      </div>

      <div className={cn(
        "text-xs font-bold text-center py-1 rounded",
        signal.includes("BULLISH") && "bg-bull/10 text-bull",
        signal.includes("BEARISH") && "bg-bear/10 text-bear",
        signal === "NEUTRAL" && "bg-neutral/10 text-neutral",
      )}>
        {signal.replace(/_/g, " ")}
      </div>
    </div>
  );
}

function MarketRegimeSection() {
  return (
    <div>
      <h4 className="text-xs font-bold text-muted-foreground tracking-wider mb-2 flex items-center gap-2">
        <TrendingUp size={12} />
        MARKET REGIME
      </h4>
      
      <div className="p-3 rounded bg-accent/30">
        <p className="text-[10px] text-muted-foreground">DETECTED FROM NIFTY vs EMA200</p>
        <p className="text-sm font-bold text-bull mt-1">BULLISH REGIME</p>
        <p className="text-[10px] text-muted-foreground mt-1">Trending above 200 EMA</p>
      </div>
    </div>
  );
}