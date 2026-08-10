// E:\tradedo\app\frontend\components\risk\var-card.tsx

"use client";

import { useVaR } from "@/lib/hooks/use-risk";
import { TrendingDown } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function VaRCard() {
  const { data, isLoading } = useVaR();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  const varData = data?.var;
  const es = data?.expected_shortfall;

  if (!varData?.has_data) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
        <div className="flex items-center gap-2 mb-4">
          <TrendingDown size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">VALUE AT RISK</h3>
        </div>
        <div className="flex items-center justify-center h-40 text-center">
          <p className="text-xs text-muted-foreground">
            {varData?.message || "Need at least 10 trades for VaR"}
          </p>
        </div>
      </div>
    );
  }

  const parametric = varData?.parametric || {};
  const historical = varData?.historical || {};

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <TrendingDown size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">VALUE AT RISK</h3>
      </div>

      {varData?.interpretation && (
        <div className="mb-4 p-2 bg-accent/30 rounded text-[10px] text-muted-foreground text-center">
          {varData.interpretation}
        </div>
      )}

      {/* Parametric VaR */}
      <div className="mb-4">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
          Parametric VaR
        </p>
        <div className="grid grid-cols-2 gap-2">
          <VaRBox
            label="95% Confidence"
            pct={parametric.var_95_pct}
            amount={parametric.var_95_amount}
          />
          <VaRBox
            label="99% Confidence"
            pct={parametric.var_99_pct}
            amount={parametric.var_99_amount}
          />
        </div>
      </div>

      {/* Historical VaR */}
      <div className="mb-4">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
          Historical VaR
        </p>
        <div className="grid grid-cols-2 gap-2">
          <VaRBox
            label="95% Confidence"
            pct={historical.var_95_pct}
            amount={historical.var_95_amount}
          />
          <VaRBox
            label="99% Confidence"
            pct={historical.var_99_pct}
            amount={historical.var_99_amount}
          />
        </div>
      </div>

      {/* Expected Shortfall */}
      {es?.has_data && (
        <div className="pt-4 border-t border-border">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
            Expected Shortfall (Tail Risk)
          </p>
          <div className="grid grid-cols-2 gap-2">
            <VaRBox
              label="ES 95%"
              pct={es.es_95_pct}
              amount={es.es_95_amount}
              highlight
            />
            <VaRBox
              label="ES 99%"
              pct={es.es_99_pct}
              amount={es.es_99_amount}
              highlight
            />
          </div>
        </div>
      )}
    </div>
  );
}

function VaRBox({ label, pct, amount, highlight }: any) {
  return (
    <div className={cn(
      "p-2 rounded border text-center",
      highlight ? "border-bear/30 bg-bear/5" : "border-border bg-accent/20"
    )}>
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className={cn("font-mono font-bold text-sm", highlight ? "text-bear" : "text-foreground")}>
        {pct?.toFixed(2)}%
      </p>
      <p className="text-[10px] text-muted-foreground font-mono">
        {formatCurrency(amount || 0, 0)}
      </p>
    </div>
  );
}