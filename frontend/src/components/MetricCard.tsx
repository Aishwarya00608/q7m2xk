import React from 'react';
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: number | null;
  unit: string;
  n_obs?: number | null;
  subtitle?: string;
  trend?: 'positive' | 'negative' | 'neutral' | null;
  accentColor?: string;
  loading?: boolean;
  id?: string;
}

const AbsFormatValue = (value: number | null, unit: string): string => {
  if (value === null) return '—';
  if (unit === 'MW') {
    return `${Math.abs(value).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
  }
  if (unit === '%') return `${Math.abs(value).toFixed(1)}%`;
  return Math.abs(value).toFixed(1);
};

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  n_obs,
  subtitle,
  trend,
  accentColor,
  loading = false,
  id,
}) => {
  const color = accentColor ?? 'var(--accent-gold)';
  const isAvailable = value !== null;

  const TrendIcon = trend === 'positive' ? TrendingUp : trend === 'negative' ? TrendingDown : Minus;
  const trendColor = trend === 'positive' ? 'var(--color-positive)' :
                     trend === 'negative' ? 'var(--color-warning)' : 'var(--text-muted)';

  return (
    <div
      id={id}
      className="card hover-lift p-4 flex flex-col gap-2 animate-fade-in"
      style={{ minHeight: 120 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <span
          style={{
            fontSize: 9,
            fontWeight: 600,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.12em',
          }}
        >
          {label}
        </span>
        {trend && isAvailable && (
          <TrendIcon size={12} style={{ color: trendColor }} />
        )}
        {!isAvailable && !loading && (
          <AlertTriangle size={12} style={{ color: 'var(--text-dim)' }} />
        )}
      </div>

      {/* Value */}
      {loading ? (
        <div className="skeleton" style={{ height: 36, width: '70%' }} />
      ) : (
        <div className="flex items-end gap-1.5">
          <span
            className="metric-value font-bold"
            style={{
              fontSize: 28,
              lineHeight: 1,
              color: isAvailable ? color : 'var(--text-dim)',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {isAvailable ? AbsFormatValue(value, unit) : '—'}
          </span>
          {isAvailable && (
            <span style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
              {unit}
            </span>
          )}
        </div>
      )}

      {/* Subtitle / obs count */}
      {loading ? (
        <div className="skeleton" style={{ height: 12, width: '50%' }} />
      ) : (
        <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>
          {subtitle ?? (n_obs != null ? `${n_obs.toLocaleString()} observations` : '')}
        </div>
      )}
    </div>
  );
};

// Bias card with direction indicator
interface BiasCardProps {
  value: number | null;
  direction: string | null;
  n_obs?: number | null;
  loading?: boolean;
}

export const BiasCard: React.FC<BiasCardProps> = ({ value, direction, n_obs, loading }) => {
  const isOver = value !== null && value > 0;
  const isUnder = value !== null && value < 0;
  const color = isOver ? 'var(--color-warning)' : isUnder ? 'var(--color-positive)' : 'var(--text-muted)';

  return (
    <div id="bias-card" className="card hover-lift p-4 flex flex-col gap-2 animate-fade-in" style={{ minHeight: 120 }}>
      <div className="flex items-center justify-between">
        <span style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>
          Forecast Bias
        </span>
        {value !== null && !loading && (
          isOver
            ? <TrendingUp size={12} style={{ color: 'var(--color-warning)' }} />
            : isUnder
            ? <TrendingDown size={12} style={{ color: 'var(--color-positive)' }} />
            : <Minus size={12} style={{ color: 'var(--text-muted)' }} />
        )}
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 36, width: '70%' }} />
      ) : (
        <div className="flex items-end gap-1.5">
          <span className="metric-value font-bold" style={{ fontSize: 28, lineHeight: 1, color: value !== null ? color : 'var(--text-dim)' }}>
            {value !== null ? `${value >= 0 ? '+' : ''}${value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}` : '—'}
          </span>
          {value !== null && <span style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>MW</span>}
        </div>
      )}

      {loading ? (
        <div className="skeleton" style={{ height: 12, width: '60%' }} />
      ) : (
        <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>
          {direction ? direction.charAt(0).toUpperCase() + direction.slice(1) : ''}
          {n_obs != null ? ` · ${n_obs.toLocaleString()} obs` : ''}
        </div>
      )}
    </div>
  );
};
