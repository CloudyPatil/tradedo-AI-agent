// E:\tradedo\app\frontend\app\settings\page.tsx

"use client";

import { MainLayout } from "@/components/layout/main-layout";
import { SettingsHeader } from "@/components/settings/settings-header";
import { SystemStatusPanel } from "@/components/settings/system-status-panel";
import { DataSourcesPanel } from "@/components/settings/data-sources-panel";
import { AgentConfigPanel } from "@/components/settings/agent-config-panel";
import { WatchlistManagement } from "@/components/settings/watchlist-management";
import { ThemePreferences } from "@/components/settings/theme-preferences";
import { DangerZone } from "@/components/settings/danger-zone";
import { UpstoxStatus } from "@/components/settings/upstox-status";

export default function SettingsPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        
        <SettingsHeader />

        {/* System Health */}
        <SystemStatusPanel />

        {/* NEW: Upstox Status */}
        <UpstoxStatus />

        {/* 2-Column Grid */}
        <div className="grid grid-cols-2 gap-6">
          <DataSourcesPanel />
          <AgentConfigPanel />
        </div>

        {/* Watchlist Management */}
        <WatchlistManagement />

        {/* Preferences */}
        <ThemePreferences />

        {/* Danger Zone */}
        <DangerZone />

      </div>
    </MainLayout>
  );
}