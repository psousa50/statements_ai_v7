import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { TransactionsPage } from './pages/Transactions'
import { Upload } from './pages/Upload'
import { AppLayout } from './components/layout/AppLayout'
import './App.css'

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<TransactionsPage />} />
          <Route path="/transactions" element={<TransactionsPage />} />
          <Route path="/upload" element={<Upload />} />
        </Routes>
      </AppLayout>
    </Router>
  )
}

export default App
