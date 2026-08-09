// E:\tradedo\app\frontend\app\stock\[symbol]\page.tsx

"use client";

import { use } from "react";
import { MainLayout } from "@/components/layout/main-layout";
import { StockHeader } from "@/components/stock/stock-header";
import { PriceChart } from "@/components/stock/price-chart";
import { MasterScoreCard } from "@/components/stock/master-score-card";
import { TradePlanCard } from "@/components/stock/trade-plan-card";
import { NewsFeed } from "@/components/stock/news-feed";
import { SocialIntel } from "@/components/stock/social-intel";
import { NseDataPanel } from "@/components/stock/nse-data-panel";
import { SafetyGatesPanel } from "@/components/stock/safety-gates-panel";

export default function StockDetailPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol: rawSymbol } = use(params);
  const symbol = rawSymbol.toUpperCase();

  return (
    <MainLayout>
      <div className="space-y-6">
        
        {/* Header */}
        <StockHeader symbol={symbol} />

        {/* Main Grid: Chart + Score */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <PriceChart symbol={symbol} />
          </div>
          <div className="col-span-4">
            <MasterScoreCard symbol={symbol} />
          </div>
        </div>

        {/* Trade Plan + Safety Gates */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <TradePlanCard symbol={symbol} />
          </div>
          <div className="col-span-4">
            <SafetyGatesPanel symbol={symbol} />
          </div>
        </div>

        {/* Intelligence Row */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-6">
            <NewsFeed symbol={symbol} />
          </div>
          <div className="col-span-6">
            <SocialIntel symbol={symbol} />
          </div>
        </div>

        {/* NSE Data */}
        <NseDataPanel symbol={symbol} />

      </div>
    </MainLayout>
  );
}