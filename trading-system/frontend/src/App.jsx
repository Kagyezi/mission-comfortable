import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard     from './pages/Dashboard'
import BotManagement from './pages/BotManagement'
import TradeLog      from './pages/TradeLog'
import Charts        from './pages/Charts'
import RiskSettings  from './pages/RiskSettings'
import SystemMonitor from './pages/SystemMonitor'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/"       element={<Dashboard />}     />
            <Route path="/bots"   element={<BotManagement />} />
            <Route path="/trades" element={<TradeLog />}      />
            <Route path="/charts" element={<Charts />}        />
            <Route path="/risk"   element={<RiskSettings />}  />
            <Route path="/system" element={<SystemMonitor />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
