// E:\tradedo\app\frontend\components\settings\agent-config-panel.tsx

"use client";

import { Bot, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTestTelegram } from "@/lib/hooks/use-settings";
import { Loader2 } from "lucide-react";

export function AgentConfigPanel() {
  const testTelegram = useTestTelegram();

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center gap-2 mb-4">
        <Bot size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">AGENT CONFIGURATION</h3>
      </div>

      {/* Config Values */}
      <div className="space-y-3">
        <ConfigRow label="Master Score Threshold" value="140 / 200" description="Min score for trade execution" />
        <ConfigRow label="Risk Per Trade" value="2%" description="Max capital risk per trade" />
        <ConfigRow label="Max Open Positions" value="3" description="Concurrent trades limit" />
        <ConfigRow label="Max Daily Loss" value="5%" description="Circuit breaker" />
        <ConfigRow label="Max Sector Concentration" value="30%" description="Per-sector limit" />
        <ConfigRow label="Scan Universe" value="150 stocks" description="Nifty 50 + Next 50 + Midcaps" />
        <ConfigRow label="Model Version" value="Intraday v3 (79%)" description="Latest trained model" />
        <ConfigRow label="Force EOD Exit" value="3:15 PM IST" description="Auto-close all trades" />
      </div>

      {/* Telegram Notifications */}
      <div className="mt-6 pt-6 border-t border-border">
        <div className="flex items-center gap-2 mb-3">
          <Bell size={14} className="text-brand" />
          <span className="text-xs font-bold uppercase tracking-wider">Telegram Alerts</span>
        </div>

        <div className="space-y-2 mb-4 text-xs">
          <NotificationRow label="Trade Entry/Exit"    enabled />
          <NotificationRow label="Morning Scan Report" enabled />
          <NotificationRow label="EOD Summary"          enabled />
          <NotificationRow label="Emergency News Exit"  enabled />
          <NotificationRow label="Strong Signals"       enabled />
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => testTelegram.mutate()}
          disabled={testTelegram.isPending}
          className="w-full text-xs"
        >
          {testTelegram.isPending ? (
            <Loader2 size={12} className="animate-spin mr-2" />
          ) : (
            <Bell size={12} className="mr-2" />
          )}
          SEND TEST MESSAGE
        </Button>
      </div>
    </div>
  );
}

function ConfigRow({ label, value, description }: any) {
  return (
    <div className="flex items-start justify-between text-xs py-2 border-b border-border last:border-0">
      <div className="flex-1">
        <p className="font-semibold">{label}</p>
        <p className="text-[10px] text-muted-foreground">{description}</p>
      </div>
      <span className="font-mono font-bold text-brand">{value}</span>
    </div>
  );
}

function NotificationRow({ label, enabled }: any) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground">{label}</span>
      <div className="flex items-center gap-1.5">
        <div className={enabled ? "w-1.5 h-1.5 rounded-full bg-bull" : "w-1.5 h-1.5 rounded-full bg-muted"} />
        <span className={enabled ? "text-bull font-bold" : "text-muted-foreground"}>
          {enabled ? "ON" : "OFF"}
        </span>
      </div>
    </div>
  );
}