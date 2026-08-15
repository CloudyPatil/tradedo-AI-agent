// E:\tradedo\app\frontend\components\screener\screener-filters.tsx

"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const SECTORS = [
  "ALL", "BANKING", "IT", "AUTO", "PHARMA", "FMCG", 
  "METALS", "ENERGY", "REALTY", "NBFC", "INSURANCE",
  "TELECOM", "TECH", "CONSUMER", "INFRA", "POWER",
];

interface Props {
  filters: any;
  setFilters: (f: any) => void;
  search: string;
  setSearch: (s: string) => void;
}

export function ScreenerFilters({ filters, setFilters, search, setSearch }: Props) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      
      {/* Row 1: Search + Confidence */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search stocks..."
            value={search}
            onChange={e => setSearch(e.target.value.toUpperCase())}
            className="pl-9 h-9 font-mono"
          />
        </div>

        {/* Min Confidence Slider */}
        <div className="flex items-center gap-2 flex-1 max-w-xs">
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            Min Confidence:
          </span>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={filters.minConfidence}
            onChange={e => setFilters({ ...filters, minConfidence: parseInt(e.target.value) })}
            className="flex-1"
          />
          <span className="text-xs font-mono font-bold text-brand min-w-[40px]">
            {filters.minConfidence}%
          </span>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Sort:</span>
          <select
            value={filters.sortBy}
            onChange={e => setFilters({ ...filters, sortBy: e.target.value })}
            className="bg-secondary border border-border rounded px-2 py-1 text-xs"
          >
            <option value="confidence">Confidence</option>
            <option value="price">Price</option>
            <option value="returns_5d">5D Returns</option>
            <option value="rsi">RSI</option>
            <option value="symbol">Symbol</option>
          </select>
        </div>
      </div>

      {/* Row 2: Signal Filters */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground tracking-wider">SIGNAL:</span>
        {["ALL", "BUY", "HOLD", "SELL"].map(s => (
          <button
            key={s}
            onClick={() => setFilters({ ...filters, signal: s })}
            className={cn(
              "px-3 py-1 rounded text-xs font-bold transition-colors",
              filters.signal === s
                ? s === "BUY" ? "bg-bull text-white"
                  : s === "SELL" ? "bg-bear text-white"
                  : s === "HOLD" ? "bg-neutral text-white"
                  : "bg-brand text-white"
                : "bg-secondary text-muted-foreground hover:text-foreground"
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Row 3: Sector Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs text-muted-foreground tracking-wider">SECTOR:</span>
        {SECTORS.map(s => (
          <button
            key={s}
            onClick={() => setFilters({ ...filters, sector: s })}
            className={cn(
              "px-2 py-1 rounded text-[10px] font-bold transition-colors",
              filters.sector === s
                ? "bg-brand text-white"
                : "bg-secondary text-muted-foreground hover:text-foreground"
            )}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}