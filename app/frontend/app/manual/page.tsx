// E:\tradedo\app\frontend\app\manual\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { ManualHeader } from "@/components/manual/manual-header";
import { ManualSummary } from "@/components/manual/manual-summary";
import { OpenPositions } from "@/components/manual/open-positions";
import { PendingOrders } from "@/components/manual/pending-orders";
import { OrderHistory } from "@/components/manual/order-history";

export default function ManualPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        <ManualHeader />

        <ManualSummary />

        <OpenPositions />

        <div className="grid grid-cols-2 gap-6">
          <PendingOrders />
          <OrderHistory />
        </div>

      </div>
    </MainLayout>
  );
}