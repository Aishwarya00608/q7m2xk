"""
Data quality router.
"""
import logging
from datetime import datetime, timezone

import pandas as pd
from fastapi import APIRouter

from app.data_store import (
    get_fuelhh_df,
    get_windfor_df,
    get_matched_df,
    get_last_load_utc,
    get_load_error,
)
from app.schemas.responses import DataQualityResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["data-quality"])

# Expected counts
EXPECTED_ACTUAL_PERIODS = 31 * 48  # 1488 half-hour periods in January 2026
EXPECTED_WINDFOR_DELIVERY_HOURS = 31 * 24  # 744 delivery hours


@router.get("/data-quality", response_model=DataQualityResponse)
def get_data_quality():
    """Return data quality report for the January 2026 dataset."""
    fuelhh_df = get_fuelhh_df()
    windfor_df = get_windfor_df()
    matched_df = get_matched_df()
    last_load = get_last_load_utc()
    load_error = get_load_error()
    
    issues = []
    if load_error:
        issues.append(load_error)
    
    n_fuelhh = len(fuelhh_df) if not fuelhh_df.empty else 0
    n_windfor = len(windfor_df) if not windfor_df.empty else 0
    
    # Only count distinct delivery startTimes in WINDFOR for January 2026
    n_windfor_delivery = 0
    windfor_delivery_range = None
    windfor_publish_range = None
    if not windfor_df.empty:
        windfor_publish_range = {
            "min_publish_time": windfor_df["publish_time"].min().isoformat(),
            "max_publish_time": windfor_df["publish_time"].max().isoformat(),
            "n_records": n_windfor,
        }
        jan_start = pd.Timestamp("2026-01-01", tz="UTC")
        jan_end = pd.Timestamp("2026-02-01", tz="UTC")
        jan_windfor = windfor_df[
            (windfor_df["start_time"] >= jan_start) &
            (windfor_df["start_time"] < jan_end)
        ]
        n_windfor_delivery = jan_windfor["start_time"].nunique()
        if not jan_windfor.empty:
            windfor_delivery_range = {
                "min_start_time": jan_windfor["start_time"].min().isoformat(),
                "max_start_time": jan_windfor["start_time"].max().isoformat(),
                "min_publish_time": windfor_df["publish_time"].min().isoformat(),
                "max_publish_time": windfor_df["publish_time"].max().isoformat(),
                "n_unique_start_times": int(n_windfor_delivery),
                "n_unique_publish_times": int(windfor_df["publish_time"].nunique()),
            }
    
    n_matched = 0
    n_missing_forecast = 0
    n_missing_actual = 0
    coverage_pct = None
    
    if not matched_df.empty:
        has_forecast = matched_df["is_eligible"] & matched_df["forecast_mw"].notna()
        has_actual = matched_df["actual_mw"].notna()
        n_matched = int((has_forecast & has_actual).sum())
        n_missing_forecast = int((~has_forecast).sum())
        n_missing_actual = int((~has_actual).sum())
        
        if EXPECTED_ACTUAL_PERIODS > 0:
            coverage_pct = round(n_matched / EXPECTED_ACTUAL_PERIODS * 100, 1)
        
        if n_matched < EXPECTED_ACTUAL_PERIODS * 0.9:
            issues.append(
                f"Only {n_matched}/{EXPECTED_ACTUAL_PERIODS} periods have matched forecast+actual"
            )
    
    fuelhh_date_range = None
    if not fuelhh_df.empty:
        fuelhh_date_range = {
            "min": fuelhh_df["start_time"].min().isoformat(),
            "max": fuelhh_df["start_time"].max().isoformat(),
            "n_records": n_fuelhh,
            "n_expected": EXPECTED_ACTUAL_PERIODS,
            "coverage_pct": round(n_fuelhh / EXPECTED_ACTUAL_PERIODS * 100, 1) if EXPECTED_ACTUAL_PERIODS else None,
        }
        if n_fuelhh < EXPECTED_ACTUAL_PERIODS:
            issues.append(f"FUELHH: only {n_fuelhh} records, expected {EXPECTED_ACTUAL_PERIODS}")
    else:
        issues.append("FUELHH data not available")
    
    if not windfor_df.empty and n_windfor_delivery < EXPECTED_WINDFOR_DELIVERY_HOURS * 0.9:
        issues.append(f"WINDFOR: only {n_windfor_delivery} delivery hours with forecasts, expected {EXPECTED_WINDFOR_DELIVERY_HOURS}")
    elif windfor_df.empty:
        issues.append("WINDFOR data not available")
    
    is_complete = (
        n_fuelhh >= EXPECTED_ACTUAL_PERIODS and
        n_windfor_delivery >= EXPECTED_WINDFOR_DELIVERY_HOURS * 0.95 and
        n_matched >= EXPECTED_ACTUAL_PERIODS * 0.9 and
        not load_error
    )
    
    if is_complete:
        status = "complete"
    elif n_matched > 0:
        status = "partial"
    elif load_error:
        status = "error"
    else:
        status = "loading"
    
    return DataQualityResponse(
        last_retrieved_utc=last_load,
        fuelhh_records=n_fuelhh,
        windfor_records=n_windfor,
        fuelhh_wind_records=n_fuelhh,
        matched_pairs=n_matched,
        missing_actuals=n_missing_actual,
        missing_forecasts=n_missing_forecast,
        fuelhh_date_range=fuelhh_date_range,
        windfor_publish_range=windfor_publish_range,
        windfor_delivery_range=windfor_delivery_range,
        coverage_pct=coverage_pct,
        is_complete=is_complete,
        issues=issues,
        status=status,
    )
