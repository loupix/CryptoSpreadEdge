/**
 * Interface de trading avancée
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  CardHeader,
  Tabs,
  Tab,
  Chip,
  CircularProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  AccountBalance as AccountBalanceIcon,
  ShowChart as ShowChartIcon,
  History as HistoryIcon,
  Security as SecurityIcon,
  // Speed as SpeedIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { 
  useOrders, 
  usePositions, 
  useTrades,
  useCreateOrder,
  useDeleteOrder,
  useClosePosition,
  usePortfolioSummary 
} from '../../hooks/useDatabaseApi';
import { Order, Position, Trade } from '../../types/domain';
import OpenPositionsCompact from './OpenPositionsCompact';
import OrdersCompact from './OrdersCompact';
import TradesTimeline from './TradesTimeline';

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
      id={`trading-tabpanel-${index}`}
      aria-labelledby={`trading-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const TradingInterface: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [isTradingActive, setIsTradingActive] = useState(false);
  // const [showOrderDialog, setShowOrderDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  
  // État pour le nouvel ordre
  const [newOrder, setNewOrder] = useState({
    symbol: 'BTCUSDT',
    side: 'buy' as 'buy' | 'sell',
    order_type: 'limit' as 'market' | 'limit' | 'stop' | 'stop_limit',
    quantity: 0,
    price: 0,
    stop_price: 0,
  });

  // Hooks pour les données
  const { data: ordersData, loading: ordersLoading, refetch: refetchOrders } = useOrders({
    symbol: selectedSymbol,
    limit: 20,
  });

  const { data: positionsData, loading: positionsLoading, refetch: refetchPositions } = usePositions({
    symbol: selectedSymbol,
    limit: 10,
  });

  const { data: tradesData, loading: tradesLoading, refetch: refetchTrades } = useTrades({
    symbol: selectedSymbol,
    limit: 20,
  });

  const { data: portfolioSummary } = usePortfolioSummary();

  // Mutations
  const createOrderMutation = useCreateOrder();
  // const updateOrderMutation = useUpdateOrder();
  const deleteOrderMutation = useDeleteOrder();
  const closePositionMutation = useClosePosition();

  const orders = ordersData?.orders || [];
  const positions = positionsData?.positions || [];
  const trades = tradesData?.trades || [];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleCreateOrder = async () => {
    try {
      await createOrderMutation.mutate({
        ...newOrder,
        exchange: 'binance', // Par défaut
        source: 'manual',
      });
      // setShowOrderDialog(false);
      setNewOrder({
        symbol: selectedSymbol,
        side: 'buy',
        order_type: 'limit',
        quantity: 0,
        price: 0,
        stop_price: 0,
      });
      refetchOrders();
    } catch (error) {
      console.error('Erreur lors de la création de l\'ordre:', error);
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      await deleteOrderMutation.mutate(orderId);
      refetchOrders();
    } catch (error) {
      console.error('Erreur lors de l\'annulation:', error);
    }
  };

  const handleClosePosition = async (positionId: string) => {
    try {
      await closePositionMutation.mutate(positionId);
      refetchPositions();
    } catch (error) {
      console.error('Erreur lors de la fermeture:', error);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'filled':
        return 'success';
      case 'pending':
        return 'warning';
      case 'open':
        return 'info';
      case 'canceled':
        return 'default';
      case 'rejected':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSideColor = (side: string) => {
    return side === 'buy' ? 'success' : 'error';
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'success';
    if (pnl < 0) return 'error';
    return 'default';
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* En-tête avec contrôles */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h4" gutterBottom>
              Interface de Trading
            </Typography>
            <Box display="flex" gap={2} alignItems="center">
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Symbole</InputLabel>
                <Select
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                  label="Symbole"
                >
                  <MenuItem value="BTCUSDT">BTC/USDT</MenuItem>
                  <MenuItem value="ETHUSDT">ETH/USDT</MenuItem>
                  <MenuItem value="ADAUSDT">ADA/USDT</MenuItem>
                  <MenuItem value="DOTUSDT">DOT/USDT</MenuItem>
                  <MenuItem value="LINKUSDT">LINK/USDT</MenuItem>
                </Select>
              </FormControl>
              <Chip
                label={isTradingActive ? 'ACTIF' : 'INACTIF'}
                color={isTradingActive ? 'success' : 'default'}
                icon={isTradingActive ? <PlayIcon /> : <PauseIcon />}
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box display="flex" gap={1} justifyContent="flex-end">
              <Button
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={() => setIsTradingActive(true)}
                disabled={isTradingActive}
              >
                Démarrer
              </Button>
              <Button
                variant="outlined"
                startIcon={<PauseIcon />}
                onClick={() => setIsTradingActive(false)}
                disabled={!isTradingActive}
              >
                Pause
              </Button>
              <Button
                variant="outlined"
                startIcon={<StopIcon />}
                onClick={() => setIsTradingActive(false)}
                color="error"
              >
                Arrêter
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => {
                  refetchOrders();
                  refetchPositions();
                  refetchTrades();
                }}
              >
                Actualiser
              </Button>
              <Button
                variant="outlined"
                startIcon={<SettingsIcon />}
                onClick={() => setShowSettingsDialog(true)}
              >
                Paramètres
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>

      {/* Résumé du portefeuille */}
      {portfolioSummary && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardHeader
                avatar={<AccountBalanceIcon color="primary" />}
                title="Valeur Totale"
                subheader="Portefeuille"
              />
              <CardContent>
                <Typography variant="h6" color="primary">
                  {formatCurrency(portfolioSummary.total_value || 0)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  PnL: {formatCurrency(portfolioSummary.unrealized_pnl || 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardHeader
                avatar={<TrendingUpIcon color="success" />}
                title="Positions Actives"
                subheader="En cours"
              />
              <CardContent>
                <Typography variant="h6" color="success.main">
                  {portfolioSummary.active_positions || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Trades: {portfolioSummary.total_trades || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardHeader
                avatar={<ShowChartIcon color="info" />}
                title="Taux de Réussite"
                subheader="Performance"
              />
              <CardContent>
                <Typography variant="h6" color="info.main">
                  {((portfolioSummary.win_rate || 0) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Sharpe: {(portfolioSummary.sharpe_ratio || 0).toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardHeader
                avatar={<SecurityIcon color="warning" />}
                title="Drawdown Max"
                subheader="Risque"
              />
              <CardContent>
                <Typography variant="h6" color="warning.main">
                  {((portfolioSummary.max_drawdown || 0) * 100).toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Cash: {formatCurrency(portfolioSummary.cash_balance || 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Onglets principaux */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="trading tabs">
            <Tab label="Ordres" icon={<HistoryIcon />} />
            <Tab label="Positions" icon={<TrendingUpIcon />} />
            <Tab label="Trades" icon={<ShowChartIcon />} />
            <Tab label="Nouvel Ordre" icon={<PlayIcon />} />
          </Tabs>
        </Box>

        <TabPanel value={activeTab} index={0}>
          <Box>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} md={6}>
                <OrdersCompact
                  items={orders.map((o: Order) => ({ id: o.id, symbol: o.symbol, side: o.side as any, type: o.order_type, qty: o.quantity, price: o.price, status: o.status }))}
                  onCancel={handleCancelOrder}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <OpenPositionsCompact
                  items={positions.map((p: Position) => ({
                    id: p.id,
                    symbol: p.symbol,
                    side: (p.side === 'buy' ? 'long' : 'short') as 'long' | 'short',
                    qty: p.quantity,
                    entry: p.entry_price ?? 0,
                    pnl: p.unrealized_pnl ?? 0,
                  }))}
                  onClose={handleClosePosition}
                />
              </Grid>
            </Grid>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Ordres Actifs</Typography>
              <Button
                variant="contained"
                // onClick={() => setShowOrderDialog(true)}
                startIcon={<PlayIcon />}
              >
                Nouvel Ordre
              </Button>
            </Box>
            
            {ordersLoading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Côté</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Quantité</TableCell>
                      <TableCell>Prix</TableCell>
                      <TableCell>Statut</TableCell>
                      <TableCell>Créé</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {orders.map((order: Order) => (
                      <TableRow key={order.id} hover>
                        <TableCell>
                          <Typography variant="body2" noWrap>
                            {order.order_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={order.side.toUpperCase()}
                            color={getSideColor(order.side)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {order.order_type.toUpperCase()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {order.quantity.toFixed(8)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {order.price ? formatCurrency(order.price) : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={order.status.toUpperCase()}
                            color={getStatusColor(order.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {order.created_at
                              ? format(new Date(order.created_at), 'HH:mm:ss', { locale: fr })
                              : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1}>
                            <Tooltip title="Annuler">
                              <IconButton
                                size="small"
                                onClick={() => handleCancelOrder(order.id)}
                                color="error"
                                disabled={order.status === 'filled' || order.status === 'canceled'}
                              >
                                <StopIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Box>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12}>
                <OpenPositionsCompact
                  items={positions.map((p: Position) => ({
                    id: p.id,
                    symbol: p.symbol,
                    side: (p.side === 'buy' ? 'long' : 'short') as 'long' | 'short',
                    qty: p.quantity,
                    entry: p.entry_price ?? 0,
                    pnl: p.unrealized_pnl ?? 0,
                  }))}
                  onClose={handleClosePosition}
                />
              </Grid>
            </Grid>
            <Typography variant="h6" gutterBottom>Positions Ouvertes</Typography>
            
            {positionsLoading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Symbole</TableCell>
                      <TableCell>Côté</TableCell>
                      <TableCell>Quantité</TableCell>
                      <TableCell>Prix Moyen</TableCell>
                      <TableCell>Prix Actuel</TableCell>
                      <TableCell>PnL Non Réalisé</TableCell>
                      <TableCell>PnL Réalisé</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {positions.map((position: Position) => (
                      <TableRow key={position.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {position.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            {position.side === 'long' ? (
                              <TrendingUpIcon color="success" fontSize="small" />
                            ) : (
                              <TrendingDownIcon color="error" fontSize="small" />
                            )}
                            <Chip
                              label={position.side.toUpperCase()}
                              color={getSideColor(position.side)}
                              size="small"
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {position.quantity.toFixed(8)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {position.average_price != null
                              ? formatCurrency(position.average_price)
                              : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {position.current_price != null
                              ? formatCurrency(position.current_price)
                              : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography
                            variant="body2"
                            color={getPnLColor(position.unrealized_pnl ?? 0)}
                            fontWeight="bold"
                          >
                            {position.unrealized_pnl != null
                              ? formatCurrency(position.unrealized_pnl)
                              : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography
                            variant="body2"
                            color={getPnLColor(position.realized_pnl ?? 0)}
                            fontWeight="bold"
                          >
                            {position.realized_pnl != null
                              ? formatCurrency(position.realized_pnl)
                              : '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Fermer la position">
                            <IconButton
                              size="small"
                              onClick={() => handleClosePosition(position.id)}
                              color="error"
                            >
                              <StopIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Box>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12}>
                <TradesTimeline
                  items={trades.map((t: Trade) => ({
                    id: t.id,
                    time: t.timestamp ? format(new Date(t.timestamp), 'HH:mm:ss', { locale: fr }) : '-',
                    symbol: t.symbol,
                    side: t.side as any,
                    price: t.price,
                    qty: t.quantity,
                  }))}
                />
              </Grid>
            </Grid>
            <Typography variant="h6" gutterBottom>Historique des Trades</Typography>
            
            {tradesLoading ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>ID</TableCell>
                      <TableCell>Côté</TableCell>
                      <TableCell>Quantité</TableCell>
                      <TableCell>Prix</TableCell>
                      <TableCell>Fees</TableCell>
                      <TableCell>PnL</TableCell>
                      <TableCell>Exécuté</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {trades.map((trade: Trade) => (
                      <TableRow key={trade.id} hover>
                        <TableCell>
                          <Typography variant="body2" noWrap>
                            {trade.trade_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={trade.side.toUpperCase()}
                            color={getSideColor(trade.side)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {trade.quantity.toFixed(8)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatCurrency(trade.price)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatCurrency(trade.fees ?? 0)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography
                            variant="body2"
                            color={getPnLColor(trade.pnl ?? 0)}
                            fontWeight="bold"
                          >
                            {formatCurrency(trade.pnl ?? 0)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {trade.executed_at
                              ? format(new Date(trade.executed_at), 'dd/MM HH:mm:ss', { locale: fr })
                              : '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Box>
            <Typography variant="h6" gutterBottom>Créer un Nouvel Ordre</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Symbole</InputLabel>
                  <Select
                    value={newOrder.symbol}
                    onChange={(e) => setNewOrder(prev => ({ ...prev, symbol: e.target.value }))}
                    label="Symbole"
                  >
                    <MenuItem value="BTCUSDT">BTC/USDT</MenuItem>
                    <MenuItem value="ETHUSDT">ETH/USDT</MenuItem>
                    <MenuItem value="ADAUSDT">ADA/USDT</MenuItem>
                    <MenuItem value="DOTUSDT">DOT/USDT</MenuItem>
                    <MenuItem value="LINKUSDT">LINK/USDT</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth margin="normal">
                  <InputLabel>Côté</InputLabel>
                  <Select
                    value={newOrder.side}
                    onChange={(e) => setNewOrder(prev => ({ ...prev, side: e.target.value as any }))}
                    label="Côté"
                  >
                    <MenuItem value="buy">Achat</MenuItem>
                    <MenuItem value="sell">Vente</MenuItem>
                  </Select>
                </FormControl>
                
                <FormControl fullWidth margin="normal">
                  <InputLabel>Type d'ordre</InputLabel>
                  <Select
                    value={newOrder.order_type}
                    onChange={(e) => setNewOrder(prev => ({ ...prev, order_type: e.target.value as any }))}
                    label="Type d'ordre"
                  >
                    <MenuItem value="market">Marché</MenuItem>
                    <MenuItem value="limit">Limite</MenuItem>
                    <MenuItem value="stop">Stop</MenuItem>
                    <MenuItem value="stop_limit">Stop Limite</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  label="Quantité"
                  type="number"
                  value={newOrder.quantity}
                  onChange={(e) => setNewOrder(prev => ({ ...prev, quantity: parseFloat(e.target.value) }))}
                  fullWidth
                  margin="normal"
                  inputProps={{ step: "0.00000001" }}
                />
                
                <TextField
                  label="Prix"
                  type="number"
                  value={newOrder.price}
                  onChange={(e) => setNewOrder(prev => ({ ...prev, price: parseFloat(e.target.value) }))}
                  fullWidth
                  margin="normal"
                  inputProps={{ step: "0.01" }}
                  disabled={newOrder.order_type === 'market'}
                />
                
                <TextField
                  label="Prix Stop"
                  type="number"
                  value={newOrder.stop_price}
                  onChange={(e) => setNewOrder(prev => ({ ...prev, stop_price: parseFloat(e.target.value) }))}
                  fullWidth
                  margin="normal"
                  inputProps={{ step: "0.01" }}
                  disabled={!['stop', 'stop_limit'].includes(newOrder.order_type)}
                />
              </Grid>
            </Grid>
            
            <Box display="flex" gap={2} mt={3}>
              <Button
                variant="contained"
                onClick={handleCreateOrder}
                disabled={createOrderMutation.loading}
                startIcon={<PlayIcon />}
              >
                {createOrderMutation.loading ? 'Création...' : 'Créer l\'ordre'}
              </Button>
              <Button
                variant="outlined"
                onClick={() => setNewOrder({
                  symbol: selectedSymbol,
                  side: 'buy',
                  order_type: 'limit',
                  quantity: 0,
                  price: 0,
                  stop_price: 0,
                })}
              >
                Réinitialiser
              </Button>
            </Box>
          </Box>
        </TabPanel>
      </Paper>

      {/* Dialog de paramètres */}
      <Dialog
        open={showSettingsDialog}
        onClose={() => setShowSettingsDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Paramètres de Trading</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={isTradingActive}
                  onChange={(e) => setIsTradingActive(e.target.checked)}
                />
              }
              label="Trading automatique activé"
            />
            
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              Limites de risque
            </Typography>
            
            <TextField
              label="Perte maximale par trade (%)"
              type="number"
              fullWidth
              margin="normal"
              inputProps={{ min: 0, max: 100, step: 0.1 }}
            />
            
            <TextField
              label="Volume maximum par trade (USD)"
              type="number"
              fullWidth
              margin="normal"
              inputProps={{ min: 0, step: 1 }}
            />
            
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              Notifications
            </Typography>
            
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Alertes par email"
            />
            
            <FormControlLabel
              control={<Switch defaultChecked />}
              label="Notifications push"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettingsDialog(false)}>
            Annuler
          </Button>
          <Button onClick={() => setShowSettingsDialog(false)} variant="contained">
            Sauvegarder
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TradingInterface;