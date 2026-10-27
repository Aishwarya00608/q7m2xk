import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import type { TimeSeriesPoint } from '../types/api';
import { format, parseISO } from 'date-fns';

interface WindGenerationChartProps {
  data: TimeSeriesPoint[];
  loading?: boolean;
  title?: string;
  height?: number;
}

interface ChartDataPoint {
  time: string;
  timeLabel: string;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  is_eligible: boolean;
}

const formatMW = (v: number) => `${(v / 1000).toFixed(1)}GW`;
const formatMWFull = (v: number) => `${v.toLocaleString()} MW`;

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label }) => {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0]?.payload as ChartDataPoint;
  if (!data) return null;

  return (
    <div
      className="glass rounded-lg p-3"
      style={{
        border: '1px solid var(--border-card)',
        minWidth: 220,
      }}
    >
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8 }}>
        {data.time
          ? format(parseISO(data.time), 'dd MMM yyyy · HH:mm') + ' UTC'
          : label}
      </div>
      {data.forecast_mw != null && (
        <div className="flex justify-between items-center gap-4 mb-1">
          <div className="flex items-center gap-2">
            <div style={{ width: 10, height: 2, background: 'var(--chart-forecast)', borderRadius: 2 }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Forecast</span>
          </div>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-gold)', fontVariantNumeric: 'tabular-nums' }}>
            {formatMWFull(data.forecast_mw)}
          </span>
        </div>
      )}
      {data.actual_mw != null && (
        <div className="flex justify-between items-center gap-4 mb-1">
          <div className="flex items-center gap-2">
            <div style={{ width: 10, height: 2, background: 'var(--chart-actual)', borderRadius: 2 }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Actual</span>
          </div>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-positive)', fontVariantNumeric: 'tabular-nums' }}>
            {formatMWFull(data.actual_mw)}
          </span>
        </div>
      )}
      {data.error_mw != null && (
        <div
          className="flex justify-between items-center gap-4 mt-2 pt-2"
          style={{ borderTop: '1px solid var(--border-subtle)' }}
        >
          <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>Error (F-A)</span>
          <span style={{
            fontSize: 11,
            fontWeight: 600,
            color: data.error_mw > 0 ? 'var(--color-warning)' : 'var(--color-positive)',
            fontVariantNumeric: 'tabular-nums',
          }}>
            {data.error_mw > 0 ? '+' : ''}{formatMWFull(data.error_mw)}
          </span>
        </div>
      )}
    </div>
  );
};

const LoadingState: React.FC<{ height: number }> = ({ height }) => (
  <div style={{ height }} className="flex items-center justify-center">
    <div className="skeleton" style={{ width: '100%', height: '100%', borderRadius: 8 }} />
  </div>
);

const EmptyState: React.FC<{ height: number }> = ({ height }) => (
  <div
    style={{ height }}
    className="flex flex-col items-center justify-center gap-3"
  >
    <div style={{ fontSize: 32 }}>📊</div>
    <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>No data available for this period</div>
    <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>Select a date within January 2026</div>
  </div>
);

const WindGenerationChart: React.FC<WindGenerationChartProps> = ({
  data,
  loading = false,
  title = 'Wind Generation Outlook',
  height = 320,
}) => {
  if (loading) return <LoadingState height={height} />;
  if (!data || data.length === 0) return <EmptyState height={height} />;

  const chartData: ChartDataPoint[] = data.map(d => ({
    time: d.start_time,
    timeLabel: format(parseISO(d.start_time), 'dd MMM HH:mm'),
    forecast_mw: d.forecast_mw,
    actual_mw: d.actual_mw,
    error_mw: d.error_mw,
    is_eligible: d.is_eligible,
  }));

  const hasActuals = chartData.some(d => d.actual_mw != null);
  const hasForecasts = chartData.some(d => d.forecast_mw != null);

  // Determine tick interval based on data length
  const tickInterval = chartData.length > 96 ? 47 : chartData.length > 48 ? 23 : 5;

  return (
    <div style={{ height }} aria-label={title}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--chart-grid)"
            vertical={false}
          />
          <XAxis
            dataKey="timeLabel"
            tick={{ fontSize: 10, fill: 'var(--text-dim)' }}
            tickLine={false}
            axisLine={{ stroke: 'var(--border-subtle)' }}
            interval={tickInterval}
          />
          <YAxis
            tickFormatter={formatMW}
            tick={{ fontSize: 10, fill: 'var(--text-dim)' }}
            tickLine={false}
            axisLine={false}
            width={52}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 11, color: 'var(--text-muted)', paddingTop: 8 }}
            formatter={(value) => (
              <span style={{ color: 'var(--text-muted)' }}>{value}</span>
            )}
          />
          {hasForecasts && (
            <Line
              type="monotone"
              dataKey="forecast_mw"
              name="Forecast"
              stroke="var(--chart-forecast)"
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, fill: 'var(--chart-forecast)' }}
              connectNulls={false}
            />
          )}
          {hasActuals && (
            <Line
              type="monotone"
              dataKey="actual_mw"
              name="Actual (retrospective)"
              stroke="var(--chart-actual)"
              strokeWidth={1.5}
              dot={false}
              activeDot={{ r: 3, fill: 'var(--chart-actual)' }}
              strokeDasharray="6 2"
              connectNulls={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default WindGenerationChart;
