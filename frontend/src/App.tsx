import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import MarketData from './pages/MarketData';
import Indicators from './pages/Indicators';
import Predictions from './pages/Predictions';
import Arbitrage from './pages/Arbitrage';
import HistoricalData from './pages/HistoricalData';
import UserManagement from './pages/UserManagement';
import Performance from './pages/Performance';
import Trading from './pages/Trading';
import ExchangeConfig from './pages/ExchangeConfig';
import Settings from './pages/Settings';

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/market-data" element={<MarketData />} />
          <Route path="/indicators" element={<Indicators />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/arbitrage" element={<Arbitrage />} />
          <Route path="/historical-data" element={<HistoricalData />} />
          <Route path="/users" element={<UserManagement />} />
          <Route path="/performance" element={<Performance />} />
          <Route path="/trading" element={<Trading />} />
          <Route path="/exchanges" element={<ExchangeConfig />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;