import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import QuoteList from './pages/QuoteList'
import QuoteComparison from './pages/QuoteComparison'
import EmailProcessing from './pages/EmailProcessing'
import Settings from './pages/Settings'
import ReviewQueue from './pages/ReviewQueue'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<QuoteList />} />
        <Route path="comparison" element={<QuoteComparison />} />
        <Route path="comparison/:partNumber" element={<QuoteComparison />} />
        <Route path="email-processing" element={<EmailProcessing />} />
        <Route path="reviews" element={<ReviewQueue />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
