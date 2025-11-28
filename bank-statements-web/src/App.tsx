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
import { AppLayout } from './components/layout/AppLayout'
import { RouterSafeApiProvider } from './api/RouterSafeApiProvider'
import './App.css'

// Create a simple router configuration
const router = createBrowserRouter(
  [
    {
      path: '/',
      element: <AppLayout />,
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

// Wrap the entire app with RouterSafeApiProvider
function App() {
  return (
    <RouterSafeApiProvider>
      <RouterProvider router={router} />
    </RouterSafeApiProvider>
  )
}

export default App
