// E:\tradedo\app\frontend\components\agent\agent-actions-panel.tsx

"use client";

import { Button } from "@/components/ui/button";
import { 
  Search, Play, StopCircle, Zap,
  Loader2, Coffee, Bell 
} from "lucide-react";
import { 
  useTriggerScan, useTriggerExecution, useTriggerEOD 
} from "@/lib/hooks/use-agent";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { toast } from "sonner";

export function AgentActionsPanel() {
  const scanMutation = useTriggerScan();
  const executeMutation = useTriggerExecution();
  const eodMutation = useTriggerEOD();

  const testTelegramMutation = useMutation({
    mutationFn: () => api.post("/telegram/test").then(r => r.data),
    onSuccess: () => toast.success("Telegram test sent!"),
    onError: () => toast.error("Telegram test failed"),
  });

  const morningPrepMutation = useMutation({
    mutationFn: () => api.post("/agent/brain/premarket").then(r => r.data),
    onSuccess: () => toast.success("Premarket prep complete!"),
    onError: () => toast.error("Premarket prep failed"),
  });

  return (
    <div className="bg-card border border-border rounded-lg p-4 corner-brackets">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-brand" />
          <h3 className="text-sm font-bold tracking-wider">MANUAL CONTROLS</h3>
        </div>
        <span className="text-[10px] text-muted-foreground font-mono">
          FORCE TRIGGER ANY BRAIN JOB
        </span>
      </div>

      <div className="grid grid-cols-5 gap-3">
        <ActionButton
          icon={<Coffee size={14} />}
          label="PREMARKET"
          description="Fetch data + prep"
          onClick={() => morningPrepMutation.mutate()}
          isPending={morningPrepMutation.isPending}
        />

        <ActionButton
          icon={<Search size={14} />}
          label="RUN SCAN"
          description="Deep market scan"
          onClick={() => scanMutation.mutate()}
          isPending={scanMutation.isPending}
        />

        <ActionButton
          icon={<Play size={14} />}
          label="EXECUTE"
          description="Trade candidates"
          onClick={() => executeMutation.mutate()}
          isPending={executeMutation.isPending}
        />

        <ActionButton
          icon={<StopCircle size={14} />}
          label="EOD SUMMARY"
          description="Send report"
          onClick={() => eodMutation.mutate()}
          isPending={eodMutation.isPending}
        />

        <ActionButton
          icon={<Bell size={14} />}
          label="TEST ALERT"
          description="Send test"
          onClick={() => testTelegramMutation.mutate()}
          isPending={testTelegramMutation.isPending}
        />
      </div>
    </div>
  );
}

function ActionButton({ icon, label, description, onClick, isPending }: any) {
  return (
    <button
      onClick={onClick}
      disabled={isPending}
      className="p-3 rounded-md border border-border hover:border-brand hover:bg-brand/5 transition-all group disabled:opacity-50 text-left"
    >
      <div className="flex items-center gap-2 text-brand mb-1">
        {isPending ? (
          <Loader2 size={14} className="animate-spin" />
        ) : (
          icon
        )}
        <span className="text-xs font-bold">{label}</span>
      </div>
      <p className="text-[10px] text-muted-foreground">{description}</p>
    </button>
  );
}