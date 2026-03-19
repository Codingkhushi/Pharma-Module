import { useState } from 'react'
import { Plus, Search, Filter, Package, CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import {
  getMedicines, getInventorySummary, getCategories,
  createMedicine, updateMedicine, updateMedicineStatus,
} from '../api'
import { useFetch } from '../hooks/useFetch'
import { StatusBadge, Button, Card, PageHeader, Spinner, EmptyState } from '../components/ui'
import toast from 'react-hot-toast'

// ── Inventory Summary Cards ──────────────────────────────────────────────────
function OverviewCard({ label, value, icon: Icon, color, loading }) {
  return (
    <div style={{
      flex: 1, minWidth: 0, padding: '16px 20px',
      background: 'var(--surface)', borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
        <Icon size={15} color={color} />
      </div>
      {loading ? <Spinner size={16} /> : (
        <div style={{ fontSize: 22, fontWeight: 600 }}>{value}</div>
      )}
    </div>
  )
}

// ── Medicine Form Modal ──────────────────────────────────────────────────────
function MedicineModal({ medicine, onClose, onSuccess }) {
  const isEdit = !!medicine
  const { data: cats } = useFetch(getCategories, [], [])

  const [form, setForm] = useState({
    name: medicine?.name || '',
    generic_name: medicine?.generic_name || '',
    category_id: medicine?.category?.id || '',
    batch_no: medicine?.batch_no || '',
    expiry_date: medicine?.expiry_date || '',
    quantity: medicine?.quantity ?? '',
    cost_price: medicine?.cost_price || '',
    mrp: medicine?.mrp || '',
    supplier: medicine?.supplier || '',
  })
  const [submitting, setSubmitting] = useState(false)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async () => {
    if (!form.name || !form.batch_no || !form.expiry_date || !form.mrp || !form.cost_price) {
      return toast.error('Fill all required fields')
    }
    setSubmitting(true)
    try {
      const payload = {
        ...form,
        category_id: form.category_id ? parseInt(form.category_id) : null,
        quantity: parseInt(form.quantity) || 0,
        cost_price: parseFloat(form.cost_price),
        mrp: parseFloat(form.mrp),
      }
      if (isEdit) {
        await updateMedicine(medicine.id, payload)
        toast.success('Medicine updated')
      } else {
        await createMedicine(payload)
        toast.success('Medicine added')
      }
      onSuccess()
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save')
    } finally {
      setSubmitting(false)
    }
  }

  const Field = ({ label, children, required }) => (
    <div>
      <label style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
        {label}{required && <span style={{ color: 'var(--red)' }}> *</span>}
      </label>
      {children}
    </div>
  )

  return (
    <div 
    onKeyDown={e => { if (e.key === 'Enter') e.preventDefault() }}
    style={{
      position: 'fixed', inset: 0, background: 'rgba(22,25,58,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: 24,
    }}>
      <Card style={{ width: '100%', maxWidth: 600, maxHeight: '90vh', overflow: 'auto', padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 17, fontWeight: 600 }}>{isEdit ? 'Edit Medicine' : 'Add Medicine'}</h2>
          <Button variant="ghost" onClick={onClose}>✕</Button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <Field label="Medicine name" required>
            <input value={form.name} onChange={e => set('name', e.target.value)}
              placeholder="e.g. Paracetamol 500mg" style={inp} />
          </Field>
          <Field label="Generic name">
            <input value={form.generic_name} onChange={e => set('generic_name', e.target.value)}
              placeholder="e.g. Acetaminophen" style={inp} />
          </Field>
          <Field label="Category">
            <select value={form.category_id} onChange={e => set('category_id', e.target.value)} style={inp}>
              <option value="">Select category</option>
              {(Array.isArray(cats) ? cats : []).map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </Field>
          <Field label="Batch number" required>
            <input value={form.batch_no} onChange={e => set('batch_no', e.target.value)}
              placeholder="e.g. PCM-2024-001" style={inp} />
          </Field>
          <Field label="Expiry date" required>
            <input type="date" value={form.expiry_date} onChange={e => set('expiry_date', e.target.value)} style={inp} />
          </Field>
          <Field label="Quantity" required>
            <input type="number" min={0} value={form.quantity} onChange={e => set('quantity', e.target.value)}
              placeholder="0" style={inp} />
          </Field>
          <Field label="Cost price (₹)" required>
            <input type="number" min={0} step="0.01" value={form.cost_price}
              onChange={e => set('cost_price', e.target.value)} placeholder="0.00" style={inp} />
          </Field>
          <Field label="MRP (₹)" required>
            <input type="number" min={0} step="0.01" value={form.mrp}
              onChange={e => set('mrp', e.target.value)} placeholder="0.00" style={inp} />
          </Field>
          <Field label="Supplier" style={{ gridColumn: 'span 2' }}>
            <input value={form.supplier} onChange={e => set('supplier', e.target.value)}
              placeholder="Supplier name" style={inp} />
          </Field>
        </div>

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 20 }}>
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button onClick={submit} disabled={submitting}>
            {submitting ? 'Saving...' : isEdit ? 'Update Medicine' : 'Add Medicine'}
          </Button>
        </div>
      </Card>
    </div>
  )
}

const inp = {
  width: '100%', padding: '8px 12px',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius-md)',
  fontSize: 13, background: 'var(--surface)',
  color: 'var(--text-primary)',
}

// ── Table header cell ────────────────────────────────────────────────────────
const TH = ({ children }) => (
  <th style={{
    padding: '10px 14px', textAlign: 'left',
    fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.05em',
    borderBottom: '1px solid var(--border)',
    background: 'var(--bg)', whiteSpace: 'nowrap',
  }}>
    {children}
  </th>
)

const TD = ({ children, mono }) => (
  <td style={{
    padding: '12px 14px', fontSize: 13,
    borderBottom: '1px solid var(--border)',
    fontFamily: mono ? 'var(--mono)' : 'var(--font)',
    color: 'var(--text-primary)',
    whiteSpace: 'nowrap',
  }}>
    {children}
  </td>
)

// ── Inventory Page ───────────────────────────────────────────────────────────
export default function Inventory() {
  const [search, setSearch]         = useState('')
  const [statusFilter, setStatus]   = useState('')
  const [categoryFilter, setCat]    = useState('')
  const [page, setPage]             = useState(1)
  const [modal, setModal]           = useState(null) // null | 'add' | medicine object
  const [refreshKey, setRefresh]    = useState(0)
  const refresh = () => { setRefresh(k => k + 1); setPage(1) }

  const { data: summary, loading: sl } = useFetch(getInventorySummary, [refreshKey])
  const { data: cats }                 = useFetch(getCategories, [])
  const { data, loading } = useFetch(
    () => getMedicines({ search, status: statusFilter, category_id: categoryFilter || undefined, page, limit: 20 }),
    [search, statusFilter, categoryFilter, page, refreshKey]
  )

  const medicines = data?.medicines || []
  const total     = data?.total || 0

  const handleStatusChange = async (med, newStatus) => {
    try {
      await updateMedicineStatus(med.id, newStatus)
      toast.success(`Marked as ${newStatus}`)
      refresh()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update status')
    }
  }

  return (
    <div>
      <PageHeader
        title="Pharmacy CRM"
        subtitle="Manage inventory, sales, and purchase orders"
        actions={
          <Button icon={Plus} onClick={() => setModal('add')}>Add Medicine</Button>
        }
      />

      {/* Inventory Overview */}
      <Card style={{ padding: 20, marginBottom: 20 }}>
        <h2 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14 }}>Inventory Overview</h2>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <OverviewCard label="Total Items"   value={summary?.total_items ?? '—'}  icon={Package}       color="var(--accent)"  loading={sl} />
          <OverviewCard label="Active Stock"  value={summary?.active_stock ?? '—'} icon={CheckCircle}   color="var(--green)"   loading={sl} />
          <OverviewCard label="Low Stock"     value={summary?.low_stock ?? '—'}    icon={AlertTriangle} color="var(--amber)"   loading={sl} />
          <OverviewCard label="Total Value"   value={summary ? `₹${Number(summary.total_value).toLocaleString('en-IN')}` : '—'} icon={Package} color="var(--purple)" loading={sl} />
        </div>
      </Card>

      {/* Filters + Table */}
      <Card>
        <div style={{
          display: 'flex', gap: 10, padding: '16px 20px',
          borderBottom: '1px solid var(--border)', flexWrap: 'wrap', alignItems: 'center',
        }}>
          <h2 style={{ fontSize: 14, fontWeight: 600, flex: 1 }}>Complete Inventory</h2>

          {/* Search */}
          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              placeholder="Search medicines..."
              style={{ ...inp, paddingLeft: 32, width: 200 }}
            />
          </div>

          {/* Status filter */}
          <select value={statusFilter} onChange={e => { setStatus(e.target.value); setPage(1) }} style={{ ...inp, width: 140 }}>
            <option value="">All statuses</option>
            <option>Active</option>
            <option>Low Stock</option>
            <option>Expired</option>
            <option>Out of Stock</option>
          </select>

          {/* Category filter */}
          <select value={categoryFilter} onChange={e => { setCat(e.target.value); setPage(1) }} style={{ ...inp, width: 150 }}>
            <option value="">All categories</option>
            {(cats || []).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}><Spinner /></div>
          ) : medicines.length === 0 ? (
            <EmptyState message="No medicines found. Try adjusting filters or add a new medicine." />
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <TH>Medicine Name</TH>
                  <TH>Generic Name</TH>
                  <TH>Category</TH>
                  <TH>Batch No</TH>
                  <TH>Expiry Date</TH>
                  <TH>Quantity</TH>
                  <TH>Cost Price</TH>
                  <TH>MRP</TH>
                  <TH>Supplier</TH>
                  <TH>Status</TH>
                  <TH>Actions</TH>
                </tr>
              </thead>
              <tbody>
                {medicines.map(med => (
                  <tr key={med.id} style={{ background: 'var(--surface)' }}>
                    <TD><span style={{ fontWeight: 500 }}>{med.name}</span></TD>
                    <TD>{med.generic_name || '—'}</TD>
                    <TD>{med.category?.name || '—'}</TD>
                    <TD mono>{med.batch_no}</TD>
                    <TD>{med.expiry_date}</TD>
                    <TD><span style={{ fontWeight: 500 }}>{med.quantity}</span></TD>
                    <TD>₹{Number(med.cost_price).toFixed(2)}</TD>
                    <TD>₹{Number(med.mrp).toFixed(2)}</TD>
                    <TD>{med.supplier || '—'}</TD>
                    <TD><StatusBadge status={med.status} /></TD>
                    <TD>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <Button size="sm" variant="secondary" onClick={() => setModal(med)}>Edit</Button>
                        {med.status !== 'Expired' && (
                          <Button size="sm" variant="danger"
                            onClick={() => handleStatusChange(med, 'Expired')}>
                            Expire
                          </Button>
                        )}
                      </div>
                    </TD>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {total > 20 && (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 20px', borderTop: '1px solid var(--border)',
          }}>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total}
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button size="sm" variant="secondary" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
              <Button size="sm" variant="secondary" disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)}>Next</Button>
            </div>
          </div>
        )}
      </Card>

      {modal && (
        <MedicineModal
          medicine={modal === 'add' ? null : modal}
          onClose={() => setModal(null)}
          onSuccess={refresh}
        />
      )}
    </div>
  )
}