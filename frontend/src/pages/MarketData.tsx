import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  CandlestickChart,
  Candlestick,
} from 'recharts';
import { apiClient, MarketDataResponse } from '../services/api';
import { wsService } from '../services/websocket';

const SYMBOLS = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'LINK', 'UNI', 'AVAX', 'MATIC'];
const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d'];

const MarketData: React.FC = () => {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['BTC', 'ETH']);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [limit, setLimit] = useState(100);
  const [marketData, setMarketData] = useState<MarketDataResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [realTimeData, setRealTimeData] = useState<Record<string, any>>({});

  useEffect(() => {
    loadMarketData();
    connectWebSocket();
    
    return () => {
      wsService.disconnect();
    };
  }, []);

  const loadMarketData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await apiClient.getMarketData(selectedSymbols, selectedTimeframe, limit);
      setMarketData(data);
    } catch (err) {
      setError('Erreur lors du chargement des données de marché');
      console.error('Market data error:', err);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    wsService.connect();
    
    wsService.subscribeToMarketData((data) => {
      setRealTimeData(prev => ({
        ...prev,
        [data.symbol]: data
      }));
    });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(price);
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
    return volume.toFixed(2);
  };

  const getPriceChange = (data: any[]) => {
    if (data.length < 2) return 0;
    const latest = data[data.length - 1];
    const previous = data[data.length - 2];
    return ((latest.close - previous.close) / previous.close) * 100;
  };

  const prepareChartData = (data: any[]) => {
    return data.map(item => ({
      ...item,
      timestamp: new Date(item.timestamp).getTime(),
    }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Données de Marché
      </Typography>

      {/* Contrôles */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Symboles</InputLabel>
                <Select
                  multiple
                  value={selectedSymbols}
                  onChange={(e) => setSelectedSymbols(e.target.value as string[])}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {SYMBOLS.map((symbol) => (
                    <MenuItem key={symbol} value={symbol}>
                      {symbol}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Timeframe</InputLabel>
                <Select
                  value={selectedTimeframe}
                  onChange={(e) => setSelectedTimeframe(e.target.value)}
                >
                  {TIMEFRAMES.map((tf) => (
                    <MenuItem key={tf} value={tf}>
                      {tf}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Limite"
                type="number"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
                inputProps={{ min: 1, max: 1000 }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={loadMarketData}
                disabled={loading}
                sx={{ height: '56px' }}
              >
                {loading ? 'Chargement...' : 'Actualiser'}
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Graphiques des prix */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {marketData.map((crypto) => {
          const chartData = prepareChartData(crypto.data);
          const priceChange = getPriceChange(crypto.data);
          const latestPrice = crypto.data[crypto.data.length - 1];
          
          return (
            <Grid item xs={12} md={6} key={crypto.symbol}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      {crypto.symbol}
                    </Typography>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="h5">
                        {latestPrice ? formatPrice(latestPrice.close) : 'N/A'}
                      </Typography>
                      <Chip
                        label={`${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)}%`}
                        color={priceChange >= 0 ? 'success' : 'error'}
                        size="small"
                      />
                    </Box>
                  </Box>
                  
                  <Box sx={{ height: 200 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                        <XAxis 
                          dataKey="timestamp"
                          type="number"
                          scale="time"
                          domain={['dataMin', 'dataMax']}
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
            </Grid>
          );
        })}
      </Grid>

      {/* Tableau des données */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Données Détaillées
          </Typography>
          <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Symbole</TableCell>
                  <TableCell>Prix</TableCell>
                  <TableCell>Volume</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Dernière MAJ</TableCell>
                  <TableCell>Cache</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {marketData.map((crypto) => {
                  const latestPrice = crypto.data[crypto.data.length - 1];
                  return (
                    <TableRow key={crypto.symbol}>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {crypto.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {latestPrice ? formatPrice(latestPrice.close) : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {latestPrice ? formatVolume(latestPrice.volume) : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={latestPrice?.source || 'N/A'} 
                          size="small" 
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(crypto.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={crypto.cached ? 'Oui' : 'Non'} 
                          color={crypto.cached ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Données temps réel */}
      {Object.keys(realTimeData).length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Mises à jour Temps Réel
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(realTimeData).map(([symbol, data]) => (
                <Grid item xs={12} sm={6} md={4} key={symbol}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {symbol}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Dernière mise à jour: {new Date(data.timestamp).toLocaleTimeString()}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default MarketData;