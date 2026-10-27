import { useQuery } from '../hooks/useQuery'
import { getAccuracy } from '../services/api'
import TopBar from '../components/TopBar'
import { MetricCard } from '../components/MetricCard'
import WindGenerationChart from '../components/WindGenerationChart'
import { useQuery as useOverviewQuery } from '../hooks/useQuery'
import { getOverview } from '../services/api'
import type { AccuracyResponse, OverviewResponse } from '../types/api'

const AccuracyPage = () => {
  const { data, loading, error } = useQuery<AccuracyResponse>(getAccuracy, [])
  const { data: overview } = useOverviewQuery<OverviewResponse>(() => getOverview(), [])
  return <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}>
    <TopBar />
    <main className="p-6" style={{ maxWidth: 1400, margin: '0 auto' }}>
      <header className="mb-6"><div style={{ color: 'var(--accent-gold)', fontSize: 10, letterSpacing: '.16em', textTransform: 'uppercase' }}>Accuracy Analysis</div><h1 className="font-serif" style={{ fontSize: 36, margin: '10px 0 6px' }}>Forecast performance, measured honestly</h1><p style={{ color: 'var(--text-muted)', maxWidth: 700, lineHeight: 1.6 }}>Primary metrics use the latest forecast published at or before the configured D-1 cutoff. Actual generation is retrospective and never treated as decision-time information.</p></header>
      {error && <div className="card p-5 mb-5" style={{ color: 'var(--color-warning)' }}>Unable to load accuracy analysis: {error}</div>}
      <section className="grid gap-4 mb-5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))' }}>
        <MetricCard label="MAE" value={data?.mae_mw ?? null} unit="MW" n_obs={data?.n_obs} loading={loading} />
        <MetricCard label="RMSE" value={data?.rmse_mw ?? null} unit="MW" n_obs={data?.n_obs} loading={loading} accentColor="var(--color-positive)" />
        <MetricCard label="Signed bias" value={data?.bias_mw ?? null} unit="MW" n_obs={data?.n_obs} loading={loading} accentColor="var(--color-warning)" />
        <MetricCard label="MAPE" value={data?.mape_pct ?? null} unit="%" n_obs={data?.n_obs != null && data?.n_mape_excluded != null ? data.n_obs - data.n_mape_excluded : null} loading={loading} subtitle={`Actuals ≥ ${data?.mape_min_actual_mw ?? 100} MW`} />
      </section>
      <section className="card p-5 mb-5"><h2 style={{ fontSize: 15, margin: '0 0 4px' }}>Forecast versus actual</h2><p style={{ color: 'var(--text-dim)', fontSize: 11, margin: '0 0 16px' }}>January 2026 eligible forecast series and retrospective FUELHH actuals.</p><WindGenerationChart data={overview?.time_series ?? []} loading={!overview && !error} height={360} /></section>
      <section className="card p-5"><div className="flex justify-between items-center mb-3"><h2 style={{ fontSize: 15, margin: 0 }}>Largest absolute errors</h2><span style={{ color: 'var(--text-dim)', fontSize: 11 }}>{data?.n_missing_forecast ?? 0} missing/ineligible forecast periods</span></div>{data?.largest_errors?.length ? <div style={{ overflowX: 'auto' }}><table className="w-full" style={{ borderCollapse: 'collapse', fontSize: 12 }}><thead><tr style={{ color: 'var(--text-dim)', textAlign: 'left' }}><th className="py-2">Delivery</th><th>Forecast</th><th>Actual</th><th>Error</th></tr></thead><tbody>{data.largest_errors.map((item) => <tr key={item.start_time} style={{ borderTop: '1px solid var(--border-subtle)' }}><td className="py-2">{item.start_time.replace('T', ' ').slice(0, 16)} UTC</td><td>{item.forecast_mw.toLocaleString()} MW</td><td>{item.actual_mw.toLocaleString()} MW</td><td style={{ color: item.error_mw >= 0 ? 'var(--color-warning)' : 'var(--color-positive)' }}>{item.error_mw >= 0 ? '+' : ''}{item.error_mw.toLocaleString()} MW</td></tr>)}</tbody></table></div> : <div style={{ color: 'var(--text-dim)' }}>No matched observations are available.</div>}</section>
    </main>
  </div>
}

export default AccuracyPage
