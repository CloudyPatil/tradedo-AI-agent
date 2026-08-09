// E:\tradedo\app\frontend\app\signals\page.tsx

"use client";

import { useState, useMemo } from "react";
import { MainLayout } from "@/components/layout/main-layout";
import { SignalsHeader } from "@/components/signals/signals-header";
import { SignalsFilters } from "@/components/signals/signals-filters";
import { SignalsGrid } from "@/components/signals/signals-grid";
import { SignalsTable } from "@/components/signals/signals-table";
import { AddStockDialog } from "@/components/signals/add-stock-dialog";
import { useWatchlist } from "@/lib/hooks/use-market";

export default function SignalsPage() {
  const [mode, setMode] = useState<"intraday" | "swing">("intraday");
  const [view, setView] = useState<"grid" | "table">("grid");
  const [filter, setFilter] = useState<"ALL" | "BUY" | "SELL" | "HOLD">("ALL");
  const [sortBy, setSortBy] = useState<"confidence" | "price" | "symbol">("confidence");
  const [search, setSearch] = useState("");
  const [addDialogOpen, setAddDialogOpen] = useState(false);

  const { data, isLoading, refetch, isFetching } = useWatchlist(mode);

  // Filter + Sort
  const stocks = useMemo(() => {
    let filtered = data?.results || [];

    // Search
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter((s: any) =>
        s.symbol.toLowerCase().includes(q)
      );
    }

    // Signal filter
    if (filter !== "ALL") {
      filtered = filtered.filter((s: any) => s.signal === filter);
    }

    // Sort
    filtered = [...filtered].sort((a: any, b: any) => {
      if (sortBy === "confidence") return (b.confidence_pct || 0) - (a.confidence_pct || 0);
      if (sortBy === "price")      return (b.current_price || 0) - (a.current_price || 0);
      if (sortBy === "symbol")     return a.symbol.localeCompare(b.symbol);
      return 0;
    });

    return filtered;
  }, [data, filter, search, sortBy]);

  const buyCount  = data?.results?.filter((s: any) => s.signal === "BUY").length || 0;
  const sellCount = data?.results?.filter((s: any) => s.signal === "SELL").length || 0;
  const holdCount = data?.results?.filter((s: any) => s.signal === "HOLD").length || 0;

  return (
    <MainLayout>
      <div className="space-y-6">
        
        <SignalsHeader
          totalCount={data?.count || 0}
          buyCount={buyCount}
          sellCount={sellCount}
          holdCount={holdCount}
          mode={mode}
          setMode={setMode}
          onRefresh={refetch}
          isRefreshing={isFetching}
          onAddStock={() => setAddDialogOpen(true)}
        />

        <SignalsFilters
          filter={filter}
          setFilter={setFilter}
          sortBy={sortBy}
          setSortBy={setSortBy}
          search={search}
          setSearch={setSearch}
          view={view}
          setView={setView}
          buyCount={buyCount}
          sellCount={sellCount}
          holdCount={holdCount}
        />

        {view === "grid" ? (
          <SignalsGrid stocks={stocks} isLoading={isLoading} />
        ) : (
          <SignalsTable stocks={stocks} isLoading={isLoading} />
        )}

        <AddStockDialog
          open={addDialogOpen}
          onOpenChange={setAddDialogOpen}
        />

      </div>
    </MainLayout>
  );
}