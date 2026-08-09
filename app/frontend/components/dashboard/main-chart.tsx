// E:\tradedo\app\frontend\components\dashboard\main-chart.tsx

"use client";

import { useEffect, useRef } from "react";
import { createChart, IChartApi, CandlestickSeries, HistogramSeries, ColorType } from "lightweight-charts";
import { ChevronDown, Maximize2, Settings2 } from "lucide-react";

export function MainChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Generate sample candlestick data
    const data = generateSampleData(150);

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "hsl(var(--muted-foreground))",
      },
      grid: {
        vertLines: { color: "hsl(var(--border))", visible: false },
        horzLines: { color: "hsl(var(--border))" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 380,
      rightPriceScale: {
        borderColor: "hsl(var(--border))",
      },
      timeScale: {
        borderColor: "hsl(var(--border))",
        timeVisible: true,
      },
    });

    chartRef.current = chart;

    // Candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22C55E",
      downColor: "#EF4444",
      borderVisible: false,
      wickUpColor: "#22C55E",
      wickDownColor: "#EF4444",
    });
    candleSeries.setData(data);

    // Volume series
    const volumeData = data.map(d => ({
      time: d.time,
      value: Math.random() * 1000000,
      color: d.close >= d.open ? "#22C55E33" : "#EF444433",
    }));

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeries.setData(volumeData as any);

    chart.timeScale().fitContent();

    // Resize handler
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      {/* Chart Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 text-sm font-semibold hover:text-brand transition-colors">
            NIFTY 50 · 1D · NSE
            <ChevronDown size={14} />
          </button>
          
          <div className="flex items-center gap-3 text-xs font-mono">
            <span className="text-muted-foreground">O</span>
            <span className="text-foreground">24185.50</span>
            <span className="text-muted-foreground">H</span>
            <span className="text-foreground">24331.85</span>
            <span className="text-muted-foreground">L</span>
            <span className="text-foreground">24120.15</span>
            <span className="text-muted-foreground">C</span>
            <span className="text-bull">24245.10</span>
            <span className="text-bull">+271.35 (+1.13%)</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button className="p-1.5 rounded hover:bg-accent">
            <Settings2 size={14} />
          </button>
          <button className="p-1.5 rounded hover:bg-accent">
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      {/* Chart Container */}
      <div ref={chartContainerRef} className="w-full" />

      {/* Time frame buttons */}
      <div className="flex items-center gap-1 mt-3 pt-3 border-t border-border">
        {["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y", "All"].map(tf => (
          <button
            key={tf}
            className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
              tf === "1D"
                ? "bg-brand text-white"
                : "text-muted-foreground hover:text-foreground hover:bg-accent"
            }`}
          >
            {tf}
          </button>
        ))}
      </div>
    </div>
  );
}

// Helper function
function generateSampleData(count: number) {
  const data = [];
  let currentPrice = 24000;
  const now = Math.floor(Date.now() / 1000);

  for (let i = 0; i < count; i++) {
    const time = now - (count - i) * 86400;
    const open = currentPrice;
    const change = (Math.random() - 0.5) * 200;
    const close = open + change;
    const high = Math.max(open, close) + Math.random() * 50;
    const low = Math.min(open, close) - Math.random() * 50;

    data.push({
      time: time as any,
      open,
      high,
      low,
      close,
    });

    currentPrice = close;
  }

  return data;
}