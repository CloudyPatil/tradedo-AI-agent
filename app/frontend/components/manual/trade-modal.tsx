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
  // ── 1. Form States ─────────────────────────────────────────
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

  // Charges & Margin States
  const [chargesInfo, setChargesInfo] = useState<any>(null);
  const [marginInfo, setMarginInfo] = useState<any>(null);

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

  // ── 2. DERIVED VALUES (Must be BEFORE useEffect!) ─────────
  const qty = parseInt(quantity) || 0;
  
  const executionPrice = orderType === "MARKET" 
    ? currentPrice 
    : orderType === "LIMIT" 
      ? parseFloat(price) || currentPrice
      : parseFloat(triggerPrice) || currentPrice;
  
  const totalCost = executionPrice * qty;

  const requiredCapital = side === "BUY" 
    ? (marginInfo?.margin_required || totalCost) + (chargesInfo?.total_charges || 0)
    : 0;
    
  const canAfford = side === "SELL" || requiredCapital <= (summary?.available || 0);

  // ── 3. EFFECTS ────────────────────────────────────────────
  
  // Reset side when prop changes
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

  // Fetch charges and margin
  useEffect(() => {
    const fetchCosts = async () => {
      if (!qty || qty <= 0 || !executionPrice || !symbol || !open) return;
      
      try {
        // Get charges
        const chargesRes = await api.post("/charges/calculate", {
          symbol,
          quantity: qty,
          price: executionPrice,
          side,
          product_type: productType,
        });
        setChargesInfo(chargesRes.data);
        
        // Get margin (only for BUY)
        if (side === "BUY") {
          const marginRes = await api.post("/leverage/margin", {
            symbol,
            quantity: qty,
            price: executionPrice,
            product_type: productType,
          });
          setMarginInfo(marginRes.data);
        }
      } catch (e) {
        console.error("Failed to fetch costs:", e);
      }
    };
    
    const timer = setTimeout(fetchCosts, 300);
    return () => clearTimeout(timer);
  }, [symbol, qty, executionPrice, side, productType, open]);

  // ── 4. SUBMIT HANDLER ─────────────────────────────────────
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

  // ── 5. JSX ────────────────────────────────────────────────
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl font-mono font-bold">{cleanSymbol}</span>
              <span className="text-lg font-mono text-brand font-bold">
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
              className="data-[state=active]:bg-bull data-[state=active]:text-white font-bold"
            >
              <TrendingUp size={16} className="mr-2" />
              BUY
            </TabsTrigger>
            <TabsTrigger 
              value="SELL"
              className="data-[state=active]:bg-bear data-[state=active]:text-white font-bold"
            >
              <TrendingDown size={16} className="mr-2" />
              SELL
            </TabsTrigger>
          </TabsList>

          <TabsContent value={side} className="space-y-4 mt-4">
            
            {/* Product Type Selection */}
            <div>
              <Label className="text-xs uppercase tracking-wider font-bold">Product Type</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => setProductType("INTRADAY")}
                  className={cn(
                    "p-3 rounded-lg border-2 transition-all text-left",
                    productType === "INTRADAY"
                      ? "border-brand bg-brand/10"
                      : "border-border hover:border-muted-foreground/30"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={cn(
                      "text-xs font-bold",
                      productType === "INTRADAY" ? "text-brand" : "text-foreground"
                    )}>
                      INTRADAY (MIS)
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 bg-brand/20 text-brand rounded font-bold">
                      5x LEVERAGE
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground">
                    Day trading · Auto square-off at 3:15 PM
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setProductType("DELIVERY")}
                  className={cn(
                    "p-3 rounded-lg border-2 transition-all text-left",
                    productType === "DELIVERY"
                      ? "border-brand bg-brand/10"
                      : "border-border hover:border-muted-foreground/30"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={cn(
                      "text-xs font-bold",
                      productType === "DELIVERY" ? "text-brand" : "text-foreground"
                    )}>
                      DELIVERY (CNC)
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 bg-bull/20 text-bull rounded font-bold">
                      SWING
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground">
                    Hold days/months · No time limit
                  </p>
                </button>
              </div>
            </div>

            {/* Product Type Warnings */}
            {productType === "INTRADAY" && (
              <div className="p-3 bg-neutral/10 border border-neutral/20 rounded-md flex items-start gap-2 text-xs">
                <AlertCircle size={14} className="text-neutral shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-neutral">Auto Square-off at 3:15 PM</p>
                  <p className="text-muted-foreground mt-0.5">
                    Intraday positions are force-closed at 3:15 PM. Cannot hold overnight.
                  </p>
                </div>
              </div>
            )}

            {productType === "DELIVERY" && (
              <div className="p-3 bg-bull/10 border border-bull/20 rounded-md flex items-start gap-2 text-xs">
                <TrendingUp size={14} className="text-bull shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-bull">Long-term Holding Enabled</p>
                  <p className="text-muted-foreground mt-0.5">
                    Hold for days/months. No leverage applied (100% capital required).
                  </p>
                </div>
              </div>
            )}

            {/* Order Type */}
            <div>
              <Label className="text-xs uppercase tracking-wider font-bold">Order Type</Label>
              <div className="grid grid-cols-4 gap-1 mt-2">
                {(["MARKET", "LIMIT", "SL", "SL_MARKET"] as const).map(type => (
                  <button
                    key={type}
                    type="button"
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

            {/* Quantity */}
            <div>
              <Label className="text-xs uppercase tracking-wider font-bold">Quantity</Label>
              <Input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="mt-2 font-mono text-lg h-11"
                min="1"
                placeholder="Number of shares"
              />
            </div>

            {/* Dynamic Price Fields */}
            {(orderType === "LIMIT" || orderType === "SL") && (
              <div>
                <Label className="text-xs uppercase tracking-wider font-bold">
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
                <Label className="text-xs uppercase tracking-wider font-bold">Trigger Price</Label>
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

            {/* Cost & Margin Summary */}
            <div className="space-y-2 pt-2 border-t border-border">
              
              <div className="p-3 rounded-lg border border-border bg-accent/30">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Turnover Value</span>
                  <span className="font-mono font-bold text-lg">
                    {formatCurrency(totalCost, 2)}
                  </span>
                </div>
              </div>

              {/* Leverage Info */}
              {side === "BUY" && marginInfo && productType === "INTRADAY" && (
                <div className="p-3 rounded-lg border border-brand/30 bg-brand/5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <Info size={12} />
                      Intraday Leverage
                    </span>
                    <span className="font-bold text-brand">
                      {marginInfo.leverage}x
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-1">
                    <span className="text-muted-foreground">Margin Blocked</span>
                    <span className="font-mono font-bold">
                      {formatCurrency(marginInfo.margin_required, 2)}
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">
                    Only {marginInfo.margin_pct?.toFixed(1)}% of turnover blocked
                  </p>
                </div>
              )}

              {/* Charges Breakdown */}
              {chargesInfo && (
                <details className="p-3 rounded-lg border border-border bg-accent/30">
                  <summary className="cursor-pointer text-xs font-semibold flex items-center justify-between">
                    <span className="text-muted-foreground">Estimated Charges</span>
                    <span className="font-mono font-bold text-bear">
                      {formatCurrency(chargesInfo.total_charges, 2)}
                    </span>
                  </summary>
                  
                  <div className="mt-2 space-y-1 text-[10px] pt-2 border-t border-border">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Brokerage</span>
                      <span className="font-mono">₹{chargesInfo.brokerage?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">STT Tax</span>
                      <span className="font-mono">₹{chargesInfo.stt?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Exchange Txn</span>
                      <span className="font-mono">₹{chargesInfo.exchange_charges?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">GST (18%)</span>
                      <span className="font-mono">₹{chargesInfo.gst?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">SEBI + Stamp</span>
                      <span className="font-mono">₹{(chargesInfo.sebi_charges + chargesInfo.stamp_duty)?.toFixed(2)}</span>
                    </div>
                  </div>
                </details>
              )}

              {/* Total Required */}
              <div className={cn(
                "p-3 rounded-lg border-2",
                canAfford ? "border-brand/30 bg-brand/5" : "border-bear/30 bg-bear/10"
              )}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-semibold">
                    {side === "BUY" ? "Total Required" : "Est. Net Receipt"}
                  </span>
                  <span className="font-mono font-bold text-lg text-brand">
                    {formatCurrency(
                      side === "BUY" 
                        ? (marginInfo?.margin_required || totalCost) + (chargesInfo?.total_charges || 0)
                        : totalCost - (chargesInfo?.total_charges || 0),
                      2
                    )}
                  </span>
                </div>
                
                {side === "BUY" && (
                  <div className="flex items-center justify-between text-xs mt-1">
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
                  <div className="flex items-center gap-2 mt-2 text-xs text-bear font-bold">
                    <AlertCircle size={12} />
                    Insufficient balance
                  </div>
                )}
              </div>
            </div>

            {/* Notes */}
            <div>
              <Label className="text-xs uppercase tracking-wider font-bold">Notes (optional)</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-2 text-sm"
                placeholder="Trade rationale..."
                maxLength={100}
              />
            </div>

            {/* Submit Button */}
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={
                placeOrder.isPending || 
                !canAfford || 
                qty <= 0 ||
                ((orderType === "LIMIT" || orderType === "SL") && !price) ||
                ((orderType === "SL" || orderType === "SL_MARKET") && !triggerPrice)
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

            <div className="flex items-center justify-between text-[10px] text-muted-foreground">
              <span>Paper trading — no real money</span>
              <span>All charges simulated</span>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}