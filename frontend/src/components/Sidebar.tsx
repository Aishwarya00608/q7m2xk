import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Search, BarChart3, ShieldCheck, Info, Zap } from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Overview', id: 'nav-overview' },
  { to: '/explorer', icon: Search, label: 'Explorer', id: 'nav-explorer' },
  { to: '/accuracy', icon: BarChart3, label: 'Accuracy', id: 'nav-accuracy' },
  { to: '/data-quality', icon: ShieldCheck, label: 'Quality', id: 'nav-quality' },
  { to: '/about', icon: Info, label: 'About', id: 'nav-about' },
];

const Sidebar: React.FC = () => {
  return (
    <aside
      className="fixed top-0 left-0 h-full flex flex-col items-center py-6 z-50"
      style={{
        width: 'var(--sidebar-width)',
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-subtle)',
      }}
    >
      {/* Brand mark */}
      <div className="flex flex-col items-center mb-8">
        <div
          className="flex items-center justify-center rounded-xl mb-3"
          style={{
            width: 44,
            height: 44,
            background: 'linear-gradient(135deg, var(--accent-gold-dim), rgba(221,187,120,0.25))',
            border: '1px solid var(--accent-gold-muted)',
          }}
        >
          <Zap size={22} style={{ color: 'var(--accent-gold)' }} />
        </div>
        <div className="text-center">
          <div
            className="font-bold tracking-widest"
            style={{ fontSize: 9, color: 'var(--text-primary)', letterSpacing: '0.15em' }}
          >
            GRIDBRICKS
          </div>
          <div
            className="font-medium tracking-wide"
            style={{ fontSize: 8, color: 'var(--accent-gold)', letterSpacing: '0.12em' }}
          >
            WindSight
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col items-center gap-1 w-full flex-1">
        {navItems.map(({ to, icon: Icon, label, id }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            id={id}
            className={({ isActive }) =>
              `nav-item flex flex-col items-center gap-1 w-full py-3 px-2 cursor-pointer transition-all ${
                isActive ? 'active' : ''
              }`
            }
            style={{ textDecoration: 'none' }}
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={18}
                  style={{ color: isActive ? 'var(--accent-gold)' : 'var(--text-muted)' }}
                />
                <span
                  style={{
                    fontSize: 9,
                    fontWeight: 500,
                    letterSpacing: '0.08em',
                    color: isActive ? 'var(--accent-gold)' : 'var(--text-muted)',
                    textTransform: 'uppercase',
                  }}
                >
                  {label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Version label */}
      <div className="mt-auto text-center" style={{ paddingBottom: 4 }}>
        <div style={{ fontSize: 8, color: 'var(--text-dim)', letterSpacing: '0.05em' }}>
          v1.0 · Jan 2026
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
