// E:\tradedo\app\frontend\components\dashboard\agent-status.tsx

"use client";

import { Bot, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAgentStatus } from "@/lib/hooks/use-agent";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";
import { toast } from "sonner";
import { formatTime } from "@/lib/utils";
import { useState, useEffect } from "react";

export function AgentStatusWidget() {
  const { data, isLoading } = useAgentStatus();
  const queryClient = useQueryClient();
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    setNow(new Date());
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const startMutation = useMutation({
    mutationFn: tradeoAPI.startAgent,
    onSuccess: () => {
      toast.success("Agent started!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
    onError: () => toast.error("Failed to start agent"),
  });

  const stopMutation = useMutation({
    mutationFn: tradeoAPI.stopAgent,
    onSuccess: () => {
      toast.success("Agent stopped");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
    onError: () => toast.error("Failed to stop agent"),
  });

  const isActive = data?.agent?.is_active || false;
  const openPositions = data?.open_trades?.length || 0;

  const toggleAgent = () => {
    if (isActive) stopMutation.mutate();
    else startMutation.mutate();
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      <h3 className="text-xs font-bold tracking-widest text-muted-foreground mb-4">
        AI AGENT STATUS
      </h3>

      <div className="flex items-center gap-4 mb-4">
        <div className="w-20 h-20 rounded-lg bg-accent flex items-center justify-center relative">
          <Bot size={40} className={isActive ? "text-brand" : "text-muted-foreground"} />
          <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-card ${
            isActive ? "bg-bull animate-pulse" : "bg-muted-foreground"
          }`} />
        </div>

        <div className="flex-1 space-y-2 text-xs">
          <div>
            <p className="text-muted-foreground">STATUS</p>
            <p className={`font-bold flex items-center gap-1 ${
              isActive ? "text-bull" : "text-muted-foreground"
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                isActive ? "bg-bull animate-pulse" : "bg-muted-foreground"
              }`} />
              {isActive ? "Active" : "Stopped"}
            </p>
          </div>
          
          <div>
            <p className="text-muted-foreground">OPEN TRADES</p>
            <p className="font-bold font-mono">{openPositions}</p>
          </div>

          <div>
            <p className="text-muted-foreground">TIME</p>
            <p className="font-mono font-bold text-[11px]">
              {now ? formatTime(now) : "--:--:--"}
            </p>
          </div>
        </div>
      </div>

      <Button
        variant={isActive ? "destructive" : "default"}
        size="sm"
        className="w-full text-xs"
        onClick={toggleAgent}
        disabled={startMutation.isPending || stopMutation.isPending || isLoading}
      >
        {(startMutation.isPending || stopMutation.isPending) ? (
          <Loader2 size={12} className="animate-spin mr-2" />
        ) : null}
        {isActive ? "STOP AGENT" : "START AGENT"}
      </Button>
    </div>
  );
}