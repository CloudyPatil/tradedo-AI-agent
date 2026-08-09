// E:\tradedo\app\frontend\components\signals\signals-header.tsx

"use client";

import { RefreshCw, Plus, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  totalCount: number;
  buyCount: number;
  sellCount: number;
  holdCount: number;
  mode: "intraday" | "swing";
  setMode: (m: "intraday" | "swing") => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  onAddStock: () => void;
}

export function SignalsHeader({
  totalCount, buyCount, sellCount, holdCount,
  mode, setMode, onRefresh, isRefreshing, onAddStock,
}: Props) {
  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        {/* Left: Title & Stats */}
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <Sparkles className="text-brand" size={24} />
              AI SIGNALS
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider mt-1">
              REAL-TIME PREDICTIONS FROM MASTER SCORER
            </p>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-4 pl-6 border-l border-border">
            <StatBadge label="TOTAL" value={totalCount} color="text-foreground" />
            <StatBadge label="BUY" value={buyCount} color="text-bull" />
            <StatBadge label="HOLD" value={holdCount} color="text-neutral" />
            <StatBadge label="SELL" value={sellCount} color="text-bear" />
          </div>
        </div>

        {/* Right: Controls */}
        <div className="flex items-center gap-2">
          
          {/* Mode Toggle */}
          <div className="flex bg-secondary border border-border rounded-md p-1">
            <button
              onClick={() => setMode("intraday")}
              className={cn(
                "px-3 py-1.5 rounded text-xs font-medium transition-colors",
                mode === "intraday" ? "bg-brand text-white" : "text-muted-foreground"
              )}
            >
              INTRADAY
            </button>
            <button
              onClick={() => setMode("swing")}
              className={cn(
                "px-3 py-1.5 rounded text-xs font-medium transition-colors",
                mode === "swing" ? "bg-brand text-white" : "text-muted-foreground"
              )}
            >
              SWING
            </button>
          </div>

          {/* Refresh */}
          <Button
            variant="outline"
            size="icon"
            onClick={onRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw size={14} className={isRefreshing ? "animate-spin" : ""} />
          </Button>

          {/* Add Stock */}
          <Button onClick={onAddStock} size="sm" className="bg-brand hover:bg-brand-500">
            <Plus size={14} className="mr-1" />
            ADD STOCK
          </Button>
        </div>
      </div>
    </div>
  );
}

function StatBadge({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-muted-foreground tracking-wider">{label}</p>
      <p className={cn("text-xl font-mono font-bold tabular-nums", color)}>
        {value.toString().padStart(2, "0")}
      </p>
    </div>
  );
}