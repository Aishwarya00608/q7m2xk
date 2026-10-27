import React, { useState } from 'react';
import { Wind } from 'lucide-react';
import { useQuery } from '../hooks/useQuery';
import { getOverview, getDataQuality } from '../services/api';
import TopBar from '../components/TopBar';
import { MetricCard, BiasCard } from '../components/MetricCard';
import WindGenerationChart from '../components/WindGenerationChart';
import type { OverviewResponse, DataQualityResponse } from '../types/api';
import { format, parseISO } from 'date-fns';

const HERO_STATS = [
  { label: 'Analysis Period', value: 'January 2026', sub: '31 days · 1,488 periods' },
  { label: 'Resolution', value: '30-min', sub: 'FUELHH actuals' },
  { label: 'Data Source', value: 'Elexon BMRS', sub: 'FUELHH + WINDFOR' },
];

type ViewMode = 'day' | 'month';

const OverviewPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState('2026-01-15');
  const [viewMode, setViewMode] = useState<ViewMode>('day');

  const dateParam = viewMode === 'day' ? selectedDate : undefined;

  const { data: overview, loading: overviewLoading, error: overviewError } =
    useQuery<OverviewResponse>(() => getOverview(dateParam), [dateParam]);

  const { data: quality } =
    useQuery<DataQualityResponse>(getDataQuality, []);

  const metrics = overview?.metrics;
  const timeSeries = overview?.time_series ?? [];

  const formatTime = (iso: string | null) => {
    if (!iso) return '—';
    try { return format(parseISO(iso), 'dd MMM HH:mm') + ' UTC'; }
    catch { return iso; }
  };

  return (
    <div className="flex flex-col min-h-screen" style={{ background: 'var(--bg-main)' }}>
      <TopBar
        showDatePicker={viewMode === 'day'}
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
        dataStatus={quality?.status}
      />

      <main className="flex-1 p-6 flex flex-col gap-6" style={{ maxWidth: 1400, margin: '0 auto', width: '100%' }}>

        {/* Hero Section */}
        <section
          className="relative rounded-2xl overflow-hidden animate-fade-in"
          style={{
            background: 'linear-gradient(135deg, #071321 0%, #0D2444 50%, #071321 100%)',
            border: '1px solid var(--border-card)',
            minHeight: 200,
          }}
        >
          {/* Background turbine silhouette */}
          <div
            className="absolute inset-0 opacity-5"
            style={{
              backgroundImage: `url("data:image/svg+xml,%3Csvg width='200' height='200' viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='100' cy='100' r='4' fill='%23DDBB78'/%3E%3Crect x='98' y='100' width='4' height='80' fill='%23DDBB78'/%3E%3Cellipse cx='100' cy='50' rx='40' ry='8' fill='%23DDBB78' transform='rotate(30 100 100)'/%3E%3Cellipse cx='100' cy='50' rx='40' ry='8' fill='%23DDBB78' transform='rotate(150 100 100)'/%3E%3Cellipse cx='100' cy='50' rx='40' ry='8' fill='%23DDBB78' transform='rotate(270 100 100)'/%3E%3C/svg%3E")`,
              backgroundSize: '120px 120px',
              backgroundRepeat: 'repeat',
            }}
          />
          
          {/* Gradient overlay */}
          <div className="absolute inset-0" style={{
            background: 'linear-gradient(to right, rgba(7,19,33,0.9) 0%, rgba(7,19,33,0.4) 60%, rgba(7,19,33,0.8) 100%)',
          }} />

          {/* Content */}
          <div className="relative z-10 p-8 flex flex-col gap-4">
            <div className="flex items-center gap-2 mb-1">
              <div style={{
                fontSize: 10,
                color: 'var(--accent-gold)',
                fontWeight: 600,
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
              }}>
                DAY-AHEAD WIND INTELLIGENCE · JANUARY 2026
              </div>
            </div>

            <h1
              className="font-serif"
              style={{
                fontSize: 'clamp(24px, 3vw, 42px)',
                fontWeight: 700,
                color: 'var(--text-primary)',
                lineHeight: 1.15,
                maxWidth: 560,
              }}
            >
              Know the wind.
              <span style={{ color: 'var(--accent-gold)', fontStyle: 'italic' }}> Plan the power.</span>
            </h1>

            <p style={{ fontSize: 13, color: 'var(--text-muted)', maxWidth: 500, lineHeight: 1.6 }}>
              Explore day-ahead wind generation forecasts, track forecast revisions, and measure historical 
              forecast accuracy across Great Britain.
            </p>

            {/* Hero stats */}
            <div className="flex gap-6 mt-2">
              {HERO_STATS.map(s => (
                <div key={s.label}>
                  <div style={{ fontSize: 10, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                    {s.label}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                    {s.value}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-dim)' }}>{s.sub}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Latest Forecast Card (separate prominent card) */}
        {metrics && (
          <section className="card p-5 animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center justify-between gap-6 flex-wrap">
              <div>
                <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em', marginBottom: 4 }}>
                  Latest Eligible Forecast
                </div>
                <div className="flex items-end gap-2">
                  <span
                    className="font-bold metric-value"
                    style={{ fontSize: 36, color: 'var(--accent-gold)', lineHeight: 1 }}
                  >
                    {metrics.latest_forecast_mw != null
                      ? `${metrics.latest_forecast_mw.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}` : '—'}
                  </span>
                  {metrics.latest_forecast_mw != null && (
                    <span style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 4 }}>MW</span>
                  )}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 4 }}>
                  Published: {formatTime(metrics.latest_forecast_publish_time)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                  Delivery: {formatTime(metrics.latest_forecast_delivery_time)}
                </div>
              </div>
              <div className="flex items-center gap-2" style={{ color: 'var(--accent-gold)', opacity: 0.4 }}>
                <Wind size={48} strokeWidth={0.8} />
              </div>
            </div>
          </section>
        )}

        {/* Metric Cards */}
        <section className="grid grid-cols-2 gap-4 animate-fade-in" style={{ animationDelay: '0.15s', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
          <MetricCard
            id="mae-card"
            label="Mean Absolute Error"
            value={metrics?.mae.value ?? null}
            unit="MW"
            n_obs={metrics?.mae.n_obs}
            loading={overviewLoading}
            accentColor="var(--accent-gold)"
          />
          <MetricCard
            id="rmse-card"
            label="Root Mean Squared Error"
            value={metrics?.rmse.value ?? null}
            unit="MW"
            n_obs={metrics?.rmse.n_obs}
            loading={overviewLoading}
            accentColor="var(--color-positive)"
          />
          <BiasCard
            value={metrics?.bias.value ?? null}
            direction={metrics?.bias_direction ?? null}
            n_obs={metrics?.bias.n_obs}
            loading={overviewLoading}
          />
          {metrics?.mape && (
            <MetricCard
              id="mape-card"
              label="Mean Abs. % Error"
              value={metrics.mape.value}
              unit="%"
              n_obs={metrics.mape.n_obs}
              loading={overviewLoading}
              accentColor="var(--color-warning)"
              subtitle={`Excludes periods < 100 MW`}
            />
          )}
        </section>

        {/* Chart */}
        <section className="card p-5 animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center justify-between mb-4 gap-4 flex-wrap">
            <div>
              <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                Wind Generation Outlook
              </h2>
              <p style={{ fontSize: 11, color: 'var(--text-dim)', margin: '4px 0 0' }}>
                Eligible day-ahead forecast vs. actual generation (retrospective)
              </p>
            </div>
            <div className="flex gap-2">
              {(['day', 'month'] as ViewMode[]).map(mode => (
                <button
                  key={mode}
                  id={`view-${mode}`}
                  onClick={() => setViewMode(mode)}
                  className="px-3 py-1.5 rounded transition-all"
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    background: viewMode === mode ? 'var(--accent-gold-dim)' : 'var(--bg-card-secondary)',
                    color: viewMode === mode ? 'var(--accent-gold)' : 'var(--text-muted)',
                    border: `1px solid ${viewMode === mode ? 'rgba(221,187,120,0.3)' : 'var(--border-card)'}`,
                    cursor: 'pointer',
                  }}
                >
                  {mode === 'day' ? 'Day' : 'Month'}
                </button>
              ))}
            </div>
          </div>

          {overviewError ? (
            <div
              className="flex flex-col items-center justify-center gap-2"
              style={{ height: 300, color: 'var(--color-warning)' }}
            >
              <div style={{ fontSize: 13 }}>Failed to load chart data</div>
              <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{overviewError}</div>
            </div>
          ) : (
            <WindGenerationChart
              data={timeSeries}
              loading={overviewLoading}
              height={viewMode === 'month' ? 340 : 300}
            />
          )}

          {/* Legend note */}
          <div className="flex gap-4 mt-4 pt-3" style={{ borderTop: '1px solid var(--border-subtle)' }}>
            <div className="flex items-center gap-2">
              <div style={{ width: 16, height: 2, background: 'var(--chart-forecast)', borderRadius: 1 }} />
              <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>Eligible day-ahead forecast (published by the configured D-1 cutoff)</span>
            </div>
            <div className="flex items-center gap-2">
              <div style={{ width: 16, height: 0, borderTop: '2px dashed var(--chart-actual)', borderRadius: 1 }} />
              <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>Actual generation (retrospective — not available at purchase time)</span>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center" style={{ padding: '8px 0 16px' }}>
          <span style={{ fontSize: 10, color: 'var(--text-dim)', letterSpacing: '0.05em' }}>
            GridBricks WindSight · Historical Analysis · January 2026 · Data: Elexon BMRS FUELHH + WINDFOR
          </span>
        </footer>
      </main>
    </div>
  );
};

export default OverviewPage;
