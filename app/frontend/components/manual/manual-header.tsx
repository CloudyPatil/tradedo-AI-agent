// E:\tradedo\app\frontend\components\manual\manual-header.tsx

"use client";

import { useState } from "react";
import { User, RefreshCw, Plus, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useManualSummary, useRefreshManualPositions, useResetManualCapital } from "@/lib/hooks/use-manual";
import { formatCurrency, cn } from "@/lib/utils";
import { TradeModal } from "./trade-modal";
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter 
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export function ManualHeader() {
  const { data, isLoading, isFetching } = useManualSummary();
  const [tradeModalOpen, setTradeModalOpen] = useState(false);
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [newCapital, setNewCapital] = useState("100000");
  const [tradeSymbol, setTradeSymbol] = useState("RELIANCE.NS");
  
  const resetMutation = useResetManualCapital();
  const refreshPositions = useRefreshManualPositions();

  const handleReset = () => {
    resetMutation.mutate(parseFloat(newCapital) || 100000);
    setResetModalOpen(false);
  };

  const totalPnl = data?.total_pnl || 0;
  const totalPnlPct = data?.starting_capital 
    ? (totalPnl / data.starting_capital) * 100 
    : 0;

  return (
    <>
      <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
        <div className="flex items-center justify-between">
          
          <div className="flex items-center gap-6">
            <div>
              <h1 className="text-2xl font-display font-bold flex items-center gap-2">
                <User className="text-brand" size={24} />
                MANUAL TRADING
              </h1>
              <p className="text-xs text-muted-foreground tracking-wider mt-1">
                YOUR PORTFOLIO · YOUR CONTROL · PAPER MODE
              </p>
            </div>

            {isLoading ? (
              <Skeleton className="h-16 w-40" />
            ) : (
              <div className={cn(
                "px-4 py-2 rounded-md border-l-4",
                totalPnl >= 0 
                  ? "border-bull bg-bull/5" 
                  : "border-bear bg-bear/5"
              )}>
                <p className="text-[10px] text-muted-foreground tracking-wider">TOTAL P&L</p>
                <p className={cn(
                  "text-3xl font-mono font-bold",
                  totalPnl >= 0 ? "text-bull" : "text-bear"
                )}>
                  {totalPnl >= 0 ? "+" : ""}{formatCurrency(totalPnl, 0)}
                </p>
                <p className={cn(
                  "text-xs font-mono",
                  totalPnl >= 0 ? "text-bull" : "text-bear"
                )}>
                  {totalPnl >= 0 ? "+" : ""}{totalPnlPct.toFixed(2)}%
                </p>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setResetModalOpen(true)}
              className="border-bear/50 text-bear hover:bg-bear/10"
            >
              <RotateCcw size={14} className="mr-2" />
              RESET
            </Button>

            <Button 
              variant="outline"
              size="sm"
              onClick={() => refreshPositions.mutate()}
              disabled={isFetching || refreshPositions.isPending}
            >
              <RefreshCw size={14} className={cn("mr-2", (isFetching || refreshPositions.isPending) && "animate-spin")} />
              REFRESH
            </Button>

            <Button 
              onClick={() => setTradeModalOpen(true)}
              className="bg-brand hover:bg-brand-500"
            >
              <Plus size={14} className="mr-2" />
              PLACE ORDER
            </Button>
          </div>
        </div>
      </div>

      {/* Trade Modal */}
      <TradeModal
        open={tradeModalOpen}
        onOpenChange={setTradeModalOpen}
        symbol={tradeSymbol}
      />

      {/* Reset Dialog */}
      <Dialog open={resetModalOpen} onOpenChange={setResetModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-bear">Reset Manual Account</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground uppercase tracking-wider block mb-2">
                New Starting Capital
              </label>
              <Input
                type="number"
                value={newCapital}
                onChange={(e) => setNewCapital(e.target.value)}
                className="font-mono"
              />
            </div>
            
            <div className="p-3 bg-bear/10 rounded text-xs">
              ⚠️ This will reset capital and clear all statistics. Trade history preserved.
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setResetModalOpen(false)}>
              CANCEL
            </Button>
            <Button 
              onClick={handleReset}
              className="bg-bear hover:bg-bear-dark"
            >
              CONFIRM RESET
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
