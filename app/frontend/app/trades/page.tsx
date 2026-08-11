// E:\tradedo\app\frontend\app\trades\page.tsx

"use client";

import { useState, useMemo } from "react";
import { MainLayout } from "@/components/layout/main-layout";
import { TradesHeader } from "@/components/trades/trades-header";
import { TradesFilters } from "@/components/trades/trades-filters";
import { TradesTable } from "@/components/trades/trades-table";
import { TradeDetailDialog } from "@/components/trades/trade-detail-dialog";
import { useTrades } from "@/lib/hooks/use-agent";

export default function TradesPage() {
  const [filter, setFilter] = useState<"all" | "open" | "closed">("all");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [directionFilter, setDirectionFilter] = useState<"ALL" | "LONG" | "SHORT">("ALL");
  const [sortBy, setSortBy] = useState<"time" | "pnl" | "symbol">("time");
  const [search, setSearch] = useState("");
  const [selectedTrade, setSelectedTrade] = useState<any>(null);

  const { data, isLoading } = useTrades(filter);

  const trades = useMemo(() => {
    let list = data?.trades || [];

    // Search
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((t: any) => 
        t.symbol.toLowerCase().includes(q)
      );
    }

    // Status filter
    if (statusFilter !== "ALL") {
      list = list.filter((t: any) => t.status === statusFilter);
    }

    // Direction filter
    if (directionFilter !== "ALL") {
      list = list.filter((t: any) => t.direction === directionFilter);
    }

    // Sort
    list = [...list].sort((a: any, b: any) => {
      if (sortBy === "time") return new Date(b.entry_time).getTime() - new Date(a.entry_time).getTime();
      if (sortBy === "pnl") return (b.pnl || 0) - (a.pnl || 0);
      if (sortBy === "symbol") return a.symbol.localeCompare(b.symbol);
      return 0;
    });

    return list;
  }, [data, search, statusFilter, directionFilter, sortBy]);

  // Stats
  const stats = useMemo(() => {
    const closed = trades.filter((t: any) => t.status !== "OPEN");
    const wins = closed.filter((t: any) => (t.pnl || 0) > 0);
    const totalPnl = closed.reduce((sum: number, t: any) => sum + (t.pnl || 0), 0);
    
    return {
      total:    trades.length,
      open:     trades.filter((t: any) => t.status === "OPEN").length,
      wins:     wins.length,
      losses:   closed.length - wins.length,
      totalPnl,
      winRate:  closed.length > 0 ? (wins.length / closed.length) * 100 : 0,
    };
  }, [trades]);

  return (
    <MainLayout>
      <div className="space-y-6">
        
        <TradesHeader stats={stats} />

        <TradesFilters
          filter={filter}
          setFilter={setFilter}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          directionFilter={directionFilter}
          setDirectionFilter={setDirectionFilter}
          sortBy={sortBy}
          setSortBy={setSortBy}
          search={search}
          setSearch={setSearch}
        />

        <TradesTable
          trades={trades}
          isLoading={isLoading}
          onSelectTrade={setSelectedTrade}
        />

        <TradeDetailDialog
          trade={selectedTrade}
          onClose={() => setSelectedTrade(null)}
        />

      </div>
    </MainLayout>
  );
}