// E:\tradedo\app\frontend\components\dashboard\ai-signals-panel.tsx

"use client";

import { ArrowUp, ArrowDown, Minus, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWatchlist } from "@/lib/hooks/use-market";
import Link from "next/link";

export function AISignalsPanel() {
  const { data, isLoading } = useWatchlist("intraday");

  const signals = data?.results?.slice(0, 5) || [];

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets h-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold tracking-wider">AI SIGNALS</h3>
        <Link
          href="/signals"
          className="text-xs text-brand hover:text-brand-500 font-medium"
        >
          VIEW ALL
        </Link>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="animate-spin text-brand" size={24} />
        </div>
      ) : signals.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          No signals available
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map((signal: any) => (
            <SignalCard key={signal.symbol} signal={signal} />
          ))}
        </div>
      )}
    </div>
  );
}

function SignalCard({ signal }: { signal: any }) {
  const type = signal.signal?.toLowerCase() || "hold";
  const cleanSymbol = signal.symbol.replace(".NS", "");
  
  return (
    <Link
      href={`/stock/${cleanSymbol}`}
      className="block p-3 rounded-md border border-border hover:border-brand hover:bg-accent/50 transition-all cursor-pointer"
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <p className="font-mono font-bold text-sm">{cleanSymbol}</p>
          <p className={cn(
            "text-xs font-semibold",
            type === "buy" && "text-bull",
            type === "sell" && "text-bear",
            type === "hold" && "text-neutral"
          )}>
            {signal.signal || "HOLD"}
          </p>
        </div>

        <SignalIcon type={type} />
      </div>

      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-muted-foreground">
          Confidence: <span className="text-foreground font-bold">
            {signal.confidence_pct?.toFixed(1) || "—"}%
          </span>
        </span>
        <span className="text-muted-foreground">
          ₹<span className="text-foreground font-bold">
            {signal.current_price?.toFixed(2) || "—"}
          </span>
        </span>
      </div>
    </Link>
  );
}

function SignalIcon({ type }: { type: string }) {
  const styles = {
    buy:  { bg: "bg-bull", icon: ArrowUp },
    sell: { bg: "bg-bear", icon: ArrowDown },
    hold: { bg: "bg-neutral", icon: Minus },
  };

  const style = styles[type as keyof typeof styles] || styles.hold;
  const Icon = style.icon;

  return (
    <div className={cn(
      "w-8 h-8 rounded-full flex items-center justify-center",
      style.bg
    )}>
      <Icon size={16} className="text-white" />
    </div>
  );
}