// E:\tradedo\app\frontend\components\risk\position-risks.tsx

"use client";

import { usePositionRisks } from "@/lib/hooks/use-risk";
import { AlertCircle, Loader2 } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import Link from "next/link";
import { Skeleton } from "@/components/ui/skeleton";

export function PositionRisks() {
  const { data, isLoading } = usePositionRisks();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const positions = data?.positions || [];

  if (positions.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
        <div className="flex items-center gap-2 mb-4">
          <AlertCircle size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">POSITION-LEVEL RISKS</h3>
        </div>
        <div className="text-center py-8 text-sm text-muted-foreground">
          No open positions
        </div>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden corner-brackets">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="text-brand" />
            <h3 className="text-sm font-bold tracking-wider">POSITION-LEVEL RISKS</h3>
          </div>
          <span className="text-xs text-muted-foreground">
            {positions.length} position{positions.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <table className="w-full">
        <thead className="bg-accent/30">
          <tr>
            <th className="text-left px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">SYMBOL</th>
            <th className="text-center px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">SECTOR</th>
            <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">ENTRY</th>
            <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">CMP</th>
            <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">RISK ₹</th>
            <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">RISK %</th>
            <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">R:R</th>
            <th className="text-right px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">P&L</th>
            <th className="text-center px-4 py-2 text-[10px] font-bold text-muted-foreground tracking-wider">WARNINGS</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((pos: any) => (
            <tr key={pos.trade_id} className="border-t border-border hover:bg-accent/30 transition-colors">
              <td className="px-4 py-3">
                <Link 
                  href={`/stock/${pos.symbol}`}
                  className="font-mono font-bold text-sm hover:text-brand"
                >
                  {pos.symbol}
                </Link>
                <p className="text-[10px] text-muted-foreground">
                  {pos.direction}
                </p>
              </td>
              
              <td className="px-4 py-3 text-center">
                <span className="text-[10px] text-muted-foreground px-2 py-0.5 bg-secondary rounded">
                  {pos.sector}
                </span>
              </td>
              
              <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
                ₹{pos.entry?.toFixed(2)}
              </td>
              
              <td className="px-4 py-3 text-right font-mono tabular-nums text-sm font-bold">
                ₹{pos.current?.toFixed(2)}
              </td>
              
              <td className="px-4 py-3 text-right font-mono tabular-nums text-bear text-sm">
                {formatCurrency(pos.risk_amount, 0)}
              </td>
              
              <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
                <span className={cn(
                  "font-bold",
                  pos.risk_pct > 3 && "text-bear",
                  pos.risk_pct <= 3 && pos.risk_pct > 1.5 && "text-neutral",
                  pos.risk_pct <= 1.5 && "text-bull",
                )}>
                  {pos.risk_pct?.toFixed(2)}%
                </span>
              </td>
              
              <td className="px-4 py-3 text-right font-mono tabular-nums text-sm font-bold">
                1:{pos.risk_reward?.toFixed(1)}
              </td>
              
              <td className={cn(
                "px-4 py-3 text-right font-mono tabular-nums font-bold text-sm",
                pos.current_pnl >= 0 ? "text-bull" : "text-bear"
              )}>
                {pos.current_pnl >= 0 ? "+" : ""}{formatCurrency(pos.current_pnl, 0)}
              </td>
              
              <td className="px-4 py-3 text-center">
                {pos.warnings && pos.warnings.length > 0 ? (
                  <div className="flex flex-col gap-1">
                    {pos.warnings.slice(0, 2).map((w: string, i: number) => (
                      <span 
                        key={i} 
                        className="text-[9px] px-1.5 py-0.5 bg-bear/10 text-bear rounded"
                      >
                        ⚠ {w}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-[10px] text-bull">✓ SAFE</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}