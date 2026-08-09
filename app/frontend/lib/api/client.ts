// E:\tradedo\app\frontend\lib\api\client.ts

import axios from "axios";

const API_BASE = "http://localhost:8000/api/v1";
const BACKEND_BASE = "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

export const tradeoAPI = {
  // ─── Predictions ──────────────────────────────────
  predict: (symbol: string, mode: string = "intraday") =>
    api.get(`/predict/${symbol}`, { params: { mode } }).then(r => r.data),
  
  predictFull: (symbol: string, mode: string = "intraday") =>
    api.get(`/predict/full/${symbol}`, { params: { mode } }).then(r => r.data),
  
  // ─── Watchlist ───────────────────────────────────
  getWatchlist: (mode: string = "intraday") =>
    api.get("/watchlist", { params: { mode } }).then(r => r.data),
  
  // ─── Agent ────────────────────────────────────────
  getAgentStatus: () =>
    api.get("/agent/status").then(r => r.data),
  
  startAgent: () =>
    api.post("/agent/start").then(r => r.data),
  
  stopAgent: () =>
    api.post("/agent/stop").then(r => r.data),
  
  getTrades: (status: string = "all") =>
    api.get("/agent/trades", { params: { status } }).then(r => r.data),
  
  getTodaysPerformance: () =>
    api.get("/agent/performance/today").then(r => r.data),
  
  // ─── Master Scorer ────────────────────────────────
  getMasterScore: (symbol: string, mode: string = "intraday") =>
    api.get(`/master/${symbol}`, { params: { mode } }).then(r => r.data),
  
  // ─── Global Markets ───────────────────────────────
  getGlobalMarkets: () =>
    api.get("/global/markets").then(r => r.data),
  
  // ─── NSE ──────────────────────────────────────────
  getFiiDii: () =>
    api.get("/nse/market/fii-dii").then(r => r.data),
  
  getNseIntel: (symbol: string) =>
    api.get(`/nse/${symbol}`).then(r => r.data),
  
  // ─── Analytics ────────────────────────────────────
  getPerformance: () =>
    api.get("/analytics/performance").then(r => r.data),
  
  getEquityCurve: () =>
    api.get("/analytics/equity-curve").then(r => r.data),
  
  // ─── Risk ─────────────────────────────────────────
  getRiskReport: () =>
    api.get("/risk/report").then(r => r.data),
  
  getRiskScore: () =>
    api.get("/risk/score").then(r => r.data),
  
  getPortfolioHeat: () =>
    api.get("/risk/heat").then(r => r.data),
  
  // ─── News & Social ────────────────────────────────
  getNews: (symbol: string) =>
    api.get(`/social/${symbol}`).then(r => r.data),
  
  // ─── Health ───────────────────────────────────────
  getHealth: () =>
    axios.get(`${BACKEND_BASE}/health`).then(r => r.data),
};