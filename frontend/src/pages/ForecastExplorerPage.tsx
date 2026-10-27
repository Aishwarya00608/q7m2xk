import { useMemo, useState } from 'react'
import { format, parseISO } from 'date-fns'
import { AlertCircle, Clock3, Eye, GitBranch } from 'lucide-react'
import { useQuery } from '../hooks/useQuery'
import { getForecastsForDate, getForecastVersions } from '../services/api'
import TopBar from '../components/TopBar'
import type { ForecastPeriodResponse, ForecastRecord } from '../types/api'

const dates = Array.from({ length: 31 }, (_, index) => `2026-01-${String(index + 1).padStart(2, '0')}`)

const formatTime = (value: string | null) => value ? `${format(parseISO(value), 'dd MMM HH:mm')} UTC` : '—'
const formatMw = (value: number | null) => value == null ? '—' : `${value.toLocaleString()} MW`

const ForecastExplorerPage = () => {
  const [date, setDate] = useState('2026-01-15')
  const [selectedStart, setSelectedStart] = useState<string | null>(null)
  const { data: periods, loading, error } = useQuery<ForecastRecord[]>(
    () => getForecastsForDate(date),
    [date],
  )
  const selected = useMemo(
    () => periods?.find((period) => period.start_time === selectedStart) ?? periods?.[0],
    [periods, selectedStart],
  )
  const { data: versions, loading: versionsLoading } = useQuery<ForecastPeriodResponse>(
    () => selected ? getForecastVersions(selected.start_time) : Promise.resolve(undefined as unknown as ForecastPeriodResponse),
    [selected?.start_time],
  )

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}>
      <TopBar showDatePicker={false} />
      <main className="p-6" style={{ maxWidth: 1400, margin: '0 auto' }}>
        <header className="mb-6">
          <div style={{ color: 'var(--accent-gold)', fontSize: 10, letterSpacing: '0.16em', textTransform: 'uppercase' }}>Forecast Explorer</div>
          <h1 className="font-serif" style={{ fontSize: 36, margin: '10px 0 6px' }}>Delivery-period intelligence</h1>
          <p style={{ color: 'var(--text-muted)', maxWidth: 680, lineHeight: 1.6 }}>
            Select a January delivery date and half-hour period to inspect the eligible forecast,
            actual retrospective outcome, and every publication revision received before or after the cutoff.
          </p>
        </header>

        <section className="card p-4 mb-5 flex flex-wrap items-center gap-4">
          <label style={{ color: 'var(--text-muted)', fontSize: 12 }}>
            Delivery date
            <select value={date} onChange={(event) => { setDate(event.target.value); setSelectedStart(null) }} className="ml-3" style={{ background: 'var(--bg-card-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border-card)', borderRadius: 6, padding: '7px 10px' }}>
              {dates.map((item) => <option key={item} value={item}>{format(parseISO(`${item}T00:00:00Z`), 'dd MMM yyyy')}</option>)}
            </select>
          </label>
          <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>Forecast resolution is hourly; actual delivery periods remain 30-minute FUELHH intervals.</span>
        </section>

        {error && <div className="card p-5 mb-5" style={{ color: 'var(--color-warning)' }}><AlertCircle size={16} className="inline mr-2" />{error}</div>}
        <section className="grid gap-5" style={{ gridTemplateColumns: 'minmax(280px, 0.9fr) minmax(420px, 1.5fr)' }}>
          <div className="card p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 style={{ fontSize: 15, margin: 0 }}>Delivery periods</h2>
              <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>{periods?.length ?? 0} returned</span>
            </div>
            {loading ? <div className="skeleton" style={{ height: 360 }} /> : periods?.length ? (
              <div style={{ maxHeight: 480, overflowY: 'auto' }}>
                {periods.map((period) => (
                  <button key={period.start_time} onClick={() => setSelectedStart(period.start_time)} className="w-full text-left p-3 mb-1 rounded" style={{ background: selected?.start_time === period.start_time ? 'var(--accent-gold-dim)' : 'transparent', border: `1px solid ${selected?.start_time === period.start_time ? 'rgba(221,187,120,.35)' : 'transparent'}`, color: 'var(--text-primary)', cursor: 'pointer' }}>
                    <div className="flex justify-between">
                      <span style={{ fontSize: 12 }}>{formatTime(period.start_time)}</span>
                      <span style={{ fontSize: 11, color: period.is_eligible ? 'var(--color-positive)' : 'var(--text-dim)' }}>{period.is_eligible ? 'Eligible' : 'Missing'}</span>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Forecast {formatMw(period.forecast_mw)} · Actual {formatMw(period.actual_mw)}</div>
                  </button>
                ))}
              </div>
            ) : <div style={{ color: 'var(--text-dim)', padding: 32, textAlign: 'center' }}>No delivery records returned for this date.</div>}
          </div>

          <div className="card p-5">
            {selected && versions ? (
              <>
                <div className="flex items-start justify-between gap-4">
                  <div><div style={{ color: 'var(--accent-gold)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '.12em' }}>Selected period</div><h2 style={{ fontSize: 22, margin: '8px 0' }}>{formatTime(versions.delivery_start_time)}</h2></div>
                  <Eye size={22} style={{ color: 'var(--accent-gold)' }} />
                </div>
                <div className="grid grid-cols-2 gap-3 mb-5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))' }}>
                  <div className="card-secondary p-3"><div style={{ color: 'var(--text-dim)', fontSize: 10 }}>Eligible forecast</div><strong>{formatMw(versions.eligible_forecast_mw)}</strong></div>
                  <div className="card-secondary p-3"><div style={{ color: 'var(--text-dim)', fontSize: 10 }}>Actual retrospective</div><strong>{formatMw(versions.actual_mw)}</strong></div>
                  <div className="card-secondary p-3"><div style={{ color: 'var(--text-dim)', fontSize: 10 }}>Error (F − A)</div><strong>{formatMw(versions.error_mw)}</strong></div>
                  <div className="card-secondary p-3"><div style={{ color: 'var(--text-dim)', fontSize: 10 }}>Cutoff</div><strong style={{ fontSize: 12 }}>{formatTime(versions.cutoff_utc)}</strong></div>
                </div>
                <h3 style={{ fontSize: 14, marginBottom: 8 }}><GitBranch size={15} className="inline mr-2" />Publication history</h3>
                {versionsLoading ? <div className="skeleton" style={{ height: 180 }} /> : versions.versions.length ? versions.versions.map((version) => (
                  <div key={version.publish_time} className="flex items-center justify-between py-2" style={{ borderBottom: '1px solid var(--border-subtle)', fontSize: 12 }}>
                    <span><Clock3 size={13} className="inline mr-2" style={{ color: 'var(--text-dim)' }} />{formatTime(version.publish_time)}</span>
                    <span>{formatMw(version.forecast_mw)}</span>
                    <span style={{ color: version.is_eligible ? 'var(--color-positive)' : 'var(--text-dim)', minWidth: 74, textAlign: 'right' }}>{version.is_latest_eligible ? 'Selected' : version.is_eligible ? 'Eligible' : 'After cutoff'}</span>
                  </div>
                )) : <div style={{ color: 'var(--text-dim)' }}>No forecast versions available.</div>}
              </>
            ) : <div style={{ padding: 48, color: 'var(--text-dim)', textAlign: 'center' }}>Select a delivery period to inspect its revisions.</div>}
          </div>
        </section>
      </main>
    </div>
  )
}

export default ForecastExplorerPage
