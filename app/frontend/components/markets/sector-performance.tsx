// E:\tradedo\app\frontend\components\markets\sector-performance.tsx

"use client";

import { useGlobalMarkets } from "@/lib/hooks/use-market";
import { Building2, TrendingUp, TrendingDown } from "lucide-react";
import { cn, formatPercent } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const SECTORS = [
  { key: "IT", label: "Information Technology", ticker: "^CNXIT" },
  { key: "BANK_NIFTY", label: "Banking", ticker: "^NSEBANK" },
  { key: "AUTO", label: "Automobile", ticker: "^CNXAUTO" },
  { key: "PHARMA", label: "Pharmaceutical", ticker: "^CNXPHARMA" },
  { key: "FMCG", label: "FMCG", ticker: "^CNXFMCG" },
  { key: "METAL", label: "Metals", ticker: "^CNXMETAL" },
  { key: "ENERGY", label: "Energy", ticker: "^CNXENERGY" },
  { key: "REALTY", label: "Real Estate", ticker: "^CNXREALTY" },
];

export function SectorPerformance() {
  const { data, isLoading } = useGlobalMarkets();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="space-y-2">
          {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-10" />)}
        </div>
      </div>
    );
  }

  const raw = data?.raw_data || {};

  const sectorData = SECTORS.map(s => {
    // Try direct key first, then various formats
    const sectorInfo = raw[s.key] || raw[s.key.toUpperCase()];
    return {
      ...s,
      changePct: sectorInfo?.change_pct || 0,
      value: sectorInfo?.value || 0,
    };
  }).sort((a, b) => b.changePct - a.changePct);

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Building2 size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">SECTOR PERFORMANCE</h3>
        </div>
        <span className="text-[10px] text-muted-foreground">
          NSE SECTOR INDICES
        </span>
      </div>

      <div className="space-y-2">
        {sectorData.map(sector => (
          <SectorRow key={sector.key} sector={sector} />
        ))}
      </div>
    </div>
  );
}

function SectorRow({ sector }: any) {
  const isPositive = sector.changePct >= 0;
  const maxAbs = Math.max(Math.abs(sector.changePct), 2);
  const barWidth = (Math.abs(sector.changePct) / maxAbs) * 100;

  return (
    <div className="p-3 rounded border border-border hover:bg-accent/30 transition-colors">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          {isPositive ? (
            <TrendingUp size={12} className="text-bull" />
          ) : (
            <TrendingDown size={12} className="text-bear" />
          )}
          <span className="text-xs font-bold">{sector.label}</span>
        </div>
        
        <span className={cn(
          "text-sm font-mono font-bold",
          isPositive ? "text-bull" : "text-bear"
        )}>
          {formatPercent(sector.changePct)}
        </span>
      </div>

      {/* Progress bar */}
      <div className="relative h-1.5 bg-secondary rounded-full overflow-hidden">
        <div
          className={cn(
            "absolute top-0 h-full transition-all",
            isPositive ? "bg-bull left-1/2" : "bg-bear right-1/2"
          )}
          style={{ width: `${barWidth / 2}%` }}
        />
      </div>
    </div>
  );
}