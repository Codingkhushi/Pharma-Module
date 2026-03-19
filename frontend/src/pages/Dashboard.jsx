import { AlertTriangle, ClipboardList, Plus, ShoppingBag } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import {
    createSale,
    getDashboardItemsSold,
    getDashboardLowStock, getDashboardPurchaseOrders,
    getDashboardRecentSales,
    getDashboardSalesSummary,
    getMedicines,
} from '../api'
import { Button, Card, EmptyState, PageHeader, Spinner, StatusBadge } from '../components/ui'
import { useFetch } from '../hooks/useFetch'

// ── Summary Card ─────────────────────────────────────────────────────────────
function SummaryCard({ label, value, badge, badgeColor, icon: Icon, iconBg, loading }) {
  return (
    <Card style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 12, flex: 1, minWidth: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--radius-md)',
          background: iconBg, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={18} color="#fff" />
        </div>
        {badge && (
          <span style={{
            fontSize: 11, fontWeight: 500, padding: '2px 8px',
            borderRadius: 999, background: badgeColor + '22', color: badgeColor,
          }}>
            {badge}
          </span>
        )}
      </div>
      {loading ? (
        <Spinner size={18} />
      ) : (
        <div>
          <div style={{ fontSize: 24, fontWeight: 600, letterSpacing: '-0.5px' }}>{value}</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{label}</div>
        </div>
      )}
    </Card>
  )
}

// ── Make a Sale Modal ────────────────────────────────────────────────────────
function SaleModal({ onClose, onSuccess }) {
  const [patientName, setPatientName] = useState('')
  const [paymentMode, setPaymentMode] = useState('Cash')
  const [search, setSearch] = useState('')
  const [items, setItems] = useState([])
  const [submitting, setSubmitting] = useState(false)

  const { data: medData, loading: medLoading } = useFetch(
    () => getMedicines({ search, status: 'Active', limit: 20 }),
    [search]
  )

  const addItem = (med) => {
    if (items.find(i => i.medicine_id === med.id)) return
    setItems(prev => [...prev, { medicine_id: med.id, name: med.name, mrp: med.mrp, quantity_sold: 1 }])
  }

  const removeItem = (id) => setItems(prev => prev.filter(i => i.medicine_id !== id))

  const updateQty = (id, qty) => setItems(prev =>
    prev.map(i => i.medicine_id === id ? { ...i, quantity_sold: Math.max(1, qty) } : i)
  )

  const total = items.reduce((sum, i) => sum + i.mrp * i.quantity_sold, 0)

  const submit = async () => {
    if (!patientName.trim()) return toast.error('Patient name required')
    if (items.length === 0) return toast.error('Add at least one medicine')
    setSubmitting(true)
    try {
      await createSale({
        patient_name: patientName,
        payment_mode: paymentMode,
        items: items.map(i => ({ medicine_id: i.medicine_id, quantity_sold: i.quantity_sold })),
      })
      toast.success('Sale recorded successfully')
      onSuccess()
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to record sale')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div 
    onKeyDown={e => { if (e.key === 'Enter') e.preventDefault() }}
    style={{
      position: 'fixed', inset: 0, background: 'rgba(22,25,58,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 24,
    }}>
      <Card style={{ width: '100%', maxWidth: 640, maxHeight: '90vh', overflow: 'auto', padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 17, fontWeight: 600 }}>Make a Sale</h2>
          <Button variant="ghost" onClick={onClose}>✕</Button>
        </div>

        {/* Patient + Payment */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Patient name</label>
            <input value={patientName} onChange={e => setPatientName(e.target.value)}
              placeholder="Enter patient name"
              style={inputStyle} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Payment mode</label>
            <select value={paymentMode} onChange={e => setPaymentMode(e.target.value)} style={inputStyle}>
              <option>Cash</option>
              <option>Card</option>
              <option>UPI</option>
            </select>
          </div>
        </div>

        {/* Medicine search */}
        <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Search medicines</label>
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Type medicine name..."
          style={{ ...inputStyle, marginBottom: 8 }} />

        {medLoading ? <Spinner /> : (
          <div style={{ maxHeight: 140, overflowY: 'auto', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', marginBottom: 16 }}>
            {(medData?.medicines || []).length === 0
              ? <EmptyState message="No active medicines found" />
              : (medData?.medicines || []).map(med => (
                <div key={med.id} onClick={() => addItem(med)} style={{
                  padding: '8px 12px', cursor: 'pointer', display: 'flex',
                  justifyContent: 'space-between', alignItems: 'center',
                  borderBottom: '1px solid var(--border)',
                  background: items.find(i => i.medicine_id === med.id) ? 'var(--accent-light)' : 'transparent',
                }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{med.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{med.batch_no}</div>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent)' }}>₹{med.mrp}</div>
                </div>
              ))}
          </div>
        )}

        {/* Selected items */}
        {items.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>Selected items</div>
            {items.map(item => (
              <div key={item.medicine_id} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '8px 0', borderBottom: '1px solid var(--border)',
              }}>
                <div style={{ flex: 1, fontSize: 13 }}>{item.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>₹{item.mrp} × </div>
                <input type="number" min={1} value={item.quantity_sold}
                  onChange={e => updateQty(item.medicine_id, parseInt(e.target.value) || 1)}
                  style={{ ...inputStyle, width: 60, textAlign: 'center', padding: '4px 8px' }} />
                <div style={{ fontSize: 13, fontWeight: 600, minWidth: 60, textAlign: 'right' }}>
                  ₹{(item.mrp * item.quantity_sold).toFixed(2)}
                </div>
                <Button variant="ghost" size="sm" onClick={() => removeItem(item.medicine_id)}>✕</Button>
              </div>
            ))}
            <div style={{ textAlign: 'right', marginTop: 10, fontSize: 15, fontWeight: 600 }}>
              Total: ₹{total.toFixed(2)}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} disabled={submitting}>
            {submitting ? 'Recording...' : 'Bill & Save'}
          </Button>
        </div>
      </Card>
    </div>
  )
}

const inputStyle = {
  width: '100%', padding: '8px 12px',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-md)',
  fontSize: 13, background: 'var(--surface)',
  color: 'var(--text-primary)',
}

// ── Dashboard Page ───────────────────────────────────────────────────────────
export default function Dashboard() {
  const [showSaleModal, setShowSaleModal] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const refresh = () => setRefreshKey(k => k + 1)

  const { data: sales, loading: l1 }  = useFetch(getDashboardSalesSummary,    [refreshKey])
  const { data: items, loading: l2 }  = useFetch(getDashboardItemsSold,       [refreshKey])
  const { data: stock, loading: l3 }  = useFetch(getDashboardLowStock,        [refreshKey])
  const { data: orders, loading: l4 } = useFetch(getDashboardPurchaseOrders,  [refreshKey])
  const { data: recent, loading: l5 } = useFetch(getDashboardRecentSales,     [refreshKey])

  const pctUp = sales?.percent_change >= 0
  const pctColor = pctUp ? 'var(--green)' : 'var(--red)'
  const pctLabel = sales ? `${pctUp ? '+' : ''}${sales.percent_change}%` : '—'

  return (
    <div>
      <PageHeader
        title="Pharmacy CRM"
        subtitle="Manage inventory, sales, and purchase orders"
        actions={
          <Button icon={Plus} onClick={() => setShowSaleModal(true)}>
            New Sale
          </Button>
        }
      />

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <SummaryCard
          label="Today's Sales"
          value={sales ? `₹${Number(sales.today_total).toLocaleString('en-IN')}` : '—'}
          badge={pctLabel}
          badgeColor={pctColor}
          icon={ShoppingBag}
          iconBg="var(--green)"
          loading={l1}
        />
        <SummaryCard
          label="Items Sold Today"
          value={items?.items_sold_today ?? '—'}
          badge={items ? `${items.items_sold_today} Orders` : null}
          badgeColor="var(--accent)"
          icon={ShoppingBag}
          iconBg="var(--accent)"
          loading={l2}
        />
        <SummaryCard
          label="Stock Alerts"
          value={stock?.low_stock_count ?? '—'}
          badge={stock?.low_stock_count > 0 ? 'Action Needed' : 'OK'}
          badgeColor={stock?.low_stock_count > 0 ? 'var(--amber)' : 'var(--green)'}
          icon={AlertTriangle}
          iconBg="var(--amber)"
          loading={l3}
        />
        <SummaryCard
          label="Purchase Orders"
          value={orders ? `${orders.pending_count} Pending` : '—'}
          badge={orders ? `${orders.pending_count} Pending` : null}
          badgeColor="var(--purple)"
          icon={ClipboardList}
          iconBg="var(--purple)"
          loading={l4}
        />
      </div>

      {/* Recent sales */}
      <Card style={{ padding: 24 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Recent Sales</h2>
        {l5 ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}><Spinner /></div>
        ) : !recent?.length ? (
          <EmptyState message="No sales recorded yet. Use the New Sale button to record one." />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {recent.map(sale => (
              <div key={sale.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '12px 16px',
                background: 'var(--bg)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: 'var(--radius-md)',
                    background: 'var(--green-light)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <ShoppingBag size={16} color="var(--green)" />
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, fontFamily: 'var(--mono)' }}>
                      {sale.invoice_no}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {sale.patient_name} · {sale.item_count} item{sale.item_count !== 1 ? 's' : ''} · {sale.payment_mode}
                    </div>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>
                    ₹{Number(sale.total).toLocaleString('en-IN')}
                  </span>
                  <StatusBadge status="Completed" />
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {new Date(sale.sale_date).toLocaleDateString('en-IN')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {showSaleModal && (
        <SaleModal onClose={() => setShowSaleModal(false)} onSuccess={refresh} />
      )}
    </div>
  )
}