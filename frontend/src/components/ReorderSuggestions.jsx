import { AlertTriangle, CheckCircle, ChevronDown, ChevronUp, Clock, PackageX, Plus, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'
import { createPurchaseOrder, getReorderSuggestions } from '../api'
import { useFetch } from '../hooks/useFetch'
import { Button, Card, Spinner } from './ui'

// ── Reason tag ───────────────────────────────────────────────────────────────
const REASON_STYLES = {
  out_of_stock:   { icon: PackageX,      bg: 'var(--red-light)',    color: 'var(--red)',    label: 'Out of Stock' },
  low_stock:      { icon: AlertTriangle, bg: 'var(--amber-light)',  color: 'var(--amber)',  label: 'Low Stock'    },
  expiring_soon:  { icon: Clock,         bg: 'var(--purple-light)', color: 'var(--purple)', label: 'Expiring Soon'},
}

function ReasonTag({ type }) {
  const s = REASON_STYLES[type] || REASON_STYLES.low_stock
  const Icon = s.icon
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 999,
      fontSize: 11, fontWeight: 500,
      background: s.bg, color: s.color,
    }}>
      <Icon size={10} />
      {s.label}
    </span>
  )
}

// ── Supplier Group ───────────────────────────────────────────────────────────
function SupplierGroup({ group, onCreatePO }) {
  const [expanded, setExpanded] = useState(true)
  const [creating, setCreating] = useState(false)

  const handleCreatePO = async () => {
    setCreating(true)
    try {
      await onCreatePO(group.supplier)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
      marginBottom: 10,
    }}>
      {/* Supplier header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '10px 14px',
        background: 'var(--bg)',
        cursor: 'pointer',
      }} onClick={() => setExpanded(e => !e)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: '50%',
            background: 'var(--accent-light)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 700, color: 'var(--accent)',
          }}>
            {group.supplier.charAt(0).toUpperCase()}
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{group.supplier}</div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {group.items.length} medicine{group.items.length !== 1 ? 's' : ''} need attention
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {group.po_exists ? (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              fontSize: 11, fontWeight: 500,
              color: 'var(--amber)', background: 'var(--amber-light)',
              padding: '3px 8px', borderRadius: 999,
            }}>
              <CheckCircle size={10} />
              PO Pending
            </span>
          ) : (
            <Button
              size="sm"
              icon={Plus}
              onClick={e => { e.stopPropagation(); handleCreatePO() }}
              disabled={creating}
            >
              {creating ? 'Creating...' : 'New PO'}
            </Button>
          )}
          {expanded ? <ChevronUp size={14} color="var(--text-muted)" /> : <ChevronDown size={14} color="var(--text-muted)" />}
        </div>
      </div>

      {/* Medicine rows */}
      {expanded && (
        <div>
          {group.items.map((item, idx) => (
            <div key={item.id} style={{
              display: 'flex', alignItems: 'flex-start',
              justifyContent: 'space-between',
              padding: '10px 14px',
              borderTop: '1px solid var(--border)',
              background: 'var(--surface)',
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>{item.name}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  {item.reasons.map(r => (
                    <ReasonTag key={r.type} type={r.type} />
                  ))}
                </div>
              </div>
              <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 12 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{item.quantity} units</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  Expires {item.expiry_date}
                </div>
                {/* Reason detail text */}
                {item.reasons.map(r => (
                  <div key={r.type} style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
                    {r.detail}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main Component ───────────────────────────────────────────────────────────
export default function ReorderSuggestions() {
  const { data, loading, refetch } = useFetch(getReorderSuggestions, [])

  const handleCreatePO = async (supplierName) => {
    try {
      await createPurchaseOrder({ supplier_name: supplierName })
      toast.success(`Purchase order created for ${supplierName}`)
      refetch()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create purchase order')
    }
  }

  const hasItems = data?.total_items > 0

  return (
    <Card style={{ padding: 24, marginBottom: 24 }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between', marginBottom: 16,
      }}>
        <div>
          <h2 style={{ fontSize: 15, fontWeight: 600 }}>Reorder Suggestions</h2>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
            Auto-detected based on stock levels and expiry dates
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {hasItems && (
            <span style={{
              fontSize: 12, fontWeight: 600,
              background: 'var(--red-light)', color: 'var(--red)',
              padding: '3px 10px', borderRadius: 999,
            }}>
              {data.total_items} item{data.total_items !== 1 ? 's' : ''} need attention
            </span>
          )}
          <Button variant="ghost" size="sm" icon={RefreshCw} onClick={refetch}>
            Refresh
          </Button>
        </div>
      </div>

      {/* Detection rules explanation */}
      <div style={{
        display: 'flex', gap: 8, flexWrap: 'wrap',
        padding: '8px 12px',
        background: 'var(--bg)',
        borderRadius: 'var(--radius-md)',
        marginBottom: 16,
        border: '1px solid var(--border)',
      }}>
        <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Flags medicines that are:</span>
        <ReasonTag type="out_of_stock" />
        <ReasonTag type="low_stock" />
        <ReasonTag type="expiring_soon" />
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>(expiring within 30 days)</span>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
          <Spinner />
        </div>
      ) : !hasItems ? (
        <div style={{
          padding: '32px 24px', textAlign: 'center',
          background: 'var(--green-light)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid #bbf7d0',
        }}>
          <CheckCircle size={28} color="var(--green)" style={{ marginBottom: 8 }} />
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--green)', marginBottom: 4 }}>
            All medicines are well-stocked
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            No reorders needed right now. Check back after the next expiry scan.
          </div>
        </div>
      ) : (
        <div>
          {data.groups.map(group => (
            <SupplierGroup
              key={group.supplier}
              group={group}
              onCreatePO={handleCreatePO}
            />
          ))}
        </div>
      )}
    </Card>
  )
}