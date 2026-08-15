// E:\tradedo\app\frontend\app\screener\page.tsx

"use client";

import { useState, useMemo } from "react";
import { MainLayout } from "@/components/layout/main-layout";
import { ScreenerHeader } from "@/components/screener/screener-header";
import { ScreenerStats } from "@/components/screener/screener-stats";
import { ScreenerFilters } from "@/components/screener/screener-filters";
import { ScreenerTable } from "@/components/screener/screener-table";
import { useScreenerStocks } from "@/lib/hooks/use-screener";

export default function ScreenerPage() {
  const [filters, setFilters] = useState({
    signal: "ALL",
    sector: "ALL",
    minConfidence: 0,
    sortBy: "confidence",
    order: "desc" as "asc" | "desc",
  });
  
  const [search, setSearch] = useState("");
  
  const { data, isLoading } = useScreenerStocks(filters);
  
  const filteredStocks = useMemo(() => {
    let stocks = data?.stocks || [];
    
    if (search) {
      const q = search.toLowerCase();
      stocks = stocks.filter((s: any) =>
        s.symbol.toLowerCase().includes(q)
      );
    }
    
    return stocks;
  }, [data, search]);

  return (
    <MainLayout>
      <div className="space-y-6">
        
        <ScreenerHeader />
        
        <ScreenerStats />
        
        <ScreenerFilters 
          filters={filters}
          setFilters={setFilters}
          search={search}
          setSearch={setSearch}
        />
        
        <ScreenerTable 
          stocks={filteredStocks}
          isLoading={isLoading}
        />
        
      </div>
    </MainLayout>
  );
}