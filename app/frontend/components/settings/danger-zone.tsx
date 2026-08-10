// E:\tradedo\app\frontend\components\settings\danger-zone.tsx

"use client";

import { useState } from "react";
import { AlertTriangle, RotateCcw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Dialog, DialogContent, DialogHeader, 
  DialogTitle, DialogDescription, DialogFooter 
} from "@/components/ui/dialog";
import { useResetCapital } from "@/lib/hooks/use-settings";
import { formatCurrency } from "@/lib/utils";

export function DangerZone() {
  const [resetOpen, setResetOpen] = useState(false);
  const [newCapital, setNewCapital] = useState("100000");
  const resetMutation = useResetCapital();

  const handleReset = async () => {
    const amount = parseFloat(newCapital);
    if (isNaN(amount) || amount <= 0) return;
    
    await resetMutation.mutateAsync(amount);
    setResetOpen(false);
  };

  return (
    <div className="bg-card border border-bear/30 rounded-lg p-6 corner-brackets">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle size={16} className="text-bear" />
        <h3 className="text-sm font-bold tracking-wider text-bear">DANGER ZONE</h3>
      </div>

      <p className="text-xs text-muted-foreground mb-4">
        Irreversible actions. Please proceed with caution.
      </p>

      <div className="space-y-3">
        <div className="p-4 rounded-md border border-bear/20 bg-bear/5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <p className="font-bold text-sm mb-1">Reset Virtual Capital</p>
              <p className="text-xs text-muted-foreground">
                This will reset your agent's capital, close all open trades, 
                and clear today's statistics. Trade history will be preserved.
              </p>
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setResetOpen(true)}
              className="border-bear/50 text-bear hover:bg-bear/10"
            >
              <RotateCcw size={12} className="mr-2" />
              RESET
            </Button>
          </div>
        </div>
      </div>

      {/* Reset Dialog */}
      <Dialog open={resetOpen} onOpenChange={setResetOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-bear">
              <AlertTriangle size={20} />
              RESET VIRTUAL CAPITAL
            </DialogTitle>
            <DialogDescription>
              Set new starting capital for your trading agent. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <label className="text-xs text-muted-foreground uppercase tracking-wider mb-2 block">
                New Capital Amount
              </label>
              <Input
                type="number"
                value={newCapital}
                onChange={(e) => setNewCapital(e.target.value)}
                placeholder="100000"
                className="font-mono text-lg"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Amount: {formatCurrency(parseFloat(newCapital) || 0, 0)}
              </p>
            </div>

            <div className="p-3 bg-bear/10 border border-bear/30 rounded-md text-xs">
              ⚠️ <strong>This will:</strong>
              <ul className="mt-2 space-y-1 list-disc pl-4">
                <li>Reset capital to new amount</li>
                <li>Zero out today's P&L counters</li>
                <li>Clear open position count</li>
                <li>Trade history remains unchanged</li>
              </ul>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setResetOpen(false)}>
              CANCEL
            </Button>
            <Button
              onClick={handleReset}
              disabled={resetMutation.isPending}
              className="bg-bear hover:bg-bear-dark"
            >
              {resetMutation.isPending ? (
                <Loader2 size={14} className="animate-spin mr-2" />
              ) : null}
              CONFIRM RESET
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}