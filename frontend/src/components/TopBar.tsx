import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { RefreshCw, Calendar, Activity } from 'lucide-react';
import { postRefresh } from '../services/api';

interface TopBarProps {
  onDateChange?: (date: string) => void;
  selectedDate?: string;
  showDatePicker?: boolean;
  dataStatus?: string;
}

const PAGE_LABELS: Record<string, string> = {
  '/': 'Overview',
  '/explorer': 'Forecast Explorer',
  '/accuracy': 'Accuracy Analysis',
  '/data-quality': 'Data Quality',
  '/about': 'About',
};

const JANUARY_DATES = Array.from({ length: 31 }, (_, i) => {
  return `2026-01-${String(i + 1).padStart(2, '0')}`;
});

const TopBar: React.FC<TopBarProps> = ({
  onDateChange,
  selectedDate,
  showDatePicker = false,
  dataStatus,
}) => {
  const location = useLocation();
  const pageLabel = PAGE_LABELS[location.pathname] ?? 'WindSight';
  const [refreshing, setRefreshing] = useState(false);
  const [refreshStatus, setRefreshStatus] = useState<string | null>(null);

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshStatus(null);
    try {
      await postRefresh();
      setRefreshStatus('ok');
      setTimeout(() => setRefreshStatus(null), 3000);
    } catch {
      setRefreshStatus('error');
      setTimeout(() => setRefreshStatus(null), 4000);
    } finally {
      setRefreshing(false);
    }
  };

  const getStatusColor = () => {
    if (dataStatus === 'complete') return 'var(--color-positive)';
    if (dataStatus === 'partial') return 'var(--accent-gold)';
    if (dataStatus === 'error') return 'var(--color-warning)';
    return 'var(--text-dim)';
  };

  return (
    <header
      className="flex items-center gap-4 px-6"
      style={{
        height: 56,
        background: 'rgba(7,19,33,0.95)',
        borderBottom: '1px solid var(--border-subtle)',
        backdropFilter: 'blur(8px)',
      }}
    >
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 flex-1">
        <span style={{ fontSize: 11, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          WindSight
        </span>
        <span style={{ color: 'var(--border-subtle)' }}>›</span>
        <span style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>
          {pageLabel}
        </span>
      </div>

      {/* Date picker (when applicable) */}
      {showDatePicker && onDateChange && (
        <div className="flex items-center gap-2">
          <Calendar size={14} style={{ color: 'var(--text-muted)' }} />
          <select
            id="date-picker"
            value={selectedDate ?? '2026-01-15'}
            onChange={e => onDateChange(e.target.value)}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-card)',
              color: 'var(--text-primary)',
              borderRadius: 6,
              padding: '4px 8px',
              fontSize: 12,
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            {JANUARY_DATES.map(d => (
              <option key={d} value={d}>
                {new Date(d + 'T12:00:00Z').toLocaleDateString('en-GB', {
                  day: 'numeric', month: 'short', year: 'numeric',
                })}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Data status */}
      {dataStatus && (
        <div className="flex items-center gap-2">
          <Activity size={12} style={{ color: getStatusColor() }} />
          <span style={{ fontSize: 11, color: getStatusColor(), textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            {dataStatus}
          </span>
        </div>
      )}

      {/* Period label */}
      <div
        className="px-3 py-1 rounded"
        style={{
          background: 'var(--accent-gold-dim)',
          border: '1px solid rgba(221,187,120,0.2)',
          fontSize: 10,
          color: 'var(--accent-gold)',
          fontWeight: 600,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}
      >
        January 2026
      </div>

      {/* Refresh */}
      <button
        id="refresh-button"
        onClick={handleRefresh}
        disabled={refreshing}
        title="Refresh data from Elexon API"
        className="flex items-center gap-2 px-3 py-1.5 rounded transition-all"
        style={{
          background: refreshStatus === 'ok' ? 'var(--color-positive-dim)' :
                      refreshStatus === 'error' ? 'var(--color-warning-dim)' : 'var(--bg-card)',
          border: `1px solid ${
            refreshStatus === 'ok' ? 'var(--color-positive)' :
            refreshStatus === 'error' ? 'var(--color-warning)' : 'var(--border-card)'
          }`,
          color: refreshStatus === 'ok' ? 'var(--color-positive)' :
                 refreshStatus === 'error' ? 'var(--color-warning)' : 'var(--text-muted)',
          cursor: refreshing ? 'not-allowed' : 'pointer',
          fontSize: 11,
        }}
      >
        <RefreshCw
          size={12}
          style={{
            animation: refreshing ? 'spin 1s linear infinite' : 'none',
          }}
        />
        <span style={{ fontSize: 11 }}>
          {refreshStatus === 'ok' ? 'Refreshed' : refreshStatus === 'error' ? 'Failed' : 'Refresh'}
        </span>
      </button>
    </header>
  );
};

export default TopBar;
