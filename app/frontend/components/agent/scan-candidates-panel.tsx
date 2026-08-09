// E:\tradedo\app\frontend\components\agent\scan-candidates-panel.tsx

"use client";

import { useScanCandidates } from "@/lib/hooks/use-agent";
import { Search, TrendingUp, TrendingDown, Loader2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function ScanCandidatesPanel() {
  const { data, isLoading } = useScanCandidates();

  const candidates = data?.candidates || [];

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Search size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">TODAY'S SCAN</h3>
        </div>
        <span className="text-[10px] text-muted-foreground font-mono">
          {candidates.length} FOUND
        </span>
      </div>

      {isLoading ? (
        <div className="space-y-2 flex-1">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : candidates.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-center">
          <div>
            <p className="text-sm text-muted-foreground">No scan results yet</p>
            <p className="text-xs text-muted-foreground mt-1">
              Trigger "RUN SCAN" or wait for morning scan
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-2 flex-1 overflow-y-auto">
          {candidates.map((c: any, i: number) => (
            <CandidateCard key={c.symbol} rank={i + 1} candidate={c} />
          ))}
        </div>
      )}
    </div>
  );
}

function CandidateCard({ rank, candidate }: any) {
  const cleanSymbol = candidate.symbol.replace(".NS", "");
  const signal = candidate.signal || "HOLD";
  const isBuy = signal === "BUY";

  return (
    <Link
      href={`/stock/${cleanSymbol}`}
      className="block p-3 rounded-md border border-border hover:border-brand hover:bg-accent/50 transition-all"
    >
      <div className="flex items-center gap-3">
        {/* Rank */}
        <div className="w-8 h-8 rounded-md bg-secondary flex items-center justify-center font-mono font-bold text-sm text-brand">
          #{rank}
        </div>

        {/* Symbol */}
        <div className="flex-1">
          <p className="font-mono font-bold">{cleanSymbol}</p>
          <div className="flex items-center gap-3 text-[10px] mt-0.5">
            <span className={cn(
              "font-bold",
              isBuy ? "text-bull" : "text-bear"
            )}>
              {signal}
            </span>
            <span className="text-muted-foreground">
              Conf: {candidate.confidence?.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Score */}
        <div className="text-right">
          <p className="font-mono font-bold text-brand">
            {candidate.composite?.toFixed(0) || "—"}
          </p>
          <p className="text-[10px] text-muted-foreground">SCORE</p>
        </div>

        {/* Icon */}
        {isBuy ? (
          <TrendingUp size={16} className="text-bull" />
        ) : (
          <TrendingDown size={16} className="text-bear" />
        )}
      </div>
    </Link>
  );
}