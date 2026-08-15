// E:\tradedo\app\frontend\components\settings\upstox-status.tsx

"use client";

import { useQuery } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";
import { Database, CheckCircle2, XCircle, Key, Clock, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function UpstoxStatus() {
  const { data, isLoading } = useQuery({
    queryKey: ["upstox-status"],
    queryFn: tradeoAPI.getUpstoxStatus,
    refetchInterval: 60000,
  });

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const status = data?.status || {};
  const conn = data?.connection || {};
  const isConnected = conn.success;
  const tokenType = status.active_token_type || "unknown";
  const analyticsSet = status.analytics_token_set;
  const tradingSet = status.trading_token_set;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">UPSTOX CONNECTION</h3>
        </div>
        
        <div className={cn(
          "flex items-center gap-2 px-3 py-1 rounded-md",
          isConnected ? "bg-bull/10 text-bull" : "bg-bear/10 text-bear"
        )}>
          {isConnected ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
          <span className="text-xs font-bold">
            {isConnected ? "CONNECTED" : "DISCONNECTED"}
          </span>
        </div>
      </div>

      {/* Active Token Card */}
      <div className={cn(
        "p-4 rounded-lg border-2 mb-4",
        tokenType === "analytics" 
          ? "border-bull/30 bg-bull/5" 
          : "border-neutral/30 bg-neutral/5"
      )}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Key size={14} className="text-brand" />
            <span className="text-xs font-bold uppercase tracking-wider">Active Token</span>
          </div>
          {tokenType === "analytics" && (
            <div className="flex items-center gap-1 px-2 py-0.5 bg-bull text-white rounded text-[10px] font-bold">
              <Clock size={10} />
              1-YEAR
            </div>
          )}
        </div>
        
        <p className="text-lg font-mono font-bold capitalize text-brand">
          {tokenType}
        </p>
        
        <p className="text-[10px] text-muted-foreground mt-1">
          {tokenType === "analytics" 
            ? "Long-lived token (renewable annually)" 
            : "Daily regeneration required"}
        </p>
      </div>

      {/* Token Availability */}
      <div className="space-y-2 mb-4">
        <TokenStatusRow 
          label="Analytics Token"
          isSet={analyticsSet}
          description="1-year validity, read-only market data"
          badge="RECOMMENDED"
        />
        <TokenStatusRow 
          label="Trading Token"
          isSet={tradingSet}
          description="Daily regeneration, for order execution"
        />
      </div>

      {/* Test Result */}
      {conn.success && conn.test_price && (
        <div className="mt-4 p-3 bg-bull/10 border border-bull/20 rounded-md">
          <div className="flex items-center gap-2 mb-1">
            <Zap size={12} className="text-bull" />
            <span className="text-[10px] font-bold text-bull uppercase">Real-Time Test</span>
          </div>
          <p className="text-sm font-mono font-bold">{conn.test_price}</p>
        </div>
      )}

      {conn.error && (
        <div className="mt-4 p-3 bg-bear/10 border border-bear/20 rounded-md">
          <p className="text-xs text-bear font-bold mb-1">Connection Error:</p>
          <p className="text-[10px] text-muted-foreground">{conn.error}</p>
          {conn.hint && (
            <p className="text-[10px] text-muted-foreground mt-2 italic">💡 {conn.hint}</p>
          )}
        </div>
      )}

      {/* Info */}
      <div className="mt-4 pt-4 border-t border-border">
        <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
          Capabilities
        </p>
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <CapabilityItem label="Real-time LTP" available={isConnected} />
          <CapabilityItem label="Historical Data" available={isConnected} />
          <CapabilityItem label="Intraday Candles" available={isConnected} />
          <CapabilityItem label="Order Book" available={isConnected} />
          <CapabilityItem label="WebSocket" available={isConnected} />
          <CapabilityItem label="Options Chain" available={isConnected} />
        </div>
      </div>
    </div>
  );
}

function TokenStatusRow({ label, isSet, description, badge }: any) {
  return (
    <div className="flex items-center justify-between p-2 rounded bg-accent/30">
      <div className="flex items-center gap-2 flex-1">
        {isSet ? (
          <CheckCircle2 size={12} className="text-bull" />
        ) : (
          <XCircle size={12} className="text-muted-foreground" />
        )}
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold">{label}</span>
            {badge && (
              <span className="text-[9px] px-1.5 py-0.5 bg-brand/20 text-brand rounded font-bold">
                {badge}
              </span>
            )}
          </div>
          <p className="text-[10px] text-muted-foreground">{description}</p>
        </div>
      </div>
      <span className={cn(
        "text-[10px] font-bold",
        isSet ? "text-bull" : "text-muted-foreground"
      )}>
        {isSet ? "SET" : "NOT SET"}
      </span>
    </div>
  );
}

function CapabilityItem({ label, available }: any) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={cn(
        "w-1.5 h-1.5 rounded-full",
        available ? "bg-bull" : "bg-muted-foreground"
      )} />
      <span className={available ? "text-foreground" : "text-muted-foreground"}>
        {label}
      </span>
    </div>
  );
}