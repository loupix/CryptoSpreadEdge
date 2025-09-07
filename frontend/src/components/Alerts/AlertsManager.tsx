/**
 * Composant pour la gestion des alertes et notifications
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
  Switch,
  FormControlLabel,
  Slider,
  Card,
  CardContent,
  CardHeader,
  Grid,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Notifications as NotificationsIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { useAlerts, useCreateAlert, useUpdateAlert, useDeleteAlert } from '../../hooks/useDatabaseApi';
import { Alert as AlertType } from '../../services/databaseApi';

interface AlertsManagerProps {
  refreshTrigger?: number;
}

const AlertsManager: React.FC<AlertsManagerProps> = ({
  refreshTrigger = 0,
}) => {
  const [filters, setFilters] = useState({
    alert_type: '',
    severity: '',
    is_active: '',
    limit: 50,
    offset: 0,
  });
  const [selectedAlert, setSelectedAlert] = useState<AlertType | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [newAlert, setNewAlert] = useState<Partial<AlertType>>({
    name: '',
    alert_type: 'price',
    severity: 'medium',
    condition: {},
    is_active: true,
    cooldown_seconds: 300,
  });

  const { data: alertsData, loading, error, refetch } = useAlerts({
    ...filters,
    offset: filters.offset * filters.limit,
  });

  const createAlertMutation = useCreateAlert();
  const updateAlertMutation = useUpdateAlert();
  const deleteAlertMutation = useDeleteAlert();

  const alerts = alertsData?.alerts || [];
  const totalCount = alertsData?.total_count || 0;
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

  const handleViewAlert = (alert: AlertType) => {
    setSelectedAlert(alert);
    setShowDetails(true);
  };

  const handleEditAlert = (alert: AlertType) => {
    setSelectedAlert(alert);
    setShowEditDialog(true);
  };

  const handleDeleteAlert = async (alertId: string) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer cette alerte ?')) {
      try {
        await deleteAlertMutation.mutate(alertId);
        refetch();
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
      }
    }
  };

  const handleCreateAlert = async () => {
    try {
      await createAlertMutation.mutate(newAlert);
      setShowCreateDialog(false);
      setNewAlert({
        name: '',
        alert_type: 'price',
        severity: 'medium',
        condition: {},
        is_active: true,
        cooldown_seconds: 300,
      });
      refetch();
    } catch (error) {
      console.error('Erreur lors de la création:', error);
    }
  };

  const handleUpdateAlert = async () => {
    if (selectedAlert) {
      try {
        await updateAlertMutation.mutate({
          id: selectedAlert.id,
          data: selectedAlert,
        });
        setShowEditDialog(false);
        setSelectedAlert(null);
        refetch();
      } catch (error) {
        console.error('Erreur lors de la mise à jour:', error);
      }
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <ErrorIcon />;
      case 'high':
        return <WarningIcon />;
      case 'medium':
        return <InfoIcon />;
      case 'low':
        return <CheckCircleIcon />;
      default:
        return <NotificationsIcon />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'price':
        return 'primary';
      case 'volume':
        return 'secondary';
      case 'risk':
        return 'error';
      case 'system':
        return 'info';
      case 'trading':
        return 'success';
      case 'performance':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'price':
        return 'Prix';
      case 'volume':
        return 'Volume';
      case 'risk':
        return 'Risque';
      case 'system':
        return 'Système';
      case 'trading':
        return 'Trading';
      case 'performance':
        return 'Performance';
      default:
        return type;
    }
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
        Erreur lors du chargement des alertes: {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Filtres */}
      <Box display="flex" gap={2} mb={2} alignItems="center">
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Type</InputLabel>
          <Select
            value={filters.alert_type}
            onChange={(e) => handleFilterChange('alert_type', e.target.value)}
            label="Type"
          >
            <MenuItem value="">Tous</MenuItem>
            <MenuItem value="price">Prix</MenuItem>
            <MenuItem value="volume">Volume</MenuItem>
            <MenuItem value="risk">Risque</MenuItem>
            <MenuItem value="system">Système</MenuItem>
            <MenuItem value="trading">Trading</MenuItem>
            <MenuItem value="performance">Performance</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Sévérité</InputLabel>
          <Select
            value={filters.severity}
            onChange={(e) => handleFilterChange('severity', e.target.value)}
            label="Sévérité"
          >
            <MenuItem value="">Toutes</MenuItem>
            <MenuItem value="low">Faible</MenuItem>
            <MenuItem value="medium">Moyenne</MenuItem>
            <MenuItem value="high">Élevée</MenuItem>
            <MenuItem value="critical">Critique</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Statut</InputLabel>
          <Select
            value={filters.is_active}
            onChange={(e) => handleFilterChange('is_active', e.target.value)}
            label="Statut"
          >
            <MenuItem value="">Tous</MenuItem>
            <MenuItem value="true">Actives</MenuItem>
            <MenuItem value="false">Inactives</MenuItem>
          </Select>
        </FormControl>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Actualiser
        </Button>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setShowCreateDialog(true)}
        >
          Nouvelle alerte
        </Button>
      </Box>

      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nom</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Sévérité</TableCell>
              <TableCell>Symbole</TableCell>
              <TableCell>Condition</TableCell>
              <TableCell>Statut</TableCell>
              <TableCell>Déclenchée</TableCell>
              <TableCell>Créée le</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow key={alert.id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {alert.name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={getTypeLabel(alert.alert_type)}
                    color={getTypeColor(alert.alert_type)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getSeverityIcon(alert.severity)}
                    <Chip
                      label={alert.severity.toUpperCase()}
                      color={getSeverityColor(alert.severity)}
                      size="small"
                    />
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {alert.symbol || '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" noWrap>
                    {JSON.stringify(alert.condition).substring(0, 50)}...
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={alert.is_active ? 'ACTIVE' : 'INACTIVE'}
                    color={alert.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {alert.triggered_count} fois
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {format(new Date(alert.created_at), 'dd/MM/yyyy HH:mm', { locale: fr })}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title="Voir les détails">
                      <IconButton
                        size="small"
                        onClick={() => handleViewAlert(alert)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Modifier">
                      <IconButton
                        size="small"
                        onClick={() => handleEditAlert(alert)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Supprimer">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteAlert(alert.id)}
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
        <DialogTitle>Détails de l'alerte</DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedAlert.name}
              </Typography>
              
              <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mt={2}>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Type
                  </Typography>
                  <Chip
                    label={getTypeLabel(selectedAlert.alert_type)}
                    color={getTypeColor(selectedAlert.alert_type)}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Sévérité
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getSeverityIcon(selectedAlert.severity)}
                    <Chip
                      label={selectedAlert.severity.toUpperCase()}
                      color={getSeverityColor(selectedAlert.severity)}
                      size="small"
                    />
                  </Box>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Symbole
                  </Typography>
                  <Typography variant="body2">
                    {selectedAlert.symbol || '-'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Statut
                  </Typography>
                  <Chip
                    label={selectedAlert.is_active ? 'ACTIVE' : 'INACTIVE'}
                    color={selectedAlert.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Déclenchée
                  </Typography>
                  <Typography variant="body2">
                    {selectedAlert.triggered_count} fois
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Dernière fois
                  </Typography>
                  <Typography variant="body2">
                    {selectedAlert.last_triggered 
                      ? format(new Date(selectedAlert.last_triggered), 'dd/MM/yyyy HH:mm:ss', { locale: fr })
                      : 'Jamais'
                    }
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Cooldown
                  </Typography>
                  <Typography variant="body2">
                    {selectedAlert.cooldown_seconds} secondes
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">
                    Créée le
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(selectedAlert.created_at), 'dd/MM/yyyy HH:mm:ss', { locale: fr })}
                  </Typography>
                </Box>
              </Box>

              <Box mt={2}>
                <Typography variant="subtitle2" color="textSecondary">
                  Condition
                </Typography>
                <Paper sx={{ p: 2, mt: 1, bgcolor: 'grey.50' }}>
                  <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                    {JSON.stringify(selectedAlert.condition, null, 2)}
                  </pre>
                </Paper>
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

      {/* Dialog de création */}
      <Dialog
        open={showCreateDialog}
        onClose={() => setShowCreateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Nouvelle Alerte</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              label="Nom de l'alerte"
              value={newAlert.name}
              onChange={(e) => setNewAlert(prev => ({ ...prev, name: e.target.value }))}
              fullWidth
              margin="normal"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Type</InputLabel>
              <Select
                value={newAlert.alert_type}
                onChange={(e) => setNewAlert(prev => ({ ...prev, alert_type: e.target.value as any }))}
                label="Type"
              >
                <MenuItem value="price">Prix</MenuItem>
                <MenuItem value="volume">Volume</MenuItem>
                <MenuItem value="risk">Risque</MenuItem>
                <MenuItem value="system">Système</MenuItem>
                <MenuItem value="trading">Trading</MenuItem>
                <MenuItem value="performance">Performance</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Sévérité</InputLabel>
              <Select
                value={newAlert.severity}
                onChange={(e) => setNewAlert(prev => ({ ...prev, severity: e.target.value as any }))}
                label="Sévérité"
              >
                <MenuItem value="low">Faible</MenuItem>
                <MenuItem value="medium">Moyenne</MenuItem>
                <MenuItem value="high">Élevée</MenuItem>
                <MenuItem value="critical">Critique</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Symbole (optionnel)"
              value={newAlert.symbol || ''}
              onChange={(e) => setNewAlert(prev => ({ ...prev, symbol: e.target.value }))}
              fullWidth
              margin="normal"
            />
            <TextField
              label="Cooldown (secondes)"
              type="number"
              value={newAlert.cooldown_seconds}
              onChange={(e) => setNewAlert(prev => ({ ...prev, cooldown_seconds: parseInt(e.target.value) }))}
              fullWidth
              margin="normal"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={newAlert.is_active}
                  onChange={(e) => setNewAlert(prev => ({ ...prev, is_active: e.target.checked }))}
                />
              }
              label="Alerte active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDialog(false)}>
            Annuler
          </Button>
          <Button 
            onClick={handleCreateAlert}
            variant="contained"
            disabled={createAlertMutation.loading}
          >
            {createAlertMutation.loading ? 'Création...' : 'Créer'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de modification */}
      <Dialog
        open={showEditDialog}
        onClose={() => setShowEditDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Modifier l'Alerte</DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box sx={{ pt: 2 }}>
              <TextField
                label="Nom de l'alerte"
                value={selectedAlert.name}
                onChange={(e) => setSelectedAlert(prev => prev ? { ...prev, name: e.target.value } : null)}
                fullWidth
                margin="normal"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Type</InputLabel>
                <Select
                  value={selectedAlert.alert_type}
                  onChange={(e) => setSelectedAlert(prev => prev ? { ...prev, alert_type: e.target.value as any } : null)}
                  label="Type"
                >
                  <MenuItem value="price">Prix</MenuItem>
                  <MenuItem value="volume">Volume</MenuItem>
                  <MenuItem value="risk">Risque</MenuItem>
                  <MenuItem value="system">Système</MenuItem>
                  <MenuItem value="trading">Trading</MenuItem>
                  <MenuItem value="performance">Performance</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth margin="normal">
                <InputLabel>Sévérité</InputLabel>
                <Select
                  value={selectedAlert.severity}
                  onChange={(e) => setSelectedAlert(prev => prev ? { ...prev, severity: e.target.value as any } : null)}
                  label="Sévérité"
                >
                  <MenuItem value="low">Faible</MenuItem>
                  <MenuItem value="medium">Moyenne</MenuItem>
                  <MenuItem value="high">Élevée</MenuItem>
                  <MenuItem value="critical">Critique</MenuItem>
                </Select>
              </FormControl>
              <TextField
                label="Symbole (optionnel)"
                value={selectedAlert.symbol || ''}
                onChange={(e) => setSelectedAlert(prev => prev ? { ...prev, symbol: e.target.value } : null)}
                fullWidth
                margin="normal"
              />
              <TextField
                label="Cooldown (secondes)"
                type="number"
                value={selectedAlert.cooldown_seconds}
                onChange={(e) => setSelectedAlert(prev => prev ? { ...prev, cooldown_seconds: parseInt(e.target.value) } : null)}
                fullWidth
                margin="normal"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={selectedAlert.is_active}
                    onChange={(e) => setSelectedAlert(prev => prev ? { ...prev, is_active: e.target.checked } : null)}
                  />
                }
                label="Alerte active"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowEditDialog(false)}>
            Annuler
          </Button>
          <Button 
            onClick={handleUpdateAlert}
            variant="contained"
            disabled={updateAlertMutation.loading}
          >
            {updateAlertMutation.loading ? 'Mise à jour...' : 'Mettre à jour'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AlertsManager;