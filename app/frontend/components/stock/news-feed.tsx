// E:\tradedo\app\frontend\components\stock\news-feed.tsx

"use client";

import { useStockPrediction } from "@/lib/hooks/use-stock";
import { Newspaper, ExternalLink, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  symbol: string;
}

export function NewsFeed({ symbol }: Props) {
  const { data, isLoading } = useStockPrediction(symbol);
  const news = data?.news || [];
  const sentiment = data?.sentiment;

  const sentimentColors: Record<string, string> = {
    VERY_POSITIVE: "text-bull",
    POSITIVE: "text-bull",
    NEUTRAL: "text-neutral",
    NEGATIVE: "text-bear",
    VERY_NEGATIVE: "text-bear",
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
          <Newspaper size={16} />
          NEWS & SENTIMENT
        </h3>
        {sentiment && (
          <span className={cn(
            "text-xs font-bold",
            sentimentColors[sentiment.label] || "text-muted-foreground"
          )}>
            {sentiment.label} ({sentiment.score > 0 ? "+" : ""}{sentiment.score})
          </span>
        )}
      </div>

      {sentiment?.reasoning && (
        <div className="p-3 bg-accent/30 rounded-md mb-3">
          <p className="text-xs text-muted-foreground">{sentiment.reasoning}</p>
        </div>
      )}

      {sentiment?.risk_flag && (
        <div className="p-2 bg-bear/10 border border-bear/20 rounded-md mb-3">
          <p className="text-xs text-bear font-bold">⚠️ Risk flag detected</p>
        </div>
      )}

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="animate-spin text-brand" size={24} />
        </div>
      ) : news.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">
          No recent news
        </div>
      ) : (
        <div className="flex-1 space-y-2 overflow-y-auto max-h-96">
          {news.map((article: any, i: number) => (
            <a
              key={i}
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-3 rounded-md hover:bg-accent/50 transition-colors border border-border hover:border-brand"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-xs text-foreground leading-snug flex-1">
                  {article.title}
                </p>
                <ExternalLink size={12} className="text-muted-foreground shrink-0 mt-0.5" />
              </div>
              <div className="flex items-center gap-2 mt-2 text-[10px]">
                <span className="text-brand capitalize">{article.source?.replace(/_/g, " ")}</span>
                <span className="text-muted-foreground">·</span>
                <span className="text-muted-foreground">{article.published?.slice(0, 16)}</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}