// E:\tradedo\app\frontend\components\stock\stock-header.tsx

"use client";

import { ArrowLeft, RefreshCw, TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import Link from "next/link";
import { useStockPrediction } from "@/lib/hooks/use-stock";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatPercent, cn } from "@/lib/utils";
import { useState } from "react";

interface Props {
  symbol: string;
}

export function StockHeader({ symbol }: Props) {
  const [mode, setMode] = useState<"intraday" | "swing">("intraday");
  const { data, isLoading, refetch, isFetching } = useStockPrediction(symbol, mode);

  const cleanSymbol = symbol.replace(".NS", "");
  const price = data?.current_price || 0;
  const signal = data?.signal || "HOLD";
  const confidence = data?.confidence_pct || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        {/* Left: Symbol Info */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="p-2 rounded-md hover:bg-accent transition-colors"
          >
            <ArrowLeft size={18} />
          </Link>
          
          <div>
            <h1 className="text-3xl font-display font-bold tracking-tight">
              {cleanSymbol}
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider uppercase mt-1">
              NSE · {mode === "intraday" ? "5-Min Analysis" : "Daily Analysis"}
            </p>
          </div>
        </div>

        {/* Center: Price */}
        <div className="text-center">
          {isLoading ? (
            <Loader2 className="animate-spin text-brand mx-auto" size={24} />
          ) : (
            <>
              <p className="text-4xl font-mono font-bold tabular-nums">
                ₹{price.toFixed(2)}
              </p>
              <p className="text-xs text-muted-foreground mt-1">LIVE PRICE</p>
            </>
          )}
        </div>

        {/* Right: Signal + Controls */}
        <div className="flex items-center gap-4">
          
          {/* Signal Badge */}
          {!isLoading && (
            <div className={cn(
              "px-4 py-2 rounded-md text-center",
              signal === "BUY" && "bg-bull/10 border border-bull/30",
              signal === "SELL" && "bg-bear/10 border border-bear/30",
              signal === "HOLD" && "bg-neutral/10 border border-neutral/30",
            )}>
              <p className={cn(
                "text-lg font-bold flex items-center gap-2",
                signal === "BUY" && "text-bull",
                signal === "SELL" && "text-bear",
                signal === "HOLD" && "text-neutral",
              )}>
                {signal === "BUY" && <TrendingUp size={18} />}
                {signal === "SELL" && <TrendingDown size={18} />}
                {signal}
              </p>
              <p className="text-xs font-mono mt-0.5">
                {confidence.toFixed(1)}% CONFIDENCE
              </p>
            </div>
          )}

          {/* Mode Toggle */}
          <div className="flex bg-secondary border border-border rounded-md p-1">
            <button
              onClick={() => setMode("intraday")}
              className={cn(
                "px-3 py-1 rounded text-xs font-medium transition-colors",
                mode === "intraday" ? "bg-brand text-white" : "text-muted-foreground"
              )}
            >
              INTRADAY
            </button>
            <button
              onClick={() => setMode("swing")}
              className={cn(
                "px-3 py-1 rounded text-xs font-medium transition-colors",
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
            onClick={() => refetch()}
            disabled={isFetching}
          >
            <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
          </Button>
        </div>
      </div>
    </div>
  );
}