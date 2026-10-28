# GridBricks WindSight

**Know the wind. Plan the power.**

WindSight is a deterministic analytics dashboard for UK day-ahead electricity
procurement. It compares Elexon BMRS FUELHH actual wind generation with
WINDFOR forecasts for January 2026 and evaluates only the latest forecast
published at or before the configurable D-1 cutoff (09:50 UTC by default).

## What is included

- React, TypeScript, Vite, Recharts frontend
- FastAPI and pandas backend
- UTC-normalized FUELHH and WINDFOR processing
- Half-hour actuals aligned to the containing hourly WINDFOR interval: the
  forecast starting at HH:00 applies to the actuals at HH:00 and HH:30 because
  WINDFOR publishes an hourly `startTime` and `generation` value for that
  delivery hour. This is interval alignment, not an invented interpolation.
- MAE, RMSE, signed bias, and guarded MAPE metrics
- In-memory caching, refresh endpoint, data-quality reporting, and CORS

The backend API is under `backend/app`; the dashboard UI is under
`frontend/src`. Elexon integration is in `backend/app/services/elexon_client.py`,
with normalization and forecast eligibility in
`backend/app/services/data_processing.py`.

## Local setup

1. Copy `.env.example` to `.env`.
2. Install backend dependencies with `python -m pip install -r backend/requirements.txt`.
3. Run the API from the project root:

   ```powershell
   $env:PYTHONPATH="backend"
   python -m uvicorn app.main:app --reload --port 8000
   ```

4. In another terminal:

   ```powershell
   Set-Location frontend
   npm ci
   npm run dev
   ```

For a separately hosted backend, create `frontend/.env.local` and set
`VITE_API_BASE_URL=https://your-backend.example.com/api`. The production
Docker build uses the same variable through its build argument and does not
use a localhost API address.

Open <http://localhost:5173>. API health is at
<http://localhost:8000/api/health>, and interactive API documentation is at
<http://localhost:8000/docs>.

## Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The frontend is served at <http://localhost:5173>; its Nginx proxy routes
browser API requests to the backend service. The backend remains available at
<http://localhost:8000>.

**Live Demo:** <https://q7m2xk.vercel.app>

## Data and assumptions

Sources: [Elexon FUELHH](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream)
and [Elexon WINDFOR](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream).
The analysis is bounded to 2026-01-01 through 2026-01-31 UTC. Missing records
remain missing; they are not replaced with zero. `error = forecast - actual`.
MAPE excludes actuals below 100 MW because that denominator is not meaningful.

The live response schemas used here are `startTime`, `publishTime`, and
`generation`; FUELHH additionally provides `fuelType`, `settlementDate`, and
`settlementPeriod`. Both datasets report generation in MW. The observed
WINDFOR January response has hourly `startTime` values, so each hourly forecast
is aligned to the two FUELHH half-hours in that hour. No interpolation or
additional forecast value is created.

The default 09:50 UTC cutoff reflects Nord Pool's official N2EX support
documentation, which states that the UK N2EX gate closes at 09:50 GMT
([official reference](https://support.nordpoolgroup.com/support/solutions/articles/8000088463-about-the-n2ex-day-ahead-auction)).
It is configurable because a utility's operational purchasing process may
differ, and the N2EX auction cutoff may not represent every procurement
workflow.
Actual generation is labelled retrospective throughout the UI.

## Verification

Backend tests:

```powershell
$env:PYTHONPATH="backend"; python -m pytest backend/tests -q
```

Frontend:

```powershell
Set-Location frontend
npm run build
npm run lint
```

## Deployment and video

No public deployment or GitHub publication is claimed from this workspace.
For deployment, set `VITE_API_BASE_URL` to the public FastAPI origin plus `/api`
and configure backend `CORS_ORIGINS` to the deployed frontend origin. The
recording outline is: customer problem and dashboard walkthrough (5 minutes),
then architecture, Elexon pipeline, cutoff selection, metrics, tests, and
Docker (5 minutes).

Google Antigravity and Claude assisted with development; no AI features,
external weather data, machine learning, or additional data sources are used
by the product.
