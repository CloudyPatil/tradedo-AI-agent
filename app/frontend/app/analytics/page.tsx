// E:\tradedo\app\frontend\app\analytics\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { AnalyticsHeader } from "@/components/analytics/analytics-header";
import { MetricsOverview } from "@/components/analytics/metrics-overview";
import { EquityCurveChart } from "@/components/analytics/equity-curve-chart";
import { RiskAdjustedMetrics } from "@/components/analytics/risk-adjusted-metrics";
import { StreaksPanel } from "@/components/analytics/streaks-panel";
import { KellyPanel } from "@/components/analytics/kelly-panel";
import { HourlyPerformance } from "@/components/analytics/hourly-performance";
import { DailyPerformance } from "@/components/analytics/daily-performance";
import { TradeDistribution } from "@/components/analytics/trade-distribution";

export default function AnalyticsPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        {/* Header */}
        <AnalyticsHeader />

        {/* Big Metrics Grid */}
        <MetricsOverview />

        {/* Equity Curve */}
        <EquityCurveChart />

        {/* Risk-Adjusted + Streaks + Kelly */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-5">
            <RiskAdjustedMetrics />
          </div>
          <div className="col-span-4">
            <StreaksPanel />
          </div>
          <div className="col-span-3">
            <KellyPanel />
          </div>
        </div>

        {/* Time Analysis */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <HourlyPerformance />
          </div>
          <div className="col-span-4">
            <DailyPerformance />
          </div>
        </div>

        {/* Distribution */}
        <TradeDistribution />

      </div>
    </MainLayout>
  );
}