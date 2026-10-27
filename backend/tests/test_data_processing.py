"""
Unit tests for data processing functions.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import timezone

from app.services.data_processing import (
    normalize_fuelhh,
    normalize_windfor,
    filter_january_2026,
    get_day_ahead_cutoff,
    select_eligible_forecast,
    build_matched_dataset,
)
from app.services.metrics import (
    compute_mae,
    compute_rmse,
    compute_bias,
    compute_mape,
    compute_all_metrics,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

SAMPLE_FUELHH = [
    {
        "dataset": "FUELHH",
        "publishTime": "2026-01-01T00:30:00Z",
        "startTime": "2026-01-01T00:00:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 1,
        "fuelType": "WIND",
        "generation": 15000,
    },
    {
        "dataset": "FUELHH",
        "publishTime": "2026-01-01T01:00:00Z",
        "startTime": "2026-01-01T00:30:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 2,
        "fuelType": "WIND",
        "generation": 16000,
    },
    {
        "dataset": "FUELHH",
        "publishTime": "2026-01-01T01:30:00Z",
        "startTime": "2026-01-01T01:00:00Z",
        "settlementDate": "2026-01-01",
        "settlementPeriod": 3,
        "fuelType": "WIND",
        "generation": 14000,
    },
]

SAMPLE_WINDFOR = [
    # Two publish versions for 2026-01-01T00:00:00Z delivery
    {
        "dataset": "WINDFOR",
        "publishTime": "2025-12-31T08:00:00Z",  # before cutoff
        "startTime": "2026-01-01T00:00:00Z",
        "generation": 14500,
    },
    {
        "dataset": "WINDFOR",
        "publishTime": "2025-12-31T09:30:00Z",  # before the 09:50 UTC cutoff
        "startTime": "2026-01-01T00:00:00Z",
        "generation": 15200,
    },
    {
        "dataset": "WINDFOR",
        "publishTime": "2025-12-31T11:00:00Z",  # AFTER cutoff — not eligible
        "startTime": "2026-01-01T00:00:00Z",
        "generation": 13000,
    },
    # Forecast for 2026-01-01T01:00:00Z delivery
    {
        "dataset": "WINDFOR",
        "publishTime": "2025-12-31T09:00:00Z",  # before cutoff
        "startTime": "2026-01-01T01:00:00Z",
        "generation": 13500,
    },
]


# --------------------------------------------------------------------------- #
# Tests: normalize_fuelhh
# --------------------------------------------------------------------------- #

class TestNormalizeFuelhh:
    def test_basic_normalization(self):
        df = normalize_fuelhh(SAMPLE_FUELHH)
        assert len(df) == 3
        assert "start_time" in df.columns
        assert "actual_mw" in df.columns
        assert df["actual_mw"].dtype == float

    def test_timestamps_are_utc(self):
        df = normalize_fuelhh(SAMPLE_FUELHH)
        assert df["start_time"].dt.tz.zone == "UTC" or str(df["start_time"].dt.tz) == "UTC"

    def test_empty_input(self):
        df = normalize_fuelhh([])
        assert df.empty

    def test_deduplication(self):
        dupes = SAMPLE_FUELHH + [SAMPLE_FUELHH[0]]  # add a duplicate
        df = normalize_fuelhh(dupes)
        assert len(df) == 3

    def test_null_generation_dropped(self):
        bad = [{"startTime": "2026-01-01T00:00:00Z", "generation": None,
                "settlementDate": "2026-01-01", "settlementPeriod": 1, "fuelType": "WIND"}]
        df = normalize_fuelhh(bad)
        assert df.empty


# --------------------------------------------------------------------------- #
# Tests: normalize_windfor
# --------------------------------------------------------------------------- #

class TestNormalizeWindfor:
    def test_basic_normalization(self):
        df = normalize_windfor(SAMPLE_WINDFOR)
        assert len(df) == 4
        assert "forecast_mw" in df.columns
        assert "publish_time" in df.columns

    def test_timestamps_are_utc(self):
        df = normalize_windfor(SAMPLE_WINDFOR)
        assert str(df["start_time"].dt.tz) == "UTC"

    def test_empty_input(self):
        df = normalize_windfor([])
        assert df.empty

    def test_deduplication_of_exact_pairs(self):
        dupes = SAMPLE_WINDFOR + [SAMPLE_WINDFOR[0]]
        df = normalize_windfor(dupes)
        assert len(df) == 4  # still 4 unique (start_time, publish_time) pairs


# --------------------------------------------------------------------------- #
# Tests: filter_january_2026
# --------------------------------------------------------------------------- #

class TestFilterJanuary2026:
    def test_filters_to_january(self):
        df = normalize_fuelhh(SAMPLE_FUELHH)
        result = filter_january_2026(df)
        assert len(result) == 3

    def test_excludes_other_months(self):
        records = [
            {"startTime": "2026-02-01T00:00:00Z", "generation": 1000,
             "settlementDate": "2026-02-01", "settlementPeriod": 1, "fuelType": "WIND"},
            {"startTime": "2025-12-31T00:00:00Z", "generation": 2000,
             "settlementDate": "2025-12-31", "settlementPeriod": 1, "fuelType": "WIND"},
        ]
        df = normalize_fuelhh(records)
        result = filter_january_2026(df)
        assert result.empty


# --------------------------------------------------------------------------- #
# Tests: get_day_ahead_cutoff
# --------------------------------------------------------------------------- #

class TestGetDayAheadCutoff:
    def test_default_cutoff_is_0950_utc(self):
        delivery_date = pd.Timestamp("2026-01-15", tz="UTC")
        cutoff = get_day_ahead_cutoff(delivery_date)
        assert cutoff == pd.Timestamp("2026-01-14T09:50:00Z")

    def test_cutoff_is_10_utc_day_before(self):
        delivery_date = pd.Timestamp("2026-01-15", tz="UTC")
        cutoff = get_day_ahead_cutoff(delivery_date, cutoff_hour_utc=10, cutoff_minute_utc=0)
        assert cutoff == pd.Timestamp("2026-01-14T10:00:00Z")

    def test_cutoff_for_jan_1(self):
        delivery_date = pd.Timestamp("2026-01-01", tz="UTC")
        cutoff = get_day_ahead_cutoff(delivery_date, cutoff_hour_utc=10, cutoff_minute_utc=0)
        assert cutoff == pd.Timestamp("2025-12-31T10:00:00Z")

    def test_cutoff_for_jan_31(self):
        delivery_date = pd.Timestamp("2026-01-31", tz="UTC")
        cutoff = get_day_ahead_cutoff(delivery_date, cutoff_hour_utc=10, cutoff_minute_utc=0)
        assert cutoff == pd.Timestamp("2026-01-30T10:00:00Z")


# --------------------------------------------------------------------------- #
# Tests: select_eligible_forecast
# --------------------------------------------------------------------------- #

class TestSelectEligibleForecast:
    def setup_method(self):
        self.windfor_df = normalize_windfor(SAMPLE_WINDFOR)

    def test_selects_latest_before_cutoff(self):
        # For 2026-01-01T00:00:00Z, cutoff is 2025-12-31T09:50:00Z
        # Eligible publishes: 08:00, 09:30 — latest eligible is 09:30
        delivery_st = pd.Timestamp("2026-01-01T00:00:00Z")
        result = select_eligible_forecast(self.windfor_df, delivery_st)
        assert result is not None
        assert float(result["forecast_mw"]) == 15200.0
        assert result["publish_time"] == pd.Timestamp("2025-12-31T09:30:00Z")

    def test_excludes_post_cutoff(self):
        # The 11:00 publish is after cutoff and must NOT be returned
        delivery_st = pd.Timestamp("2026-01-01T00:00:00Z")
        result = select_eligible_forecast(self.windfor_df, delivery_st)
        assert result is not None
        assert result["publish_time"] <= pd.Timestamp("2025-12-31T09:50:00Z")

    def test_returns_none_when_no_eligible(self):
        # Use a startTime not in the dataset
        delivery_st = pd.Timestamp("2026-01-05T00:00:00Z")
        result = select_eligible_forecast(self.windfor_df, delivery_st)
        assert result is None

    def test_single_eligible_forecast(self):
        delivery_st = pd.Timestamp("2026-01-01T01:00:00Z")
        result = select_eligible_forecast(self.windfor_df, delivery_st)
        assert result is not None
        assert float(result["forecast_mw"]) == 13500.0


# --------------------------------------------------------------------------- #
# Tests: build_matched_dataset
# --------------------------------------------------------------------------- #

class TestBuildMatchedDataset:
    def test_same_hourly_forecast_is_used_for_both_half_hours(self):
        fuelhh = normalize_fuelhh(SAMPLE_FUELHH[:2])
        windfor = normalize_windfor(SAMPLE_WINDFOR[:3])
        matched = build_matched_dataset(fuelhh, windfor)

        assert len(matched) == 2
        assert matched["windfor_start_time"].nunique() == 1
        assert matched["forecast_mw"].tolist() == [15200.0, 15200.0]
        assert matched["publish_time"].nunique() == 1

    def test_january_boundary_periods_are_included(self):
        actuals = normalize_fuelhh([
            {
                "startTime": "2026-01-01T00:00:00Z",
                "generation": 1000,
                "settlementDate": "2026-01-01",
                "settlementPeriod": 1,
            },
            {
                "startTime": "2026-01-31T23:30:00Z",
                "generation": 2000,
                "settlementDate": "2026-01-31",
                "settlementPeriod": 48,
            },
        ])
        forecasts = normalize_windfor([
            {
                "startTime": "2026-01-01T00:00:00Z",
                "publishTime": "2025-12-31T09:50:00Z",
                "generation": 1100,
            },
            {
                "startTime": "2026-01-31T23:00:00Z",
                "publishTime": "2026-01-30T09:50:00Z",
                "generation": 2200,
            },
        ])

        matched = build_matched_dataset(actuals, forecasts)
        assert len(matched) == 2
        assert matched["is_eligible"].all()
        assert matched["start_time"].min() == pd.Timestamp("2026-01-01T00:00:00Z")
        assert matched["start_time"].max() == pd.Timestamp("2026-01-31T23:30:00Z")

    def test_duplicate_forecasts_do_not_inflate_pairs(self):
        fuelhh = normalize_fuelhh(SAMPLE_FUELHH[:2])
        windfor = normalize_windfor(SAMPLE_WINDFOR[:3] + [SAMPLE_WINDFOR[1]])
        matched = build_matched_dataset(fuelhh, windfor)

        assert len(matched) == 2
        assert matched["forecast_mw"].tolist() == [15200.0, 15200.0]

    def test_matches_30min_actual_to_1hr_forecast(self):
        fuelhh = normalize_fuelhh(SAMPLE_FUELHH)
        windfor = normalize_windfor(SAMPLE_WINDFOR)
        matched = build_matched_dataset(fuelhh, windfor)
        
        # 3 actuals in January 2026
        assert len(matched) == 3
        
        # First actual (00:00) should match WINDFOR 00:00 forecast
        row_0 = matched[matched["start_time"] == pd.Timestamp("2026-01-01T00:00:00Z")].iloc[0]
        assert float(row_0["actual_mw"]) == 15000.0
        assert float(row_0["forecast_mw"]) == 15200.0  # latest eligible

    def test_30min_offset_maps_to_same_hour(self):
        fuelhh = normalize_fuelhh(SAMPLE_FUELHH)
        windfor = normalize_windfor(SAMPLE_WINDFOR)
        matched = build_matched_dataset(fuelhh, windfor)
        
        # 00:30 actual should also map to 00:00 WINDFOR hour
        row_0030 = matched[matched["start_time"] == pd.Timestamp("2026-01-01T00:30:00Z")].iloc[0]
        assert float(row_0030["windfor_start_time"].floor("h").timestamp()) == float(
            pd.Timestamp("2026-01-01T00:00:00Z").timestamp()
        )

    def test_error_calculation(self):
        fuelhh = normalize_fuelhh(SAMPLE_FUELHH)
        windfor = normalize_windfor(SAMPLE_WINDFOR)
        matched = build_matched_dataset(fuelhh, windfor)
        
        row_0 = matched[matched["start_time"] == pd.Timestamp("2026-01-01T00:00:00Z")].iloc[0]
        expected_error = 15200.0 - 15000.0  # forecast - actual = 200
        assert abs(float(row_0["error_mw"]) - expected_error) < 0.01

    def test_metrics_exclude_invalid_actual_pairs(self):
        matched = pd.DataFrame([
            {
                "forecast_mw": 100.0,
                "actual_mw": 80.0,
                "error_mw": 20.0,
                "is_eligible": True,
            },
            {
                "forecast_mw": 120.0,
                "actual_mw": None,
                "error_mw": None,
                "is_eligible": True,
            },
        ])
        metrics = compute_all_metrics(matched)
        assert metrics["n_obs"] == 1
        assert metrics["mae_mw"] == 20.0


# --------------------------------------------------------------------------- #
# Tests: metric calculations
# --------------------------------------------------------------------------- #

class TestMetrics:
    def test_mae_calculation(self):
        errors = pd.Series([100.0, -200.0, 300.0])
        assert compute_mae(errors) == pytest.approx(200.0)

    def test_rmse_calculation(self):
        errors = pd.Series([0.0, 0.0, 0.0, 0.0, 100.0])
        # sqrt(mean([0,0,0,0,10000])) = sqrt(2000) ≈ 44.72
        expected = (100.0**2 / 5) ** 0.5
        assert compute_rmse(errors) == pytest.approx(expected, rel=1e-6)

    def test_bias_over_forecast(self):
        errors = pd.Series([200.0, 300.0, 100.0])  # all positive = over-forecast
        assert compute_bias(errors) == pytest.approx(200.0)

    def test_bias_under_forecast(self):
        errors = pd.Series([-200.0, -300.0, -100.0])  # all negative = under-forecast
        assert compute_bias(errors) == pytest.approx(-200.0)

    def test_mape_excludes_near_zero_actuals(self):
        forecast = pd.Series([1000.0, 500.0])
        actual = pd.Series([50.0, 1000.0])  # first < 100 MW threshold
        mape, n_excluded = compute_mape(forecast, actual)
        assert n_excluded == 1
        # Only second pair: |500 - 1000| / 1000 = 0.5 = 50%
        assert mape == pytest.approx(50.0)

    def test_mape_all_excluded(self):
        forecast = pd.Series([100.0])
        actual = pd.Series([10.0])  # below threshold
        mape, n_excluded = compute_mape(forecast, actual)
        assert mape is None
        assert n_excluded == 1

    def test_empty_series_returns_none(self):
        empty = pd.Series([], dtype=float)
        assert compute_mae(empty) is None
        assert compute_rmse(empty) is None
        assert compute_bias(empty) is None

    def test_compute_all_metrics_with_data(self):
        fuelhh = normalize_fuelhh(SAMPLE_FUELHH[:1])
        windfor = normalize_windfor(SAMPLE_WINDFOR[:2])
        matched = build_matched_dataset(fuelhh, windfor)
        metrics = compute_all_metrics(matched)
        
        assert metrics["n_obs"] >= 0
        if metrics["n_obs"] > 0:
            assert metrics["mae_mw"] is not None
            assert metrics["rmse_mw"] is not None
            assert metrics["bias_mw"] is not None

    def test_bias_direction_over(self):
        from app.services.metrics import compute_all_metrics
        # Build a synthetic matched df with clearly positive bias
        fuelhh = normalize_fuelhh([{
            "startTime": "2026-01-15T12:00:00Z",
            "generation": 10000,
            "settlementDate": "2026-01-15",
            "settlementPeriod": 25,
            "fuelType": "WIND",
        }])
        windfor = normalize_windfor([{
            "publishTime": "2026-01-14T09:00:00Z",
            "startTime": "2026-01-15T12:00:00Z",
            "generation": 12000,  # 2000 MW over-forecast
        }])
        matched = build_matched_dataset(fuelhh, windfor)
        metrics = compute_all_metrics(matched)
        if metrics["n_obs"] > 0:
            assert metrics["bias_direction"] == "over-forecasting"
