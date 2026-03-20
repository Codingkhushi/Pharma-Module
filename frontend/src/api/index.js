import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

// ── Dashboard ────────────────────────────────────────────────────────────────
export const getDashboardSalesSummary = () => api.get('/api/dashboard/sales-summary')
export const getDashboardItemsSold    = () => api.get('/api/dashboard/items-sold')
export const getDashboardLowStock     = () => api.get('/api/dashboard/low-stock')
export const getDashboardPurchaseOrders = () => api.get('/api/dashboard/purchase-orders')
export const getDashboardRecentSales  = () => api.get('/api/dashboard/recent-sales')

// ── Medicines ────────────────────────────────────────────────────────────────
export const getMedicines = (params) => api.get('/api/medicines', { params })
export const getMedicine  = (id) => api.get(`/api/medicines/${id}`)
export const getInventorySummary = () => api.get('/api/medicines/summary')
export const createMedicine = (data) => api.post('/api/medicines', data)
export const updateMedicine = (id, data) => api.put(`/api/medicines/${id}`, data)
export const updateMedicineStatus = (id, status) =>
  api.patch(`/api/medicines/${id}/status`, { status })

// ── Sales ────────────────────────────────────────────────────────────────────
export const createSale = (data) => api.post('/api/sales', data)
export const getSale    = (id)   => api.get(`/api/sales/${id}`)

// ── Purchase Orders ──────────────────────────────────────────────────────────
export const getPurchaseOrders   = (params) => api.get('/api/purchase-orders', { params })
export const createPurchaseOrder = (data) => api.post('/api/purchase-orders', data)
export const updatePOStatus = (id, status) =>
  api.patch(`/api/purchase-orders/${id}/status`, { status })

// ── Categories ───────────────────────────────────────────────────────────────
export const getCategories = () => api.get('/api/categories')

// ── Reorder Suggestions ──────────────────────────────────────────────────────
export const getReorderSuggestions = () => api.get('/api/dashboard/reorder-suggestions')

export default api