// ── StatusBadge ──────────────────────────────────────────────────────────────
const STATUS_STYLES = {
  'Active':       { bg: 'var(--green-light)',  color: 'var(--green)'  },
  'Low Stock':    { bg: 'var(--amber-light)',  color: 'var(--amber)'  },
  'Expired':      { bg: 'var(--red-light)',    color: 'var(--red)'    },
  'Out of Stock': { bg: 'var(--surface-2)',    color: 'var(--text-secondary)' },
  'Pending':      { bg: 'var(--amber-light)',  color: 'var(--amber)'  },
  'Completed':    { bg: 'var(--green-light)',  color: 'var(--green)'  },
}

export function StatusBadge({ status }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES['Out of Stock']
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 10px', borderRadius: 999,
      fontSize: 12, fontWeight: 500,
      background: s.bg, color: s.color,
      whiteSpace: 'nowrap',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: s.color, flexShrink: 0 }} />
      {status}
    </span>
  )
}

// ── Button ───────────────────────────────────────────────────────────────────
export function Button({ children, variant = 'primary', size = 'md', onClick, disabled, style: extra, icon: Icon }) {
  const sizes  = { sm: { padding: '5px 10px', fontSize: 12 }, md: { padding: '8px 16px', fontSize: 13 }, lg: { padding: '10px 20px', fontSize: 14 } }
  const variants = {
    primary:   { background: 'var(--accent)',    color: '#fff' },
    secondary: { background: 'var(--surface-2)', color: 'var(--text-primary)', border: '1px solid var(--border)' },
    ghost:     { background: 'transparent',      color: 'var(--text-secondary)' },
    danger:    { background: 'var(--red-light)',  color: 'var(--red)' },
  }
  return (
    <button type="button" onClick={onClick} disabled={disabled} style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      borderRadius: 'var(--radius-md)', fontWeight: 500,
      fontFamily: 'var(--font)', border: 'none',
      transition: 'all 0.15s',
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.6 : 1,
      ...sizes[size], ...variants[variant], ...extra,
    }}>
      {Icon && <Icon size={14} />}
      {children}
    </button>
  )
}

// ── Spinner ──────────────────────────────────────────────────────────────────
export function Spinner({ size = 20 }) {
  return (
    <div style={{
      width: size, height: size,
      border: '2px solid var(--border)',
      borderTopColor: 'var(--accent)',
      borderRadius: '50%',
      animation: 'spin 0.7s linear infinite',
    }} />
  )
}

// ── Card ─────────────────────────────────────────────────────────────────────
export function Card({ children, style: extra }) {
  return (
    <div style={{
      background: 'var(--surface)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border)',
      boxShadow: 'var(--shadow-sm)',
      ...extra,
    }}>
      {children}
    </div>
  )
}

// ── PageHeader ───────────────────────────────────────────────────────────────
export function PageHeader({ title, subtitle, actions }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start',
      justifyContent: 'space-between', marginBottom: 24,
    }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
          {title}
        </h1>
        {subtitle && <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 3 }}>{subtitle}</p>}
      </div>
      {actions && <div style={{ display: 'flex', gap: 8 }}>{actions}</div>}
    </div>
  )
}

// ── EmptyState ───────────────────────────────────────────────────────────────
export function EmptyState({ message = 'No data found' }) {
  return (
    <div style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
      {message}
    </div>
  )
}

// ── Spin keyframe ─────────────────────────────────────────────────────────────
if (typeof document !== 'undefined' && !document.getElementById('ui-keyframes')) {
  const s = document.createElement('style')
  s.id = 'ui-keyframes'
  s.textContent = `@keyframes spin { to { transform: rotate(360deg); } }`
  document.head.appendChild(s)
}

