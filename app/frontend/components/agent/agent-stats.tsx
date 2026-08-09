// E:\tradedo\app\frontend\components\agent/agent-stats.tsx

"use client";

import { useAgentStatus, useTodaysPerformance } from "@/lib/hooks/use-agent";
import { formatCurrency, cn, formatPercent } from "@/lib/utils";
import { TrendingUp, Trophy, Target, Clock, DollarSign } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function AgentStats() {
  const { data: statusData, isLoading: statusLoading } = useAgentStatus();
  const { data: perfData, isLoading: perfLoading } = useTodaysPerformance();

  if (statusLoading || perfLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  const agent = statusData?.agent;
  const totalPnl = agent?.total_pnl || 0;
  const totalPnlPct = agent?.total_pnl_pct || 0;
  const winRate = perfData?.win_rate || 0;
  const totalTrades = perfData?.total_trades || 0;
  const winning = perfData?.winning_trades || 0;
  const losing = perfData?.losing_trades || 0;
  const openTrades = statusData?.open_trades?.length || 0;
  const pnlToday = perfData?.total_pnl || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-6">
        <TrendingUp size={20} className="text-brand" />
        <h2 className="text-sm font-bold tracking-wider">PERFORMANCE OVERVIEW</h2>
      </div>

      {/* Big Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign size={16} />}
          label="TOTAL P&L"
          value={formatCurrency(totalPnl, 0)}
          subvalue={formatPercent(totalPnlPct)}
          color={totalPnl >= 0 ? "text-bull" : "text-bear"}
          highlight
        />
        
        <StatCard
          icon={<Clock size={16} />}
          label="TODAY P&L"
          value={formatCurrency(pnlToday, 0)}
          subvalue={`${totalTrades} trades`}
          color={pnlToday >= 0 ? "text-bull" : "text-bear"}
        />
        
        <StatCard
          icon={<Trophy size={16} />}
          label="WIN RATE"
          value={`${winRate.toFixed(1)}%`}
          subvalue={`${winning}W · ${losing}L`}
          color={winRate >= 60 ? "text-bull" : winRate >= 40 ? "text-neutral" : "text-bear"}
        />
        
        <StatCard
          icon={<Target size={16} />}
          label="OPEN"
          value={openTrades.toString().padStart(2, "0")}
          subvalue="positions"
          color="text-brand"
        />
      </div>

      {/* Additional metrics */}
      <div className="grid grid-cols-4 gap-4 mt-4 pt-4 border-t border-border">
        <MiniStat 
          label="Largest Win"  
          value={formatCurrency(perfData?.largest_win || 0, 0)}
          color="text-bull"
        />
        <MiniStat 
          label="Largest Loss" 
          value={formatCurrency(perfData?.largest_loss || 0, 0)}
          color="text-bear"
        />
        <MiniStat 
          label="Avg Win"      
          value={formatCurrency(perfData?.avg_win || 0, 0)}
          color="text-bull"
        />
        <MiniStat 
          label="Avg Loss"     
          value={formatCurrency(perfData?.avg_loss || 0, 0)}
          color="text-bear"
        />
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, subvalue, color, highlight }: any) {
  return (
    <div className={cn(
      "p-4 rounded-md border transition-all",
      highlight 
        ? "border-brand/30 bg-brand/5" 
        : "border-border bg-accent/20"
    )}>
      <div className="flex items-center gap-2 mb-2 text-muted-foreground">
        {icon}
        <span className="text-[10px] tracking-wider font-bold">{label}</span>
      </div>
      <p className={cn("text-2xl font-mono font-bold tabular-nums", color)}>
        {value}
      </p>
      <p className="text-xs text-muted-foreground mt-1 font-mono">
        {subvalue}
      </p>
    </div>
  );
}

function MiniStat({ label, value, color }: any) {
  return (
    <div>
      <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
        {label}
      </p>
      <p className={cn("text-sm font-mono font-bold tabular-nums mt-1", color)}>
        {value}
      </p>
    </div>
  );
}