// E:\tradedo\app\frontend\components\trades\trades-filters.tsx

"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface Props {
  filter: string;
  setFilter: (f: any) => void;
  statusFilter: string;
  setStatusFilter: (f: string) => void;
  directionFilter: string;
  setDirectionFilter: (f: any) => void;
  sortBy: string;
  setSortBy: (s: any) => void;
  search: string;
  setSearch: (s: string) => void;
}

export function TradesFilters({
  filter, setFilter, statusFilter, setStatusFilter,
  directionFilter, setDirectionFilter,
  sortBy, setSortBy, search, setSearch,
}: Props) {
  const statuses = ["ALL", "OPEN", "T1_HIT", "T2_HIT", "SL_HIT", "EOD", "MANUAL"];
  const directions = ["ALL", "LONG", "SHORT"];
  const sorts = [
    { key: "time", label: "Latest" },
    { key: "pnl", label: "P&L" },
    { key: "symbol", label: "Symbol" },
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      
      {/* Row 1: Search + Filter Type */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by symbol..."
            value={search}
            onChange={e => setSearch(e.target.value.toUpperCase())}
            className="pl-9 h-9 font-mono"
          />
        </div>

        {/* Trade Type */}
        <div className="flex bg-secondary border border-border rounded-md p-1">
          {[
            { key: "all", label: "ALL TRADES" },
            { key: "open", label: "OPEN ONLY" },
            { key: "closed", label: "CLOSED ONLY" },
          ].map(t => (
            <button
              key={t.key}
              onClick={() => setFilter(t.key)}
              className={cn(
                "px-3 py-1.5 rounded text-xs font-medium transition-colors",
                filter === t.key ? "bg-brand text-white" : "text-muted-foreground"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">SORT:</span>
          {sorts.map(s => (
            <button
              key={s.key}
              onClick={() => setSortBy(s.key)}
              className={cn(
                "px-2 py-1 rounded transition-colors",
                sortBy === s.key ? "text-brand font-semibold" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Row 2: Status + Direction */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground tracking-wider">STATUS:</span>
          <div className="flex gap-1">
            {statuses.map(s => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={cn(
                  "text-[10px] px-2 py-1 rounded transition-colors font-mono",
                  statusFilter === s
                    ? "bg-brand text-white"
                    : "bg-secondary text-muted-foreground hover:text-foreground"
                )}
              >
                {s.replace(/_/g, " ")}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 pl-4 border-l border-border">
          <span className="text-xs text-muted-foreground tracking-wider">DIR:</span>
          <div className="flex gap-1">
            {directions.map(d => (
              <button
                key={d}
                onClick={() => setDirectionFilter(d as any)}
                className={cn(
                  "text-[10px] px-2 py-1 rounded transition-colors font-mono",
                  directionFilter === d
                    ? "bg-brand text-white"
                    : "bg-secondary text-muted-foreground hover:text-foreground"
                )}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}