// E:\tradedo\app\frontend\components\trades\trade-detail-dialog.tsx

"use client";

import { 
  Dialog, DialogContent, DialogHeader, DialogTitle 
} from "@/components/ui/dialog";
import { formatCurrency, formatTime, cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Clock, Target, Shield, DollarSign } from "lucide-react";
import Link from "next/link";

interface Props {
  trade: any;
  onClose: () => void;
}

export function TradeDetailDialog({ trade, onClose }: Props) {
  if (!trade) return null;

  const isLong = trade.direction === "LONG";
  const isOpen = trade.status === "OPEN";
  const pnl = trade.pnl || 0;
  const isWin = pnl > 0;
  const cleanSymbol = trade.symbol.replace(".NS", "");

  let metadata: any = {};
  try {
    metadata = trade.metadata ? JSON.parse(trade.metadata) : {};
  } catch (e) {}

  return (
    <Dialog open={!!trade} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link 
                href={`/stock/${cleanSymbol}`}
                className="text-xl font-mono font-bold hover:text-brand"
              >
                {cleanSymbol}
              </Link>
              <div className={cn(
                "flex items-center gap-1 px-2 py-1 rounded text-xs font-bold",
                isLong ? "text-bull bg-bull/10" : "text-bear bg-bear/10"
              )}>
                {isLong ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                {trade.direction}
              </div>
              <span className="text-xs text-muted-foreground">Trade #{trade.id}</span>
            </div>

            {!isOpen && (
              <div className={cn(
                "text-right",
                isWin ? "text-bull" : "text-bear"
              )}>
                <p className="text-2xl font-mono font-bold">
                  {isWin ? "+" : ""}{formatCurrency(pnl, 0)}
                </p>
                <p className="text-xs">
                  {trade.pnl_pct?.toFixed(2)}% return
                </p>
              </div>
            )}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          
          {/* Price Levels */}
          <div className="grid grid-cols-4 gap-3">
            <DetailBox
              icon={<DollarSign size={12} />}
              label="ENTRY"
              value={`₹${trade.entry_price?.toFixed(2)}`}
              color="text-foreground"
            />
            <DetailBox
              icon={<Shield size={12} />}
              label="STOP LOSS"
              value={`₹${(trade.trailing_sl || trade.stop_loss)?.toFixed(2)}`}
              color="text-bear"
            />
            <DetailBox
              icon={<Target size={12} />}
              label="TARGET 1"
              value={`₹${trade.target_1?.toFixed(2)}`}
              color="text-bull"
            />
            <DetailBox
              icon={<Target size={12} />}
              label="TARGET 2"
              value={`₹${trade.target_2?.toFixed(2)}`}
              color="text-bull"
            />
          </div>

          {/* Position */}
          <div className="p-4 bg-accent/30 rounded-lg">
            <h4 className="text-xs font-bold uppercase tracking-wider mb-3 text-muted-foreground">
              Position Details
            </h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-[10px] text-muted-foreground">Quantity</p>
                <p className="font-mono font-bold">{trade.quantity}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">Investment</p>
                <p className="font-mono font-bold">{formatCurrency(trade.investment || 0, 0)}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">Risk Amount</p>
                <p className="font-mono font-bold text-bear">
                  {formatCurrency(trade.risk_amount || 0, 0)} ({trade.risk_pct?.toFixed(2)}%)
                </p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">Sector</p>
                <p className="font-bold text-brand">{trade.sector}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">ML Confidence</p>
                <p className="font-mono font-bold">{trade.ml_confidence?.toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">Composite Score</p>
                <p className="font-mono font-bold text-brand">{trade.composite_score?.toFixed(1)}</p>
              </div>
            </div>
          </div>

          {/* Times */}
          <div className="p-4 bg-accent/30 rounded-lg">
            <h4 className="text-xs font-bold uppercase tracking-wider mb-3 text-muted-foreground flex items-center gap-2">
              <Clock size={12} />
              Timing
            </h4>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-[10px] text-muted-foreground">Entry Time</p>
                <p className="font-mono font-bold">
                  {trade.entry_time ? new Date(trade.entry_time).toLocaleString("en-IN") : "—"}
                </p>
              </div>
              {trade.exit_time && (
                <div>
                  <p className="text-[10px] text-muted-foreground">Exit Time</p>
                  <p className="font-mono font-bold">
                    {new Date(trade.exit_time).toLocaleString("en-IN")}
                  </p>
                </div>
              )}
              {trade.hold_duration_mins > 0 && (
                <div>
                  <p className="text-[10px] text-muted-foreground">Duration</p>
                  <p className="font-mono font-bold">
                    {Math.floor(trade.hold_duration_mins / 60)}h {trade.hold_duration_mins % 60}m
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Exit Info */}
          {!isOpen && (
            <div className={cn(
              "p-4 rounded-lg border",
              isWin ? "bg-bull/5 border-bull/20" : "bg-bear/5 border-bear/20"
            )}>
              <h4 className="text-xs font-bold uppercase tracking-wider mb-3 text-muted-foreground">
                Exit Details
              </h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-[10px] text-muted-foreground">Exit Price</p>
                  <p className="font-mono font-bold">₹{trade.exit_price?.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">Exit Reason</p>
                  <p className="font-bold">{trade.exit_reason?.replace(/_/g, " ")}</p>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">Status</p>
                  <p className="font-bold">{trade.status?.replace(/_/g, " ")}</p>
                </div>
              </div>
            </div>
          )}

          {/* AI Reasoning */}
          {trade.ai_reasoning && (
            <div className="p-4 bg-brand/5 border border-brand/20 rounded-lg">
              <h4 className="text-xs font-bold uppercase tracking-wider mb-2 text-brand">
                🤖 AI Reasoning
              </h4>
              <p className="text-sm text-foreground leading-relaxed">
                {trade.ai_reasoning}
              </p>
            </div>
          )}

          {/* Journal Snapshot Preview */}
          {metadata.master_result && (
            <div className="p-4 bg-accent/30 rounded-lg">
              <h4 className="text-xs font-bold uppercase tracking-wider mb-3 text-muted-foreground">
                Analysis at Entry
              </h4>
              <div className="grid grid-cols-3 gap-3 text-xs">
                <div>
                  <p className="text-[10px] text-muted-foreground">Verdict</p>
                  <p className="font-bold">{metadata.master_result.verdict}</p>
                </div>
                {metadata.master_result.sentiment && (
                  <div>
                    <p className="text-[10px] text-muted-foreground">News Sentiment</p>
                    <p className="font-bold">{metadata.master_result.sentiment}</p>
                  </div>
                )}
                {metadata.master_result.social && (
                  <div>
                    <p className="text-[10px] text-muted-foreground">Social Sentiment</p>
                    <p className="font-bold">{metadata.master_result.social}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Highest/Lowest */}
          {(trade.highest_price || trade.lowest_price) && (
            <div className="grid grid-cols-2 gap-3">
              {trade.highest_price && (
                <div className="p-3 bg-bull/5 border border-bull/20 rounded-lg">
                  <p className="text-[10px] text-bull font-bold uppercase">Highest Price</p>
                  <p className="text-lg font-mono font-bold">₹{trade.highest_price.toFixed(2)}</p>
                </div>
              )}
              {trade.lowest_price && (
                <div className="p-3 bg-bear/5 border border-bear/20 rounded-lg">
                  <p className="text-[10px] text-bear font-bold uppercase">Lowest Price</p>
                  <p className="text-lg font-mono font-bold">₹{trade.lowest_price.toFixed(2)}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function DetailBox({ icon, label, value, color }: any) {
  return (
    <div className="p-3 bg-accent/30 rounded-lg">
      <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
        {icon}
        <span className="text-[10px] font-bold uppercase tracking-wider">{label}</span>
      </div>
      <p className={cn("font-mono font-bold text-sm", color)}>{value}</p>
    </div>
  );
}