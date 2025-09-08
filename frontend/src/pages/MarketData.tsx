import React, { useState, useEffect, useCallback } from 'react';
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
  // LinearProgress,
  Skeleton,
} from '@mui/material';
import { useDebouncedCallback } from '../hooks/useDebouncedCallback';
// import { ResponsiveContainer } from 'recharts';
// import TimeSeriesChart from '../components/Charts/TimeSeriesChart';
import VolumeBarChart from '../components/Charts/VolumeBarChart';
import OrderBookMini from '../components/Charts/OrderBookMini';
import DepthChart from '../components/Charts/DepthChart';
import CandlestickPro from '../components/Charts/CandlestickPro';
import OrderFlowChart from '../components/Charts/OrderFlowChart';
import Sparkline from '../components/Charts/Sparkline';
import { apiClient } from '../services/api';
import { MarketDataResponse } from '../types/api';
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

  const loadMarketData = useCallback(async () => {
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
  }, [selectedSymbols, selectedTimeframe, limit]);

  const { debounced: debouncedReload } = useDebouncedCallback(loadMarketData, 300);

  const connectWebSocket = useCallback(() => {
    wsService.connect();
    
    wsService.subscribeToMarketData((data) => {
      setRealTimeData(prev => ({
        ...prev,
        [data.symbol]: data
      }));
    });
  }, []);

  useEffect(() => {
    loadMarketData();
    connectWebSocket();
    
    return () => {
      wsService.disconnect();
    };
  }, [selectedSymbols, selectedTimeframe, limit, loadMarketData, connectWebSocket]);

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

  const prepareChartData = React.useCallback((data: any[]) => {
    return data.map(item => ({
      ...item,
      timestamp: new Date(item.timestamp).getTime(),
    }));
  }, []);

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
                  onChange={(e) => { setSelectedSymbols(e.target.value as string[]); debouncedReload(); }}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {SYMBOLS.map((symbol: string) => (
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
                  onChange={(e) => { setSelectedTimeframe(e.target.value); debouncedReload(); }}
                >
                  {TIMEFRAMES.map((tf: string) => (
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
                onChange={(e) => { setLimit(parseInt(e.target.value) || 100); debouncedReload(); }}
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

      {loading && (
        <Box>
          <Skeleton variant="rectangular" height={100} sx={{ mb: 2 }} />
          <Grid container spacing={3} sx={{ mb: 3 }}>
            {Array.from({ length: 2 }).map((_: unknown, i: number) => (
              <Grid item xs={12} md={6} key={i}>
                <Skeleton variant="rectangular" height={360} />
              </Grid>
            ))}
          </Grid>
          <Skeleton variant="rectangular" height={300} />
        </Box>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Graphiques des prix */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {marketData.map((crypto: any) => {
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
                  
                  <Box sx={{ height: 220 }}>
                    <CandlestickPro
                      title={undefined}
                      data={crypto.data.map((p: MarketDataResponse['data'][number]) => ({ timestamp: new Date(p.timestamp).getTime(), open: p.open, high: p.high, low: p.low, close: p.close }))}
                      height={220}
                      showMA
                    />
                  </Box>
                  <Box sx={{ mt: 2 }}>
                    <VolumeBarChart
                      data={chartData.map((p: { timestamp: number; volume: number }) => ({ timestamp: p.timestamp, volume: p.volume }))}
                      height={120}
                      color="#7aa2f7"
                      valueFormatter={(v) => formatVolume(v)}
                      timestampFormatter={(t) => new Date(t as number).toLocaleTimeString()}
                      outlined
                      title="Volume"
                    />
                  </Box>
                  <Box sx={{ mt: 2 }}>
                    <DepthChart
                      bids={(crypto as any).orderbook?.bids || []}
                      asks={(crypto as any).orderbook?.asks || []}
                      height={180}
                      title="Profondeur"
                    />
                  </Box>
                  <Box sx={{ mt: 2 }}>
                    <OrderFlowChart
                      title="Order Flow (mock)"
                      data={chartData.slice(-60).map((p, i) => ({ timestamp: p.timestamp, delta: ((i%2)*2-1) * (p.volume*0.1), cvd: i===0? p.volume : (i%2? 1 : -1)*p.volume + (chartData[i-1]?.volume || 0) }))}
                      height={160}
                    />
                  </Box>
                  <Box sx={{ mt: 2 }}>
                    <OrderBookMini
                      bids={(crypto as any).orderbook?.bids || []}
                      asks={(crypto as any).orderbook?.asks || []}
                      maxLevels={8}
                    />
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
                {marketData.map((crypto: any) => {
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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip 
                          label={crypto.cached ? 'Oui' : 'Non'} 
                          color={crypto.cached ? 'success' : 'default'}
                          size="small"
                        />
                          <Box sx={{ width: 100 }}>
                            <Sparkline
                              data={crypto.data.slice(-20).map((p: MarketDataResponse['data'][number]) => ({ value: p.close }))}
                              height={32}
                              color={(latestPrice && crypto.data.length > 1 && latestPrice.close >= crypto.data[crypto.data.length - 2].close) ? '#22c55e' : '#ef4444'}
                            />
                          </Box>
                        </Box>
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
              {Object.entries(realTimeData).map(([symbol, data]: [string, any]) => (
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