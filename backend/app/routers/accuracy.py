"""
Accuracy router: full accuracy analysis for January 2026.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query

from app.data_store import get_matched_df
from app.schemas.responses import AccuracyResponse, DailyAccuracy, ErrorDistributionBin
from app.services.metrics import (
    compute_all_metrics,
    compute_daily_metrics,
    get_largest_errors,
    MAPE_MIN_ACTUAL_MW,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["accuracy"])


def _build_error_distribution(errors: pd.Series, n_bins: int = 15) -> list[dict]:
    """Build a histogram of forecast errors."""
    valid = errors.dropna()
    if valid.empty:
        return []
    
    min_e, max_e = float(valid.min()), float(valid.max())
    bin_size = (max_e - min_e) / n_bins if max_e > min_e else 1.0
    
    bins = []
    for i in range(n_bins):
        lower = min_e + i * bin_size
        upper = min_e + (i + 1) * bin_size
        count = int(((valid >= lower) & (valid < upper)).sum())
        bins.append({
            "bin_label": f"{lower:+.0f}",
            "count": count,
            "lower_mw": lower,
            "upper_mw": upper,
        })
    
    return bins


@router.get("/accuracy", response_model=AccuracyResponse)
def get_accuracy(
    start_date: str = Query("2026-01-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2026-01-31", description="End date YYYY-MM-DD (inclusive)"),
):
    """Full accuracy analysis over the specified date range within January 2026."""
    matched_df = get_matched_df()
    
    if matched_df.empty:
        return AccuracyResponse(
            mae_mw=None,
            rmse_mw=None,
            bias_mw=None,
            mape_pct=None,
            n_obs=0,
        )
    
    # Filter to requested date range
    try:
        start_ts = pd.Timestamp(start_date, tz="UTC").normalize()
        end_ts = pd.Timestamp(end_date, tz="UTC").normalize() + pd.Timedelta(days=1)
    except Exception:
        start_ts = pd.Timestamp("2026-01-01", tz="UTC")
        end_ts = pd.Timestamp("2026-02-01", tz="UTC")
    
    view_df = matched_df[
        (matched_df["start_time"] >= start_ts) &
        (matched_df["start_time"] < end_ts)
    ]
    
    metrics = compute_all_metrics(view_df)
    daily = compute_daily_metrics(view_df)
    largest = get_largest_errors(view_df, n=10)
    
    # Error distribution
    paired = view_df[view_df["is_eligible"] & view_df["forecast_mw"].notna()]
    error_dist = _build_error_distribution(paired["error_mw"].astype(float))
    
    return AccuracyResponse(
        mae_mw=metrics["mae_mw"],
        rmse_mw=metrics["rmse_mw"],
        bias_mw=metrics["bias_mw"],
        mape_pct=metrics["mape_pct"],
        bias_direction=metrics["bias_direction"],
        n_obs=metrics["n_obs"],
        n_missing_forecast=metrics["n_missing_forecast"],
        n_mape_excluded=metrics["n_mape_excluded"],
        mape_min_actual_mw=MAPE_MIN_ACTUAL_MW,
        daily_summary=[DailyAccuracy(**d) for d in daily],
        error_distribution=[ErrorDistributionBin(**b) for b in error_dist],
        largest_errors=largest,
        evaluation_period=f"{start_date} to {end_date}",
    )
