import { createBrowserRouter, RouterProvider, createRoutesFromElements, Route } from 'react-router-dom'
import { TransactionsPage } from './pages/Transactions'
import { TransactionCategorizationsPage } from './pages/TransactionCategorizations'
import { CategoriesPage } from './pages/Categories'
import { ChartsPage } from './pages/Charts'
import { Upload } from './pages/Upload'
import { AppLayout } from './components/layout/AppLayout'
import { RouterSafeApiProvider } from './api/RouterSafeApiProvider'
import './App.css'

// Create a simple router configuration
const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <TransactionsPage /> },
      { path: 'transactions', element: <TransactionsPage /> },
      { path: 'categorizations', element: <TransactionCategorizationsPage /> },
      { path: 'categories', element: <CategoriesPage /> },
      { path: 'charts', element: <ChartsPage /> },
      { path: 'upload', element: <Upload /> }
    ]
  }
], {
  // Future flags configuration with type assertion to bypass TypeScript errors
  future: {
    v7_relativeSplatPath: true,
    v7_startTransition: true
  } as any
})

// Wrap the entire app with RouterSafeApiProvider
function App() {
  return (
    <RouterSafeApiProvider>
      <RouterProvider router={router} />
    </RouterSafeApiProvider>
  )
}

export default App
