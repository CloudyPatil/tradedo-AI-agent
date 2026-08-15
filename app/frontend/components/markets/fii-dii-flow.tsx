// E:\tradedo\app\frontend\components\markets\fii-dii-flow.tsx

"use client";

import { useFiiDii } from "@/lib/hooks/use-market";
import { Building2, TrendingUp, TrendingDown } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function FiiDiiFlow() {
  const { data, isLoading } = useFiiDii();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  const available = data?.available;
  const fiiNet = data?.fii_net || 0;
  const diiNet = data?.dii_net || 0;
  const totalNet = data?.total_net || 0;
  const signal = data?.signal || "NEUTRAL";

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-4">
        <Building2 size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">INSTITUTIONAL FLOW</h3>
      </div>

      {!available ? (
        <div className="flex items-center justify-center h-40 text-center">
          <div>
            <p className="text-sm text-muted-foreground">Data updating...</p>
            <p className="text-xs text-muted-foreground mt-1">
              Updates after market close
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* FII Card */}
          <div className={cn(
            "p-4 rounded-lg border mb-3",
            fiiNet >= 0 
              ? "bg-bull/5 border-bull/20" 
              : "bg-bear/5 border-bear/20"
          )}>
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">
                  FII (Foreign)
                </p>
                <p className="text-[10px] text-muted-foreground">Institutional Investors</p>
              </div>
              {fiiNet >= 0 ? (
                <TrendingUp className="text-bull" size={20} />
              ) : (
                <TrendingDown className="text-bear" size={20} />
              )}
            </div>
            
            <p className={cn(
              "text-2xl font-mono font-bold",
              fiiNet >= 0 ? "text-bull" : "text-bear"
            )}>
              {fiiNet >= 0 ? "+" : ""}{formatCurrency(fiiNet, 0)}
            </p>
            <p className="text-[10px] text-muted-foreground mt-1">
              Net investment today
            </p>
          </div>

          {/* DII Card */}
          <div className={cn(
            "p-4 rounded-lg border mb-3",
            diiNet >= 0 
              ? "bg-bull/5 border-bull/20" 
              : "bg-bear/5 border-bear/20"
          )}>
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-bold">
                  DII (Domestic)
                </p>
                <p className="text-[10px] text-muted-foreground">Mutual Funds & Others</p>
              </div>
              {diiNet >= 0 ? (
                <TrendingUp className="text-bull" size={20} />
              ) : (
                <TrendingDown className="text-bear" size={20} />
              )}
            </div>
            
            <p className={cn(
              "text-2xl font-mono font-bold",
              diiNet >= 0 ? "text-bull" : "text-bear"
            )}>
              {diiNet >= 0 ? "+" : ""}{formatCurrency(diiNet, 0)}
            </p>
            <p className="text-[10px] text-muted-foreground mt-1">
              Net investment today
            </p>
          </div>

          {/* Net + Signal */}
          <div className="pt-3 border-t border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground">Combined Net</span>
              <span className={cn(
                "text-sm font-mono font-bold",
                totalNet >= 0 ? "text-bull" : "text-bear"
              )}>
                {totalNet >= 0 ? "+" : ""}{formatCurrency(totalNet, 0)}
              </span>
            </div>
            
            <div className={cn(
              "text-center py-2 rounded font-bold text-xs",
              signal.includes("BULLISH") && "bg-bull/10 text-bull",
              signal.includes("BEARISH") && "bg-bear/10 text-bear",
              signal === "NEUTRAL" && "bg-neutral/10 text-neutral",
            )}>
              {signal.replace(/_/g, " ")}
            </div>
          </div>
        </>
      )}
    </div>
  );
}