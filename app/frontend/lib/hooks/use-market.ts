// E:\tradedo\app\frontend\lib\hooks\use-market.ts

import { useQuery } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api/client";

export function useGlobalMarkets() {
  return useQuery({
    queryKey: ["global-markets"],
    queryFn: tradeoAPI.getGlobalMarkets,
    refetchInterval: 60000, // Every 1 min
  });
}

export function useWatchlist(mode: string = "intraday") {
  return useQuery({
    queryKey: ["watchlist", mode],
    queryFn: () => tradeoAPI.getWatchlist(mode),
    refetchInterval: 60000,
  });
}

export function useFiiDii() {
  return useQuery({
    queryKey: ["fii-dii"],
    queryFn: tradeoAPI.getFiiDii,
    refetchInterval: 300000, // Every 5 mins
  });
}

// Add to watchlist
export function useAddToWatchlist() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (symbol: string) => 
      api.post(`/watchlist/${symbol}`).then(r => r.data),
    onSuccess: (_, symbol) => {
      toast.success(`${symbol} added to watchlist`);
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
    onError: () => toast.error("Failed to add stock"),
  });
}

// Remove from watchlist
export function useRemoveFromWatchlist() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (symbol: string) => 
      api.delete(`/watchlist/${symbol}`).then(r => r.data),
    onSuccess: (_, symbol) => {
      toast.success(`${symbol} removed from watchlist`);
      queryClient.invalidateQueries({ queryKey: ["watchlist"] });
    },
    onError: () => toast.error("Failed to remove stock"),
  });
}