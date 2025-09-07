/**
 * Page pour afficher les données historiques de trading
 */

import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AccountBalance as AccountBalanceIcon,
  Assessment as AssessmentIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import OrdersTable from '../components/HistoricalData/OrdersTable';
import PositionsTable from '../components/HistoricalData/PositionsTable';
import { 
  useTradesSummary, 
  usePortfolioSummary, 
  usePerformanceSummary,
  useSystemHealth 
} from '../hooks/useDatabaseApi';

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
      id={`historical-tabpanel-${index}`}
      aria-labelledby={`historical-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const HistoricalData: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [dateRange, setDateRange] = useState({
    start: format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd'),
  });
  const [selectedSymbol, setSelectedSymbol] = useState('');

  // Hooks pour les données
  const { data: tradesSummary, loading: tradesLoading } = useTradesSummary({
    start_date: dateRange.start,
    end_date: dateRange.end,
    symbol: selectedSymbol || undefined,
  });

  const { data: portfolioSummary, loading: portfolioLoading } = usePortfolioSummary();

  const { data: performanceSummary, loading: performanceLoading } = usePerformanceSummary();

  const { data: systemHealth, loading: healthLoading } = useSystemHealth();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Données Historiques
        </Typography>
        <Typography variant="body1" color="textSecondary" gutterBottom>
          Analyse des performances et historique des opérations de trading
        </Typography>
      </Box>

      {/* Filtres globaux */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField
              label="Date de début"
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              label="Date de fin"
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              label="Symbole"
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              fullWidth
              placeholder="Ex: BTCUSDT"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              variant="contained"
              fullWidth
              onClick={() => window.location.reload()}
            >
              Actualiser
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Résumé des performances */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Résumé des trades */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<AssessmentIcon color="primary" />}
              title="Résumé des Trades"
              subheader="Période sélectionnée"
            />
            <CardContent>
              {tradesLoading ? (
                <CircularProgress size={24} />
              ) : tradesSummary ? (
                <Box>
                  <Typography variant="h6" color="primary">
                    {tradesSummary.total_trades || 0} trades
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Taux de réussite: {formatPercentage(tradesSummary.win_rate || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    PnL total: {formatCurrency(tradesSummary.total_pnl || 0)}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  Aucune donnée disponible
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Résumé du portefeuille */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<AccountBalanceIcon color="success" />}
              title="Portefeuille"
              subheader="État actuel"
            />
            <CardContent>
              {portfolioLoading ? (
                <CircularProgress size={24} />
              ) : portfolioSummary ? (
                <Box>
                  <Typography variant="h6" color="success.main">
                    {formatCurrency(portfolioSummary.total_value || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    PnL non réalisé: {formatCurrency(portfolioSummary.unrealized_pnl || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Positions actives: {portfolioSummary.active_positions || 0}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  Aucune donnée disponible
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performances */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<TrendingUpIcon color="info" />}
              title="Performances"
              subheader="Métriques clés"
            />
            <CardContent>
              {performanceLoading ? (
                <CircularProgress size={24} />
              ) : performanceSummary ? (
                <Box>
                  <Typography variant="h6" color="info.main">
                    Sharpe: {(performanceSummary.sharpe_ratio || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Drawdown max: {formatPercentage(performanceSummary.max_drawdown || 0)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Latence: {(performanceSummary.avg_execution_time || 0).toFixed(0)}ms
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  Aucune donnée disponible
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Santé du système */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardHeader
              avatar={<SettingsIcon color="warning" />}
              title="Système"
              subheader="État de santé"
            />
            <CardContent>
              {healthLoading ? (
                <CircularProgress size={24} />
              ) : systemHealth ? (
                <Box>
                  <Chip
                    label={systemHealth.status || 'Inconnu'}
                    color={systemHealth.status === 'healthy' ? 'success' : 'error'}
                    size="small"
                  />
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                    Connexions: {systemHealth.connections || 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Uptime: {systemHealth.uptime || 'N/A'}
                  </Typography>
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  Aucune donnée disponible
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Onglets */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="historical data tabs">
            <Tab label="Ordres" icon={<HistoryIcon />} />
            <Tab label="Positions" icon={<TrendingUpIcon />} />
            <Tab label="Trades" icon={<AssessmentIcon />} />
            <Tab label="Portefeuille" icon={<AccountBalanceIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <OrdersTable />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <PositionsTable />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Historique des Trades
            </Typography>
            <Alert severity="info">
              Composant des trades en cours de développement...
            </Alert>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Box>
            <Typography variant="h6" gutterBottom>
              Historique du Portefeuille
            </Typography>
            <Alert severity="info">
              Composant du portefeuille en cours de développement...
            </Alert>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default HistoricalData;