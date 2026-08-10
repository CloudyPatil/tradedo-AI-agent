// E:\tradedo\app\frontend\app\risk\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { RiskHeader } from "@/components/risk/risk-header";
import { RiskScoreGauge } from "@/components/risk/risk-score-gauge";
import { PortfolioHeatCard } from "@/components/risk/portfolio-heat-card";
import { DiversificationCard } from "@/components/risk/diversification-card";
import { SectorConcentration } from "@/components/risk/sector-concentration";
import { PositionRisks } from "@/components/risk/position-risks";
import { VaRCard } from "@/components/risk/var-card";
import { StressTestPanel } from "@/components/risk/stress-test-panel";

export default function RiskPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        <RiskHeader />

        {/* Top Row: Risk Score + Heat + Diversification */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-4">
            <RiskScoreGauge />
          </div>
          <div className="col-span-4">
            <PortfolioHeatCard />
          </div>
          <div className="col-span-4">
            <DiversificationCard />
          </div>
        </div>

        {/* Middle Row: Sector Concentration + VaR */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-7">
            <SectorConcentration />
          </div>
          <div className="col-span-5">
            <VaRCard />
          </div>
        </div>

        {/* Position-Level Risks */}
        <PositionRisks />

        {/* Stress Tests */}
        <StressTestPanel />

      </div>
    </MainLayout>
  );
}