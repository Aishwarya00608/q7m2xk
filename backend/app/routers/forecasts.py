"""
Forecasts router: forecast explorer for a specific delivery period.
"""
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.data_store import get_windfor_df, get_fuelhh_df, get_matched_df
from app.schemas.responses import ForecastPeriodResponse, ForecastVersion
from app.services.forecast_selection import (
    get_forecast_versions_for_period,
    get_eligible_forecast_for_period,
)
from app.services.data_processing import get_day_ahead_cutoff
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["forecasts"])


@router.get("/forecasts", response_model=list[dict])
def get_forecasts_for_date(
    date: str = Query(..., description="Delivery date YYYY-MM-DD in January 2026"),
):
    """
    Return all 48 half-hour delivery periods for a given date,
    each with their eligible forecast and actual generation.
    """
    try:
        target_date = pd.Timestamp(date, tz="UTC").normalize()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {date}")
    
    jan_start = pd.Timestamp("2026-01-01", tz="UTC")
    jan_end = pd.Timestamp("2026-02-01", tz="UTC")
    if not (jan_start <= target_date < jan_end):
        raise HTTPException(status_code=400, detail="Date must be within January 2026")
    
    matched_df = get_matched_df()
    
    if matched_df.empty:
        return []
    
    day_start = target_date
    day_end = day_start + pd.Timedelta(days=1)
    day_rows = matched_df[
        (matched_df["start_time"] >= day_start) &
        (matched_df["start_time"] < day_end)
    ]
    
    result = []
    for _, row in day_rows.iterrows():
        result.append({
            "start_time": row["start_time"].isoformat(),
            "settlement_period": int(row["settlement_period"]) if pd.notna(row.get("settlement_period")) else None,
            "forecast_mw": float(row["forecast_mw"]) if pd.notna(row.get("forecast_mw")) else None,
            "actual_mw": float(row["actual_mw"]) if pd.notna(row.get("actual_mw")) else None,
            "error_mw": float(row["error_mw"]) if pd.notna(row.get("error_mw")) else None,
            "publish_time": row["publish_time"].isoformat() if pd.notna(row.get("publish_time")) and row.get("publish_time") is not None else None,
            "is_eligible": bool(row.get("is_eligible", False)),
        })
    
    return result


@router.get("/forecasts/versions", response_model=ForecastPeriodResponse)
def get_forecast_versions(
    start_time: str = Query(..., description="Delivery period start time ISO UTC, e.g. 2026-01-15T12:00:00Z"),
):
    """
    Return all forecast versions (revisions) for a specific delivery period.
    """
    try:
        delivery_st = pd.Timestamp(start_time)
        if delivery_st.tzinfo is None:
            delivery_st = delivery_st.tz_localize("UTC")
        else:
            delivery_st = delivery_st.tz_convert("UTC")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid start_time: {exc}")
    
    # Check within January 2026 (floor to hour for WINDFOR)
    windfor_st = delivery_st.floor("h")
    jan_start = pd.Timestamp("2026-01-01", tz="UTC")
    jan_end = pd.Timestamp("2026-02-01", tz="UTC")
    if not (jan_start <= windfor_st < jan_end):
        raise HTTPException(status_code=400, detail="Delivery time must be within January 2026")
    
    windfor_df = get_windfor_df()
    fuelhh_df = get_fuelhh_df()
    
    # Get all versions
    versions = get_forecast_versions_for_period(
        windfor_df,
        windfor_st,
        cutoff_hour_utc=settings.DAY_AHEAD_CUTOFF_HOUR_UTC,
        cutoff_minute_utc=settings.DAY_AHEAD_CUTOFF_MINUTE_UTC,
    )
    
    # Cutoff for this delivery period
    delivery_date = windfor_st.normalize()
    cutoff = get_day_ahead_cutoff(
        delivery_date,
        settings.DAY_AHEAD_CUTOFF_HOUR_UTC,
        settings.DAY_AHEAD_CUTOFF_MINUTE_UTC,
    )
    
    # Find actual generation
    actual_mw = None
    error_mw = None
    if not fuelhh_df.empty:
        actual_rows = fuelhh_df[fuelhh_df["start_time"] == windfor_st]
        if not actual_rows.empty:
            actual_mw = float(actual_rows.iloc[0]["actual_mw"])
    
    # Find eligible forecast
    eligible_mw = None
    eligible_publish = None
    for v in versions:
        if v["is_latest_eligible"]:
            eligible_mw = v["forecast_mw"]
            eligible_publish = v["publish_time"]
            break
    
    if eligible_mw is not None and actual_mw is not None:
        error_mw = eligible_mw - actual_mw
    
    n_eligible = sum(1 for v in versions if v["is_eligible"])
    
    return ForecastPeriodResponse(
        delivery_start_time=windfor_st.isoformat(),
        cutoff_utc=cutoff.isoformat(),
        eligible_forecast_mw=eligible_mw,
        eligible_publish_time=eligible_publish,
        actual_mw=actual_mw,
        error_mw=error_mw,
        versions=[ForecastVersion(**v) for v in versions],
        n_versions=len(versions),
        n_eligible_versions=n_eligible,
    )
