import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import OverviewPage from './pages/OverviewPage'
import ForecastExplorerPage from './pages/ForecastExplorerPage'
import AccuracyPage from './pages/AccuracyPage'
import DataQualityPage from './pages/DataQualityPage'
import AboutPage from './pages/AboutPage'

function App() {
  return (
    <BrowserRouter>
      <Sidebar />
      <div style={{ marginLeft: 'var(--sidebar-width)', minHeight: '100vh' }}>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/explorer" element={<ForecastExplorerPage />} />
          <Route path="/accuracy" element={<AccuracyPage />} />
          <Route path="/data-quality" element={<DataQualityPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
