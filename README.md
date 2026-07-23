# 🤖 TRADEDO — AI Trading Platform

Personal AI-powered stock prediction platform for NSE.

## Status
- ✅ Phase 1: Backend (ML + News + Sentiment + DB)
- ✅ Phase 2: Frontend Dashboard (Next.js)
- 🚧 Phase 2.5: Trade Plan Generator
- ⏭️ Phase 3: Telegram Bot
- ⏭️ Phase 4: Autonomous Agent

## Tech Stack
- **Backend:** FastAPI + LightGBM + Groq LLM
- **Frontend:** Next.js 14 + TailwindCSS + TypeScript
- **Database:** SQLite
- **Data:** yfinance + RSS feeds

## Setup
```bash
# Backend
cd app/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend
cd app/frontend
npm install
npm run dev