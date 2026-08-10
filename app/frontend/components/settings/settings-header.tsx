// E:\tradedo\app\frontend\components\settings\settings-header.tsx

"use client";

import { Settings as SettingsIcon, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useQueryClient } from "@tanstack/react-query";
import { useSystemHealth } from "@/lib/hooks/use-settings";
import { cn } from "@/lib/utils";

export function SettingsHeader() {
  const queryClient = useQueryClient();
  const { data, isFetching } = useSystemHealth();

  const handleRefresh = () => {
    queryClient.invalidateQueries();
  };

  const status = data?.status || "unknown";

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <SettingsIcon className="text-brand" size={24} />
              SETTINGS & PREFERENCES
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider mt-1">
              SYSTEM CONFIGURATION · REAL-TIME MONITORING
            </p>
          </div>

          {/* System Status */}
          <div className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-md border",
            status === "healthy" && "bg-bull/10 border-bull/30",
            status === "degraded" && "bg-neutral/10 border-neutral/30",
            status === "unhealthy" && "bg-bear/10 border-bear/30",
            status === "unknown" && "bg-muted/50 border-border",
          )}>
            <div className={cn(
              "w-2 h-2 rounded-full",
              status === "healthy" && "bg-bull animate-pulse",
              status === "degraded" && "bg-neutral",
              status === "unhealthy" && "bg-bear",
              status === "unknown" && "bg-muted-foreground",
            )} />
            <span className={cn(
              "text-xs font-bold uppercase tracking-wider",
              status === "healthy" && "text-bull",
              status === "degraded" && "text-neutral",
              status === "unhealthy" && "text-bear",
            )}>
              {status}
            </span>
          </div>
        </div>

        <Button variant="outline" onClick={handleRefresh} disabled={isFetching}>
          <RefreshCw size={14} className={cn("mr-2", isFetching && "animate-spin")} />
          REFRESH ALL
        </Button>
      </div>
    </div>
  );
}