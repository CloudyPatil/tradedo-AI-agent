// E:\tradedo\app\frontend\lib\hooks\use-screener.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { toast } from "sonner";

export function useScreenerStocks(filters: {
  signal?: string;
  sector?: string;
  minConfidence?: number;
  sortBy?: string;
  order?: string;
}) {
  return useQuery({
    queryKey: ["screener-stocks", filters],
    queryFn: () => api.get("/screener/stocks", {
      params: {
        signal: filters.signal || "ALL",
        sector: filters.sector || "ALL",
        min_confidence: filters.minConfidence || 0,
        sort_by: filters.sortBy || "confidence",
        order: filters.order || "desc",
      }
    }).then(r => r.data),
    refetchInterval: 60000,
  });
}

export function useScreenerStats() {
  return useQuery({
    queryKey: ["screener-stats"],
    queryFn: () => api.get("/screener/stats").then(r => r.data),
    refetchInterval: 60000,
  });
}

export function useTriggerScreenerScan() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ tier, mode }: { tier: string; mode: string }) =>
      api.post(`/screener/scan?tier=${tier}&mode=${mode}`).then(r => r.data),
    onSuccess: (result) => {
      toast.success(
        `Scanned ${result.total_scanned} stocks in ${result.duration_seconds}s`
      );
      queryClient.invalidateQueries({ queryKey: ["screener-stocks"] });
      queryClient.invalidateQueries({ queryKey: ["screener-stats"] });
    },
    onError: (error: any) => {
      toast.error("Scan failed: " + error.message);
    },
  });
}

export function useTopPicks(mode: string = "swing") {
  return useQuery({
    queryKey: ["top-picks", mode],
    queryFn: () => api.get(`/screener/top-picks?mode=${mode}`).then(r => r.data),
    refetchInterval: 60000,
  });
}