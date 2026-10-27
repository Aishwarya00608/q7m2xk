// API response types matching the FastAPI schemas

export interface MetricCard {
  value: number | null;
  unit: string;
  n_obs: number | null;
  label: string;
}

export interface OverviewMetrics {
  mae: MetricCard;
  rmse: MetricCard;
  bias: MetricCard;
  mape: MetricCard | null;
  latest_forecast_mw: number | null;
  latest_forecast_publish_time: string | null;
  latest_forecast_delivery_time: string | null;
  bias_direction: string | null;
  n_obs: number;
}

export interface TimeSeriesPoint {
  start_time: string;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  publish_time: string | null;
  is_eligible: boolean;
}

export interface OverviewResponse {
  metrics: OverviewMetrics;
  time_series: TimeSeriesPoint[];
  date: string | null;
}

export interface ForecastVersion {
  publish_time: string;
  forecast_mw: number;
  is_eligible: boolean;
  is_latest_eligible: boolean;
  delta_from_prev_mw: number | null;
}

export interface ForecastPeriodResponse {
  delivery_start_time: string;
  cutoff_utc: string;
  eligible_forecast_mw: number | null;
  eligible_publish_time: string | null;
  actual_mw: number | null;
  error_mw: number | null;
  versions: ForecastVersion[];
  n_versions: number;
  n_eligible_versions: number;
}

export interface DailyAccuracy {
  date: string;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  mape_pct: number | null;
  n_obs: number;
  mean_forecast_mw: number | null;
  mean_actual_mw: number | null;
}

export interface ErrorDistributionBin {
  bin_label: string;
  count: number;
  lower_mw: number;
  upper_mw: number;
}

export interface AccuracyResponse {
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  mape_pct: number | null;
  bias_direction: string | null;
  n_obs: number;
  n_missing_forecast: number;
  n_mape_excluded: number;
  mape_min_actual_mw: number;
  daily_summary: DailyAccuracy[];
  error_distribution: ErrorDistributionBin[];
  largest_errors: LargestError[];
  evaluation_period: string;
}

export interface LargestError {
  start_time: string;
  forecast_mw: number;
  actual_mw: number;
  error_mw: number;
  abs_error_mw: number;
  settlement_date: string;
  settlement_period: number | null;
}

export interface DataQualityResponse {
  last_retrieved_utc: string | null;
  fuelhh_records: number;
  windfor_records: number;
  fuelhh_wind_records: number;
  matched_pairs: number;
  missing_actuals: number;
  missing_forecasts: number;
  fuelhh_date_range: {
    min: string;
    max: string;
    n_records: number;
    n_expected: number;
    coverage_pct: number | null;
  } | null;
  windfor_publish_range: {
    min_publish_time: string;
    max_publish_time: string;
    n_records: number;
  } | null;
  windfor_delivery_range: {
    min_start_time: string;
    max_start_time: string;
    min_publish_time: string;
    max_publish_time: string;
    n_unique_start_times: number;
    n_unique_publish_times: number;
  } | null;
  coverage_pct: number | null;
  is_complete: boolean;
  issues: string[];
  status: string;
}

export interface ForecastRecord {
  start_time: string;
  settlement_period: number | null;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  publish_time: string | null;
  is_eligible: boolean;
}

export interface HealthResponse {
  status: string;
  version: string;
  analysis_period: string;
}
