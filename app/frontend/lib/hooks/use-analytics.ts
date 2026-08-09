// E:\tradedo\app\frontend\lib\hooks\use-analytics.ts

import { useQuery } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";
import { api } from "@/lib/api/client";

export function usePerformance() {
  return useQuery({
    queryKey: ["performance"],
    queryFn: tradeoAPI.getPerformance,
    refetchInterval: 60000,
    staleTime: 30000,
  });
}

export function useEquityCurve() {
  return useQuery({
    queryKey: ["equity-curve"],
    queryFn: tradeoAPI.getEquityCurve,
    refetchInterval: 60000,
  });
}

export function useHourlyPerformance() {
  return useQuery({
    queryKey: ["hourly-perf"],
    queryFn: () => api.get("/analytics/hourly").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useDailyPerformance() {
  return useQuery({
    queryKey: ["daily-perf"],
    queryFn: () => api.get("/analytics/daily").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSharpeRatios() {
  return useQuery({
    queryKey: ["sharpe-ratios"],
    queryFn: () => api.get("/analytics/sharpe").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useDrawdown() {
  return useQuery({
    queryKey: ["drawdown"],
    queryFn: () => api.get("/analytics/drawdown").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useKelly() {
  return useQuery({
    queryKey: ["kelly"],
    queryFn: () => api.get("/analytics/kelly").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useStreaks() {
  return useQuery({
    queryKey: ["streaks"],
    queryFn: () => api.get("/analytics/streaks").then(r => r.data),
    staleTime: 60000,
  });
}

export function useDistribution() {
  return useQuery({
    queryKey: ["distribution"],
    queryFn: () => api.get("/analytics/distribution").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}