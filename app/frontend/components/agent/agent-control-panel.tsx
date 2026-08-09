// E:\tradedo\app\frontend\components\agent\agent-control-panel.tsx

"use client";

import { Bot, Power, PowerOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAgentStatus } from "@/lib/hooks/use-agent";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";
import { toast } from "sonner";
import { formatCurrency, cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export function AgentControlPanel() {
  const { data, isLoading } = useAgentStatus();
  const queryClient = useQueryClient();

  const startMutation = useMutation({
    mutationFn: tradeoAPI.startAgent,
    onSuccess: () => {
      toast.success("🚀 Agent activated!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
    onError: () => toast.error("Failed to start agent"),
  });

  const stopMutation = useMutation({
    mutationFn: tradeoAPI.stopAgent,
    onSuccess: () => {
      toast.success("🛑 Agent stopped");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
    onError: () => toast.error("Failed to stop agent"),
  });

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const agent = data?.agent;
  const isActive = agent?.is_active || false;

  return (
    <div className="bg-card border border-border rounded-lg p-6 corner-brackets h-full">
      <div className="flex items-center gap-2 mb-6">
        <Bot size={20} className="text-brand" />
        <h2 className="text-sm font-bold tracking-wider">AGENT CONTROL</h2>
      </div>

      {/* Agent Avatar */}
      <div className="flex flex-col items-center py-6">
        <div className={cn(
          "w-24 h-24 rounded-2xl flex items-center justify-center mb-4 relative transition-all",
          isActive ? "bg-brand shadow-lg shadow-brand/30" : "bg-secondary"
        )}>
          <Bot size={48} className={isActive ? "text-white" : "text-muted-foreground"} />
          
          {isActive && (
            <>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-bull border-2 border-card animate-pulse" />
              <div className="absolute inset-0 rounded-2xl border-2 border-brand animate-pulse" />
            </>
          )}
        </div>

        <div className="text-center mb-4">
          <p className={cn(
            "text-lg font-bold flex items-center gap-2",
            isActive ? "text-bull" : "text-muted-foreground"
          )}>
            <span className={cn(
              "w-2 h-2 rounded-full",
              isActive ? "bg-bull animate-pulse" : "bg-muted-foreground"
            )} />
            {isActive ? "ACTIVE" : "STOPPED"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            AUTONOMOUS MODE
          </p>
        </div>
      </div>

      {/* Capital Info */}
      <div className="space-y-2 mb-6 pt-6 border-t border-border">
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">CAPITAL</span>
          <span className="font-mono font-bold">
            {formatCurrency(agent?.capital || 0, 0)}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">AVAILABLE</span>
          <span className="font-mono font-bold">
            {formatCurrency(agent?.available || 0, 0)}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">DEPLOYED</span>
          <span className="font-mono font-bold text-brand">
            {formatCurrency(agent?.current_exposure || 0, 0)}
          </span>
        </div>
      </div>

      {/* Control Button */}
      <Button
        onClick={() => isActive ? stopMutation.mutate() : startMutation.mutate()}
        disabled={startMutation.isPending || stopMutation.isPending}
        className={cn(
          "w-full h-12 font-bold",
          isActive ? "bg-bear hover:bg-bear-dark" : "bg-bull hover:bg-bull-dark"
        )}
      >
        {(startMutation.isPending || stopMutation.isPending) ? (
          <Loader2 size={16} className="animate-spin mr-2" />
        ) : isActive ? (
          <PowerOff size={16} className="mr-2" />
        ) : (
          <Power size={16} className="mr-2" />
        )}
        {isActive ? "STOP AGENT" : "START AGENT"}
      </Button>

      <p className="text-[10px] text-muted-foreground text-center mt-3">
        {isActive 
          ? "Agent is scanning market and executing trades" 
          : "Click to activate autonomous trading"}
      </p>
    </div>
  );
}