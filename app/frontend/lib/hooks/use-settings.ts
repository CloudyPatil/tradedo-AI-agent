// E:\tradedo\app\frontend\lib\hooks\use-settings.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, tradeoAPI } from "@/lib/api/client";
import { toast } from "sonner";

export function useSystemHealth() {
  return useQuery({
    queryKey: ["system-health"],
    queryFn: tradeoAPI.getHealth,
    refetchInterval: 30000,
    retry: false,
  });
}

export function useModelsStatus() {
  return useQuery({
    queryKey: ["models-status"],
    queryFn: () => api.get("/models/status").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useLLMStatus() {
  return useQuery({
    queryKey: ["llm-status"],
    queryFn: () => api.get("/agent/llm-status").then(r => r.data),
    refetchInterval: 60000,
  });
}

export function useResetCapital() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (capital: number) => 
      api.post("/agent/reset-capital", null, { params: { new_capital: capital } })
        .then(r => r.data),
    onSuccess: () => {
      toast.success("Capital reset successfully!");
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
    },
    onError: () => toast.error("Failed to reset capital"),
  });
}

export function useTestTelegram() {
  return useMutation({
    mutationFn: () => api.post("/telegram/test").then(r => r.data),
    onSuccess: () => toast.success("Test message sent to Telegram!"),
    onError: () => toast.error("Telegram test failed - check bot token"),
  });
}