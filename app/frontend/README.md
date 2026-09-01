# TRADEDO frontend

This is the Next.js dashboard for TRADEDO. It provides screens for the market overview, watchlists, signals, trade plans, portfolio and risk views, reports, and agent controls.

## Requirements

- Node.js 20 or newer
- npm (the committed `package-lock.json` is used for reproducible installs)

## Development

```powershell
npm ci
npm run dev
```

Open `http://localhost:3000` after the development server starts.

## Quality checks

Run these before submitting frontend changes:

```powershell
npm run lint
npm run build
```

## Backend dependency

The dashboard is designed to work with the FastAPI service in `../backend`. Start that service separately and confirm its health endpoint is reachable before diagnosing missing market or account data in the UI.

## Project structure

```text
app/          # Routes, layout, and global styles
components/   # Page and reusable UI components
lib/          # API client, hooks, and shared utilities
public/       # Static assets
```

## Safety note

Dashboard signals and analytics are informational. They are not financial advice and should not be used as the sole basis for trading decisions.
