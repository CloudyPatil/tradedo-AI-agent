// E:\tradedo\app\frontend\components\stock\price-chart.tsx

"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, IChartApi, CandlestickSeries, HistogramSeries, LineSeries, LineStyle, ColorType } from "lightweight-charts";
import { Loader2, Maximize2, Minimize2 } from "lucide-react";
import { useStockChart, useStockPrediction } from "@/lib/hooks/use-stock";
import { Button } from "@/components/ui/button";

interface Props {
  symbol: string;
}

export function PriceChart({ symbol }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<"swing" | "intraday">("swing");
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const { data: chartData, isLoading } = useStockChart(symbol, mode);
  const { data: predictionData } = useStockPrediction(symbol, mode);
  const tradePlan = predictionData?.trade_plan;

  useEffect(() => {
    if (!containerRef.current || !chartData) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "hsl(var(--muted-foreground))",
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: "hsl(var(--border))" },
      },
      width: containerRef.current.clientWidth,
      height: isFullscreen ? window.innerHeight - 200 : 400,
      rightPriceScale: { borderColor: "hsl(var(--border))" },
      timeScale: {
        borderColor: "hsl(var(--border))",
        timeVisible: mode === "intraday",
      },
    });

    // Candles
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: "#22C55E",
      downColor: "#EF4444",
      borderVisible: false,
      wickUpColor: "#22C55E",
      wickDownColor: "#EF4444",
    });
    candles.setData(chartData.candles);

    // Volume
    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });
    volume.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volume.setData(chartData.volume as any);

    // Moving averages
    if (chartData.overlays?.ema20?.length > 0) {
      const ema = chart.addSeries(LineSeries, {
        color: "#F59E0B",
        lineWidth: 2,
        title: "EMA 20",
        priceLineVisible: false,
        lastValueVisible: false,
      });
      ema.setData(chartData.overlays.ema20);
    }

    if (chartData.overlays?.sma50?.length > 0) {
      const sma = chart.addSeries(LineSeries, {
        color: "#3B82F6",
        lineWidth: 2,
        title: "SMA 50",
        priceLineVisible: false,
        lastValueVisible: false,
      });
      sma.setData(chartData.overlays.sma50);
    }

    // Trade Plan Lines
    if (tradePlan?.tradeable) {
      if (tradePlan.entry?.price) {
        candles.createPriceLine({
          price: tradePlan.entry.price,
          color: "#FF5722",
          lineWidth: 2,
          lineStyle: LineStyle.Solid,
          axisLabelVisible: true,
          title: `Entry ₹${tradePlan.entry.price}`,
        });
      }
      
      if (tradePlan.target_1?.price) {
        candles.createPriceLine({
          price: tradePlan.target_1.price,
          color: "#22C55E",
          lineWidth: 2,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: `T1 ₹${tradePlan.target_1.price}`,
        });
      }
      
      if (tradePlan.target_2?.price) {
        candles.createPriceLine({
          price: tradePlan.target_2.price,
          color: "#16A34A",
          lineWidth: 2,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: `T2 ₹${tradePlan.target_2.price}`,
        });
      }
      
      if (tradePlan.stop_loss?.price) {
        candles.createPriceLine({
          price: tradePlan.stop_loss.price,
          color: "#EF4444",
          lineWidth: 2,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: `SL ₹${tradePlan.stop_loss.price}`,
        });
      }
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [chartData, tradePlan, isFullscreen, mode]);

  return (
    <div className={`bg-card border border-border rounded-lg p-4 corner-brackets ${
      isFullscreen ? "fixed inset-4 z-50" : ""
    }`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold tracking-wider">
          PRICE CHART
          <span className="text-xs text-muted-foreground ml-2 font-normal">
            {chartData?.candles?.length || 0} candles
          </span>
        </h3>

        <div className="flex items-center gap-2">
          {/* Mode Toggle */}
          <div className="flex bg-secondary border border-border rounded p-1">
            <button
              onClick={() => setMode("swing")}
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                mode === "swing" ? "bg-brand text-white" : "text-muted-foreground"
              }`}
            >
              DAILY
            </button>
            <button
              onClick={() => setMode("intraday")}
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                mode === "intraday" ? "bg-brand text-white" : "text-muted-foreground"
              }`}
            >
              5MIN
            </button>
          </div>

          <Button
            variant="ghost"
            size="icon"
            className="w-7 h-7"
            onClick={() => setIsFullscreen(!isFullscreen)}
          >
            {isFullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="h-96 flex items-center justify-center">
          <Loader2 className="animate-spin text-brand" size={32} />
        </div>
      ) : (
        <div ref={containerRef} className="w-full" />
      )}

      {tradePlan?.tradeable && (
        <div className="mt-3 pt-3 border-t border-border flex items-center gap-4 text-xs">
          <LegendDot color="#FF5722" label="Entry" solid />
          <LegendDot color="#22C55E" label="Target 1" />
          <LegendDot color="#16A34A" label="Target 2" />
          <LegendDot color="#EF4444" label="Stop Loss" />
        </div>
      )}
    </div>
  );
}

function LegendDot({ color, label, solid }: { color: string; label: string; solid?: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <div
        className="w-4 h-0.5"
        style={{
          background: solid ? color : `repeating-linear-gradient(to right, ${color} 0 4px, transparent 4px 7px)`,
        }}
      />
      <span className="text-muted-foreground">{label}</span>
    </div>
  );
}