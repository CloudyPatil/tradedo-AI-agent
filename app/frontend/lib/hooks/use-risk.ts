// E:\tradedo\app\frontend\lib\hooks\use-risk.ts

import { useQuery } from "@tanstack/react-query";
import { tradeoAPI, api } from "@/lib/api/client";

export function useRiskReport() {
  return useQuery({
    queryKey: ["risk-report"],
    queryFn: tradeoAPI.getRiskReport,
    refetchInterval: 30000,
    staleTime: 15000,
  });
}

export function useRiskScore() {
  return useQuery({
    queryKey: ["risk-score"],
    queryFn: tradeoAPI.getRiskScore,
    refetchInterval: 30000,
  });
}

export function usePortfolioHeat() {
  return useQuery({
    queryKey: ["portfolio-heat"],
    queryFn: tradeoAPI.getPortfolioHeat,
    refetchInterval: 30000,
  });
}

export function useVaR() {
  return useQuery({
    queryKey: ["var"],
    queryFn: () => api.get("/risk/var").then(r => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useSectorConcentration() {
  return useQuery({
    queryKey: ["sector-concentration"],
    queryFn: () => api.get("/risk/concentration").then(r => r.data),
    refetchInterval: 60000,
  });
}

export function useDiversification() {
  return useQuery({
    queryKey: ["diversification"],
    queryFn: () => api.get("/risk/diversification").then(r => r.data),
    refetchInterval: 60000,
  });
}

export function usePositionRisks() {
  return useQuery({
    queryKey: ["position-risks"],
    queryFn: () => api.get("/risk/positions").then(r => r.data),
    refetchInterval: 30000,
  });
}

export function useStressTest() {
  return useQuery({
    queryKey: ["stress-test"],
    queryFn: () => api.get("/risk/stress-test").then(r => r.data),
    refetchInterval: 60000,
  });
}