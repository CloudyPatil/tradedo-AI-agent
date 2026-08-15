// E:\tradedo\app\frontend\components\screener\screener-header.tsx

"use client";

import { useState } from "react";
import { Scan, Play, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTriggerScreenerScan } from "@/lib/hooks/use-screener";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { cn } from "@/lib/utils";

export function ScreenerHeader() {
  const [tier, setTier] = useState<"tier1" | "tier2" | "tier3" | "full">("tier2");
  const [mode, setMode] = useState<"swing" | "intraday">("swing");
  
  const { data: universe } = useQuery({
    queryKey: ["universe-info"],
    queryFn: () => api.get("/screener/universe").then(r => r.data),
    staleTime: Infinity,
  });
  
  const scanMutation = useTriggerScreenerScan();
  
  const tiers = [
    { key: "tier1", label: "Nifty 50",  count: universe?.nifty_50 || 50, time: "~2 min" },
    { key: "tier2", label: "Nifty 100", count: universe?.nifty_100 || 100, time: "~5 min" },
    { key: "tier3", label: "Nifty 200", count: universe?.nifty_200 || 200, time: "~10 min" },
    { key: "full",  label: "Nifty 500", count: universe?.nifty_500 || 500, time: "~25 min" },
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        <div>
          <h1 className="text-2xl font-display font-bold flex items-center gap-2">
            <Scan className="text-brand" size={24} />
            UNIVERSAL STOCK SCREENER
          </h1>
          <p className="text-xs text-muted-foreground tracking-wider mt-1">
            AI-POWERED ANALYSIS · UP TO 500 STOCKS
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Mode Toggle */}
          <div className="flex bg-secondary border border-border rounded-md p-1">
            {(["swing", "intraday"] as const).map(m => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={cn(
                  "px-3 py-1.5 rounded text-xs font-medium transition-colors capitalize",
                  mode === m ? "bg-brand text-white" : "text-muted-foreground"
                )}
              >
                {m}
              </button>
            ))}
          </div>

          {/* Scan Button */}
          <Button 
            onClick={() => scanMutation.mutate({ tier, mode })}
            disabled={scanMutation.isPending}
            className="bg-brand hover:bg-brand-500"
          >
            {scanMutation.isPending ? (
              <Loader2 className="animate-spin mr-2" size={14} />
            ) : (
              <Play size={14} className="mr-2" />
            )}
            SCAN NOW
          </Button>
        </div>
      </div>

      {/* Tier selection */}
      <div className="mt-4 pt-4 border-t border-border">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
          Scan Universe (choose tier)
        </p>
        <div className="grid grid-cols-4 gap-3">
          {tiers.map(t => (
            <button
              key={t.key}
              onClick={() => setTier(t.key as any)}
              className={cn(
                "p-3 rounded-lg border-2 transition-all text-left",
                tier === t.key
                  ? "border-brand bg-brand/10"
                  : "border-border hover:border-muted-foreground/30"
              )}
            >
              <p className={cn(
                "text-xs font-bold",
                tier === t.key ? "text-brand" : "text-foreground"
              )}>
                {t.label}
              </p>
              <p className="text-lg font-mono font-bold mt-1">
                {t.count}
              </p>
              <p className="text-[10px] text-muted-foreground">
                stocks · {t.time}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}