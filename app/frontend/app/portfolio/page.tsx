// E:\tradedo\app\frontend\app\portfolio\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { PortfolioHeader } from "@/components/portfolio/portfolio-header";
import { PortfolioOverview } from "@/components/portfolio/portfolio-overview";
import { HoldingsList } from "@/components/portfolio/holdings-list";
import { AllocationChart } from "@/components/portfolio/allocation-chart";
import { PortfolioPerformance } from "@/components/portfolio/portfolio-performance";

export default function PortfolioPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        <PortfolioHeader />

        {/* Overview cards */}
        <PortfolioOverview />

        {/* Charts row */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <PortfolioPerformance />
          </div>
          <div className="col-span-4">
            <AllocationChart />
          </div>
        </div>

        {/* Holdings */}
        <HoldingsList />

      </div>
    </MainLayout>
  );
}