"""
Overview router: high-level metrics and time-series for the dashboard.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.data_store import get_fuelhh_df, get_windfor_df, get_matched_df
from app.schemas.responses import (
    OverviewResponse,
    OverviewMetrics,
    MetricCard,
    TimeSeriesPoint,
)
from app.services.metrics import compute_all_metrics
from app.services.data_processing import filter_january_2026
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["overview"])


def _safe_float(v) -> Optional[float]:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return float(v)


@router.get("/overview", response_model=OverviewResponse)
def get_overview(date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD in January 2026")):
    """
    Overview metrics and time series.
    
    If `date` is provided, time series is filtered to that date (48 30-min periods).
    Otherwise, the entire January 2026 month is returned.
    """
    matched_df = get_matched_df()
    windfor_df = get_windfor_df()
    
    if matched_df.empty:
        # Return empty state
        empty_metrics = OverviewMetrics(
            mae=MetricCard(value=None, unit="MW", label="MAE"),
            rmse=MetricCard(value=None, unit="MW", label="RMSE"),
            bias=MetricCard(value=None, unit="MW", label="Forecast Bias"),
            n_obs=0,
        )
        return OverviewResponse(metrics=empty_metrics, time_series=[], date=date)
    
    # Filter matched data for the selected date if specified
    if date:
        try:
            target_date = pd.Timestamp(date, tz="UTC")
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid date: {date}")
        
        day_start = target_date.normalize()
        day_end = day_start + pd.Timedelta(days=1)
        
        # Validate it's within January 2026
        jan_start = pd.Timestamp("2026-01-01", tz="UTC")
        jan_end = pd.Timestamp("2026-02-01", tz="UTC")
        if not (jan_start <= day_start < jan_end):
            raise HTTPException(status_code=400, detail="Date must be within January 2026")
        
        view_df = matched_df[
            (matched_df["start_time"] >= day_start) &
            (matched_df["start_time"] < day_end)
        ]
    else:
        view_df = matched_df
    
    # Compute metrics over the full month always (for metric cards)
    month_metrics = compute_all_metrics(matched_df)
    
    # Build time series
    ts_points = []
    for _, row in view_df.iterrows():
        ts_points.append(TimeSeriesPoint(
            start_time=row["start_time"].isoformat(),
            forecast_mw=_safe_float(row.get("forecast_mw")),
            actual_mw=_safe_float(row.get("actual_mw")),
            error_mw=_safe_float(row.get("error_mw")),
            publish_time=row["publish_time"].isoformat() if pd.notna(row.get("publish_time")) and row.get("publish_time") is not None else None,
            is_eligible=bool(row.get("is_eligible", False)),
        ))
    
    # Latest eligible forecast (first eligible in the view, or from full month)
    latest_forecast_mw = None
    latest_forecast_publish_time = None
    latest_forecast_delivery_time = None
    
    eligible_rows = view_df[view_df["is_eligible"] & view_df["forecast_mw"].notna()]
    if not eligible_rows.empty:
        # Latest delivery period in view
        last_row = eligible_rows.iloc[-1]
        latest_forecast_mw = _safe_float(last_row["forecast_mw"])
        latest_forecast_publish_time = last_row["publish_time"].isoformat() if pd.notna(last_row.get("publish_time")) else None
        latest_forecast_delivery_time = last_row["start_time"].isoformat()
    
    metrics = OverviewMetrics(
        mae=MetricCard(
            value=month_metrics["mae_mw"],
            unit="MW",
            n_obs=month_metrics["n_obs"],
            label="Mean Absolute Error",
        ),
        rmse=MetricCard(
            value=month_metrics["rmse_mw"],
            unit="MW",
            n_obs=month_metrics["n_obs"],
            label="Root Mean Squared Error",
        ),
        bias=MetricCard(
            value=month_metrics["bias_mw"],
            unit="MW",
            n_obs=month_metrics["n_obs"],
            label="Forecast Bias",
        ),
        mape=MetricCard(
            value=month_metrics["mape_pct"],
            unit="%",
            n_obs=month_metrics["n_obs"] - month_metrics["n_mape_excluded"],
            label="MAPE",
        ) if month_metrics["mape_pct"] is not None else None,
        latest_forecast_mw=latest_forecast_mw,
        latest_forecast_publish_time=latest_forecast_publish_time,
        latest_forecast_delivery_time=latest_forecast_delivery_time,
        bias_direction=month_metrics["bias_direction"],
        n_obs=month_metrics["n_obs"],
    )
    
    return OverviewResponse(metrics=metrics, time_series=ts_points, date=date)
