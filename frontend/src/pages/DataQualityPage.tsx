import { CheckCircle2, AlertTriangle, Database, RefreshCw } from 'lucide-react'
import { useQuery } from '../hooks/useQuery'
import { getDataQuality, postRefresh } from '../services/api'
import TopBar from '../components/TopBar'
import type { DataQualityResponse } from '../types/api'
import { useState } from 'react'

const DataQualityPage = () => {
  const { data, loading, error } = useQuery<DataQualityResponse>(getDataQuality, [])
  const [refreshing, setRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState<string | null>(null)
  const refresh = async () => {
    setRefreshing(true)
    setRefreshError(null)
    try {
      await postRefresh()
      window.location.reload()
    } catch (reason: unknown) {
      setRefreshError(reason instanceof Error ? reason.message : 'Refresh failed')
    } finally {
      setRefreshing(false)
    }
  }
  const value = (item: number | null | undefined) => loading ? '…' : (item ?? 0).toLocaleString()
  return <div className="min-h-screen" style={{ background: 'var(--bg-main)' }}><TopBar dataStatus={data?.status} /><main className="p-6" style={{ maxWidth: 1400, margin: '0 auto' }}>
    <header className="flex justify-between gap-4 items-start mb-6"><div><div style={{ color: 'var(--accent-gold)', fontSize: 10, letterSpacing: '.16em', textTransform: 'uppercase' }}>Data Quality</div><h1 className="font-serif" style={{ fontSize: 36, margin: '10px 0 6px' }}>Know what the data can support</h1><p style={{ color: 'var(--text-muted)', maxWidth: 680, lineHeight: 1.6 }}>Coverage and retrieval status are shown explicitly. Missing records remain missing and are never silently converted to zero.</p></div><button onClick={refresh} disabled={refreshing} className="px-3 py-2 rounded" style={{ background: 'var(--bg-card)', color: 'var(--text-muted)', border: '1px solid var(--border-card)', cursor: 'pointer' }}><RefreshCw size={14} className="inline mr-2" />{refreshing ? 'Refreshing…' : 'Refresh data'}</button></header>
    {(error || refreshError) && <div className="card p-5 mb-5" style={{ color: 'var(--color-warning)' }}><AlertTriangle size={15} className="inline mr-2" />{error ?? refreshError}</div>}
    <section className="grid gap-4 mb-5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))' }}>{[['FUELHH records', data?.fuelhh_records], ['WINDFOR records', data?.windfor_records], ['Matched pairs', data?.matched_pairs], ['Coverage', data?.coverage_pct == null ? null : `${data.coverage_pct}%`]].map(([label, item]) => <div className="card p-4" key={String(label)}><Database size={16} style={{ color: 'var(--accent-gold)' }} /><div style={{ color: 'var(--text-dim)', fontSize: 10, marginTop: 12 }}>{label}</div><strong style={{ display: 'block', fontSize: 25, marginTop: 4 }}>{typeof item === 'number' ? value(item) : loading ? '…' : (item ?? '—')}</strong></div>)}</section>
    <section className="grid gap-5" style={{ gridTemplateColumns: 'minmax(280px,1fr) minmax(300px,1fr)' }}><div className="card p-5"><h2 style={{ fontSize: 15, marginTop: 0 }}>Retrieval status</h2><div className="flex items-center gap-2" style={{ color: data?.status === 'complete' ? 'var(--color-positive)' : 'var(--accent-gold)' }}>{data?.status === 'complete' ? <CheckCircle2 size={17} /> : <AlertTriangle size={17} />}<strong>{loading ? 'Loading…' : data?.status ?? 'unknown'}</strong></div><p style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 14 }}>Last retrieved: {data?.last_retrieved_utc ?? '—'}</p><p style={{ color: 'var(--text-dim)', fontSize: 11 }}>Expected actual periods: 1,488 · expected WINDFOR delivery hours: 744</p></div><div className="card p-5"><h2 style={{ fontSize: 15, marginTop: 0 }}>Issues and limitations</h2>{data?.issues?.length ? <ul style={{ color: 'var(--color-warning)', fontSize: 12, paddingLeft: 18 }}>{data.issues.map((issue) => <li key={issue} className="mb-2">{issue}</li>)}</ul> : <p style={{ color: 'var(--color-positive)', fontSize: 12 }}>No data-quality issues were reported.</p>}</div></section>
  </main></div>
}

export default DataQualityPage
