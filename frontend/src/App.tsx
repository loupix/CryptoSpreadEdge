import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import MarketData from './pages/MarketData';
import Indicators from './pages/Indicators';
import Predictions from './pages/Predictions';
import Arbitrage from './pages/Arbitrage';
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
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;