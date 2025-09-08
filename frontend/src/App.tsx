import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout/Layout';
import React from 'react';
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const MarketData = React.lazy(() => import('./pages/MarketData'));
const Indicators = React.lazy(() => import('./pages/Indicators'));
const Predictions = React.lazy(() => import('./pages/Predictions'));
const Arbitrage = React.lazy(() => import('./pages/Arbitrage'));
const HistoricalData = React.lazy(() => import('./pages/HistoricalData'));
const UserManagement = React.lazy(() => import('./pages/UserManagement'));
const Performance = React.lazy(() => import('./pages/Performance'));
const Trading = React.lazy(() => import('./pages/Trading'));
const ExchangeConfig = React.lazy(() => import('./pages/ExchangeConfig'));
const Settings = React.lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <React.Suspense fallback={<div />}> 
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
        </React.Suspense>
      </Layout>
    </Box>
  );
}

export default App;