// E:\tradedo\app\frontend\components\signals\signals-filters.tsx

"use client";

import { Search, LayoutGrid, List } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  filter: string;
  setFilter: (f: any) => void;
  sortBy: string;
  setSortBy: (s: any) => void;
  search: string;
  setSearch: (s: string) => void;
  view: "grid" | "table";
  setView: (v: "grid" | "table") => void;
  buyCount: number;
  sellCount: number;
  holdCount: number;
}

export function SignalsFilters({
  filter, setFilter, sortBy, setSortBy,
  search, setSearch, view, setView,
  buyCount, sellCount, holdCount,
}: Props) {
  const filters = [
    { key: "ALL", label: "ALL", count: buyCount + sellCount + holdCount, color: "text-foreground" },
    { key: "BUY", label: "BUY", count: buyCount, color: "text-bull" },
    { key: "HOLD", label: "HOLD", count: holdCount, color: "text-neutral" },
    { key: "SELL", label: "SELL", count: sellCount, color: "text-bear" },
  ];

  const sortOptions = [
    { key: "confidence", label: "Confidence" },
    { key: "price", label: "Price" },
    { key: "symbol", label: "Symbol" },
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-4">
      
      {/* Search */}
      <div className="relative flex-1 max-w-xs">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search stocks..."
          value={search}
          onChange={e => setSearch(e.target.value.toUpperCase())}
          className="pl-9 h-9 font-mono"
        />
      </div>

      {/* Signal Filters */}
      <div className="flex items-center gap-1">
        {filters.map(f => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key)}
            className={cn(
              "px-3 py-1.5 rounded text-xs font-semibold transition-all border",
              filter === f.key
                ? "border-brand bg-brand/10 text-brand"
                : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
            )}
          >
            {f.label}
            <span className={cn("ml-1.5 font-mono", filter !== f.key && f.color)}>
              {f.count}
            </span>
          </button>
        ))}
      </div>

      {/* Sort */}
      <div className="flex items-center gap-2 pl-4 border-l border-border">
        <span className="text-xs text-muted-foreground">SORT:</span>
        {sortOptions.map(opt => (
          <button
            key={opt.key}
            onClick={() => setSortBy(opt.key)}
            className={cn(
              "text-xs px-2 py-1 rounded transition-colors",
              sortBy === opt.key
                ? "text-brand font-semibold"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* View Toggle */}
      <div className="flex bg-secondary border border-border rounded-md p-0.5 ml-auto">
        <Button
          variant={view === "grid" ? "default" : "ghost"}
          size="icon"
          className="w-7 h-7"
          onClick={() => setView("grid")}
        >
          <LayoutGrid size={14} />
        </Button>
        <Button
          variant={view === "table" ? "default" : "ghost"}
          size="icon"
          className="w-7 h-7"
          onClick={() => setView("table")}
        >
          <List size={14} />
        </Button>
      </div>
    </div>
  );
}