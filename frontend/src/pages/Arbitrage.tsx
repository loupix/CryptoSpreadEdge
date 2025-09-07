import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
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
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Tabs,
  Tab,
  Badge,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  CompareArrows,
  Speed,
  AttachMoney,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { apiClient } from '../services/api';
import { wsService } from '../services/websocket';

const SYMBOLS = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'];
const EXCHANGES = ['binance', 'okx', 'bybit', 'gateio', 'kraken'];

interface ArbitrageOpportunity {
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  spread: number;
  spreadPercent: number;
  profit: number;
  volume: number;
  timestamp: string;
  confidence: number;
}

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
      id={`arbitrage-tabpanel-${index}`}
      aria-labelledby={`arbitrage-tab-${index}`}
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

const Arbitrage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [minSpread, setMinSpread] = useState(0.5);
  const [minVolume, setMinVolume] = useState(1000);
  const [opportunities, setOpportunities] = useState<ArbitrageOpportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [realTimeOpportunities, setRealTimeOpportunities] = useState<ArbitrageOpportunity[]>([]);

  useEffect(() => {
    loadArbitrageData();
    connectWebSocket();
    
    return () => {
      wsService.disconnect();
    };
  }, [selectedSymbol, minSpread, minVolume]);

  const loadArbitrageData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Simuler des opportunités d'arbitrage pour l'instant
      // Dans un vrai système, cela viendrait de l'API d'arbitrage
      const mockOpportunities: ArbitrageOpportunity[] = [
        {
          symbol: 'BTC',
          buyExchange: 'binance',
          sellExchange: 'okx',
          buyPrice: 45000,
          sellPrice: 45150,
          spread: 150,
          spreadPercent: 0.33,
          profit: 150,
          volume: 5000,
          timestamp: new Date().toISOString(),
          confidence: 0.85,
        },
        {
          symbol: 'ETH',
          buyExchange: 'bybit',
          sellExchange: 'gateio',
          buyPrice: 3200,
          sellPrice: 3220,
          spread: 20,
          spreadPercent: 0.63,
          profit: 20,
          volume: 2000,
          timestamp: new Date().toISOString(),
          confidence: 0.72,
        },
        {
          symbol: 'BNB',
          buyExchange: 'kraken',
          sellExchange: 'binance',
          buyPrice: 350,
          sellPrice: 352,
          spread: 2,
          spreadPercent: 0.57,
          profit: 2,
          volume: 1000,
          timestamp: new Date().toISOString(),
          confidence: 0.68,
        },
      ];
      
      setOpportunities(mockOpportunities);
    } catch (err) {
      setError('Erreur lors du chargement des opportunités d\'arbitrage');
      console.error('Arbitrage error:', err);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    wsService.connect();
    
    wsService.subscribeToArbitrage((data) => {
      setRealTimeOpportunities(prev => [...prev, data]);
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
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
    return volume.toFixed(2);
  };

  const getSpreadColor = (spread: number) => {
    if (spread >= 1) return 'success';
    if (spread >= 0.5) return 'warning';
    return 'error';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const prepareChartData = () => {
    return opportunities.map(opp => ({
      timestamp: new Date(opp.timestamp).getTime(),
      spread: opp.spreadPercent,
      profit: opp.profit,
      confidence: opp.confidence * 100,
    }));
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const executeArbitrage = (opportunity: ArbitrageOpportunity) => {
    // Simuler l'exécution d'arbitrage
    console.log('Exécution arbitrage:', opportunity);
    // Dans un vrai système, cela déclencherait l'exécution via l'API
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Opportunités d'Arbitrage
      </Typography>

      {/* Contrôles */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
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
            
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Spread minimum (%)"
                type="number"
                value={minSpread}
                onChange={(e) => setMinSpread(parseFloat(e.target.value) || 0)}
                inputProps={{ min: 0, max: 10, step: 0.1 }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Volume minimum"
                type="number"
                value={minVolume}
                onChange={(e) => setMinVolume(parseFloat(e.target.value) || 0)}
                inputProps={{ min: 0 }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={loadArbitrageData}
                disabled={loading}
                sx={{ height: '56px' }}
              >
                {loading ? 'Recherche...' : 'Rechercher'}
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

      {/* Statistiques rapides */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CompareArrows color="primary" />
                <Typography variant="h6">
                  {opportunities.length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Opportunités trouvées
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AttachMoney color="success" />
                <Typography variant="h6">
                  {formatPrice(opportunities.reduce((sum, opp) => sum + opp.profit, 0))}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Profit total potentiel
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TrendingUp color="info" />
                <Typography variant="h6">
                  {opportunities.length > 0 ? (opportunities.reduce((sum, opp) => sum + opp.spreadPercent, 0) / opportunities.length).toFixed(2) : 0}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Spread moyen
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Speed color="warning" />
                <Typography variant="h6">
                  {realTimeOpportunities.length}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Nouvelles opportunités
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Liste des Opportunités" />
              <Tab label="Graphique des Spreads" />
              <Tab label="Temps Réel" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Typography variant="h6" gutterBottom>
              Opportunités d'Arbitrage - {selectedSymbol}
            </Typography>
            <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbole</TableCell>
                    <TableCell>Acheter</TableCell>
                    <TableCell>Vendre</TableCell>
                    <TableCell>Spread</TableCell>
                    <TableCell>Profit</TableCell>
                    <TableCell>Volume</TableCell>
                    <TableCell>Confiance</TableCell>
                    <TableCell>Action</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {opportunities
                    .filter(opp => opp.symbol === selectedSymbol)
                    .filter(opp => opp.spreadPercent >= minSpread)
                    .filter(opp => opp.volume >= minVolume)
                    .map((opportunity, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {opportunity.symbol}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="bold">
                            {opportunity.buyExchange}
                          </Typography>
                          <Typography variant="body2">
                            {formatPrice(opportunity.buyPrice)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="bold">
                            {opportunity.sellExchange}
                          </Typography>
                          <Typography variant="body2">
                            {formatPrice(opportunity.sellPrice)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${opportunity.spreadPercent.toFixed(2)}%`}
                          color={getSpreadColor(opportunity.spreadPercent) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body1" fontWeight="bold" color="success.main">
                          {formatPrice(opportunity.profit)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {formatVolume(opportunity.volume)}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${(opportunity.confidence * 100).toFixed(0)}%`}
                          color={getConfidenceColor(opportunity.confidence) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => executeArbitrage(opportunity)}
                          disabled={opportunity.confidence < 0.7}
                        >
                          Exécuter
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" gutterBottom>
              Évolution des Spreads
            </Typography>
            <Box sx={{ height: 300 }}>
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
                  <YAxis 
                    tickFormatter={(value) => `${value}%`}
                    stroke="#b0b0b0"
                  />
                  <Tooltip 
                    formatter={(value: number, name: string) => [
                      name === 'spread' ? `${value}%` : formatPrice(value),
                      name === 'spread' ? 'Spread' : name === 'profit' ? 'Profit' : 'Confiance'
                    ]}
                    labelFormatter={(label) => new Date(label).toLocaleString()}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="spread" 
                    stroke="#00ff88" 
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="profit" 
                    stroke="#ff6b35" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" gutterBottom>
              Opportunités Temps Réel
            </Typography>
            {realTimeOpportunities.length === 0 ? (
              <Alert severity="info">
                Aucune nouvelle opportunité en temps réel pour le moment.
              </Alert>
            ) : (
              <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbole</TableCell>
                      <TableCell>Spread</TableCell>
                      <TableCell>Profit</TableCell>
                      <TableCell>Confiance</TableCell>
                      <TableCell>Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {realTimeOpportunities.map((opportunity, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Badge color="primary" variant="dot">
                            <Typography variant="subtitle2" fontWeight="bold">
                              {opportunity.symbol}
                            </Typography>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={`${opportunity.spreadPercent.toFixed(2)}%`}
                            color={getSpreadColor(opportunity.spreadPercent) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" fontWeight="bold" color="success.main">
                            {formatPrice(opportunity.profit)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={`${(opportunity.confidence * 100).toFixed(0)}%`}
                            color={getConfidenceColor(opportunity.confidence) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(opportunity.timestamp).toLocaleTimeString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Arbitrage;