/**
 * Composant pour afficher les ordres historiques
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
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { useOrders, useDeleteOrder } from '../../hooks/useDatabaseApi';
import { Order } from '../../services/databaseApi';

interface OrdersTableProps {
  onViewOrder?: (order: Order) => void;
  onEditOrder?: (order: Order) => void;
  refreshTrigger?: number;
}

const OrdersTable: React.FC<OrdersTableProps> = ({
  onViewOrder,
  onEditOrder,
  refreshTrigger = 0,
}) => {
  const [filters, setFilters] = useState({
    symbol: '',
    status: '',
    exchange: '',
    limit: 50,
    offset: 0,
  });
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const { data: ordersData, loading, error, refetch } = useOrders({
    ...filters,
    offset: filters.offset * filters.limit,
  });

  const deleteOrderMutation = useDeleteOrder();

  const orders = ordersData?.orders || [];
  const totalCount = ordersData?.total_count || 0;
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

  const handleViewOrder = (order: Order) => {
    setSelectedOrder(order);
    setShowDetails(true);
    onViewOrder?.(order);
  };

  const handleEditOrder = (order: Order) => {
    onEditOrder?.(order);
  };

  const handleDeleteOrder = async (orderId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cet ordre ?')) {
      try {
        await deleteOrderMutation.mutate(orderId);
        refetch();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
      }
    }
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
        Erreur lors du chargement des ordres: {error}
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
            <MenuItem value="pending">En attente</MenuItem>
            <MenuItem value="open">Ouvert</MenuItem>
            <MenuItem value="filled">Rempli</MenuItem>
            <MenuItem value="partially_filled">Partiellement rempli</MenuItem>
            <MenuItem value="canceled">Annulé</MenuItem>
            <MenuItem value="rejected">Rejeté</MenuItem>
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
              <TableCell>ID</TableCell>
              <TableCell>Symbole</TableCell>
              <TableCell>Côté</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Quantité</TableCell>
              <TableCell>Prix</TableCell>
              <TableCell>Statut</TableCell>
              <TableCell>Exchange</TableCell>
              <TableCell>Créé le</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {orders.map((order) => (
              <TableRow key={order.id} hover>
                <TableCell>
                  <Typography variant="body2" noWrap>
                    {order.order_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {order.symbol}
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
                    {order.price ? order.price.toFixed(2) : '-'}
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
                    {order.exchange.toUpperCase()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {format(new Date(order.created_at), 'dd/MM/yyyy HH:mm', { locale: fr })}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title="Voir les détails">
                      <IconButton
                        size="small"
                        onClick={() => handleViewOrder(order)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Modifier">
                      <IconButton
                        size="small"
                        onClick={() => handleEditOrder(order)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Supprimer">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteOrder(order.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
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
        <DialogTitle>Détails de l'ordre</DialogTitle>
        <DialogContent>
          {selectedOrder && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedOrder.symbol} - {selectedOrder.order_id}
              </Typography>
              <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mt={2}>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Côté
                  </Typography>
                  <Chip
                    label={selectedOrder.side.toUpperCase()}
                    color={getSideColor(selectedOrder.side)}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Type
                  </Typography>
                  <Typography variant="body2">
                    {selectedOrder.order_type.toUpperCase()}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Quantité
                  </Typography>
                  <Typography variant="body2">
                    {selectedOrder.quantity.toFixed(8)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Prix
                  </Typography>
                  <Typography variant="body2">
                    {selectedOrder.price ? selectedOrder.price.toFixed(2) : '-'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Quantité remplie
                  </Typography>
                  <Typography variant="body2">
                    {selectedOrder.filled_quantity.toFixed(8)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Prix moyen
                  </Typography>
                  <Typography variant="body2">
                    {selectedOrder.average_price.toFixed(2)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Statut
                  </Typography>
                  <Chip
                    label={selectedOrder.status.toUpperCase()}
                    color={getStatusColor(selectedOrder.status)}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Exchange
                  </Typography>
                  <Typography variant="body2">
                    {selectedOrder.exchange.toUpperCase()}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Créé le
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(selectedOrder.created_at), 'dd/MM/yyyy HH:mm:ss', { locale: fr })}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Modifié le
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(selectedOrder.updated_at), 'dd/MM/yyyy HH:mm:ss', { locale: fr })}
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

export default OrdersTable;