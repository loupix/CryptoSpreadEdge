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
  Slider,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts';
import { apiClient, PredictionResponse, MarketDataResponse } from '../services/api';
import { wsService } from '../services/websocket';

const SYMBOLS = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL'];
const MODEL_TYPES = ['ensemble', 'RandomForest', 'GradientBoosting', 'LSTM', 'CNN'];

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
      id={`prediction-tabpanel-${index}`}
      aria-labelledby={`prediction-tab-${index}`}
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

const Predictions: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [selectedModel, setSelectedModel] = useState('ensemble');
  const [predictionHorizon, setPredictionHorizon] = useState(5);
  const [includeConfidence, setIncludeConfidence] = useState(true);
  const [marketData, setMarketData] = useState<MarketDataResponse | null>(null);
  const [predictions, setPredictions] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  useEffect(() => {
    loadAvailableModels();
    loadPredictions();
    connectWebSocket();
    
    return () => {
      wsService.disconnect();
    };
  }, [selectedSymbol, selectedModel, predictionHorizon]);

  const loadAvailableModels = async () => {
    try {
      const response = await apiClient.getAvailableModels();
      setAvailableModels(response.models);
    } catch (err) {
      console.error('Error loading models:', err);
    }
  };

  const loadPredictions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Charger les données de marché d'abord
      const marketDataResponse = await apiClient.getMarketData([selectedSymbol], '1h', 100);
      if (marketDataResponse.length > 0) {
        setMarketData(marketDataResponse[0]);
        
        // Faire des prédictions
        const predictionsResponse = await apiClient.getPredictions(
          selectedSymbol,
          marketDataResponse[0].data,
          selectedModel,
          predictionHorizon
        );
        setPredictions(predictionsResponse);
      }
    } catch (err) {
      setError('Erreur lors du chargement des prédictions');
      console.error('Predictions error:', err);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    wsService.connect();
    
    wsService.subscribeToPredictions((data) => {
      if (data.symbol === selectedSymbol) {
        setPredictions(data);
      }
    });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(price);
  };

  const formatChange = (change: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const prepareChartData = () => {
    if (!marketData || !predictions) return [];
    
    const historicalData = marketData.data.map(candle => ({
      timestamp: new Date(candle.timestamp).getTime(),
      price: candle.close,
      type: 'historical',
    }));
    
    const predictionData = predictions.predictions.map((pred, index) => ({
      timestamp: new Date(pred.timestamp).getTime(),
      price: pred.predicted_price,
      change: pred.predicted_change,
      confidence: pred.confidence,
      type: 'prediction',
    }));
    
    return [...historicalData, ...predictionData];
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const trainModel = async () => {
    try {
      setLoading(true);
      if (marketData) {
        await apiClient.trainModels(selectedSymbol, marketData.data);
        await loadAvailableModels();
        await loadPredictions();
      }
    } catch (err) {
      setError('Erreur lors de l\'entraînement du modèle');
      console.error('Training error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Prédictions ML
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
              <FormControl fullWidth>
                <InputLabel>Modèle</InputLabel>
                <Select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  {MODEL_TYPES.map((model) => (
                    <MenuItem key={model} value={model}>
                      {model}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Typography gutterBottom>
                Horizon: {predictionHorizon} périodes
              </Typography>
              <Slider
                value={predictionHorizon}
                onChange={(e, value) => setPredictionHorizon(value as number)}
                min={1}
                max={20}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={includeConfidence}
                    onChange={(e) => setIncludeConfidence(e.target.checked)}
                  />
                }
                label="Confiance"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={loadPredictions}
                disabled={loading}
                sx={{ height: '56px' }}
              >
                {loading ? 'Prédiction...' : 'Prédire'}
              </Button>
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              onClick={trainModel}
              disabled={loading}
            >
              Entraîner le Modèle
            </Button>
            <Button
              variant="outlined"
              onClick={loadAvailableModels}
            >
              Actualiser Modèles
            </Button>
          </Box>
        </CardContent>
      </Card>

      {loading && <LinearProgress sx={{ mb: 2 }} />}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {predictions && (
        <Card>
          <CardContent>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Graphique" />
                <Tab label="Prédictions" />
                <Tab label="Modèles" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              <Typography variant="h6" gutterBottom>
                Graphique des Prédictions - {selectedSymbol}
              </Typography>
              <Box sx={{ height: 400 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={prepareChartData()}>
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
                      formatter={(value: number, name: string) => [formatPrice(value), 'Prix']}
                      labelFormatter={(label) => new Date(label).toLocaleString()}
                    />
                    
                    {/* Données historiques */}
                    <Area
                      type="monotone"
                      dataKey="price"
                      stroke="#00ff88"
                      fill="#00ff88"
                      fillOpacity={0.3}
                      connectNulls={false}
                    />
                    
                    {/* Ligne de séparation */}
                    <ReferenceLine 
                      x={marketData?.data[marketData.data.length - 1]?.timestamp} 
                      stroke="#ff6b35" 
                      strokeDasharray="5 5"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              <Typography variant="h6" gutterBottom>
                Détails des Prédictions
              </Typography>
              <TableContainer component={Paper} sx={{ backgroundColor: 'background.paper' }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Période</TableCell>
                      <TableCell>Prix Prédit</TableCell>
                      <TableCell>Changement</TableCell>
                      <TableCell>Confiance</TableCell>
                      <TableCell>Modèle</TableCell>
                      <TableCell>Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {predictions.predictions.map((pred, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography variant="subtitle2" fontWeight="bold">
                            +{index + 1}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" fontWeight="bold">
                            {formatPrice(pred.predicted_price)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={formatChange(pred.predicted_change)}
                            color={pred.predicted_change >= 0 ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={`${(pred.confidence * 100).toFixed(1)}%`}
                            color={getConfidenceColor(pred.confidence) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={pred.model_name} 
                            variant="outlined"
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(pred.timestamp).toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              <Typography variant="h6" gutterBottom>
                Modèles Disponibles
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {availableModels.length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Modèles entraînés
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {predictions.model_used}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Modèle utilisé
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {(predictions.confidence * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Confiance moyenne
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        {predictions.processing_time.toFixed(3)}s
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Temps de calcul
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Liste des Modèles
                </Typography>
                <Grid container spacing={1}>
                  {availableModels.map((model) => (
                    <Grid item key={model}>
                      <Chip 
                        label={model} 
                        color={model === predictions.model_used ? 'primary' : 'default'}
                        variant={model === predictions.model_used ? 'filled' : 'outlined'}
                      />
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </TabPanel>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Predictions;