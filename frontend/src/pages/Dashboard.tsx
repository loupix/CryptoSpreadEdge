import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
} from '@mui/material';
import Skeleton from '@mui/material/Skeleton';
import {
  TrendingUp,
  TrendingDown,
  Speed,
  Psychology,
  CompareArrows,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import TimeSeriesChart from '../components/Charts/TimeSeriesChart';
import HeatmapChart from '../components/Charts/HeatmapChart';
import AlertsTicker from '../components/Dashboard/AlertsTicker';
import NewsFeed from '../components/Dashboard/NewsFeed';
import { apiClient, MarketDataResponse, HealthResponse } from '../services/api';
import { useAlerts } from '../hooks/useDatabaseApi';
import { wsService } from '../services/websocket';

interface DashboardStats {
  totalSymbols: number;
  activeConnections: number;
  cacheHitRate: number;
  avgResponseTime: number;
  errorRate: number;
}

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [marketData, setMarketData] = useState<MarketDataResponse[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalSymbols: 0,
    activeConnections: 0,
    cacheHitRate: 0,
    avgResponseTime: 0,
    errorRate: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { data: alertsData } = (useAlerts as any)?.({ limit: 5 }) || { data: null };

  useEffect(() => {
    loadDashboardData();
    connectWebSocket();
    
    return () => {
      wsService.disconnect();
    };
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Charger les données de santé
      const healthData = await apiClient.getHealth();
      setHealth(healthData);
      
      // Charger les données de marché pour les principales cryptos
      const symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'];
      const marketDataResponse = await apiClient.getMarketData(symbols, '1h', 24);
      setMarketData(marketDataResponse);
      
      // Calculer les statistiques
      const totalSymbols = marketDataResponse.length;
      const activeConnections = Object.values(healthData.services).filter(s => s.status === 'healthy').length;
      const errorRate = healthData.error_rate;
      
      setStats({
        totalSymbols,
        activeConnections,
        cacheHitRate: 85, // Simulé pour l'instant
        avgResponseTime: 120, // Simulé pour l'instant
        errorRate,
      });
      
    } catch (err) {
      setError('Erreur lors du chargement des données du dashboard');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    wsService.connect();
    
    // Écouter les mises à jour de données de marché
    wsService.subscribeToMarketData((data) => {
      console.log('Market data update:', data);
      // Mettre à jour les données en temps réel
    });
  };

  const renderServiceLatency = () => {
    if (!health) return null;
    const entries = Object.entries(health.services);
    return (
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Latence API par Service
          </Typography>
          <Grid container spacing={2}>
            {entries.map(([name, s]: any) => (
              <Grid item xs={12} sm={6} md={4} key={name}>
                <Card variant="outlined">
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {name}
                      </Typography>
                      <Chip
                        label={`${s.response_time} ms`}
                        color={s.response_time < 150 ? 'success' : s.response_time < 400 ? 'warning' : 'error'}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {s.status}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(price);
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%' }}>
        <Skeleton variant="rectangular" height={56} sx={{ mb: 2 }} />
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <Skeleton variant="rectangular" height={120} />
            </Grid>
          ))}
        </Grid>
        <Skeleton variant="rectangular" height={320} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard CryptoSpreadEdge
      </Typography>
      
      {/* Statut des services */}
      {health && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Statut des Services
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(health.services).map(([service, status]) => (
                <Grid item xs={12} sm={6} md={4} key={service}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={status.status}
                      color={getStatusColor(status.status) as any}
                      size="small"
                    />
                    <Typography variant="body2">
                      {service} ({status.response_time}ms)
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Statistiques principales */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp color="primary" />
                <Typography variant="h6">
                  {stats.totalSymbols}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Symboles surveillés
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Speed color="success" />
                <Typography variant="h6">
                  {stats.activeConnections}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Connexions actives
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Psychology color="info" />
                <Typography variant="h6">
                  {stats.cacheHitRate}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Taux de cache
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CompareArrows color="warning" />
                <Typography variant="h6">
                  {stats.errorRate.toFixed(2)}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Taux d'erreur
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Graphique des prix */}
      <TimeSeriesChart
        title="Prix des Cryptomonnaies (24h)"
        data={(marketData[0]?.data || []).map(p => ({ timestamp: p.timestamp, value: p.close }))}
        height={320}
        variant="area"
        color="#00e19d"
        valueFormatter={(v) => formatPrice(v)}
        timestampFormatter={(t) => new Date(t).toLocaleTimeString()}
      />

      {/* Liste des cryptos */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cryptomonnaies Surveillées
          </Typography>
          <Grid container spacing={2}>
            {marketData.map((crypto) => {
              const latestPrice = crypto.data[crypto.data.length - 1];
              const previousPrice = crypto.data[crypto.data.length - 2];
              const change = latestPrice && previousPrice 
                ? ((latestPrice.close - previousPrice.close) / previousPrice.close) * 100
                : 0;
              
              return (
                <Grid item xs={12} sm={6} md={4} key={crypto.symbol}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="h6">
                          {crypto.symbol}
                        </Typography>
                        <Chip
                          icon={change >= 0 ? <TrendingUp /> : <TrendingDown />}
                          label={`${change >= 0 ? '+' : ''}${change.toFixed(2)}%`}
                          color={change >= 0 ? 'success' : 'error'}
                          size="small"
                        />
                      </Box>
                      <Typography variant="h5" sx={{ mt: 1 }}>
                        {latestPrice ? formatPrice(latestPrice.close) : 'N/A'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Volume: {latestPrice ? latestPrice.volume.toLocaleString() : 'N/A'}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </CardContent>
      </Card>

      {/* Dernières alertes */}
      {alertsData?.alerts?.length ? (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Dernières alertes
            </Typography>
            <Grid container spacing={2}>
              {alertsData.alerts.map((al: any) => (
                <Grid item xs={12} md={6} key={al.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          {al.name}
                        </Typography>
                        <Chip label={al.severity.toUpperCase()} size="small" color={al.severity === 'critical' ? 'error' : al.severity === 'high' ? 'warning' : al.severity === 'medium' ? 'info' : 'success'} />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {al.alert_type} · {al.symbol || '-'} · {al.triggered_count}x
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      ) : null}

      {renderServiceLatency()}

      {/* Heatmap corrélations (mock basique) */}
      <Box sx={{ mt: 3 }}>
        <HeatmapChart
          title="Corrélations (mock)"
          labelsX={['BTC','ETH','BNB','ADA','SOL']}
          labelsY={['BTC','ETH','BNB','ADA','SOL']}
          values={[
            [1, 0.82, 0.55, 0.41, 0.36],
            [0.82, 1, 0.58, 0.39, 0.33],
            [0.55, 0.58, 1, 0.29, 0.25],
            [0.41, 0.39, 0.29, 1, 0.18],
            [0.36, 0.33, 0.25, 0.18, 1],
          ]}
        />
      </Box>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={8}>
          <AlertsTicker items={(alertsData?.alerts || []).slice(0, 8).map((a: any) => ({ id: a.id, text: `${a.severity.toUpperCase()} • ${a.alert_type} • ${a.symbol || '-'}` }))} />
        </Grid>
        <Grid item xs={12} md={4}>
          <NewsFeed items={[{ id: '1', title: 'BTC franchit 70k$ (mock)', source: 'MarketWire', time: 'il y a 2 min' }, { id: '2', title: 'ETH mise à jour réseau (mock)', source: 'CryptoNews', time: 'il y a 10 min' }]} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;