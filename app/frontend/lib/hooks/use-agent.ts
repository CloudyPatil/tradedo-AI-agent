// E:\tradedo\app\frontend\lib\hooks\use-agent.ts

import { useQuery } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api/client";

export function useAgentStatus() {
  return useQuery({
    queryKey: ["agent-status"],
    queryFn: tradeoAPI.getAgentStatus,
    refetchInterval: 10000, // Every 10s
  });
}

export function useTrades(status: string = "all") {
  return useQuery({
    queryKey: ["trades", status],
    queryFn: () => tradeoAPI.getTrades(status),
    refetchInterval: 30000,
  });
}

export function useTodaysPerformance() {
  return useQuery({
    queryKey: ["todays-performance"],
    queryFn: tradeoAPI.getTodaysPerformance,
    refetchInterval: 30000,
  });
}

// Trigger morning scan
export function useTriggerScan() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => api.post("/agent/brain/scan").then(r => r.data),
    onSuccess: () => {
      toast.success("Morning scan triggered!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
      queryClient.invalidateQueries({ queryKey: ["scan-results"] });
    },
    onError: () => toast.error("Failed to trigger scan"),
  });
}

// Trigger execution
export function useTriggerExecution() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => api.post("/agent/brain/execute").then(r => r.data),
    onSuccess: () => {
      toast.success("Execution triggered!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
      queryClient.invalidateQueries({ queryKey: ["trades"] });
    },
    onError: () => toast.error("Failed to execute"),
  });
}

// Trigger EOD
export function useTriggerEOD() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => api.post("/agent/brain/eod").then(r => r.data),
    onSuccess: () => {
      toast.success("EOD summary sent!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
    onError: () => toast.error("Failed to trigger EOD"),
  });
}

// Get today's scan candidates
export function useScanCandidates() {
  return useQuery({
    queryKey: ["scan-candidates"],
    queryFn: () => api.get("/agent/scan/latest").then(r => r.data),
    refetchInterval: 60000,
  });
}

// Get journal insights
export function useJournalInsights() {
  return useQuery({
    queryKey: ["journal-insights"],
    queryFn: () => api.get("/journal/insights").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

// Get brain status  
export function useBrainStatus() {
  return useQuery({
    queryKey: ["brain-status"],
    queryFn: () => api.get("/agent/brain/status").then(r => r.data),
    refetchInterval: 30000,
  });
}