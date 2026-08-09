// E:\tradedo\app\frontend\components\stock\trade-plan-card.tsx

"use client";

import { useStockPrediction } from "@/lib/hooks/use-stock";
import { Target, ShieldAlert, TrendingUp, TrendingDown, Clock, AlertTriangle, Loader2 } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";

interface Props {
  symbol: string;
}

export function TradePlanCard({ symbol }: Props) {
  const { data, isLoading } = useStockPrediction(symbol);
  const plan = data?.trade_plan;

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 flex items-center justify-center">
        <Loader2 className="animate-spin text-brand" size={32} />
      </div>
    );
  }

  if (!plan?.tradeable) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
        <div className="text-center py-4">
          <AlertTriangle className="mx-auto text-neutral mb-2" size={32} />
          <h3 className="text-sm font-bold mb-1">NO TRADE SETUP</h3>
          <p className="text-xs text-muted-foreground">
            {plan?.reason || "Signal doesn't meet criteria for trading"}
          </p>
        </div>
      </div>
    );
  }

  const isLong = plan.direction === "LONG";
  const currentPrice = data?.current_price || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            isLong ? "bg-bull/20" : "bg-bear/20"
          )}>
            {isLong ? <TrendingUp className="text-bull" size={20} /> : <TrendingDown className="text-bear" size={20} />}
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-wider">TRADE PLAN</h3>
            <p className="text-xs text-muted-foreground">
              {plan.direction} · R:R {plan.risk_reward?.avg || "N/A"}
            </p>
          </div>
        </div>

        <div className="text-right">
          <p className="text-xs text-muted-foreground">CONFIDENCE</p>
          <p className="text-lg font-mono font-bold text-brand">
            {plan.confidence?.overall || 0}%
          </p>
        </div>
      </div>

      {/* Entry */}
      <div className="bg-accent/30 rounded-md p-3 mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground tracking-wider">🎯 ENTRY</span>
          <span className="text-xs text-brand">{plan.entry?.window}</span>
        </div>
        <p className="text-2xl font-mono font-bold">
          {formatCurrency(plan.entry?.price || 0)}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {plan.entry?.best_time}
        </p>
      </div>

      {/* Price Journey */}
      <PriceJourney
        entry={plan.entry?.price || 0}
        target1={plan.target_1?.price || 0}
        target2={plan.target_2?.price || 0}
        stopLoss={plan.stop_loss?.price || 0}
        current={currentPrice}
        isLong={isLong}
      />

      {/* Targets & SL Grid */}
      <div className="grid grid-cols-3 gap-2 mt-4">
        <div className="bg-bear/10 border border-bear/20 rounded-md p-2 text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <ShieldAlert size={10} className="text-bear" />
            <span className="text-[10px] text-bear font-bold">STOP</span>
          </div>
          <p className="font-mono text-sm font-bold">₹{plan.stop_loss?.price}</p>
          <p className="text-[10px] text-bear">-{plan.stop_loss?.loss_pct}%</p>
        </div>

        <div className="bg-bull/10 border border-bull/20 rounded-md p-2 text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Target size={10} className="text-bull" />
            <span className="text-[10px] text-bull font-bold">T1</span>
          </div>
          <p className="font-mono text-sm font-bold">₹{plan.target_1?.price}</p>
          <p className="text-[10px] text-bull">+{plan.target_1?.profit_pct}%</p>
        </div>

        <div className="bg-bull/20 border border-bull/30 rounded-md p-2 text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Target size={10} className="text-bull" />
            <span className="text-[10px] text-bull font-bold">T2</span>
          </div>
          <p className="font-mono text-sm font-bold">₹{plan.target_2?.price}</p>
          <p className="text-[10px] text-bull">+{plan.target_2?.profit_pct}%</p>
        </div>
      </div>

      {/* Position Info */}
      <div className="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-border">
        <div>
          <p className="text-[10px] text-muted-foreground uppercase">Shares</p>
          <p className="font-mono font-bold text-lg">{plan.position?.shares || 0}</p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground uppercase">Investment</p>
          <p className="font-mono font-bold text-lg">
            {formatCurrency(plan.position?.investment || 0, 0)}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground uppercase">Max Loss</p>
          <p className="font-mono font-bold text-bear">
            -{formatCurrency(plan.position?.max_loss || 0, 0)}
          </p>
        </div>
        <div>
          <p className="text-[10px] text-muted-foreground uppercase">Max Profit</p>
          <p className="font-mono font-bold text-bull">
            +{formatCurrency(plan.position?.max_profit || 0, 0)}
          </p>
        </div>
      </div>

      {/* Exit Time */}
      {plan.time_exit && (
        <div className="mt-3 flex items-center gap-2 text-xs text-neutral bg-neutral/10 border border-neutral/20 rounded-md p-2">
          <Clock size={12} />
          <span>Exit by <strong>{plan.time_exit.exit_by}</strong></span>
        </div>
      )}
    </div>
  );
}

function PriceJourney({ entry, target1, target2, stopLoss, current, isLong }: any) {
  const min = Math.min(entry, target1, target2, stopLoss, current);
  const max = Math.max(entry, target1, target2, stopLoss, current);
  const range = max - min || 1;
  
  const pct = (val: number) => ((val - min) / range) * 100;
  
  return (
    <div className="relative h-16">
      <div className="absolute top-1/2 left-0 right-0 h-1 bg-secondary rounded-full transform -translate-y-1/2" />
      
      <div
        className={`absolute top-1/2 h-1 rounded-full transform -translate-y-1/2 ${
          isLong ? "bg-bull" : "bg-bear"
        }`}
        style={{
          left: `${Math.min(pct(entry), pct(current))}%`,
          width: `${Math.abs(pct(current) - pct(entry))}%`,
        }}
      />
      
      <Marker pct={pct(stopLoss)} label="SL" color="text-bear" />
      <Marker pct={pct(entry)} label="Entry" color="text-foreground" />
      <Marker pct={pct(current)} label="Now" color="text-brand" pulse />
      <Marker pct={pct(target1)} label="T1" color="text-bull" />
      <Marker pct={pct(target2)} label="T2" color="text-bull" />
    </div>
  );
}

function Marker({ pct, label, color, pulse }: any) {
  return (
    <div
      className="absolute top-1/2 transform -translate-x-1/2 -translate-y-1/2"
      style={{ left: `${pct}%` }}
    >
      <div className={`w-2 h-2 rounded-full bg-current ${color} ${pulse ? "animate-pulse" : ""}`} />
      <p className={`text-[9px] font-semibold mt-1 whitespace-nowrap ${color}`}>{label}</p>
    </div>
  );
}