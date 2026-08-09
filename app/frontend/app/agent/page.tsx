// E:\tradedo\app\frontend\app\agent\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { AgentControlPanel } from "@/components/agent/agent-control-panel";
import { AgentStats } from "@/components/agent/agent-stats";
import { OpenTradesTable } from "@/components/agent/open-trades-table";
import { ScanCandidatesPanel } from "@/components/agent/scan-candidates-panel";
import { TradeHistory } from "@/components/agent/trade-history";
import { AgentActionsPanel } from "@/components/agent/agent-actions-panel";

export default function AgentPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        {/* Top: Control + Stats */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-4">
            <AgentControlPanel />
          </div>
          <div className="col-span-8">
            <AgentStats />
          </div>
        </div>

        {/* Actions Panel */}
        <AgentActionsPanel />

        {/* Open Trades */}
        <OpenTradesTable />

        {/* Scan Candidates + Trade History */}
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-5">
            <ScanCandidatesPanel />
          </div>
          <div className="col-span-7">
            <TradeHistory />
          </div>
        </div>

      </div>
    </MainLayout>
  );
}