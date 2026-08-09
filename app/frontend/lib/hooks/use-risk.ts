// E:\tradedo\app\frontend\lib\hooks\use-risk.ts

import { useQuery } from "@tanstack/react-query";
import { tradeoAPI } from "@/lib/api/client";

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