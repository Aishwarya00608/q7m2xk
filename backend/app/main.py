"""
FastAPI application main entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import overview, forecasts, accuracy, data_quality
from app.schemas.responses import HealthResponse
from app import data_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data on startup."""
    logger.info("GridBricks WindSight backend starting — loading January 2026 data...")
    try:
        data_store.ensure_loaded()
        logger.info("Data load complete.")
    except Exception as exc:
        logger.error("Data load failed at startup: %s", exc)
    yield
    logger.info("Backend shutting down.")


app = FastAPI(
    title="GridBricks WindSight API",
    description=(
        "Day-ahead wind generation forecasting and accuracy analytics "
        "for January 2026. Uses Elexon BMRS FUELHH and WINDFOR datasets."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow configured origins (frontend dev server + production URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Routers
app.include_router(overview.router)
app.include_router(forecasts.router)
app.include_router(accuracy.router)
app.include_router(data_quality.router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health():
    """Health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/api/refresh", tags=["health"])
def refresh():
    """Force-refresh all data from the Elexon API."""
    result = data_store.refresh_data()
    return result
