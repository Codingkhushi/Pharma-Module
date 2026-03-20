import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Package, ShoppingCart, Settings } from 'lucide-react'

const links = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/inventory', icon: Package,         label: 'Inventory'  },
]

export default function Sidebar() {
  return (
    <aside style={{
      width: 'var(--sidebar-w)',
      height: '100vh',
      background: 'var(--text-primary)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '16px 0',
      gap: '4px',
      position: 'fixed',
      left: 0, top: 0,
      zIndex: 100,
    }}>
      {/* <div style={{
        width: 28, height: 28,
        borderRadius: '50%',
        background: 'var(--accent)',
        marginBottom: 20,
        flexShrink: 0,
      }} /> */}

      {links.map(({ to, icon: Icon, label }) => (
        <NavLink key={to} to={to} end={to === '/'} title={label}
          style={({ isActive }) => ({
            width: 40, height: 40,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            borderRadius: 'var(--radius-md)',
            color: isActive ? '#fff' : 'rgba(255,255,255,0.4)',
            background: isActive ? 'rgba(255,255,255,0.12)' : 'transparent',
            transition: 'all 0.15s',
          })}>
          <Icon size={18} />
        </NavLink>
      ))}

      <div style={{ marginTop: 'auto' }}>
        <div style={{
          width: 40, height: 40,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'rgba(255,255,255,0.4)',
        }}>
          {/* <Settings size={18} /> */}
        </div>
      </div>
    </aside>
  )
}