// E:\tradedo\app\frontend\components\manual\trade-modal.tsx

"use client";

import { useState, useEffect } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { usePlaceOrder, useManualSummary } from "@/lib/hooks/use-manual";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { formatCurrency, cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Info, Loader2, AlertCircle } from "lucide-react";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  symbol: string;
  defaultSide?: "BUY" | "SELL";
}

export function TradeModal({ open, onOpenChange, symbol, defaultSide = "BUY" }: Props) {
  const [side, setSide] = useState<"BUY" | "SELL">(defaultSide);
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT" | "SL" | "SL_MARKET">("MARKET");
  const [quantity, setQuantity] = useState<string>("1");
  const [price, setPrice] = useState<string>("");
  const [triggerPrice, setTriggerPrice] = useState<string>("");
  const [productType, setProductType] = useState<"INTRADAY" | "DELIVERY">("INTRADAY");
  const [isBracket, setIsBracket] = useState(false);
  const [stopLoss, setStopLoss] = useState<string>("");
  const [target, setTarget] = useState<string>("");
  const [notes, setNotes] = useState<string>("");

  const placeOrder = usePlaceOrder();
  const { data: summary } = useManualSummary();
  
  // Get current price
  const { data: priceData } = useQuery({
    queryKey: ["price", symbol],
    queryFn: () => api.get(`/predict/${symbol}`, { params: { mode: "swing" } }).then(r => r.data),
    enabled: open && !!symbol,
    staleTime: 30000,
  });
  
  const currentPrice = priceData?.current_price || 0;
  const cleanSymbol = symbol.replace(".NS", "");
  
  // Update side when default changes
  useEffect(() => {
    setSide(defaultSide);
  }, [defaultSide, open]);

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setQuantity("1");
      setPrice(currentPrice.toString());
      setTriggerPrice(currentPrice.toString());
      setStopLoss("");
      setTarget("");
      setNotes("");
    }
  }, [open, currentPrice]);

  // Calculate required capital
  const executionPrice = orderType === "MARKET" 
    ? currentPrice 
    : orderType === "LIMIT" 
      ? parseFloat(price) || currentPrice
      : parseFloat(triggerPrice) || currentPrice;
  
  const qty = parseInt(quantity) || 0;
  const totalCost = executionPrice * qty;
  const canAfford = side === "SELL" || totalCost <= (summary?.available || 0);

  const handleSubmit = () => {
    const orderData: any = {
      symbol,
      order_type: orderType,
      side,
      quantity: qty,
      product_type: productType,
      notes: notes || undefined,
    };

    if (orderType === "LIMIT") {
      orderData.price = parseFloat(price);
    }

    if (orderType === "SL" || orderType === "SL_MARKET") {
      orderData.trigger_price = parseFloat(triggerPrice);
      if (orderType === "SL") {
        orderData.price = parseFloat(price);
      }
    }

    if (isBracket && side === "BUY") {
      orderData.is_bracket = true;
      orderData.stop_loss = parseFloat(stopLoss);
      orderData.target = parseFloat(target);
    }

    placeOrder.mutate(orderData, {
      onSuccess: (data) => {
        if (data.success) {
          onOpenChange(false);
        }
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl font-mono">{cleanSymbol}</span>
              <span className="text-lg font-mono text-brand">
                ₹{currentPrice.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <div className="w-1.5 h-1.5 rounded-full bg-bull animate-pulse" />
              LIVE
            </div>
          </DialogTitle>
        </DialogHeader>

        {/* Buy/Sell Tabs */}
        <Tabs value={side} onValueChange={(v) => setSide(v as any)}>
          <TabsList className="grid w-full grid-cols-2 h-12">
            <TabsTrigger 
              value="BUY"
              className="data-[state=active]:bg-bull data-[state=active]:text-white"
            >
              <TrendingUp size={16} className="mr-2" />
              BUY
            </TabsTrigger>
            <TabsTrigger 
              value="SELL"
              className="data-[state=active]:bg-bear data-[state=active]:text-white"
            >
              <TrendingDown size={16} className="mr-2" />
              SELL
            </TabsTrigger>
          </TabsList>

          <TabsContent value={side} className="space-y-4 mt-4">
            
            {/* Order Type */}
            <div>
              <Label className="text-xs uppercase tracking-wider">Order Type</Label>
              <div className="grid grid-cols-4 gap-1 mt-2">
                {(["MARKET", "LIMIT", "SL", "SL_MARKET"] as const).map(type => (
                  <button
                    key={type}
                    onClick={() => setOrderType(type)}
                    className={cn(
                      "py-2 rounded text-xs font-bold transition-colors",
                      orderType === type
                        ? "bg-brand text-white"
                        : "bg-secondary text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {type.replace("_", "-")}
                  </button>
                ))}
              </div>
            </div>

            {/* Product Type */}
            <div>
              <Label className="text-xs uppercase tracking-wider">Product</Label>
              <div className="grid grid-cols-2 gap-1 mt-2">
                {(["INTRADAY", "DELIVERY"] as const).map(type => (
                  <button
                    key={type}
                    onClick={() => setProductType(type)}
                    className={cn(
                      "py-2 rounded text-xs font-bold transition-colors",
                      productType === type
                        ? "bg-brand text-white"
                        : "bg-secondary text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Quantity */}
            <div>
              <Label className="text-xs uppercase tracking-wider">Quantity</Label>
              <Input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="mt-2 font-mono text-lg h-11"
                min="1"
                placeholder="Number of shares"
              />
            </div>

            {/* Price fields (dynamic based on order type) */}
            {(orderType === "LIMIT" || orderType === "SL") && (
              <div>
                <Label className="text-xs uppercase tracking-wider">
                  {orderType === "SL" ? "Limit Price" : "Price"}
                </Label>
                <Input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  className="mt-2 font-mono text-lg h-11"
                  step="0.05"
                  placeholder="₹"
                />
              </div>
            )}

            {(orderType === "SL" || orderType === "SL_MARKET") && (
              <div>
                <Label className="text-xs uppercase tracking-wider">Trigger Price</Label>
                <Input
                  type="number"
                  value={triggerPrice}
                  onChange={(e) => setTriggerPrice(e.target.value)}
                  className="mt-2 font-mono text-lg h-11"
                  step="0.05"
                  placeholder="Trigger ₹"
                />
              </div>
            )}

            {/* Bracket Order (BUY only) */}
            {side === "BUY" && (
              <div className="pt-2 border-t border-border">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <Label className="text-xs uppercase tracking-wider">Bracket Order</Label>
                    <p className="text-[10px] text-muted-foreground">Auto SL + Target</p>
                  </div>
                  <Switch
                    checked={isBracket}
                    onCheckedChange={setIsBracket}
                  />
                </div>

                {isBracket && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-[10px] text-bear">Stop Loss</Label>
                      <Input
                        type="number"
                        value={stopLoss}
                        onChange={(e) => setStopLoss(e.target.value)}
                        className="mt-1 font-mono h-10 text-sm"
                        step="0.05"
                        placeholder="₹"
                      />
                    </div>
                    <div>
                      <Label className="text-[10px] text-bull">Target</Label>
                      <Input
                        type="number"
                        value={target}
                        onChange={(e) => setTarget(e.target.value)}
                        className="mt-1 font-mono h-10 text-sm"
                        step="0.05"
                        placeholder="₹"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Notes */}
            <div>
              <Label className="text-xs uppercase tracking-wider">Notes (optional)</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-2 text-sm"
                placeholder="Trade rationale..."
                maxLength={100}
              />
            </div>

            {/* Cost Summary */}
            <div className={cn(
              "p-4 rounded-lg border",
              canAfford ? "bg-accent/30" : "bg-bear/10 border-bear/30"
            )}>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-muted-foreground">Estimated Value</span>
                <span className="font-mono font-bold text-lg">
                  {formatCurrency(totalCost, 2)}
                </span>
              </div>
              
              {side === "BUY" && (
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Available Balance</span>
                  <span className={cn(
                    "font-mono font-bold",
                    canAfford ? "text-foreground" : "text-bear"
                  )}>
                    {formatCurrency(summary?.available || 0, 2)}
                  </span>
                </div>
              )}
              
              {!canAfford && side === "BUY" && (
                <div className="flex items-center gap-2 mt-2 text-xs text-bear">
                  <AlertCircle size={12} />
                  Insufficient balance
                </div>
              )}
            </div>

            {/* Submit Button */}
            <Button
              onClick={handleSubmit}
              disabled={
                placeOrder.isPending || 
                !canAfford || 
                qty <= 0 ||
                ((orderType === "LIMIT" || orderType === "SL") && !price) ||
                ((orderType === "SL" || orderType === "SL_MARKET") && !triggerPrice) ||
                (isBracket && (!stopLoss || !target))
              }
              className={cn(
                "w-full h-12 text-base font-bold",
                side === "BUY" 
                  ? "bg-bull hover:bg-bull-dark" 
                  : "bg-bear hover:bg-bear-dark"
              )}
            >
              {placeOrder.isPending ? (
                <Loader2 className="animate-spin mr-2" size={16} />
              ) : side === "BUY" ? (
                <TrendingUp size={16} className="mr-2" />
              ) : (
                <TrendingDown size={16} className="mr-2" />
              )}
              {side} {qty} {cleanSymbol}
            </Button>

            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <Info size={12} />
              <span>Paper trading — no real money involved</span>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}