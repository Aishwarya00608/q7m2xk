"""
Data processing: normalization, deduplication, matching, and alignment
of FUELHH and WINDFOR data.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import pandas as pd
import pytz

logger = logging.getLogger(__name__)


def normalize_fuelhh(records: list[dict]) -> pd.DataFrame:
    """
    Parse and normalize raw FUELHH WIND records.

    Returns a DataFrame with columns:
      - start_time (UTC-aware datetime)
      - settlement_date (str YYYY-MM-DD)
      - settlement_period (int)
      - actual_mw (float)
    Deduplicated by start_time (first occurrence kept).
    """
    if not records:
        return pd.DataFrame(columns=["start_time", "settlement_date", "settlement_period", "actual_mw"])

    df = pd.DataFrame(records)
    
    # Validate required fields
    required = {"startTime", "generation", "settlementDate", "settlementPeriod"}
    missing = required - set(df.columns)
    if missing:
        logger.warning("FUELHH missing fields: %s", missing)
        return pd.DataFrame(columns=["start_time", "settlement_date", "settlement_period", "actual_mw"])

    df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
    df["start_time"] = df["start_time"].dt.tz_convert(pytz.UTC)
    df["actual_mw"] = pd.to_numeric(df["generation"], errors="coerce").astype(float)
    df["settlement_date"] = df["settlementDate"].astype(str)
    df["settlement_period"] = pd.to_numeric(df["settlementPeriod"], errors="coerce").astype("Int64")

    # Drop rows with null generation
    n_before = len(df)
    df = df.dropna(subset=["actual_mw", "start_time"])
    n_dropped = n_before - len(df)
    if n_dropped:
        logger.warning("FUELHH dropped %d rows with null values", n_dropped)

    # Deduplicate by start_time (keep first)
    n_before = len(df)
    df = df.drop_duplicates(subset=["start_time"], keep="first")
    n_dupes = n_before - len(df)
    if n_dupes:
        logger.info("FUELHH dropped %d duplicate start_time records", n_dupes)

    return df[["start_time", "settlement_date", "settlement_period", "actual_mw"]].sort_values("start_time").reset_index(drop=True)


def normalize_windfor(records: list[dict]) -> pd.DataFrame:
    """
    Parse and normalize raw WINDFOR records.

    WINDFOR has 1-hour startTime resolution and multiple publishTimes per startTime.
    
    Returns a DataFrame with columns:
      - start_time (UTC-aware datetime)
      - publish_time (UTC-aware datetime)
      - forecast_mw (float)
    Sorted by (start_time, publish_time).
    """
    if not records:
        return pd.DataFrame(columns=["start_time", "publish_time", "forecast_mw"])

    df = pd.DataFrame(records)

    required = {"startTime", "publishTime", "generation"}
    missing = required - set(df.columns)
    if missing:
        logger.warning("WINDFOR missing fields: %s", missing)
        return pd.DataFrame(columns=["start_time", "publish_time", "forecast_mw"])

    df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
    df["publish_time"] = pd.to_datetime(df["publishTime"], utc=True)
    df["start_time"] = df["start_time"].dt.tz_convert(pytz.UTC)
    df["publish_time"] = df["publish_time"].dt.tz_convert(pytz.UTC)
    df["forecast_mw"] = pd.to_numeric(df["generation"], errors="coerce").astype(float)

    # Drop rows with null values
    n_before = len(df)
    df = df.dropna(subset=["forecast_mw", "start_time", "publish_time"])
    n_dropped = n_before - len(df)
    if n_dropped:
        logger.warning("WINDFOR dropped %d rows with null values", n_dropped)

    # Deduplicate exact (start_time, publish_time) pairs
    n_before = len(df)
    df = df.drop_duplicates(subset=["start_time", "publish_time"], keep="first")
    n_dupes = n_before - len(df)
    if n_dupes:
        logger.info("WINDFOR dropped %d duplicate (start_time, publish_time) records", n_dupes)

    return df[["start_time", "publish_time", "forecast_mw"]].sort_values(
        ["start_time", "publish_time"]
    ).reset_index(drop=True)


def filter_january_2026(df: pd.DataFrame, time_col: str = "start_time") -> pd.DataFrame:
    """Filter DataFrame to rows where time_col falls in January 2026 UTC."""
    jan_start = pd.Timestamp("2026-01-01T00:00:00Z")
    jan_end = pd.Timestamp("2026-02-01T00:00:00Z")
    mask = (df[time_col] >= jan_start) & (df[time_col] < jan_end)
    return df[mask].reset_index(drop=True)


def get_day_ahead_cutoff(delivery_date: pd.Timestamp, cutoff_hour_utc: int = 9, cutoff_minute_utc: int = 50) -> pd.Timestamp:
    """
    Compute the day-ahead decision cutoff UTC timestamp for a given delivery date.

    The configured day-ahead market gate closes on the day before delivery.

    For delivery_date = 2026-01-15:
      cutoff = 2026-01-14T09:50:00Z

    Args:
        delivery_date: The delivery date (any time component is ignored).
        cutoff_hour_utc: Hour component of cutoff in UTC (default 9).
        cutoff_minute_utc: Minute component (default 50).

    Returns:
        UTC-aware Timestamp for the cutoff.
    """
    d_minus_1 = delivery_date.normalize() - pd.Timedelta(days=1)
    cutoff = d_minus_1 + pd.Timedelta(hours=cutoff_hour_utc, minutes=cutoff_minute_utc)
    return cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff


def select_eligible_forecast(
    windfor_df: pd.DataFrame,
    delivery_start_time: pd.Timestamp,
    cutoff_hour_utc: int = 9,
    cutoff_minute_utc: int = 50,
) -> Optional[pd.Series]:
    """
    Select the eligible day-ahead forecast for a given delivery period.

    Rule: From all WINDFOR forecasts for this startTime, select the one
    with the LATEST publishTime that is at or before the day-ahead cutoff.

    The cutoff defaults to 09:50 UTC on the day before the delivery date.
    For a delivery startTime of 2026-01-15T12:00:00Z, the delivery
    date is 2026-01-15 and the cutoff is 2026-01-14T09:50:00Z.

    Args:
        windfor_df: Normalized WINDFOR DataFrame.
        delivery_start_time: The UTC startTime of the delivery period.
        cutoff_hour_utc: Hour of cutoff in UTC.
        cutoff_minute_utc: Minute of cutoff in UTC.

    Returns:
        The eligible forecast row as a Series, or None if no eligible forecast.
    """
    # Get the delivery date from startTime
    delivery_date = delivery_start_time.normalize()
    cutoff = get_day_ahead_cutoff(delivery_date, cutoff_hour_utc, cutoff_minute_utc)

    # Filter to forecasts for this startTime
    mask = windfor_df["start_time"] == delivery_start_time
    candidates = windfor_df[mask]

    if candidates.empty:
        return None

    # Filter to forecasts published at or before cutoff
    eligible = candidates[candidates["publish_time"] <= cutoff]

    if eligible.empty:
        return None

    # Select the latest eligible forecast
    return eligible.loc[eligible["publish_time"].idxmax()]


def build_matched_dataset(
    fuelhh_df: pd.DataFrame,
    windfor_df: pd.DataFrame,
    cutoff_hour_utc: int = 9,
    cutoff_minute_utc: int = 50,
) -> pd.DataFrame:
    """
    Build a matched dataset of (forecast, actual) pairs for January 2026.

    Since FUELHH is 30-min and WINDFOR is 1-hour resolution, we align by
    mapping each 30-min actual to the matching 1-hour forecast startTime.

    WINDFOR startTimes are on the hour (e.g., 12:00, 13:00).
    FUELHH startTimes can be on the hour or half-hour (12:00, 12:30).

    Mapping strategy:
      - A 30-min actual period at HH:00 maps to the WINDFOR period at HH:00.
      - A 30-min actual period at HH:30 maps to the WINDFOR period at HH:00 
        (the same hour window covers :00 and :30).

    Returns DataFrame with columns:
      - start_time (UTC, the actual 30-min FUELHH startTime)
      - windfor_start_time (UTC, the matched 1-hour WINDFOR startTime)
      - forecast_mw (float, the eligible forecast)
      - actual_mw (float, the actual generation)
      - publish_time (UTC, when the eligible forecast was published)
      - is_eligible (bool, always True for rows in this dataset)
      - error_mw (float, forecast - actual)
      - cutoff (UTC Timestamp, the cutoff used)
    """
    # Filter actuals to January 2026
    actual_jan = filter_january_2026(fuelhh_df, "start_time")
    
    rows = []
    for _, actual_row in actual_jan.iterrows():
        actual_st = actual_row["start_time"]
        
        # Map to WINDFOR's 1-hour startTime (floor to hour)
        windfor_st = actual_st.floor("h")
        
        # Get eligible forecast for this windfor startTime
        forecast_row = select_eligible_forecast(
            windfor_df, windfor_st, cutoff_hour_utc, cutoff_minute_utc
        )
        
        delivery_date = windfor_st.normalize()
        cutoff = get_day_ahead_cutoff(delivery_date, cutoff_hour_utc, cutoff_minute_utc)
        
        if forecast_row is not None:
            rows.append({
                "start_time": actual_st,
                "windfor_start_time": windfor_st,
                "forecast_mw": forecast_row["forecast_mw"],
                "actual_mw": actual_row["actual_mw"],
                "publish_time": forecast_row["publish_time"],
                "is_eligible": True,
                "error_mw": forecast_row["forecast_mw"] - actual_row["actual_mw"],
                "cutoff": cutoff,
                "settlement_date": actual_row["settlement_date"],
                "settlement_period": actual_row["settlement_period"],
            })
        else:
            rows.append({
                "start_time": actual_st,
                "windfor_start_time": windfor_st,
                "forecast_mw": None,
                "actual_mw": actual_row["actual_mw"],
                "publish_time": None,
                "is_eligible": False,
                "error_mw": None,
                "cutoff": cutoff,
                "settlement_date": actual_row["settlement_date"],
                "settlement_period": actual_row["settlement_period"],
            })
    
    if not rows:
        return pd.DataFrame(columns=[
            "start_time", "windfor_start_time", "forecast_mw", "actual_mw",
            "publish_time", "is_eligible", "error_mw", "cutoff",
            "settlement_date", "settlement_period"
        ])
    
    return pd.DataFrame(rows).sort_values("start_time").reset_index(drop=True)
