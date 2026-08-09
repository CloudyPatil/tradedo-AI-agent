// E:\tradedo\app\frontend\components\signals\add-stock-dialog.tsx

"use client";

import { useState } from "react";
import { 
  Dialog, DialogContent, DialogHeader, 
  DialogTitle, DialogDescription 
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAddToWatchlist } from "@/lib/hooks/use-market";
import { Plus, Loader2 } from "lucide-react";

const POPULAR_STOCKS = [
  "RELIANCE", "TCS", "HDFCBANK", "INFY", "WIPRO",
  "TATAMOTORS", "SBIN", "ICICIBANK", "AXISBANK", "MARUTI",
  "SUNPHARMA", "TITAN", "BAJFINANCE", "HDFCLIFE", "ADANIENT",
];

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddStockDialog({ open, onOpenChange }: Props) {
  const [symbol, setSymbol] = useState("");
  const addMutation = useAddToWatchlist();

  const handleAdd = async (stockSymbol: string) => {
    const clean = stockSymbol.trim().toUpperCase();
    if (!clean) return;
    
    const fullSymbol = clean.endsWith(".NS") ? clean : `${clean}.NS`;
    
    try {
      await addMutation.mutateAsync(fullSymbol);
      setSymbol("");
      onOpenChange(false);
    } catch (e) {
      // Error handled in mutation
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Plus size={18} className="text-brand" />
            ADD STOCK TO WATCHLIST
          </DialogTitle>
          <DialogDescription>
            Enter any NSE stock symbol to add to your watchlist
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAdd(symbol);
          }}
          className="space-y-4"
        >
          <div>
            <Input
              placeholder="e.g. RELIANCE, TCS, WIPRO"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="font-mono"
              autoFocus
            />
            <p className="text-[10px] text-muted-foreground mt-1">
              .NS suffix will be added automatically
            </p>
          </div>

          <Button
            type="submit"
            className="w-full bg-brand hover:bg-brand-500"
            disabled={!symbol || addMutation.isPending}
          >
            {addMutation.isPending ? (
              <Loader2 size={14} className="animate-spin mr-2" />
            ) : (
              <Plus size={14} className="mr-2" />
            )}
            ADD TO WATCHLIST
          </Button>
        </form>

        <div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">
            Popular Stocks
          </p>
          <div className="flex flex-wrap gap-1">
            {POPULAR_STOCKS.map(s => (
              <button
                key={s}
                onClick={() => handleAdd(s)}
                disabled={addMutation.isPending}
                className="text-[10px] px-2 py-1 bg-secondary hover:bg-accent hover:text-brand rounded transition-colors font-mono"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}