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
import {
  TrendingUp,
  TrendingDown,
  Speed,
  Psychology,
  CompareArrows,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiClient, MarketDataResponse, HealthResponse } from '../services/api';
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
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Chargement du dashboard...
        </Typography>
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
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Prix des Cryptomonnaies (24h)
          </Typography>
          <Box sx={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={marketData[0]?.data || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  stroke="#b0b0b0"
                />
                <YAxis 
                  tickFormatter={(value) => formatPrice(value)}
                  stroke="#b0b0b0"
                />
                <Tooltip 
                  formatter={(value: number) => [formatPrice(value), 'Prix']}
                  labelFormatter={(label) => new Date(label).toLocaleString()}
                />
                <Line 
                  type="monotone" 
                  dataKey="close" 
                  stroke="#00ff88" 
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Box>
        </CardContent>
      </Card>

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
    </Box>
  );
};

export default Dashboard;