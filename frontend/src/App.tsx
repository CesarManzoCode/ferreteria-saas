import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './hooks/useAuth'
import ProtectedRoute from './components/layout/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import { LoginPage, RegisterPage } from './pages/Auth'
import DashboardPage from './pages/Dashboard'
import QuotesPage from './pages/Quotes'
import QuoteDetailPage from './pages/QuoteDetail'
import NewQuotePage from './pages/NewQuote'
import CatalogsPage from './pages/Catalogs'
import AdminPage from './pages/Admin'
import SubscriptionExpiredPage from './pages/SubscriptionExpired'

export default function App() {
  return (
    <>
      <Toaster position="top-right" toastOptions={{
        style: { fontFamily: 'Inter, system-ui, sans-serif', fontSize: '14px', borderRadius: '8px', border: '0.5px solid #E0DEDA' },
        success: { iconTheme: { primary: '#2E7D52', secondary: '#FFFFFF' } },
        error:   { iconTheme: { primary: '#B83232', secondary: '#FFFFFF' } },
      }} />
      <AuthProvider>
        <Routes>
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/"             element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard"    element={<DashboardPage />} />
              <Route path="/quotes"       element={<QuotesPage />} />
              <Route path="/quotes/new"   element={<NewQuotePage />} />
              <Route path="/quotes/:id"   element={<QuoteDetailPage />} />
              <Route path="/catalogs"     element={<CatalogsPage />} />
              <Route path="/admin"         element={<AdminPage />} />
              <Route path="/expired"       element={<SubscriptionExpiredPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </>
  )
}
