/**
 * Composant pour afficher les positions historiques
 */

import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Typography,
  Pagination,
  Alert,
  CircularProgress,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { usePositions, useClosePosition } from '../../hooks/useDatabaseApi';
import { Position } from '../../services/databaseApi';

interface PositionsTableProps {
  onViewPosition?: (position: Position) => void;
  refreshTrigger?: number;
}

const PositionsTable: React.FC<PositionsTableProps> = ({
  onViewPosition,
  refreshTrigger = 0,
}) => {
  const [filters, setFilters] = useState({
    symbol: '',
    status: '',
    exchange: '',
    strategy_id: '',
    limit: 50,
    offset: 0,
  });
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const { data: positionsData, loading, error, refetch } = usePositions({
    ...filters,
    offset: filters.offset * filters.limit,
  });

  const closePositionMutation = useClosePosition();

  const positions = positionsData?.positions || [];
  const totalCount = positionsData?.total_count || 0;
  const totalPages = Math.ceil(totalCount / filters.limit);

  const handleFilterChange = (field: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      offset: 0, // Reset to first page when filtering
    }));
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setFilters(prev => ({
      ...prev,
      offset: page - 1,
    }));
  };

  const handleViewPosition = (position: Position) => {
    setSelectedPosition(position);
    setShowDetails(true);
    onViewPosition?.(position);
  };

  const handleClosePosition = async (positionId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir fermer cette position ?')) {
      try {
        await closePositionMutation.mutate(positionId);
        refetch();
      } catch (error) {
        console.error('Erreur lors de la fermeture:', error);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'success';
      case 'closed':
        return 'default';
      case 'partially_closed':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getSideColor = (side: string) => {
    return side === 'long' ? 'success' : 'error';
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'success';
    if (pnl < 0) return 'error';
    return 'default';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Erreur lors du chargement des positions: {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Filtres */}
      <Box display="flex" gap={2} mb={2} alignItems="center">
        <TextField
          label="Symbole"
          value={filters.symbol}
          onChange={(e) => handleFilterChange('symbol', e.target.value)}
          size="small"
          sx={{ minWidth: 120 }}
        />
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Statut</InputLabel>
          <Select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            label="Statut"
          >
            <MenuItem value="">Tous</MenuItem>
            <MenuItem value="open">Ouverte</MenuItem>
            <MenuItem value="closed">Fermée</MenuItem>
            <MenuItem value="partially_closed">Partiellement fermée</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Exchange</InputLabel>
          <Select
            value={filters.exchange}
            onChange={(e) => handleFilterChange('exchange', e.target.value)}
            label="Exchange"
          >
            <MenuItem value="">Tous</MenuItem>
            <MenuItem value="binance">Binance</MenuItem>
            <MenuItem value="coinbase">Coinbase</MenuItem>
            <MenuItem value="kraken">Kraken</MenuItem>
            <MenuItem value="bybit">Bybit</MenuItem>
            <MenuItem value="gateio">Gate.io</MenuItem>
            <MenuItem value="okx">OKX</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="Stratégie ID"
          value={filters.strategy_id}
          onChange={(e) => handleFilterChange('strategy_id', e.target.value)}
          size="small"
          sx={{ minWidth: 150 }}
        />
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Actualiser
        </Button>
      </Box>

      {/* Table */}
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
              <TableCell>Statut</TableCell>
              <TableCell>Exchange</TableCell>
              <TableCell>Ouverte le</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {positions.map((position) => (
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
                    {formatCurrency(position.average_price)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {position.current_price ? formatCurrency(position.current_price) : '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color={getPnLColor(position.unrealized_pnl)}
                    fontWeight="bold"
                  >
                    {formatCurrency(position.unrealized_pnl)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography
                    variant="body2"
                    color={getPnLColor(position.realized_pnl)}
                    fontWeight="bold"
                  >
                    {formatCurrency(position.realized_pnl)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={position.status.toUpperCase()}
                    color={getStatusColor(position.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {position.exchange.toUpperCase()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {format(new Date(position.opened_at), 'dd/MM/yyyy HH:mm', { locale: fr })}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title="Voir les détails">
                      <IconButton
                        size="small"
                        onClick={() => handleViewPosition(position)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    {position.status === 'open' && (
                      <Tooltip title="Fermer la position">
                        <IconButton
                          size="small"
                          onClick={() => handleClosePosition(position.id)}
                          color="error"
                        >
                          <CloseIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {totalPages > 1 && (
        <Box display="flex" justifyContent="center" mt={2}>
          <Pagination
            count={totalPages}
            page={filters.offset + 1}
            onChange={handlePageChange}
            color="primary"
          />
        </Box>
      )}

      {/* Dialog de détails */}
      <Dialog
        open={showDetails}
        onClose={() => setShowDetails(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Détails de la position</DialogTitle>
        <DialogContent>
          {selectedPosition && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedPosition.symbol} - {selectedPosition.side.toUpperCase()}
              </Typography>
              
              {/* PnL Summary */}
              <Box display="flex" gap={2} mb={3}>
                <Box flex={1}>
                  <Typography variant="subtitle2" color="textSecondary">
                    PnL Non Réalisé
                  </Typography>
                  <Typography
                    variant="h6"
                    color={getPnLColor(selectedPosition.unrealized_pnl)}
                    fontWeight="bold"
                  >
                    {formatCurrency(selectedPosition.unrealized_pnl)}
                  </Typography>
                </Box>
                <Box flex={1}>
                  <Typography variant="subtitle2" color="textSecondary">
                    PnL Réalisé
                  </Typography>
                  <Typography
                    variant="h6"
                    color={getPnLColor(selectedPosition.realized_pnl)}
                    fontWeight="bold"
                  >
                    {formatCurrency(selectedPosition.realized_pnl)}
                  </Typography>
                </Box>
                <Box flex={1}>
                  <Typography variant="subtitle2" color="textSecondary">
                    PnL Total
                  </Typography>
                  <Typography
                    variant="h6"
                    color={getPnLColor(selectedPosition.unrealized_pnl + selectedPosition.realized_pnl)}
                    fontWeight="bold"
                  >
                    {formatCurrency(selectedPosition.unrealized_pnl + selectedPosition.realized_pnl)}
                  </Typography>
                </Box>
              </Box>

              <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mt={2}>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Quantité
                  </Typography>
                  <Typography variant="body2">
                    {selectedPosition.quantity.toFixed(8)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Prix Moyen
                  </Typography>
                  <Typography variant="body2">
                    {formatCurrency(selectedPosition.average_price)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Prix Actuel
                  </Typography>
                  <Typography variant="body2">
                    {selectedPosition.current_price ? formatCurrency(selectedPosition.current_price) : '-'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Statut
                  </Typography>
                  <Chip
                    label={selectedPosition.status.toUpperCase()}
                    color={getStatusColor(selectedPosition.status)}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Exchange
                  </Typography>
                  <Typography variant="body2">
                    {selectedPosition.exchange.toUpperCase()}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Stratégie
                  </Typography>
                  <Typography variant="body2">
                    {selectedPosition.strategy_id || '-'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Ouverte le
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(selectedPosition.opened_at), 'dd/MM/yyyy HH:mm:ss', { locale: fr })}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Fermée le
                  </Typography>
                  <Typography variant="body2">
                    {selectedPosition.closed_at 
                      ? format(new Date(selectedPosition.closed_at), 'dd/MM/yyyy HH:mm:ss', { locale: fr })
                      : '-'
                    }
                  </Typography>
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDetails(false)}>
            Fermer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PositionsTable;