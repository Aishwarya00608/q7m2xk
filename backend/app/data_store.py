"""
Application-level data store.

Loads and caches the full January 2026 dataset on first access.
Provides a refresh mechanism.
"""
import logging
import time
from datetime import datetime, timezone
from threading import Lock

import pandas as pd

from app.services.elexon_client import (
    fetch_fuelhh_wind_january_2026,
    fetch_windfor_for_january_2026,
    clear_cache,
)
from app.services.data_processing import (
    normalize_fuelhh,
    normalize_windfor,
    build_matched_dataset,
)
from app.config import settings

logger = logging.getLogger(__name__)

_lock = Lock()

# Cached DataFrames
_fuelhh_df: pd.DataFrame | None = None
_windfor_df: pd.DataFrame | None = None
_matched_df: pd.DataFrame | None = None
_last_load_utc: str | None = None
_load_error: str | None = None


def _load_data() -> None:
    """Load and process all January 2026 data. Not thread-safe; call under lock."""
    global _fuelhh_df, _windfor_df, _matched_df, _last_load_utc, _load_error

    errors = []

    # Fetch FUELHH actuals
    try:
        raw_fuelhh = fetch_fuelhh_wind_january_2026()
        _fuelhh_df = normalize_fuelhh(raw_fuelhh)
        logger.info("Loaded %d FUELHH wind records", len(_fuelhh_df))
    except Exception as exc:
        logger.error("Failed to load FUELHH: %s", exc)
        _fuelhh_df = pd.DataFrame(columns=["start_time", "settlement_date", "settlement_period", "actual_mw"])
        errors.append(f"FUELHH load failed: {exc}")

    # Fetch WINDFOR forecasts
    try:
        raw_windfor = fetch_windfor_for_january_2026()
        _windfor_df = normalize_windfor(raw_windfor)
        logger.info("Loaded %d WINDFOR records", len(_windfor_df))
    except Exception as exc:
        logger.error("Failed to load WINDFOR: %s", exc)
        _windfor_df = pd.DataFrame(columns=["start_time", "publish_time", "forecast_mw"])
        errors.append(f"WINDFOR load failed: {exc}")

    # Build matched dataset
    try:
        _matched_df = build_matched_dataset(
            _fuelhh_df,
            _windfor_df,
            cutoff_hour_utc=settings.DAY_AHEAD_CUTOFF_HOUR_UTC,
            cutoff_minute_utc=settings.DAY_AHEAD_CUTOFF_MINUTE_UTC,
        )
        logger.info("Built matched dataset: %d rows", len(_matched_df))
    except Exception as exc:
        logger.error("Failed to build matched dataset: %s", exc)
        _matched_df = pd.DataFrame()
        errors.append(f"Matching failed: {exc}")

    _last_load_utc = datetime.now(tz=timezone.utc).isoformat()
    _load_error = "; ".join(errors) if errors else None


def ensure_loaded() -> None:
    """Load data if not already loaded."""
    global _fuelhh_df
    if _fuelhh_df is None:
        with _lock:
            if _fuelhh_df is None:
                _load_data()


def refresh_data() -> dict:
    """Force-reload all data. Returns summary."""
    global _fuelhh_df
    with _lock:
        clear_cache()
        _fuelhh_df = None  # trigger reload
        _load_data()
    return {
        "status": "error" if _load_error else "refreshed",
        "last_load_utc": _last_load_utc,
        "fuelhh_records": len(_fuelhh_df) if _fuelhh_df is not None else 0,
        "windfor_records": len(_windfor_df) if _windfor_df is not None else 0,
        "matched_pairs": len(_matched_df[_matched_df["is_eligible"] & _matched_df["forecast_mw"].notna()]) if _matched_df is not None and not _matched_df.empty else 0,
        "error": _load_error,
    }


def get_fuelhh_df() -> pd.DataFrame:
    ensure_loaded()
    return _fuelhh_df if _fuelhh_df is not None else pd.DataFrame()


def get_windfor_df() -> pd.DataFrame:
    ensure_loaded()
    return _windfor_df if _windfor_df is not None else pd.DataFrame()


def get_matched_df() -> pd.DataFrame:
    ensure_loaded()
    return _matched_df if _matched_df is not None else pd.DataFrame()


def get_last_load_utc() -> str | None:
    ensure_loaded()
    return _last_load_utc


def get_load_error() -> str | None:
    return _load_error
