import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import QuoteList from './pages/QuoteList'
import QuoteComparison from './pages/QuoteComparison'
import EmailImport from './pages/EmailImport'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<QuoteList />} />
        <Route path="comparison" element={<QuoteComparison />} />
        <Route path="comparison/:partNumber" element={<QuoteComparison />} />
        <Route path="import" element={<EmailImport />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
