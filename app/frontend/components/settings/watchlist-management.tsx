// E:\tradedo\app\frontend\components\settings\watchlist-management.tsx

"use client";

import { useState } from "react";
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist } from "@/lib/hooks/use-market";
import { List, Plus, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export function WatchlistManagement() {
  const [newSymbol, setNewSymbol] = useState("");
  const { data, isLoading } = useWatchlist("intraday");
  const addMutation = useAddToWatchlist();
  const removeMutation = useRemoveFromWatchlist();

  const handleAdd = async () => {
    const clean = newSymbol.trim().toUpperCase();
    if (!clean) return;
    
    const fullSymbol = clean.endsWith(".NS") ? clean : `${clean}.NS`;
    
    try {
      await addMutation.mutateAsync(fullSymbol);
      setNewSymbol("");
    } catch (e) {}
  };

  const stocks = data?.results || [];

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <List size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">WATCHLIST MANAGEMENT</h3>
        </div>
        <span className="text-xs text-muted-foreground">
          {stocks.length} stocks
        </span>
      </div>

      {/* Add stock */}
      <div className="flex gap-2 mb-4">
        <Input
          placeholder="Add stock (e.g. RELIANCE)"
          value={newSymbol}
          onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          className="font-mono text-sm"
        />
        <Button
          onClick={handleAdd}
          disabled={!newSymbol || addMutation.isPending}
          className="bg-brand hover:bg-brand-500"
        >
          {addMutation.isPending ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Plus size={14} />
          )}
        </Button>
      </div>

      {/* Stocks Grid */}
      {isLoading ? (
        <div className="grid grid-cols-6 gap-2">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : stocks.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground text-sm">
          No stocks in watchlist. Add some above.
        </div>
      ) : (
        <div className="grid grid-cols-6 gap-2">
          {stocks.map((stock: any) => (
            <div
              key={stock.symbol}
              className="group flex items-center justify-between p-2 rounded border border-border hover:border-brand/50 transition-all"
            >
              <div className="flex-1 min-w-0">
                <p className="font-mono font-bold text-xs truncate">
                  {stock.symbol.replace(".NS", "")}
                </p>
                <p className="text-[10px] text-muted-foreground font-mono">
                  ₹{stock.current_price?.toFixed(0) || "—"}
                </p>
              </div>
              
              <button
                onClick={() => removeMutation.mutate(stock.symbol)}
                disabled={removeMutation.isPending}
                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-bear/20 transition-all"
              >
                <X size={12} className="text-muted-foreground hover:text-bear" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}