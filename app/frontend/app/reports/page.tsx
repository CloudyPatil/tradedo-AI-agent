// E:\tradedo\app\frontend\app\reports\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { ReportsHeader } from "@/components/reports/reports-header";
import { QuickStatsGrid } from "@/components/reports/quick-stats-grid";
import { ReportsList } from "@/components/reports/reports-list";
import { DailyReport } from "@/components/reports/daily-report";
import { InsightsPanel } from "@/components/reports/insights-panel";

export default function ReportsPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        <ReportsHeader />

        {/* Quick stats */}
        <QuickStatsGrid />

        {/* Reports + Insights */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-8">
            <ReportsList />
          </div>
          <div className="col-span-4">
            <InsightsPanel />
          </div>
        </div>

        {/* Daily Report */}
        <DailyReport />

      </div>
    </MainLayout>
  );
}