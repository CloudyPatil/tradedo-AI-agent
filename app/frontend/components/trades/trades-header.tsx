// E:\tradedo\app\frontend\components\trades\trades-header.tsx

"use client";

import { Target, Download, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatCurrency, cn } from "@/lib/utils";
import { toast } from "sonner";

interface Props {
  stats: {
    total: number;
    open: number;
    wins: number;
    losses: number;
    totalPnl: number;
    winRate: number;
  };
}

export function TradesHeader({ stats }: Props) {
  const handleExport = () => {
    toast.info("CSV export coming soon!");
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between">
        
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-2xl font-display font-bold flex items-center gap-2">
              <Target className="text-brand" size={24} />
              TRADE HISTORY
            </h1>
            <p className="text-xs text-muted-foreground tracking-wider mt-1">
              COMPLETE TRADE JOURNAL · REAL-TIME
            </p>
          </div>

          <div className="pl-6 border-l border-border">
            <p className="text-[10px] text-muted-foreground tracking-wider">TOTAL P&L</p>
            <p className={cn(
              "text-3xl font-mono font-bold flex items-center gap-2",
              stats.totalPnl >= 0 ? "text-bull" : "text-bear"
            )}>
              <TrendingUp size={20} />
              {stats.totalPnl >= 0 ? "+" : ""}{formatCurrency(stats.totalPnl, 0)}
            </p>
          </div>
        </div>

        <Button variant="outline" onClick={handleExport}>
          <Download size={14} className="mr-2" />
          EXPORT CSV
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-5 gap-4 mt-6">
        <StatBox label="TOTAL" value={stats.total} color="text-foreground" />
        <StatBox label="OPEN" value={stats.open} color="text-brand" />
        <StatBox label="WINS" value={stats.wins} color="text-bull" />
        <StatBox label="LOSSES" value={stats.losses} color="text-bear" />
        <StatBox 
          label="WIN RATE" 
          value={`${stats.winRate.toFixed(1)}%`} 
          color={stats.winRate >= 60 ? "text-bull" : stats.winRate >= 40 ? "text-neutral" : "text-bear"}
        />
      </div>
    </div>
  );
}

function StatBox({ label, value, color }: any) {
  return (
    <div className="p-3 rounded-md bg-accent/30 text-center">
      <p className="text-[10px] text-muted-foreground tracking-wider">{label}</p>
      <p className={cn("text-2xl font-mono font-bold tabular-nums mt-1", color)}>
        {value}
      </p>
    </div>
  );
}