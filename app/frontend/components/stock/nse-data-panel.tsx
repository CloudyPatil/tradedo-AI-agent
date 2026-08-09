// E:\tradedo\app\frontend\components\stock\nse-data-panel.tsx

"use client";

import { useStockNse } from "@/lib/hooks/use-stock";
import { Building2, TrendingUp, AlertCircle, Loader2 } from "lucide-react";
import { formatCurrency, cn } from "@/lib/utils";

interface Props {
  symbol: string;
}

export function NseDataPanel({ symbol }: Props) {
  const { data, isLoading } = useStockNse(symbol);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 flex items-center justify-center h-40">
        <Loader2 className="animate-spin text-brand" size={24} />
      </div>
    );
  }

  const nseData = data?.data || {};
  const optionChain = nseData.option_chain;
  const bulkDeals = nseData.bulk_deals;
  const delivery = nseData.delivery;
  const announcements = nseData.announcements || [];
  const fnoBanned = nseData.fno_banned;

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
          <Building2 size={16} />
          NSE OFFICIAL DATA
        </h3>
        <span className="text-[10px] text-muted-foreground font-mono">
          FROM NSE INDIA
        </span>
      </div>

      {fnoBanned && (
        <div className="mb-3 p-2 bg-bear/10 border border-bear/20 rounded-md flex items-center gap-2">
          <AlertCircle size={14} className="text-bear" />
          <span className="text-xs text-bear font-bold">F&O BANNED TODAY</span>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        
        {/* Options PCR */}
        <div className="p-3 rounded-md border border-border">
          <p className="text-[10px] text-muted-foreground uppercase mb-2">Options PCR</p>
          {optionChain ? (
            <>
              <p className="font-mono text-xl font-bold">
                {optionChain.pcr_oi?.toFixed(2)}
              </p>
              <p className={cn(
                "text-xs font-bold mt-1",
                optionChain.pcr_signal?.includes("BULLISH") && "text-bull",
                optionChain.pcr_signal?.includes("BEARISH") && "text-bear",
                optionChain.pcr_signal === "NEUTRAL" && "text-neutral",
              )}>
                {optionChain.pcr_signal}
              </p>
              {optionChain.max_pain && (
                <p className="text-[10px] text-muted-foreground mt-2">
                  Max Pain: ₹{optionChain.max_pain}
                </p>
              )}
            </>
          ) : (
            <p className="text-xs text-muted-foreground">No data</p>
          )}
        </div>

        {/* Delivery % */}
        <div className="p-3 rounded-md border border-border">
          <p className="text-[10px] text-muted-foreground uppercase mb-2">Delivery %</p>
          {delivery ? (
            <>
              <p className="font-mono text-xl font-bold">
                {delivery.avg_delivery_pct?.toFixed(1)}%
              </p>
              <p className={cn(
                "text-xs font-bold mt-1",
                delivery.signal?.includes("INVESTMENT") && "text-bull",
                delivery.signal?.includes("SPECULATIVE") && "text-bear",
                delivery.signal === "NORMAL" && "text-neutral",
              )}>
                {delivery.signal?.replace(/_/g, " ")}
              </p>
              <p className="text-[10px] text-muted-foreground mt-2">
                Latest: {delivery.latest_delivery_pct?.toFixed(1)}%
              </p>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">No data</p>
          )}
        </div>

        {/* Bulk Deals */}
        <div className="p-3 rounded-md border border-border">
          <p className="text-[10px] text-muted-foreground uppercase mb-2">Bulk Deals</p>
          {bulkDeals?.has_activity ? (
            <>
              <p className="font-mono text-xl font-bold">
                {bulkDeals.deal_count}
              </p>
              <p className={cn(
                "text-xs font-bold mt-1",
                bulkDeals.signal?.includes("BUY") && "text-bull",
                bulkDeals.signal?.includes("SELL") && "text-bear",
              )}>
                {bulkDeals.signal?.replace(/_/g, " ")}
              </p>
              <p className="text-[10px] text-muted-foreground mt-2">
                Net: ₹{(bulkDeals.net_value / 1e7).toFixed(1)}Cr
              </p>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">No activity</p>
          )}
        </div>
      </div>

      {/* Announcements */}
      {announcements.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border">
          <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
            Recent Announcements
          </p>
          <div className="space-y-2">
            {announcements.slice(0, 3).map((ann: any, i: number) => (
              <div key={i} className="p-2 bg-accent/30 rounded text-xs">
                <p className="text-foreground">{ann.subject}</p>
                <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
                  <span className="uppercase font-bold text-brand">{ann.type}</span>
                  <span>·</span>
                  <span>{ann.date}</span>
                  <span>·</span>
                  <span className={cn(
                    "font-bold",
                    ann.impact?.includes("POSITIVE") && "text-bull",
                    ann.impact?.includes("NEGATIVE") && "text-bear",
                  )}>
                    {ann.impact?.replace(/_/g, " ")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}