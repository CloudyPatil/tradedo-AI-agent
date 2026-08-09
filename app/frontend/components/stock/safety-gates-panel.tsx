// E:\tradedo\app\frontend\components\stock\safety-gates-panel.tsx

"use client";

import { useSafetyGates } from "@/lib/hooks/use-stock";
import { Shield, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  symbol: string;
}

export function SafetyGatesPanel({ symbol }: Props) {
  const { data, isLoading } = useSafetyGates(symbol);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-brand" size={24} />
      </div>
    );
  }

  const safeToTrade = data?.safe_to_trade;
  const gates = data?.gate_results || [];
  const passed = data?.gates_passed || 0;
  const total = data?.total_gates || 12;

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
          <Shield size={16} />
          SAFETY GATES
        </h3>
        <span className={cn(
          "text-xs font-bold px-2 py-0.5 rounded",
          safeToTrade ? "bg-bull/10 text-bull" : "bg-bear/10 text-bear"
        )}>
          {passed}/{total}
        </span>
      </div>

      {/* Overall Status */}
      <div className={cn(
        "text-center py-2 px-3 rounded-md border font-bold text-sm mb-3",
        safeToTrade
          ? "bg-bull/10 border-bull/30 text-bull"
          : "bg-bear/10 border-bear/30 text-bear"
      )}>
        {safeToTrade ? "✅ ALL GATES PASSED" : "❌ GATES FAILED"}
      </div>

      {/* Gates List */}
      <div className="flex-1 space-y-1 overflow-y-auto max-h-80">
        {gates.map((gate: any, i: number) => (
          <div
            key={i}
            className={cn(
              "flex items-center gap-2 p-2 rounded text-xs",
              gate.passed 
                ? "bg-bull/5 text-foreground" 
                : "bg-bear/10 text-foreground"
            )}
          >
            {gate.passed ? (
              <CheckCircle2 size={12} className="text-bull shrink-0" />
            ) : (
              <XCircle size={12} className="text-bear shrink-0" />
            )}
            <div className="flex-1 min-w-0">
              <p className="font-semibold truncate">{gate.gate}</p>
              <p className="text-[10px] text-muted-foreground truncate">
                {gate.reason}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}