// E:\tradedo\app\frontend\components\settings\system-status-panel.tsx

"use client";

import { useSystemHealth } from "@/lib/hooks/use-settings";
import { Activity, CheckCircle2, XCircle, AlertTriangle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function SystemStatusPanel() {
  const { data, isLoading } = useSystemHealth();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-40 mb-4" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    );
  }

  const services = data?.services || {};
  const serviceEntries = Object.entries(services);

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">SYSTEM SERVICES</h3>
        <span className="ml-auto text-[10px] text-muted-foreground font-mono">
          {data?.timestamp?.slice(11, 19)}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {serviceEntries.map(([name, info]: [string, any]) => (
          <ServiceCard key={name} name={name} info={info} />
        ))}
      </div>
    </div>
  );
}

// In system-status-panel.tsx

// UPDATE the ServiceCard function - add better display for upstox:

function ServiceCard({ name, info }: { name: string; info: any }) {
  const status = info?.status || "unknown";
  const isHealthy = status === "healthy";
  const isError = status === "error" || status === "unhealthy";

  const displayName = name.replace(/_/g, " ").toUpperCase();
  const Icon = isHealthy ? CheckCircle2 : isError ? XCircle : AlertTriangle;
  const color = isHealthy ? "text-bull" : isError ? "text-bear" : "text-neutral";
  const bg = isHealthy ? "bg-bull/5 border-bull/20" : isError ? "bg-bear/5 border-bear/20" : "bg-neutral/5 border-neutral/20";

  return (
    <div className={cn("p-4 rounded-lg border", bg)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold tracking-wider">{displayName}</span>
        <Icon size={16} className={color} />
      </div>
      
      <p className={cn("text-sm font-bold capitalize", color)}>{status}</p>

      {/* Additional details */}
      <div className="mt-2 space-y-1 text-[10px] text-muted-foreground">
        {info.error && (
          <p className="text-bear truncate">Error: {info.error}</p>
        )}
        {info.loaded !== undefined && (
          <p>Loaded: {info.loaded ? "Yes" : "No"}</p>
        )}
        {info.features && (
          <p>Features: {info.features}</p>
        )}
        {info.ready !== undefined && (
          <p>Ready: {info.ready ? "Yes" : "No"}</p>
        )}
        {info.is_active !== undefined && (
          <p>Active: {info.is_active ? "Yes" : "No"}</p>
        )}
        {info.open_positions !== undefined && (
          <p>Open Positions: {info.open_positions}</p>
        )}
        {info.running !== undefined && (
          <p>Running: {info.running ? "Yes" : "No"}</p>
        )}
        {info.preferred && (
          <p>Preferred: <span className="text-brand font-bold">{info.preferred}</span></p>
        )}
        {info.upstox_available !== undefined && (
          <p>Upstox: <span className={info.upstox_available ? "text-bull font-bold" : "text-bear"}>
            {info.upstox_available ? "✓ Real-time" : "✗ Unavailable"}
          </span></p>
        )}
        {info.active_source && (
          <p>Source: <span className="text-brand font-bold">{info.active_source}</span></p>
        )}
      </div>
    </div>
  );
}