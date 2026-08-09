// E:\tradedo\app\frontend\components\stock\social-intel.tsx

"use client";

import { useStockNews } from "@/lib/hooks/use-stock";
import { MessageSquare, Video, Loader2, Users, Hash } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  symbol: string;
}

export function SocialIntel({ symbol }: Props) {
  const { data, isLoading } = useStockNews(symbol);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4 h-full flex items-center justify-center">
        <Loader2 className="animate-spin text-brand" size={24} />
      </div>
    );
  }

  const sources = data?.sources || {};
  const reddit = sources.reddit;
  const stocktwits = sources.stocktwits;
  const youtube = sources.youtube;
  const twitter = sources.twitter;

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold tracking-wider flex items-center gap-2">
          <Users size={16} />
          SOCIAL INTELLIGENCE
        </h3>
        {data?.label && (
          <span className={cn(
            "text-xs font-bold px-2 py-0.5 rounded",
            data.label === "BULLISH" && "bg-bull/10 text-bull",
            data.label === "BEARISH" && "bg-bear/10 text-bear",
            data.label === "NEUTRAL" && "bg-neutral/10 text-neutral",
            data.label === "NO_DATA" && "bg-muted text-muted-foreground",
          )}>
            {data.label}
          </span>
        )}
      </div>

      {/* Overall Buzz */}
      {data?.buzz_score !== undefined && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted-foreground">SOCIAL BUZZ</span>
            <span className="font-mono font-bold">{data.buzz_score}/100</span>
          </div>
          <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand to-bull rounded-full transition-all"
              style={{ width: `${data.buzz_score}%` }}
            />
          </div>
        </div>
      )}

      {/* Source Cards */}
      <div className="space-y-3 flex-1 overflow-y-auto">
        <SourceCard
          icon={<MessageSquare size={14} />}
          name="Reddit"
          count={reddit?.posts || 0}
          score={reddit?.score || 0}
          label={reddit?.label}
          color="text-orange-500"
        />
        
        <SourceCard
          icon={<Hash size={14} />}
          name="StockTwits"
          count={stocktwits?.messages || 0}
          score={stocktwits?.score || 0}
          label={stocktwits?.label}
          color="text-blue-500"
          extra={stocktwits ? `${stocktwits.bullish || 0} bull | ${stocktwits.bearish || 0} bear` : ""}
        />
        
        <SourceCard
          icon={<Video size={14} />}
          name="YouTube"
          count={youtube?.videos || 0}
          score={youtube?.score || 0}
          label={youtube?.label}
          color="text-red-500"
          extra={youtube?.trusted_videos ? `${youtube.trusted_videos} trusted` : ""}
        />
        
        <SourceCard
          icon={<Hash size={14} />}
          name="Twitter/X"
          count={twitter?.tweets || 0}
          score={twitter?.score || 0}
          label={twitter?.label}
          color="text-sky-500"
          extra={twitter?.trusted ? `${twitter.trusted} verified` : ""}
        />
      </div>

      {data?.consensus_target && (
        <div className="mt-3 pt-3 border-t border-border">
          <p className="text-xs text-muted-foreground">CONSENSUS TARGET (YT)</p>
          <p className="font-mono font-bold text-lg text-brand">
            ₹{data.consensus_target}
          </p>
        </div>
      )}
    </div>
  );
}

function SourceCard({ icon, name, count, score, label, color, extra }: any) {
  return (
    <div className="p-3 rounded-md border border-border">
      <div className="flex items-center justify-between mb-2">
        <div className={cn("flex items-center gap-2 text-sm font-semibold", color)}>
          {icon}
          {name}
        </div>
        <span className={cn(
          "text-[10px] font-bold px-2 py-0.5 rounded",
          label === "BULLISH" && "bg-bull/10 text-bull",
          label === "BEARISH" && "bg-bear/10 text-bear",
          label === "NEUTRAL" && "bg-neutral/10 text-neutral",
          (label === "NO_DATA" || !label) && "bg-muted text-muted-foreground",
        )}>
          {label || "NO DATA"}
        </span>
      </div>
      
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">
          {count} items {extra && `· ${extra}`}
        </span>
        <span className="font-mono font-bold">
          {score > 0 ? "+" : ""}{score.toFixed(2)}
        </span>
      </div>
    </div>
  );
}