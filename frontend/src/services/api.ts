import axios from 'axios';
import type {
  OverviewResponse,
  ForecastPeriodResponse,
  ForecastRecord,
  AccuracyResponse,
  DataQualityResponse,
  HealthResponse,
} from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

export const getHealth = (): Promise<HealthResponse> =>
  api.get<HealthResponse>('/health').then(r => r.data);

export const getOverview = (date?: string): Promise<OverviewResponse> =>
  api.get<OverviewResponse>('/overview', { params: date ? { date } : {} }).then(r => r.data);

export const getForecastsForDate = (date: string): Promise<ForecastRecord[]> =>
  api.get<ForecastRecord[]>('/forecasts', { params: { date } }).then(r => r.data);

export const getForecastVersions = (startTime: string): Promise<ForecastPeriodResponse> =>
  api.get<ForecastPeriodResponse>('/forecasts/versions', { params: { start_time: startTime } }).then(r => r.data);

export const getAccuracy = (startDate?: string, endDate?: string): Promise<AccuracyResponse> =>
  api.get<AccuracyResponse>('/accuracy', {
    params: {
      start_date: startDate ?? '2026-01-01',
      end_date: endDate ?? '2026-01-31',
    },
  }).then(r => r.data);

export const getDataQuality = (): Promise<DataQualityResponse> =>
  api.get<DataQualityResponse>('/data-quality').then(r => r.data);

export const postRefresh = (): Promise<{ status: string }> =>
  api.post<{ status: string }>('/refresh').then(r => r.data);

export default api;
