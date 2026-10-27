"""
Accuracy metric calculations.

Error convention: error = forecast - actual
  Positive error = over-forecast (forecast > actual)
  Negative error = under-forecast (forecast < actual)

All generation values are in MW.
"""
import logging
import math
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Minimum actual generation (MW) for MAPE denominator.
# Periods with actual < this value are excluded from percentage calculations.
MAPE_MIN_ACTUAL_MW = 100.0


def compute_mae(errors: pd.Series) -> Optional[float]:
    """Mean Absolute Error in MW."""
    valid = errors.dropna()
    if valid.empty:
        return None
    return float(valid.abs().mean())


def compute_rmse(errors: pd.Series) -> Optional[float]:
    """Root Mean Squared Error in MW."""
    valid = errors.dropna()
    if valid.empty:
        return None
    return float(math.sqrt((valid ** 2).mean()))


def compute_bias(errors: pd.Series) -> Optional[float]:
    """Mean Signed Error (Bias) in MW. Positive = over-forecast."""
    valid = errors.dropna()
    if valid.empty:
        return None
    return float(valid.mean())


def compute_mape(forecast: pd.Series, actual: pd.Series) -> tuple[Optional[float], int]:
    """
    Mean Absolute Percentage Error.

    Excludes periods where actual < MAPE_MIN_ACTUAL_MW to avoid
    division by near-zero actuals.

    Returns:
        (mape_percent, n_excluded): MAPE as a percentage, and count excluded.
    """
    mask = actual >= MAPE_MIN_ACTUAL_MW
    n_excluded = int((~mask).sum())
    
    valid_forecast = forecast[mask].dropna()
    valid_actual = actual[mask].reindex(valid_forecast.index).dropna()
    valid_forecast = valid_forecast.reindex(valid_actual.index)
    
    if valid_actual.empty:
        return None, n_excluded
    
    pct_errors = ((valid_forecast - valid_actual).abs() / valid_actual) * 100.0
    return float(pct_errors.mean()), n_excluded


def compute_all_metrics(matched_df: pd.DataFrame) -> dict:
    """
    Compute all accuracy metrics from a matched forecast/actual DataFrame.

    Args:
        matched_df: DataFrame from build_matched_dataset() with columns
                    forecast_mw, actual_mw, error_mw, and is_eligible.

    Returns:
        Dict with keys: mae_mw, rmse_mw, bias_mw, mape_pct, n_obs,
                        n_missing_forecast, n_mape_excluded, bias_direction.
    """
    # Only use rows with both forecast and actual (matched pairs)
    paired = matched_df[
        matched_df["is_eligible"]
        & matched_df["forecast_mw"].notna()
        & matched_df["actual_mw"].notna()
        & matched_df["error_mw"].notna()
    ]
    
    n_obs = len(paired)
    n_missing = int(matched_df["is_eligible"].eq(False).sum() + matched_df["forecast_mw"].isna().sum())
    
    if n_obs == 0:
        return {
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
            "mape_pct": None,
            "n_obs": 0,
            "n_missing_forecast": n_missing,
            "n_mape_excluded": 0,
            "bias_direction": None,
        }
    
    errors = paired["error_mw"].astype(float)
    mape, n_mape_excl = compute_mape(
        paired["forecast_mw"].astype(float),
        paired["actual_mw"].astype(float),
    )
    
    bias = compute_bias(errors)
    bias_direction = None
    if bias is not None:
        if bias > 50:
            bias_direction = "over-forecasting"
        elif bias < -50:
            bias_direction = "under-forecasting"
        else:
            bias_direction = "near-neutral"
    
    return {
        "mae_mw": compute_mae(errors),
        "rmse_mw": compute_rmse(errors),
        "bias_mw": bias,
        "mape_pct": mape,
        "n_obs": n_obs,
        "n_missing_forecast": n_missing,
        "n_mape_excluded": n_mape_excl,
        "bias_direction": bias_direction,
    }


def compute_daily_metrics(matched_df: pd.DataFrame) -> list[dict]:
    """
    Compute per-day accuracy metrics.

    Returns list of dicts sorted by date.
    """
    paired = matched_df[matched_df["is_eligible"] & matched_df["forecast_mw"].notna()].copy()
    
    if paired.empty:
        return []
    
    paired["date"] = paired["start_time"].dt.date
    results = []
    
    for date, group in paired.groupby("date"):
        errors = group["error_mw"].astype(float)
        mape, _ = compute_mape(
            group["forecast_mw"].astype(float),
            group["actual_mw"].astype(float),
        )
        results.append({
            "date": str(date),
            "mae_mw": compute_mae(errors),
            "rmse_mw": compute_rmse(errors),
            "bias_mw": compute_bias(errors),
            "mape_pct": mape,
            "n_obs": len(group),
            "mean_forecast_mw": float(group["forecast_mw"].mean()),
            "mean_actual_mw": float(group["actual_mw"].mean()),
        })
    
    return results


def get_largest_errors(matched_df: pd.DataFrame, n: int = 10) -> list[dict]:
    """
    Return the n delivery periods with the largest absolute forecast errors.
    """
    paired = matched_df[matched_df["is_eligible"] & matched_df["forecast_mw"].notna()].copy()
    if paired.empty:
        return []
    
    paired["abs_error_mw"] = paired["error_mw"].abs()
    top = paired.nlargest(n, "abs_error_mw")
    
    result = []
    for _, row in top.iterrows():
        result.append({
            "start_time": row["start_time"].isoformat(),
            "forecast_mw": float(row["forecast_mw"]),
            "actual_mw": float(row["actual_mw"]),
            "error_mw": float(row["error_mw"]),
            "abs_error_mw": float(row["abs_error_mw"]),
            "settlement_date": str(row["settlement_date"]),
            "settlement_period": int(row["settlement_period"]) if pd.notna(row["settlement_period"]) else None,
        })
    return result
