import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: {
          fontFamily: 'var(--font)',
          fontSize: 13,
          borderRadius: 10,
          border: '1px solid var(--border)',
          boxShadow: 'var(--shadow-md)',
        }
      }} />

      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar />

        {/* Main content area */}
        <main style={{
          marginLeft: 'var(--sidebar-w)',
          flex: 1,
          padding: '28px 32px',
          minHeight: '100vh',
          maxWidth: 1400,
        }}>
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="*"          element={<Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}