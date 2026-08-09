// E:\tradedo\app\frontend\lib\hooks\use-stock.ts

import { useQuery } from "@tanstack/react-query";
import { api, tradeoAPI } from "@/lib/api/client";

export function useStockPrediction(symbol: string, mode: string = "intraday") {
  return useQuery({
    queryKey: ["prediction-full", symbol, mode],
    queryFn: () => tradeoAPI.predictFull(symbol, mode),
    staleTime: 3 * 60 * 1000,
  });
}

export function useMasterScore(symbol: string, mode: string = "intraday") {
  return useQuery({
    queryKey: ["master-score", symbol, mode],
    queryFn: () => tradeoAPI.getMasterScore(symbol, mode),
    staleTime: 5 * 60 * 1000,
  });
}

export function useStockNews(symbol: string) {
  return useQuery({
    queryKey: ["stock-news", symbol],
    queryFn: () => tradeoAPI.getNews(symbol),
    staleTime: 5 * 60 * 1000,
  });
}

export function useStockNse(symbol: string) {
  return useQuery({
    queryKey: ["stock-nse", symbol],
    queryFn: () => tradeoAPI.getNseIntel(symbol),
    staleTime: 10 * 60 * 1000,
  });
}

export function useStockChart(symbol: string, mode: string = "swing") {
  return useQuery({
    queryKey: ["stock-chart", symbol, mode],
    queryFn: () => api.get(`/chart/${symbol}`, { params: { mode } }).then(r => r.data),
    staleTime: 60 * 1000,
  });
}

export function useSafetyGates(symbol: string, mode: string = "intraday") {
  return useQuery({
    queryKey: ["safety-gates", symbol, mode],
    queryFn: () => api.get(`/gates/${symbol}`, { params: { mode } }).then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}