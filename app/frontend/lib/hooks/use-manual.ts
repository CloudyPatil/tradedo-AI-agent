// E:\tradedo\app\frontend\lib\hooks\use-manual.ts

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { toast } from "sonner";

// Account summary
export function useManualSummary() {
  return useQuery({
    queryKey: ["manual-summary"],
    queryFn: () => api.get("/manual/summary").then(r => r.data),
    refetchInterval: 5000,
  });
}

// Orders
export function useManualOrders(status: string = "all") {
  return useQuery({
    queryKey: ["manual-orders", status],
    queryFn: () => api.get("/manual/orders", { params: { status } }).then(r => r.data),
    refetchInterval: 15000,
  });
}

// Trades
export function useManualTrades(status: string = "all") {
  return useQuery({
    queryKey: ["manual-trades", status],
    queryFn: () => api.get("/manual/trades", { params: { status } }).then(r => r.data),
    refetchInterval: status === "OPEN" ? 5000 : 15000,
  });
}

// Place order
export function usePlaceOrder() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (order: any) => api.post("/manual/order/place", order).then(r => r.data),
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message || "Order placed!");
        queryClient.invalidateQueries({ queryKey: ["manual-summary"] });
        queryClient.invalidateQueries({ queryKey: ["manual-orders"] });
        queryClient.invalidateQueries({ queryKey: ["manual-trades"] });
      } else {
        toast.error(data.errors?.join(", ") || "Order failed");
      }
    },
    onError: (error: any) => {
      toast.error("Order failed: " + error.message);
    },
  });
}

// Cancel order
export function useCancelOrder() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (orderId: number) => 
      api.post(`/manual/order/${orderId}/cancel`).then(r => r.data),
    onSuccess: () => {
      toast.success("Order cancelled");
      queryClient.invalidateQueries({ queryKey: ["manual-orders"] });
      queryClient.invalidateQueries({ queryKey: ["manual-summary"] });
    },
    onError: () => toast.error("Failed to cancel order"),
  });
}

// Close position
export function useClosePosition() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (tradeId: number) => 
      api.post(`/manual/close-position/${tradeId}`).then(r => r.data),
    onSuccess: (data) => {
      const pnl = data.pnl || 0;
      toast.success(`Position closed! P&L: ₹${pnl.toFixed(2)}`);
      queryClient.invalidateQueries({ queryKey: ["manual-summary"] });
      queryClient.invalidateQueries({ queryKey: ["manual-trades"] });
    },
    onError: () => toast.error("Failed to close position"),
  });
}

// Reset capital
export function useResetManualCapital() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (capital: number) => 
      api.post(`/manual/reset-capital?new_capital=${capital}`).then(r => r.data),
    onSuccess: () => {
      toast.success("Manual capital reset!");
      queryClient.invalidateQueries({ queryKey: ["manual-summary"] });
    },
    onError: () => toast.error("Reset failed"),
  });
}
