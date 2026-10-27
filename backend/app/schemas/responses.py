"""
Pydantic schemas for API responses.
"""
from typing import Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    analysis_period: str = "January 2026"


class MetricCard(BaseModel):
    value: Optional[float]
    unit: str
    n_obs: Optional[int] = None
    label: str


class OverviewMetrics(BaseModel):
    mae: MetricCard
    rmse: MetricCard
    bias: MetricCard
    mape: Optional[MetricCard] = None
    latest_forecast_mw: Optional[float] = None
    latest_forecast_publish_time: Optional[str] = None
    latest_forecast_delivery_time: Optional[str] = None
    bias_direction: Optional[str] = None
    n_obs: int = 0


class TimeSeriesPoint(BaseModel):
    start_time: str
    forecast_mw: Optional[float] = None
    actual_mw: Optional[float] = None
    error_mw: Optional[float] = None
    publish_time: Optional[str] = None
    is_eligible: bool = False


class OverviewResponse(BaseModel):
    metrics: OverviewMetrics
    time_series: list[TimeSeriesPoint]
    date: Optional[str] = None


class ForecastVersion(BaseModel):
    publish_time: str
    forecast_mw: float
    is_eligible: bool
    is_latest_eligible: bool
    delta_from_prev_mw: Optional[float] = None


class ForecastPeriodResponse(BaseModel):
    delivery_start_time: str
    cutoff_utc: str
    eligible_forecast_mw: Optional[float] = None
    eligible_publish_time: Optional[str] = None
    actual_mw: Optional[float] = None
    error_mw: Optional[float] = None
    versions: list[ForecastVersion]
    n_versions: int
    n_eligible_versions: int


class DailyAccuracy(BaseModel):
    date: str
    mae_mw: Optional[float] = None
    rmse_mw: Optional[float] = None
    bias_mw: Optional[float] = None
    mape_pct: Optional[float] = None
    n_obs: int = 0
    mean_forecast_mw: Optional[float] = None
    mean_actual_mw: Optional[float] = None


class ErrorDistributionBin(BaseModel):
    bin_label: str
    count: int
    lower_mw: float
    upper_mw: float


class AccuracyResponse(BaseModel):
    mae_mw: Optional[float] = None
    rmse_mw: Optional[float] = None
    bias_mw: Optional[float] = None
    mape_pct: Optional[float] = None
    bias_direction: Optional[str] = None
    n_obs: int = 0
    n_missing_forecast: int = 0
    n_mape_excluded: int = 0
    mape_min_actual_mw: float = 100.0
    daily_summary: list[DailyAccuracy] = []
    error_distribution: list[ErrorDistributionBin] = []
    largest_errors: list[dict] = []
    evaluation_period: str = "January 2026"


class DataQualityResponse(BaseModel):
    last_retrieved_utc: Optional[str] = None
    fuelhh_records: int = 0
    windfor_records: int = 0
    fuelhh_wind_records: int = 0
    matched_pairs: int = 0
    missing_actuals: int = 0
    missing_forecasts: int = 0
    fuelhh_date_range: Optional[dict] = None
    windfor_publish_range: Optional[dict] = None
    windfor_delivery_range: Optional[dict] = None
    coverage_pct: Optional[float] = None
    is_complete: bool = False
    issues: list[str] = []
    status: str = "unknown"
