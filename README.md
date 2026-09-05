# TRADEDO

TRADEDO is a personal, AI-assisted platform for researching and monitoring NSE stocks. It combines market data, technical and sentiment signals, a FastAPI backend, and a Next.js dashboard.

> **Important:** TRADEDO is a research tool, not investment advice. Predictions, scores, and trade plans can be wrong. Review every decision independently and do not risk money you cannot afford to lose.

## Project status

| Area | Status |
| --- | --- |
| Backend API, data pipeline, and local database | Available |
| Frontend dashboard | Available |
| Trade-plan generation | In progress |
| Telegram automation | Available when configured |
| Autonomous agent workflows | Under active development |

## Repository layout

```text
app/
├── backend/   # FastAPI application, ML/data pipeline, database, and agent modules
└── frontend/  # Next.js dashboard
```

## Prerequisites

- Python 3.10 or newer
- Node.js 20 or newer and npm
- Optional service credentials for features that use Groq, Upstox, or Telegram

## Run locally

Start the backend from `app/backend`:

```powershell
cd app/backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

The API runs on `http://localhost:8000`; interactive API documentation is available at `http://localhost:8000/docs`.

In a second terminal, start the dashboard:

```powershell
cd app/frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

## Configuration

The backend loads environment variables from a `.env` file in its working directory. Do not commit secrets. The application reads these values when present:

| Variable | Purpose |
| --- | --- |
| `GROQ_API_KEY` | Enables Groq-backed LLM features. |
| `DATA_PATH` | Overrides the location used for data files. |
| `MODELS_PATH` | Overrides the location used for model files. |
| `LOGS_PATH` | Overrides the location used for logs. |
| `TRADEDO_CORS_ORIGINS` | Comma-separated dashboard origins; defaults to local Next.js origins. |

Additional integrations, including Upstox and Telegram, may require their own credentials. Configure them only for accounts you control.

## Useful endpoints

| Endpoint | Description |
| --- | --- |
| `GET /health` | Returns detailed backend health information. |
| `GET /api/v1/health` | Returns a lightweight API health response. |
| `GET /api/v1/predict/{symbol}` | Returns a prediction; use `mode=swing` or `mode=intraday`. |
| `GET /api/v1/predict/full/{symbol}` | Returns an extended prediction including market and sentiment context. |
| `GET /api/v1/models/status` | Shows whether the swing and intraday models are loaded. |

For the complete and current API surface, use the OpenAPI documentation at `/docs` after starting the backend.

## Verification

Before opening a pull request, run the frontend checks:

```powershell
cd app/frontend
npm run lint
npm run build
```

Then start the backend and confirm `http://localhost:8000/health` returns a response appropriate to your local configuration.

## Documentation maintenance

The backend dependency manifest is maintained at `app/backend/requirements.txt`. Use a lockfile for production deployments when the environment is finalized.
