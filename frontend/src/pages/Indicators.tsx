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
  Tabs,
  Tab,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  // Area,
  // AreaChart,
} from 'recharts';
import { apiClient } from '../services/api';
import { IndicatorResponse, MarketDataResponse } from '../types/api';
import { wsService } from '../services/websocket';

const SYMBOLS = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'];
const INDICATORS = [
  'SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'MACD', 
  'BB_20', 'STOCH_14', 'VOLUME_20', 'ATR_14', 
  'ICHIMOKU', 'WILLIAMS_R', 'VOLATILITY'
];

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`indicator-tabpanel-${index}`}
      aria-labelledby={`indicator-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Indicators: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['SMA_20', 'RSI_14', 'MACD']);
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [indicators, setIndicators] = useState<IndicatorResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  const loadIndicators = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Charger les données de marché d'abord
      const marketDataResponse = await apiClient.getMarketData([selectedSymbol], '1h', 100);
      if (marketDataResponse.length > 0) {
        setMarketData(marketDataResponse[0]);
        
        // Calculer les indicateurs
        const indicatorsResponse = await apiClient.getIndicators(
          selectedSymbol,
          marketDataResponse[0].data,
          selectedIndicators
        );
        setIndicators(indicatorsResponse);
      }
    } catch (err) {
      setError('Erreur lors du chargement des indicateurs');
      console.error('Indicators error:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, selectedIndicators]);

  const connectWebSocket = useCallback(() => {
    wsService.connect();
    
    wsService.subscribeToIndicators((data) => {
      if (data.symbol === selectedSymbol) {
        setIndicators(data);
      }
    });
  }, [selectedSymbol]);

  useEffect(() => {
    loadIndicators();
    connectWebSocket();
    
    return () => {
      wsService.disconnect();
    };
  }, [selectedSymbol, selectedIndicators, connectWebSocket, loadIndicators]);

  const formatValue = (value: number, indicator: string) => {
    if (indicator.includes('RSI') || indicator.includes('STOCH') || indicator.includes('WILLIAMS')) {
      return value.toFixed(2);
    }
    if (indicator.includes('VOLUME')) {
      return new Intl.NumberFormat('fr-FR').format(value);
    }
    return value.toFixed(4);
  };

  const getIndicatorColor = (indicator: string, value: number) => {
    if (indicator.includes('RSI')) {
      if (value > 70) return '#ff4444';
      if (value < 30) return '#44ff44';
      return '#00ff88';
    }
    if (indicator.includes('MACD')) {
      return value > 0 ? '#44ff44' : '#ff4444';
    }
    return '#00ff88';
  };

  const prepareChartData = () => {
    if (!marketData || !indicators) return [];
    
    return marketData.data.map((candle, index) => {
      const dataPoint: any = {
        timestamp: new Date(candle.timestamp).getTime(),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume,
      };
      
      // Ajouter les indicateurs
      Object.entries(indicators.indicators).forEach(([indicator, values]) => {
        if (values[index]) {
          dataPoint[indicator] = values[index].value;
        }
      });
      
      return dataPoint;
    });
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Indicateurs Techniques
      </Typography>

      {/* Contrôles */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth>
                <InputLabel>Symbole</InputLabel>
                <Select
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                >
                  {SYMBOLS.map((symbol) => (
                    <MenuItem key={symbol} value={symbol}>
                      {symbol}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <FormControl fullWidth>
                <InputLabel>Indicateurs</InputLabel>
                <Select
                  multiple
                  value={selectedIndicators}
                  onChange={(e) => setSelectedIndicators(e.target.value as string[])}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {INDICATORS.map((indicator) => (
                    <MenuItem key={indicator} value={indicator}>
                      {indicator}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <Button
                fullWidth
                variant="contained"
                onClick={loadIndicators}
                disabled={loading}
                sx={{ height: '56px' }}
              >
                {loading ? 'Calcul...' : 'Calculer'}
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

      {indicators && (
        <Card>
          <CardContent>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Graphique" />
                <Tab label="Valeurs" />
                <Tab label="Statistiques" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <Typography variant="h6" gutterBottom>
                Graphique des Indicateurs - {selectedSymbol}
              </Typography>
              <Box sx={{ height: 400 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={prepareChartData()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis 
                      dataKey="timestamp"
                      type="number"
                      scale="time"
                      domain={['dataMin', 'dataMax']}
                      tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                      stroke="#b0b0b0"
                    />
                    <YAxis stroke="#b0b0b0" />
                    <Tooltip 
                      formatter={(value: number, name: string) => [formatValue(value, name), name]}
                      labelFormatter={(label) => new Date(label).toLocaleString()}
                    />
                    
                    {/* Prix */}
                    <Line 
                      type="monotone" 
                      dataKey="close" 
                      stroke="#ffffff" 
                      strokeWidth={2}
                      dot={false}
                    />
                    
                    {/* Indicateurs */}
                    {selectedIndicators.map((indicator, index) => (
                      <Line
                        key={indicator}
                        type="monotone"
                        dataKey={indicator}
                        stroke={getIndicatorColor(indicator, 0)}
                        strokeWidth={1.5}
                        dot={false}
                        connectNulls={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Typography variant="h6" gutterBottom>
                Valeurs des Indicateurs
              </Typography>
              <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Indicateur</TableCell>
                      <TableCell>Valeur Actuelle</TableCell>
                      <TableCell>Confiance</TableCell>
                      <TableCell>Dernière MAJ</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(indicators.indicators).map(([indicator, values]) => {
                      const latestValue = values[values.length - 1];
                      return (
                        <TableRow key={indicator}>
                          <TableCell>
                            <Typography variant="subtitle2" fontWeight="bold">
                              {indicator}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography 
                              variant="body1" 
                              sx={{ color: getIndicatorColor(indicator, latestValue?.value || 0) }}
                            >
                              {latestValue ? formatValue(latestValue.value, indicator) : 'N/A'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={`${(latestValue?.confidence || 0) * 100}%`}
                              color={latestValue?.confidence && latestValue.confidence > 0.7 ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {latestValue ? new Date(latestValue.timestamp).toLocaleString() : 'N/A'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Typography variant="h6" gutterBottom>
                Statistiques des Indicateurs
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {indicators.processing_time.toFixed(3)}s
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Temps de calcul
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {Object.keys(indicators.indicators).length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Indicateurs calculés
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {indicators.cached ? 'Oui' : 'Non'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Données en cache
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {new Date(indicators.timestamp).toLocaleTimeString()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Dernière MAJ
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </TabPanel>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Indicators;