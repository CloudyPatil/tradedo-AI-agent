// E:\tradedo\app\frontend\app\markets\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { MarketsHeader } from "@/components/markets/markets-header";
import { IndicesGrid } from "@/components/markets/indices-grid";
import { SectorPerformance } from "@/components/markets/sector-performance";
import { GlobalMarketsPanel } from "@/components/markets/global-markets-panel";
import { MarketBreadth } from "@/components/markets/market-breadth";
import { FiiDiiFlow } from "@/components/markets/fii-dii-flow";
import { TopMovers } from "@/components/markets/top-movers";

export default function MarketsPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        <MarketsHeader />

        {/* Indices */}
        <IndicesGrid />

        {/* Row: Sectors + FII/DII */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <SectorPerformance />
          </div>
          <div className="col-span-4">
            <FiiDiiFlow />
          </div>
        </div>

        {/* Global Markets */}
        <GlobalMarketsPanel />

        {/* Row: Breadth + Top Movers */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-5">
            <MarketBreadth />
          </div>
          <div className="col-span-7">
            <TopMovers />
          </div>
        </div>

      </div>
    </MainLayout>
  );
}