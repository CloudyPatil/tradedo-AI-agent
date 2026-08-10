// E:\tradedo\app\frontend\components\settings\data-sources-panel.tsx

"use client";

import { useLLMStatus } from "@/lib/hooks/use-settings";
import { Database, Zap, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function DataSourcesPanel() {
  const { data: llmStatus, isLoading } = useLLMStatus();

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center gap-2 mb-4">
        <Database size={16} className="text-brand" />
        <h3 className="text-sm font-bold tracking-wider">DATA SOURCES & APIs</h3>
      </div>

      {/* LLM Pool Status */}
      <div className="mb-6">
        <p className="text-xs text-muted-foreground mb-2 flex items-center gap-2">
          <Zap size={12} className="text-brand" />
          <span className="font-bold uppercase tracking-wider">Groq LLM Pool</span>
        </p>
        
        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : (
          <div className="p-4 bg-accent/30 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-muted-foreground">Total Keys</span>
              <span className="font-mono font-bold text-lg text-brand">
                {llmStatus?.total_keys || 0}
              </span>
            </div>
            
            <div className="space-y-1.5">
              {llmStatus?.keys?.slice(0, 3).map((key: any, i: number) => (
                <div key={i} className="flex items-center justify-between text-[10px]">
                  <span className="font-mono">{key.key}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">
                      {key.requests}/{key.req_limit} req
                    </span>
                    {key.available ? (
                      <CheckCircle2 size={12} className="text-bull" />
                    ) : (
                      <XCircle size={12} className="text-bear" />
                    )}
                  </div>
                </div>
              ))}
              {(llmStatus?.keys?.length || 0) > 3 && (
                <p className="text-[10px] text-muted-foreground text-center pt-1">
                  +{llmStatus.keys.length - 3} more keys
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* API Sources */}
      <div>
        <p className="text-xs text-muted-foreground mb-2 font-bold uppercase tracking-wider">
          Data Sources
        </p>
        <div className="space-y-1">
          <SourceRow name="Upstox API" description="Real-time NSE data" status="active" />
          <SourceRow name="yfinance" description="Backup + historical" status="active" />
          <SourceRow name="RSS News" description="5 Indian financial feeds" status="active" />
          <SourceRow name="Reddit API" description="Social sentiment" status="active" />
          <SourceRow name="StockTwits" description="Trader sentiment" status="active" />
          <SourceRow name="YouTube" description="Expert opinions" status="active" />
          <SourceRow name="NSE Official" description="Announcements, FII/DII" status="active" />
          <SourceRow name="Google Trends" description="Retail interest" status="active" />
        </div>
      </div>
    </div>
  );
}

function SourceRow({ name, description, status }: any) {
  return (
    <div className="flex items-center justify-between p-2 rounded hover:bg-accent/30 transition-colors text-xs">
      <div>
        <p className="font-semibold">{name}</p>
        <p className="text-[10px] text-muted-foreground">{description}</p>
      </div>
      <div className="flex items-center gap-1.5">
        <div className={cn(
          "w-1.5 h-1.5 rounded-full",
          status === "active" ? "bg-bull animate-pulse" : "bg-muted"
        )} />
        <span className={cn(
          "text-[10px] font-bold uppercase",
          status === "active" ? "text-bull" : "text-muted-foreground"
        )}>
          {status}
        </span>
      </div>
    </div>
  );
}