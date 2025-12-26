import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { TransactionsPage } from './pages/Transactions'
import { TransactionCategorizationsPage } from './pages/TransactionCategorizations'
import { EnhancementRules } from './pages/EnhancementRules'
import { CategoriesPage } from './pages/Categories'
import { AccountsPage } from './pages/Accounts'
import { ChartsPage } from './pages/Charts'
import { RecurringExpensesPage } from './pages/RecurringExpensesPage'
import { Statements } from './pages/Statements'
import { Upload } from './pages/Upload'
import { SettingsPage } from './pages/Settings'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { AuthCallback } from './pages/AuthCallback'
import { AppLayout } from './components/layout/AppLayout'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { RouterSafeApiProvider } from './api/RouterSafeApiProvider'
import './App.css'

const router = createBrowserRouter(
  [
    {
      path: '/login',
      element: <Login />,
    },
    {
      path: '/register',
      element: <Register />,
    },
    {
      path: '/auth/callback',
      element: <AuthCallback />,
    },
    {
      path: '/',
      element: (
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      ),
      children: [
        { index: true, element: <TransactionsPage /> },
        { path: 'transactions', element: <TransactionsPage /> },
        { path: 'categorizations', element: <TransactionCategorizationsPage /> },
        { path: 'enhancement-rules', element: <EnhancementRules /> },
        { path: 'categories', element: <CategoriesPage /> },
        { path: 'accounts', element: <AccountsPage /> },
        { path: 'charts', element: <ChartsPage /> },
        { path: 'recurring', element: <RecurringExpensesPage /> },
        { path: 'statements', element: <Statements /> },
        { path: 'upload', element: <Upload /> },
        { path: 'settings', element: <SettingsPage /> },
      ],
    },
  ],
  {
    future: {
      v7_relativeSplatPath: true,
      v7_startTransition: true,
    } as Record<string, boolean>,
  }
)

function App() {
  return (
    <RouterSafeApiProvider>
      <RouterProvider router={router} />
    </RouterSafeApiProvider>
  )
}

export default App
