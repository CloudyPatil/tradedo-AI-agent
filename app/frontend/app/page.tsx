// E:\tradedo\app\frontend\app\page.tsx

import { MainLayout } from "@/components/layout/main-layout";
import { MarketTickerBar } from "@/components/dashboard/market-ticker";
import { WelcomeHero } from "@/components/dashboard/welcome-hero";
import { MainChart } from "@/components/dashboard/main-chart";
import { AISignalsPanel } from "@/components/dashboard/ai-signals-panel";
import { PortfolioWidget } from "@/components/dashboard/portfolio-widget";
import { PositionsWidget } from "@/components/dashboard/positions-widget";
import { AgentStatusWidget } from "@/components/dashboard/agent-status";
import { SentimentGauge } from "@/components/dashboard/sentiment-gauge";
import { IntelligencePanel } from "@/components/dashboard/intelligence-panel";

export default function DashboardPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        {/* Market Ticker Bar - REAL DATA */}
        <MarketTickerBar />

        {/* Main Row: Hero + Chart + Signals */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3">
            <WelcomeHero />
          </div>
          <div className="col-span-6">
            <MainChart />
          </div>
          <div className="col-span-3">
            <AISignalsPanel />
          </div>
        </div>

        {/* Widgets Row - REAL DATA */}
        <div className="grid grid-cols-4 gap-6">
          <PortfolioWidget />
          <PositionsWidget />
          <AgentStatusWidget />
          <SentimentGauge />
        </div>

        {/* Intelligence Row - NEW */}
        <div className="grid grid-cols-1 gap-6">
          <IntelligencePanel />
        </div>

      </div>
    </MainLayout>
  );
}