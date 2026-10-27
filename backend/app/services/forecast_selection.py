"""
Forecast selection helpers (complementing data_processing.py).
"""
import logging
from typing import Optional

import pandas as pd

from app.services.data_processing import get_day_ahead_cutoff, select_eligible_forecast

logger = logging.getLogger(__name__)


def get_forecast_versions_for_period(
    windfor_df: pd.DataFrame,
    delivery_start_time: pd.Timestamp,
    cutoff_hour_utc: int = 9,
    cutoff_minute_utc: int = 50,
) -> list[dict]:
    """
    Return all forecast versions for a given delivery period,
    annotated with eligibility.

    Args:
        windfor_df: Normalized WINDFOR data.
        delivery_start_time: UTC timestamp of the delivery hour.
        cutoff_hour_utc: Hour of cutoff (UTC).
        cutoff_minute_utc: Minute of cutoff.

    Returns:
        List of dicts sorted by publish_time ascending, each with:
          - publish_time (ISO str)
          - forecast_mw (float)
          - is_eligible (bool)
          - delta_from_prev (float or None)
    """
    # Get the WINDFOR hour-resolution startTime
    windfor_st = delivery_start_time.floor("h")
    
    mask = windfor_df["start_time"] == windfor_st
    candidates = windfor_df[mask].sort_values("publish_time")
    
    if candidates.empty:
        return []
    
    delivery_date = windfor_st.normalize()
    cutoff = get_day_ahead_cutoff(delivery_date, cutoff_hour_utc, cutoff_minute_utc)
    
    results = []
    prev_mw = None
    for _, row in candidates.iterrows():
        is_eligible = row["publish_time"] <= cutoff
        delta = float(row["forecast_mw"] - prev_mw) if prev_mw is not None else None
        results.append({
            "publish_time": row["publish_time"].isoformat(),
            "forecast_mw": float(row["forecast_mw"]),
            "is_eligible": bool(is_eligible),
            "is_latest_eligible": False,  # will set below
            "delta_from_prev_mw": delta,
        })
        prev_mw = row["forecast_mw"]
    
    # Mark the latest eligible as such
    for item in reversed(results):
        if item["is_eligible"]:
            item["is_latest_eligible"] = True
            break
    
    return results


def get_eligible_forecast_for_period(
    windfor_df: pd.DataFrame,
    delivery_start_time: pd.Timestamp,
    cutoff_hour_utc: int = 9,
    cutoff_minute_utc: int = 50,
) -> Optional[dict]:
    """
    Return the single eligible day-ahead forecast for the delivery period.

    Returns None if no eligible forecast exists.
    """
    windfor_st = delivery_start_time.floor("h")
    row = select_eligible_forecast(windfor_df, windfor_st, cutoff_hour_utc, cutoff_minute_utc)
    
    if row is None:
        return None
    
    delivery_date = windfor_st.normalize()
    cutoff = get_day_ahead_cutoff(delivery_date, cutoff_hour_utc, cutoff_minute_utc)
    
    return {
        "delivery_start_time": windfor_st.isoformat(),
        "publish_time": row["publish_time"].isoformat(),
        "forecast_mw": float(row["forecast_mw"]),
        "cutoff_utc": cutoff.isoformat(),
    }
