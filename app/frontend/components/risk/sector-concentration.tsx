// E:\tradedo\app\frontend\components\risk\sector-concentration.tsx

"use client";

import { useSectorConcentration } from "@/lib/hooks/use-risk";
import { Building2 } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function SectorConcentration() {
  const { data, isLoading } = useSectorConcentration();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!data?.has_positions) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
        <div className="flex items-center gap-2 mb-4">
          <Building2 size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">SECTOR CONCENTRATION</h3>
        </div>
        <div className="flex items-center justify-center h-48 text-sm text-muted-foreground">
          No open positions
        </div>
      </div>
    );
  }

  const sectors = data?.sectors || {};
  const totalInvestment = data?.total_investment || 0;
  const concentrationRisk = data?.concentration_risk || "LOW";
  const highestSector = data?.highest_sector;
  const highestSectorPct = data?.highest_sector_pct || 0;

  const sectorEntries = Object.entries(sectors);

  const getSectorColor = (pct: number) => {
    if (pct >= 30) return "bg-bear";
    if (pct >= 20) return "bg-brand";
    if (pct >= 10) return "bg-neutral";
    return "bg-bull";
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Building2 size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">SECTOR CONCENTRATION</h3>
        </div>
        <span className={cn(
          "text-[10px] font-bold px-2 py-0.5 rounded",
          concentrationRisk === "LOW" && "bg-bull/10 text-bull",
          concentrationRisk === "MEDIUM" && "bg-neutral/10 text-neutral",
          concentrationRisk === "HIGH" && "bg-bear/10 text-bear",
        )}>
          {concentrationRisk} RISK
        </span>
      </div>

      {/* Warning if highly concentrated */}
      {highestSector && highestSectorPct >= 25 && (
        <div className="mb-4 p-2 bg-neutral/10 border border-neutral/20 rounded text-xs">
          ⚠️ <strong>{highestSector}</strong> represents {highestSectorPct.toFixed(1)}% of portfolio
        </div>
      )}

      {/* Sectors List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {sectorEntries.map(([sector, info]: [string, any]) => (
          <div key={sector} className="p-3 rounded border border-border bg-accent/20">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-sm font-bold">{sector}</p>
                <p className="text-[10px] text-muted-foreground">
                  {info.trades} trades · {info.symbols.join(", ")}
                </p>
              </div>
              <div className="text-right">
                <p className="text-lg font-mono font-bold">
                  {info.capital_pct.toFixed(1)}%
                </p>
                <p className="text-[10px] text-muted-foreground">of capital</p>
              </div>
            </div>

            <div className="h-2 bg-secondary rounded-full overflow-hidden mb-1">
              <div 
                className={cn("h-full rounded-full transition-all", getSectorColor(info.capital_pct))}
                style={{ width: `${Math.min(info.capital_pct * 2, 100)}%` }}
              />
            </div>
            
            <div className="flex items-center justify-between text-[10px] text-muted-foreground">
              <span>{formatCurrency(info.investment, 0)}</span>
              <span className={cn(
                "font-bold",
                info.risk_level === "HIGH" && "text-bear",
                info.risk_level === "MEDIUM" && "text-neutral",
                info.risk_level === "LOW" && "text-bull",
              )}>
                {info.risk_level}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-border flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Total Invested</span>
        <span className="font-mono font-bold">{formatCurrency(totalInvestment, 0)}</span>
      </div>
    </div>
  );
}